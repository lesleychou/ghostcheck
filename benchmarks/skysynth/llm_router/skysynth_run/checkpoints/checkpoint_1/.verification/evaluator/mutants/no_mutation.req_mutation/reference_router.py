"""The TRUSTED REFERENCE for this run: the pass oracle every kept test is validated against.

Two parts, and no third:

1. `ReferenceRouter.decide` is `evaluator/reference_router.py` from the task root, verbatim
   (task.md: "Every test must pass evaluator/reference_router.py"). Requested model, first
   provider in fleet-view order that stocks it, retry via the harness's own wake-ups, never
   sheds, no affinity, no pacing. Slow and expensive on purpose. Not one byte of placement
   policy is added here, so the decision stream of this reference is the shipped one.

2. `incident(req_id)` is the operator-observability extension adopted by decision-log row
   `observability-extension` and stated by cards/properties.json `operator_observability`:
   the shipped Router interface has no output channel, so the shipped reference cannot satisfy
   the positive half of that class. Both delivered routers expose

       incident(req_id) -> {"provider": str|None, "model": str|None,
                            "attempts": int, "errors": [(kind, now_ms), ...]} | None

   written here FROM THE SPECIFICATION, never from the candidate.

   DECLARED RETENTION BOUND. At most RETENTION = 2048 request records are kept, evicted
   strictly oldest-first by insertion order, and each record's `errors` list keeps at most
   ERRORS_PER_REQ = 32 entries (the most recent, again oldest-first). The retained footprint
   is therefore O(RETENTION * ERRORS_PER_REQ), a constant that does not grow with how many
   requests the router has served -- which is exactly what `bounded_router_memory` bounds.
   `incident()` returns None both for a req_id the router never saw and for one whose record
   has aged out of that bound; the bound is the contract, the table is not.

   The record is what the ROUTER did (where it sent the request, how many times it tried, and
   the typed reason each attempt failed). It is never accounting: quality, cost, tokens and
   SLO come from the harness's books alone, and nothing here is published to the harness.
"""

import os
import sys

try:  # the suite and the benchmark both put the vendored harness package on sys.path
    from evaluator.router_interface import Action, Router
except ImportError:  # pragma: no cover - a bare $SKYDISCOVER_INTERFACE directory
    _iface = os.environ.get("SKYDISCOVER_INTERFACE")
    if _iface and _iface not in sys.path:
        sys.path.insert(0, _iface)
    from router_interface import Action, Router  # type: ignore[no-redef]


class ReferenceRouter(Router):
    # Declared retention bound (see the module docstring). Constant, not per-request.
    RETENTION = 2048
    ERRORS_PER_REQ = 32

    def __init__(self):
        # insertion-ordered: the oldest key is the first key, so eviction is O(1) and
        # deterministic. Nothing else is retained between requests.
        self._incidents = {}

    # ---- MUTANT: it edits the request it was handed ------------------------------------
    # THE ONE DEFECT, and nothing else: the copy strikes the model it just placed out of
    # req.equiv_class, "so the retry does not pick it again". Placement is byte-for-byte the
    # trusted reference's; only the read-only contract on the Request is broken, which the
    # harness types as req_mutation (replay_tenants.py guard()).
    def decide(self, req, now_ms, fleet_view):
        for name, view in fleet_view.items():
            if req.model_requested in view["models"]:
                if req.model_requested in req.equiv_class:
                    req.equiv_class.remove(req.model_requested)
                self._note_dispatch(req.req_id, name, req.model_requested)
                return Action("dispatch", provider=name, model=req.model_requested)
        return Action("defer", until_ms=now_ms + 1000)

    # ---- the adopted observability extension ------------------------------------------
    def on_error(self, req, now_ms, kind, retry_after_ms):
        rec = self._incidents.get(req.req_id)
        if rec is None:
            return
        rec["errors"].append((kind, now_ms))
        if len(rec["errors"]) > self.ERRORS_PER_REQ:
            del rec["errors"][: len(rec["errors"]) - self.ERRORS_PER_REQ]

    def incident(self, req_id):
        """What the router did with req_id, or None if it never saw it (or the record has
        aged out of the declared retention bound). A copy: the caller cannot reach in."""
        rec = self._incidents.get(req_id)
        if rec is None:
            return None
        return {
            "provider": rec["provider"],
            "model": rec["model"],
            "attempts": rec["attempts"],
            "errors": list(rec["errors"]),
        }

    def _note_dispatch(self, req_id, provider, model):
        rec = self._incidents.get(req_id)
        if rec is None:
            rec = self._incidents[req_id] = {
                "provider": None,
                "model": None,
                "attempts": 0,
                "errors": [],
            }
            while len(self._incidents) > self.RETENTION:
                self._incidents.pop(next(iter(self._incidents)))
        rec["provider"] = provider
        rec["model"] = model
        rec["attempts"] += 1
