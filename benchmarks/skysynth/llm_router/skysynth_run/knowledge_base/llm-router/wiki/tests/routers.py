"""The trusted-correct reference policy these tests check a mutant against.

It is slow and unimaginative on purpose: it honours the model the caller named when any
provider has room for it, substitutes only inside the request's declared equivalence class,
paces itself against published headroom, avoids an announced outage, waits when the fleet is
full, and refuses only when nothing could serve the request at all.

It keeps no cross-request state, so a replay of one trace always produces the same decisions.
`reported_cost_usd` is what the router believes it spent. Nothing scored reads it: the books
in sim.Run are the only bill.
"""

from sim import Dispatch, Shed, Wait

WAIT_MS = 500


class ReferenceRouter:
    """Correct. Deterministic: every candidate list is sorted before it is read."""

    # None means "use the whole fleet"; 0.5 means "never push a provider past half full,
    # so a sibling tenant always finds room". A pure function of the published view.
    per_tenant_share = None

    def __init__(self):
        self.reported_cost_usd = 0.0
        self._live = {}    # (tenant, provider) -> slots this router believes it holds there
        self._placed = {}  # rid -> (tenant, provider)

    # -- helpers -------------------------------------------------------
    def _room(self, view, model, tenant=None):
        out = []
        for name in sorted(view.providers):
            pv = view.providers[name]
            if pv.inflight == 0:
                # the fleet says nothing of ours is running there, so any count we kept is stale
                for key in [k for k in self._live if k[1] == name]:
                    self._live[key] = 0
            if not pv.has_room(model):
                continue
            if self.per_tenant_share is not None and tenant is not None:
                cap = max(1, int(pv.concurrency * self.per_tenant_share))
                if self._live.get((tenant, name), 0) >= cap:
                    continue
            out.append(pv)
        return out

    def _reachable(self, view, req):
        """Could any provider serve this request at all once the fleet frees up?"""
        return any(
            view.providers[n].stocks(m) and view.providers[n].down_until_ms is None
            for n in view.providers
            for m in req.equiv_class
        )

    def _book(self, req, pv, model, rule):
        self.reported_cost_usd += pv.prices[model]
        self._live[(req.tenant, pv.name)] = self._live.get((req.tenant, pv.name), 0) + 1
        self._placed[req.rid] = (req.tenant, pv.name)
        return Dispatch(pv.name, model, {"rule": rule, "provider": pv.name, "model": model})

    # -- policy --------------------------------------------------------
    def decide(self, req, now_ms, view):
        room = self._room(view, req.model, req.tenant)
        if room:
            return self._book(req, room[0], req.model, "requested")

        best = None
        for model in sorted(req.equiv_class):
            for pv in self._room(view, model, req.tenant):
                price = pv.prices[model]
                if best is None or price < best[0]:
                    best = (price, pv, model)
        if best is not None:
            return self._book(req, best[1], best[2], "cheapest")

        if not self._reachable(view, req):
            return Shed("nothing in the equivalence class is reachable")
        return Wait(WAIT_MS)

    def on_complete(self, req, now_ms, status):
        """The harness tells the router a request finished. A correct router answers nothing,
        and releases the slot it was holding."""
        key = self._placed.pop(req.rid, None)
        if key is not None and self._live.get(key):
            self._live[key] -= 1
        return None


class FairShareRouter(ReferenceRouter):
    """Correct, and additionally holds each tenant to half of every provider's concurrency, so
    one tenant's burst cannot take the slots the other tenant needs."""

    per_tenant_share = 0.5
