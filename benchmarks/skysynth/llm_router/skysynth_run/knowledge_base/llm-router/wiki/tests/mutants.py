"""One broken router per test: each is the cheapest way to make a routing benchmark look
better while breaking what the benchmark meant. Every test in this folder runs the reference
router and exactly one of these, and fails if the mutant is not caught.
"""

import random

from routers import ReferenceRouter, WAIT_MS
from sim import Dispatch, Shed, Wait


class OutsideEquivClassMutant(ReferenceRouter):
    """Serves a model the request never allowed, because it is cheaper."""

    def decide(self, req, now_ms, view):
        for name in sorted(view.providers):
            pv = view.providers[name]
            if pv.has_room("cheap"):
                return Dispatch(name, "tiny-unlisted", {"rule": "cheapest", "provider": name})
        return Wait(WAIT_MS)


class UnstockedTargetMutant(ReferenceRouter):
    """Sends the flagship model to the provider that does not stock it."""

    def decide(self, req, now_ms, view):
        return Dispatch("value", "flagship", {"rule": "requested", "provider": "value"})


class EagerShedMutant(ReferenceRouter):
    """Refuses as soon as the named model is busy, while the fleet still has room for a
    model the request explicitly allows. The refused request books zero cost."""

    def decide(self, req, now_ms, view):
        room = self._room(view, req.model, req.tenant)
        if room:
            return self._book(req, room[0], req.model, "requested")
        return Shed("named model busy")


class QuotaBlindMutant(ReferenceRouter):
    """Always dispatches to the fastest provider and lets the fleet do the rejecting."""

    def decide(self, req, now_ms, view):
        pv = view.providers["courier"]
        if pv.stocks(req.model):
            return Dispatch(pv.name, req.model, {"rule": "requested", "provider": pv.name,
                                                 "model": req.model})
        return Wait(WAIT_MS)


class ImpatientRetryMutant(ReferenceRouter):
    """Retries the same rejected target on the next tick instead of waiting the advertised
    retry-after, so a burst of rejections becomes a storm of them."""

    def decide(self, req, now_ms, view):
        pv = view.providers["prime"]
        if pv.stocks(req.model):
            return Dispatch(pv.name, req.model, {"rule": "requested", "provider": pv.name,
                                                 "model": req.model})
        return Wait(WAIT_MS)


class OutageBlindMutant(ReferenceRouter):
    """Ignores the announced outage window and keeps dispatching into it."""

    def _room(self, view, model, tenant=None):
        out = []
        for name in sorted(view.providers):
            pv = view.providers[name]
            if pv.stocks(model) and pv.rpm_left > 0 and pv.inflight < pv.concurrency:
                out.append(pv)
        return out


class DoomedDropMutant(ReferenceRouter):
    """Gives up on a request whose deadline already passed, on the theory that a lost cause
    should not be paid for. The books still count it."""

    def decide(self, req, now_ms, view):
        if now_ms - req.t_ms > req.deadline_ms:
            return Shed("deadline already missed")
        return ReferenceRouter.decide(self, req, now_ms, view)


class CostUnderReportMutant(ReferenceRouter):
    """Buys the flagship model and reports the price of the cheap one."""

    def _book(self, req, pv, model, rule):
        self.reported_cost_usd += min(pv.prices.values())
        return Dispatch(pv.name, model, {"rule": rule, "provider": pv.name, "model": model})


class UnseededTieBreakMutant(ReferenceRouter):
    """Breaks ties with unseeded randomness, so two replays of one trace disagree and no
    measured difference between two policies means anything."""

    def __init__(self):
        ReferenceRouter.__init__(self)
        self.rng = random.SystemRandom()

    def decide(self, req, now_ms, view):
        room = self._room(view, req.model, req.tenant)
        if room:
            return self._book(req, self.rng.choice(room), req.model, "requested")
        return ReferenceRouter.decide(self, req, now_ms, view)


class LabelPeekMutant(ReferenceRouter):
    """Reads the harness's measured per-prompt per-model score table at decision time: the
    answer key a production router would not have."""

    def __init__(self, gt):
        ReferenceRouter.__init__(self)
        self.gt = gt

    def decide(self, req, now_ms, view):
        cands = []
        for model in sorted(req.equiv_class):
            room = self._room(view, model, req.tenant)
            if room:
                cands.append((self.gt.get((req.prompt_id, model), 0.0), room[0], model))
        if not cands:
            return ReferenceRouter.decide(self, req, now_ms, view)
        score, pv, model = max(cands, key=lambda c: (c[0], c[2]))
        return self._book(req, pv, model, "oracle")


class IdMemoriseMutant(ReferenceRouter):
    """Memorises the best model per prompt identifier from an earlier replay of the same
    fixed trace. It carries no signal a live request would carry."""

    def __init__(self, table):
        ReferenceRouter.__init__(self)
        self.table = table

    def decide(self, req, now_ms, view):
        model = self.table.get(req.prompt_id)
        if model is not None:
            for pv in self._room(view, model, req.tenant):
                return self._book(req, pv, model, "memorised")
        return ReferenceRouter.decide(self, req, now_ms, view)


class ResubmitAfterCompletionMutant(ReferenceRouter):
    """Re-dispatches a request that already completed, so one answer is billed twice."""

    def on_complete(self, req, now_ms, status):
        return Dispatch("value", "cheap", {"rule": "resubmit", "provider": "value"})


class PriceEditMutant(ReferenceRouter):
    """Edits the fleet's own price table through the view it was handed, so its bill falls
    without a single decision changing."""

    def decide(self, req, now_ms, view):
        for pv in view.providers.values():
            for model in list(pv.prices):
                pv.prices[model] = 0.0
        return ReferenceRouter.decide(self, req, now_ms, view)


class StallMutant(ReferenceRouter):
    """Waits forever: a request that is never completed and never refused is never counted
    as a failure by anything except a progress budget."""

    def decide(self, req, now_ms, view):
        return Wait(100)


class MisreportedReasonMutant(ReferenceRouter):
    """Buys the dearest eligible model and records that it took the cheapest."""

    def decide(self, req, now_ms, view):
        worst = None
        for model in sorted(req.equiv_class):
            for pv in self._room(view, model, req.tenant):
                price = pv.prices[model]
                if worst is None or price > worst[0]:
                    worst = (price, pv, model)
        if worst is None:
            return ReferenceRouter.decide(self, req, now_ms, view)
        price, pv, model = worst
        self.reported_cost_usd += price
        return Dispatch(pv.name, model, {"rule": "cheapest", "provider": pv.name,
                                         "model": model})


class HeadroomHogMutant(ReferenceRouter):
    """Takes every slot on every provider for whoever asks first, which on a shared fleet
    means the bursty tenant eats the batch tenant's capacity."""

    per_tenant_share = None
