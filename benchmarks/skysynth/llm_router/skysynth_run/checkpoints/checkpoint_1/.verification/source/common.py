"""Two specialist LLM routers on one shared 3-provider / 12-model fleet.

Candidate C0, bootstrap instance (synthesis/plan.md `## Brief`). The smallest complete pair that
compiles, honours every declared correctness class, and produces a first honest train score. It
is not meant to win yet.

The spine, shared by both tenants
---------------------------------
Every request is a free choice among the legal (provider, model) placements. `decide()` is

    1. HARD FILTER   provider is up (non-empty catalogue, no published `outage_until`), stocks
                     the model, the model is a legal substitution, `rpm_left >= 1`,
                     `tpm_left >= prompt + expected_output`, `inflight < the card's concurrency
                     cap` (concurrency is public spec, not published live), and the request's
                     deadline is still reachable at that placement's published latency.
    2. SOFT RANK     argmax over `qhat[model] - LAM * cost(provider, model, request)`, with the
                     dollars computed exactly from the provider's published per-token prices and
                     the request's own token counts -- there is no estimation error in the cost
                     term. Ties break on (provider name, model name), both iterated in sorted
                     order, so the decision stream is a pure function of the inputs.
    3. RELAX / WAIT  if the deadline filter emptied the set, rank the capacity-eligible set
                     anyway (the request must still complete); if that is empty too, DEFER with
                     a tenant-sized backoff.

    NEVER SHED. A shed books zero quality AND counts as an SLO violation
    (replay_tenants.py:483, :493), so it is strictly dominated on every axis and is only ever a
    correctness risk (`illegal_shed`). These routers return "dispatch" or "defer", never "shed".

What the router is allowed to read
----------------------------------
`req.features`, `req.cls`, the token counts, `req.slo`, `req.model_requested`, `req.equiv_class`,
`req.downgrade_ok`, `req.retry_safe`, `req.session_id`, `req.prefix_id`, `now_ms`, and the fleet
view. It NEVER reads `req.quality`, and it never joins `req.features['prompt_id']` against any
ground-truth score matrix. The quality estimate comes from `generic_predictions.json`, the
Qwen2.5-0.5B + per-model Ridge(alpha=10) head fit on the merged TRAIN matrices that the shipped
baseline itself reads (generic_policy.py:42,:60; decision row `ridge-head-in-bounds`). That is a
generalizing estimator keyed by prompt text, not a label lookup.

Outage handling is driven only by the fleet view's published signal -- an empty `models`
catalogue plus an `outage_until` ETA. No absolute trace position, no literal window constants.

Memory
------
Everything retained across requests carries an explicit capacity:

  * the prediction head: a module-level, read-only, FIXED-SIZE table (8136 prompt ids x 12
    models), loaded once at import and shared by reference by every instance. It is a constant,
    not an accumulator.
  * `_live`      <= LIVE_CAPACITY     in-flight decision records, popped in `on_complete()`
  * `_incidents` <= INCIDENT_CAPACITY completed records that saw a retry (FIFO eviction)
  * `_recent`    <= RECENT_CAPACITY   most recent completed records (FIFO eviction)
  * each record's `errors` list       <= MAX_ERRORS_PER_REQUEST entries

so the retained footprint after 4x the traffic is the footprint after the first quarter.
`incident(req_id)` reads those three maps; that bound IS the observability retention bound
(decision row `observability-extension`).
"""

import json
import os
import sys
from collections import OrderedDict

_HERE = os.path.dirname(os.path.abspath(__file__))
_SYNTH = os.path.dirname(_HERE)


# --------------------------------------------------------------------------------------------
# interface binding
#
# Bind to whichever `evaluator.router_interface` is already on sys.path -- the kept tests and the
# benchmark each vendor their own copy of the harness package and put it on sys.path before
# importing the candidate, and the routers must subclass THAT `Router`. Only if no such package
# is importable do we load the published contract by file path.
# --------------------------------------------------------------------------------------------
def _load_interface():
    try:
        from evaluator.router_interface import Action, Request, Router  # noqa: F401

        return Action, Request, Router
    except Exception:
        pass
    import importlib.util

    candidates = [
        os.environ.get("SKYDISCOVER_ROUTER_INTERFACE"),
        os.path.join(_SYNTH, "evaluator", "interface", "router_interface.py"),
        os.path.join(
            _SYNTH, "evaluator", "benchmark", "vendor", "evaluator", "router_interface.py"
        ),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            spec = importlib.util.spec_from_file_location("_skydiscover_router_interface", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            return mod.Action, mod.Request, mod.Router
    raise ImportError(
        "router_interface.py not found; set SKYDISCOVER_ROUTER_INTERFACE or put the "
        "evaluator package on sys.path"
    )


Action, Request, Router = _load_interface()


# --------------------------------------------------------------------------------------------
# frozen public artifacts, loaded once at import
# --------------------------------------------------------------------------------------------
def _first_existing(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


_PRED_PATH = _first_existing(
    os.environ.get("SKYDISCOVER_PREDICTIONS"),
    os.path.join(_HERE, "artifacts", "generic_predictions.json"),
    os.path.join(
        _SYNTH,
        "evaluator",
        "benchmark",
        "vendor",
        "evaluator",
        "benchmark",
        "artifacts",
        "generic_predictions.json",
    ),
)
_CARD_PATH = _first_existing(
    os.environ.get("SKYDISCOVER_ENV_CARD"),
    os.path.join(_HERE, "artifacts", "env_card.yaml"),
    os.path.join(
        _SYNTH, "evaluator", "benchmark", "vendor", "evaluator", "benchmark", "env_card.yaml"
    ),
)

# The frozen, public per-provider service spec: (ttft_base_ms, prefill_tps, decode_tps,
# concurrency). Read from the env card when one is reachable; these are the fallback values, and
# they are spec, not tuning -- concurrency in particular is a standing published cap that the
# fleet view does not republish (the shipped baseline reads exactly the same four fields,
# generic_policy.py:44-49).
_FALLBACK_SPEC = {
    "value": (700.0, 25000.0, 70.0, 96),
    "prime": (400.0, 60000.0, 100.0, 32),
    "courier": (1700.0, 12000.0, 40.0, 48),
}


def _load_head(path):
    """The fixed-size quality head: (model -> column index, prompt_id -> [12 scores])."""
    if path is None:
        return {}, {}
    art = json.load(open(path))
    index = {m: j for j, m in enumerate(art["fleet"])}
    return index, art["pred"]


def _load_spec(path):
    if path is None:
        return dict(_FALLBACK_SPEC)
    try:
        import yaml
    except ImportError:
        return dict(_FALLBACK_SPEC)
    try:
        card = yaml.safe_load(open(path))
        spec = {}
        for name, cfg in card["providers"].items():
            spec[name] = (
                float(cfg["ttft_base_ms"]),
                float(cfg["prefill_tps"]),
                float(cfg["decode_tps"]),
                int(cfg["concurrency"]),
            )
        return spec or dict(_FALLBACK_SPEC)
    except Exception:
        return dict(_FALLBACK_SPEC)


# Module-level, read-only, constant size. Shared by reference by every router instance; nothing
# is ever written back into these.
_MODEL_INDEX, _PRED = _load_head(_PRED_PATH)
_PROVIDER_SPEC = _load_spec(_CARD_PATH)

_UNKNOWN_SPEC = (1000.0, 20000.0, 40.0, 10**9)


class BudgetedJointRouter(Router):
    """The shared C0 spine. Subclasses set the tenant-specific knobs and nothing else."""

    # --- tenant knobs -------------------------------------------------------------------
    TENANT = None
    LAM = 3.0  # dollars-to-quality shadow price; 3.0 is U's own weight
    DEFER_MS = 1000  # backoff when nothing is eligible
    TTFT_MARGIN_MS = 0.0  # headroom the deadline filter keeps in reserve (C1 knob)
    E2E_MARGIN_MS = 0.0

    # --- progress ladder ----------------------------------------------------------------
    # A request that can never find capacity must not defer forever (that is a `lost_request`).
    # After MAX_DEFERS quiet rounds we force the best structurally-legal placement for at most
    # MAX_FORCED attempts, then hand the request back to the harness's own liveness machinery.
    MAX_DEFERS = 24
    MAX_FORCED = 6

    # --- declared retention bounds ------------------------------------------------------
    LIVE_CAPACITY = 1024
    INCIDENT_CAPACITY = 256
    RECENT_CAPACITY = 256
    MAX_ERRORS_PER_REQUEST = 16

    def __init__(self):
        self.model_index = _MODEL_INDEX  # shared, constant
        self.pred = _PRED  # shared, constant, 8136 x 12
        self.spec = _PROVIDER_SPEC  # shared, constant, 3 providers
        self._live = OrderedDict()
        self._incidents = OrderedDict()
        self._recent = OrderedDict()

    # ---------------------------------------------------------------- bounded bookkeeping
    def _put(self, store, cap, key, value):
        if key in store:
            del store[key]
        store[key] = value
        while len(store) > cap:
            store.popitem(last=False)

    def _touch(self, req_id):
        rec = self._live.get(req_id)
        if rec is None:
            rec = {
                "provider": None,
                "model": None,
                "attempts": 0,
                "errors": [],
                "defers": 0,
            }
            self._put(self._live, self.LIVE_CAPACITY, req_id, rec)
        return rec

    # ---------------------------------------------------------------------- legal choices
    def _allowed(self, req):
        """{model_requested} plus equiv_class when downgrade_ok -- exactly what the harness
        accepts (replay_tenants.py:310-314). Never mutates the request's own list."""
        allowed = set()
        if req.model_requested:
            allowed.add(req.model_requested)
        if req.downgrade_ok and req.equiv_class:
            allowed.update(req.equiv_class)
        return allowed

    # ------------------------------------------------------------------------------ costs
    @staticmethod
    def _dollars(price, fresh, cached, out_tokens):
        return (
            fresh * float(price.get("in", 0.0))
            + cached * float(price.get("cached", price.get("in", 0.0)))
            + out_tokens * float(price.get("out", 0.0))
        ) / 1e6

    def _deadline_ok(self, req, now_ms, pname, price, fresh, cached):
        slo = req.slo or {}
        if not slo:
            return True
        base, prefill, dec_default, _cap = self.spec.get(pname, _UNKNOWN_SPEC)
        prefill = prefill if prefill > 0 else 1.0
        prefill_ms = fresh / prefill * 1000.0 + cached / (prefill * 8.0) * 1000.0
        ttft = base + float(price.get("ttft_extra_ms", 0.0)) + prefill_ms
        elapsed = now_ms - req.t_ms
        limit = slo.get("ttft_ms")
        if limit is not None and elapsed + ttft > float(limit) - self.TTFT_MARGIN_MS:
            return False
        limit = slo.get("latency_ms")
        if limit is not None:
            dec = float(price.get("decode_tps", dec_default)) or 1.0
            total = ttft + (req.expected_output_tokens or 0) / dec * 1000.0
            if elapsed + total > float(limit) - self.E2E_MARGIN_MS:
                return False
        return True

    # ----------------------------------------------------------------------------- decide
    def decide(self, req, now_ms, fleet_view):
        rec = self._touch(req.req_id)
        allowed = self._allowed(req)

        preds = None
        pid = (req.features or {}).get("prompt_id")
        if pid is not None:
            preds = self.pred.get(pid)
        if preds is None:
            # No estimate for this prompt: honour what the caller asked for and place it on
            # price alone. (Never a ground-truth lookup; this is the documented fallback.)
            allowed = {req.model_requested} if req.model_requested else set()

        prompt_tokens = max(int(req.prompt_tokens or 0), 0)
        out_tokens = max(int(req.expected_output_tokens or 0), 0)
        window_tokens = prompt_tokens + out_tokens

        best_deadline = None  # capacity-eligible AND deadline-reachable
        best_capacity = None  # capacity-eligible
        best_legal = None  # provider up and stocking a legal model, capacity ignored

        for pname in sorted(fleet_view):
            view = fleet_view[pname] or {}
            models = view.get("models") or {}
            if not models or view.get("outage_until") is not None:
                continue  # announced outage: empty catalogue + ETA. Route around it.
            warm = False
            hp = view.get("has_prefix")
            if callable(hp) and req.prefix_id is not None:
                try:
                    warm = bool(hp(req.prefix_id))
                except Exception:
                    warm = False
            cached = min(max(int(req.prefix_tokens or 0), 0), prompt_tokens) if warm else 0
            fresh = prompt_tokens - cached

            cap_ok = (
                view.get("rpm_left", 0) >= 1
                and view.get("tpm_left", 0) >= window_tokens
                and view.get("inflight", 0) < self.spec.get(pname, _UNKNOWN_SPEC)[3]
            )

            for model in sorted(models):
                if model not in allowed:
                    continue
                price = models[model] or {}
                qhat = 0.0
                if preds is not None:
                    j = self.model_index.get(model)
                    if j is not None and j < len(preds):
                        qhat = float(preds[j])
                score = qhat - self.LAM * self._dollars(price, fresh, cached, out_tokens)
                choice = (score, pname, model)
                if best_legal is None or score > best_legal[0]:
                    best_legal = choice
                if cap_ok:
                    if best_capacity is None or score > best_capacity[0]:
                        best_capacity = choice
                    if self._deadline_ok(req, now_ms, pname, price, fresh, cached):
                        if best_deadline is None or score > best_deadline[0]:
                            best_deadline = choice

        pick = best_deadline or best_capacity
        if pick is None:
            rec["defers"] += 1
            if self.MAX_DEFERS < rec["defers"] <= self.MAX_DEFERS + self.MAX_FORCED:
                pick = best_legal
            if pick is None:
                return Action("defer", until_ms=now_ms + self.DEFER_MS)

        rec["attempts"] += 1
        rec["provider"] = pick[1]
        rec["model"] = pick[2]
        return Action("dispatch", provider=pick[1], model=pick[2])

    # ------------------------------------------------------------------------- informational
    def on_error(self, req, now_ms, kind, retry_after_ms):
        rec = self._touch(req.req_id)
        errors = rec["errors"]
        errors.append((str(kind), int(now_ms)))
        if len(errors) > self.MAX_ERRORS_PER_REQUEST:
            del errors[0 : len(errors) - self.MAX_ERRORS_PER_REQUEST]

    def on_complete(self, req, now_ms):
        rec = self._live.pop(req.req_id, None)
        if rec is not None:
            if rec["attempts"] >= 2 or rec["errors"]:
                self._put(self._incidents, self.INCIDENT_CAPACITY, req.req_id, rec)
            self._put(self._recent, self.RECENT_CAPACITY, req.req_id, rec)
        return None  # returning an Action here would re-enter the harness and double-bill

    # ------------------------------------------------------------------------ observability
    def incident(self, req_id):
        """What an operator can recover about one request: the provider and model it ended on,
        how many dispatch attempts it took, and the typed reason each earlier attempt failed.

        Retention is bounded and declared: in-flight records (<= LIVE_CAPACITY), then the last
        INCIDENT_CAPACITY completed records that saw a retry, then the last RECENT_CAPACITY
        completed records. Outside that window this returns None, as it does for an id the
        router never saw. Nothing here is accounting: quality, cost, tokens and SLO come from
        the harness's books alone and are not reported by the router at all.
        """
        for store in (self._live, self._incidents, self._recent):
            rec = store.get(req_id)
            if rec is not None:
                return {
                    "provider": rec["provider"],
                    "model": rec["model"],
                    "attempts": rec["attempts"],
                    "errors": list(rec["errors"]),
                }
        return None


class TenantARouter(BudgetedJointRouter):
    """Tenant A, "interactive analyst": 2.5 s TTFT from arrival on 100% of rows, 100% streaming,
    bursty diurnal arrivals. The whole budget is 2500 ms, so deferral is measured in tens of
    milliseconds and the deadline filter scores time-to-first-token.
    """

    TENANT = "A"
    LAM = 3.0
    DEFER_MS = 50


class TenantBRouter(BudgetedJointRouter):
    """Tenant B, "batch reasoning": 600 s end-to-end on 100% of rows, arriving in five waves
    separated by minutes of silence. There is no latency pressure, so the deadline filter scores
    end-to-end (ttft + decode) and deferral in the seconds is correct.
    """

    TENANT = "B"
    LAM = 3.0
    DEFER_MS = 2000
