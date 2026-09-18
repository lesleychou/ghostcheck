"""A miniature of the two-tenant replay: enough fleet, clock and books to make one
routing invariant executable and to let a broken router violate it.

It is deliberately small and deliberately not the task harness. What it copies from the
real thing is the part every test here depends on:

  * the harness owns the clock, the capacity, the ledger and the quality table;
  * the router owns only policy and never reports a number that counts;
  * every finished request is completed exactly once or refused exactly once;
  * an illegal action is a typed violation, not a bad score.

One deviation is on purpose: the fleet view handed to the router aliases the fleet's own
price tables instead of copying them, so a router that edits its own bill can be written
and then caught. The real harness passes a snapshot by value, which is the fix.
"""

import hashlib
import json
import random
from dataclasses import dataclass, field

TICK_MS = 100
RETRY_AFTER_MS = 2000
RPM_WINDOW_MS = 60_000
MAX_DECISIONS = 64
OUTAGE_GRACE = 4


# ---------------------------------------------------------------- actions


@dataclass
class Dispatch:
    provider: str
    model: str
    reason: dict = field(default_factory=dict)


@dataclass
class Wait:
    ms: int = TICK_MS


@dataclass
class Shed:
    reason: str = ""


# ---------------------------------------------------------------- fleet


@dataclass
class Provider:
    name: str
    prices: dict          # model -> dollars per request
    rpm: int
    concurrency: int
    speed: float = 1.0    # multiplies each model's base service time
    outages: tuple = ()   # (start_ms, end_ms) windows announced in advance

    def stocks(self, model):
        return model in self.prices

    def down_until(self, now):
        for start, end in self.outages:
            if start <= now < end:
                return end
        return None


@dataclass
class Fleet:
    providers: dict           # name -> Provider
    base_service_ms: dict     # model -> service time on a speed 1.0 provider

    def checksum(self):
        blob = {
            p.name: [sorted(p.prices.items()), p.rpm, p.concurrency, p.speed, list(p.outages)]
            for p in self.providers.values()
        }
        blob["base_service_ms"] = sorted(self.base_service_ms.items())
        return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


@dataclass
class ProviderView:
    """What the router may look at. `prices` aliases the fleet table on purpose."""

    name: str
    prices: dict
    rpm_left: int
    inflight: int
    concurrency: int
    down_until_ms: int = None
    retry_after_ms: int = RETRY_AFTER_MS

    def stocks(self, model):
        return model in self.prices

    def has_room(self, model):
        return (
            self.stocks(model)
            and self.down_until_ms is None
            and self.rpm_left > 0
            and self.inflight < self.concurrency
        )


@dataclass
class FleetView:
    now_ms: int
    providers: dict  # name -> ProviderView


# ---------------------------------------------------------------- requests


@dataclass
class Request:
    rid: int
    t_ms: int
    tenant: str
    model: str            # the model the caller named
    equiv_class: tuple    # the models that may serve it instead
    deadline_ms: int      # relative to arrival
    prompt_id: str
    features: dict        # what a production request carries: no quality label
    retry_safe: bool = True


# ---------------------------------------------------------------- the run


@dataclass
class Entry:
    rid: int
    tenant: str
    status: str = "open"   # open | completed | shed | lost
    provider: str = None
    model: str = None
    billed: float = 0.0
    quality: float = 0.0
    finish_ms: int = None
    slo_ok: bool = False
    attempts: int = 0
    rejections: int = 0
    decisions: int = 0


@dataclass
class Run:
    entries: dict = field(default_factory=dict)
    violations: list = field(default_factory=list)
    dispatch_log: list = field(default_factory=list)   # (rid, provider, model)
    reason_log: list = field(default_factory=list)     # (rid, provider, model, reason)
    early_retries: int = 0
    quota_rejections: int = 0
    outage_rejections: int = 0
    fleet_checksum_before: str = ""
    fleet_checksum_after: str = ""

    # ---- the books. Everything scored is read from here, never from the router.
    def n(self):
        return len(self.entries)

    def billed_total(self):
        return sum(e.billed for e in self.entries.values())

    def cost_per_request(self):
        return self.billed_total() / max(1, self.n())

    def mean_quality(self):
        return sum(e.quality for e in self.entries.values()) / max(1, self.n())

    def slo_violation_rate(self, tenant=None):
        rows = [e for e in self.entries.values() if tenant is None or e.tenant == tenant]
        if not rows:
            return 0.0
        # a refused, lost or late request is a violation. Dropping hard traffic cannot help.
        return sum(0 if (e.status == "completed" and e.slo_ok) else 1 for e in rows) / len(rows)

    def utility(self, tenant=None):
        rows = [e for e in self.entries.values() if tenant is None or e.tenant == tenant]
        if not rows:
            return 0.0
        q = sum(e.quality for e in rows) / len(rows)
        c = sum(e.billed for e in rows) / len(rows)
        return q - 1.0 * self.slo_violation_rate(tenant) - 3.0 * c

    def served_share(self, tenant):
        rows = [e for e in self.entries.values() if e.tenant == tenant]
        if not rows:
            return 1.0
        return sum(1 for e in rows if e.status == "completed" and e.slo_ok) / len(rows)


# ---------------------------------------------------------------- ground truth


def ground_truth(prompt_ids, models, seed=7):
    """The measured per-prompt per-model score table. The harness owns it; a production
    router never sees it, which is why the tests permute it to catch one that peeked."""
    rng = random.Random(seed)
    return {(p, m): round(rng.random(), 4) for p in prompt_ids for m in models}


# ---------------------------------------------------------------- the harness


class Violation(Exception):
    """An illegal action. It carries the books as they stood, so a test can read them."""

    def __init__(self, message, run=None):
        Exception.__init__(self, message)
        self.run = run


def _view(fleet, now, sent, inflight):
    pv = {}
    for name, p in sorted(fleet.providers.items()):
        recent = sum(1 for t in sent[name] if t > now - RPM_WINDOW_MS)
        pv[name] = ProviderView(
            name=name,
            prices=p.prices,  # aliased on purpose, see module docstring
            rpm_left=max(0, p.rpm - recent),
            inflight=len(inflight[name]),
            concurrency=p.concurrency,
            down_until_ms=p.down_until(now),
        )
    return FleetView(now_ms=now, providers=pv)


def replay(fleet, requests, gt, router, horizon_ms=None):
    """Run one trace against one router and return the books."""
    run = Run(fleet_checksum_before=fleet.checksum())
    sent = {n: [] for n in fleet.providers}
    inflight = {n: [] for n in fleet.providers}  # (finish_ms, rid, model, price)
    pend = {}
    for r in requests:
        run.entries[r.rid] = Entry(rid=r.rid, tenant=r.tenant)
        pend[r.rid] = {
            "req": r,
            "next_ms": r.t_ms,
            "outage_hits": 0,
            "last_reject": {},  # target -> (t, retry_after)
        }
    horizon = horizon_ms or (max(r.t_ms for r in requests) + 600_000)
    by_rid = {r.rid: r for r in requests}

    now = 0
    while now <= horizon and any(e.status == "open" for e in run.entries.values()):
        # 1. completions the fleet books itself
        for name in fleet.providers:
            done = [a for a in inflight[name] if a[0] <= now]
            inflight[name] = [a for a in inflight[name] if a[0] > now]
            for finish, rid, model, price in done:
                e = run.entries[rid]
                if e.status != "open":
                    run.violations.append(f"double_completion:{rid}")
                    raise Violation(f"request {rid} completed twice", run)
                e.status = "completed"
                e.provider, e.model = name, model
                e.billed += price
                e.quality = gt[(by_rid[rid].prompt_id, model)]
                e.finish_ms = finish
                e.slo_ok = (finish - by_rid[rid].t_ms) <= by_rid[rid].deadline_ms
                pend.pop(rid, None)
                hook = getattr(router, "on_complete", None)
                if hook is not None:
                    act = hook(by_rid[rid], finish, e.status)
                    if isinstance(act, Dispatch):
                        run.violations.append(f"resubmit_after_completion:{rid}")
                        raise Violation(f"request {rid} was dispatched again after completing", run)

        # 2. decisions
        for rid in sorted(list(pend)):
            st = pend[rid]
            req = st["req"]
            e = run.entries[rid]
            if e.status != "open" or now < st["next_ms"]:
                continue
            e.decisions += 1
            if e.decisions > MAX_DECISIONS:
                e.status = "lost"
                run.violations.append(f"no_progress:{rid}")
                raise Violation(
                    f"request {rid} burned the decision budget without finishing", run
                )
            view = _view(fleet, now, sent, inflight)
            act = router.decide(req, now, view)

            if isinstance(act, Wait):
                st["next_ms"] = now + max(TICK_MS, int(act.ms))
                continue

            if isinstance(act, Shed):
                could = any(
                    view.providers[p].has_room(m)
                    for p in view.providers
                    for m in req.equiv_class
                )
                e.status = "shed"
                e.finish_ms = now
                pend.pop(rid, None)
                if could:
                    run.violations.append(f"illegal_shed:{rid}")
                    raise Violation(f"request {rid} was refused while the fleet had room", run)
                continue

            if not isinstance(act, Dispatch):
                raise Violation(f"request {rid}: {act!r} is not an action", run)

            # 3. a dispatch: legality first, capacity second
            if act.model not in req.equiv_class:
                run.violations.append(f"equiv_class:{rid}")
                raise Violation(
                    f"request {rid} asked for {req.model} and was served {act.model}, "
                    "which is outside its equivalence class",
                    run,
                )
            p = fleet.providers.get(act.provider)
            if p is None or not p.stocks(act.model):
                run.violations.append(f"illegal_target:{rid}")
                raise Violation(
                    f"request {rid} was dispatched to {act.provider} which does not stock "
                    f"{act.model}",
                    run,
                )
            run.reason_log.append((rid, act.provider, act.model, act.reason))

            key = (act.provider, act.model)
            last = st["last_reject"].get(key)
            if last and now < last[0] + last[1]:
                run.early_retries += 1

            down = p.down_until(now)
            if down is not None:
                st["outage_hits"] += 1
                run.outage_rejections += 1
                e.rejections += 1
                st["last_reject"][key] = (now, RETRY_AFTER_MS)
                if st["outage_hits"] > OUTAGE_GRACE:
                    e.status = "lost"
                    e.finish_ms = now
                    pend.pop(rid, None)
                    run.violations.append(f"outage_lost:{rid}")
                    raise Violation(
                        f"request {rid} kept being dispatched into an announced outage on "
                        f"{act.provider} and was lost",
                        run,
                    )
                st["next_ms"] = now + TICK_MS
                continue

            recent = sum(1 for t in sent[act.provider] if t > now - RPM_WINDOW_MS)
            if recent >= p.rpm or len(inflight[act.provider]) >= p.concurrency:
                run.quota_rejections += 1
                e.rejections += 1
                st["last_reject"][key] = (now, RETRY_AFTER_MS)
                st["next_ms"] = now + TICK_MS
                continue

            sent[act.provider].append(now)
            service = int(fleet.base_service_ms[act.model] * p.speed)
            inflight[act.provider].append((now + service, rid, act.model, p.prices[act.model]))
            run.dispatch_log.append((rid, act.provider, act.model))
            e.attempts += 1
            st["next_ms"] = now + service + TICK_MS

        now += TICK_MS

    for rid, e in run.entries.items():
        if e.status == "open":
            e.status = "lost"
            run.violations.append(f"never_finished:{rid}")
    run.fleet_checksum_after = fleet.checksum()
    if run.fleet_checksum_after != run.fleet_checksum_before:
        run.violations.append("fleet_mutated")
    return run
