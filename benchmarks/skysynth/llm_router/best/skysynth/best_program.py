# benchmarks/skysynth/llm_router/best/skysynth/best_program.py
"""P': the routers SkySynth synthesized, selected per tenant.

Class names are READ from the artifact's routers.json (SkySynth's own delivery
convention, decision-log row `routers-json`), never hardcoded, so a re-run with
different class names needs no edit here.

tenant="merged" is the case that matters most. task.md's deployment is two tenants
sharing ONE rate-limited fleet, but the tuning protocol fits and selects each
specialist on its own isolated trace -- nobody ever replays both against the shared
fleet. _TenantDispatcher keeps BOTH specialists live and routes each request to its
own, which is what a real deployment does and what their protocol never tests.
"""
import importlib
import json
import os
import sys

import paths

paths.bind_upstream()

from evaluator.router_interface import Router  # noqa: E402

_IMPL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifact")
_ROUTERS_JSON = os.path.join(_IMPL, "routers.json")


def _tenant_map() -> dict:
    """{tenant: "module.Class"} from the artifact's routers.json, "_"-keys dropped."""
    if not os.path.isfile(_ROUTERS_JSON):
        raise RuntimeError(
            f"no routers.json at {_ROUTERS_JSON}; harvest a finished SkySynth run into "
            "best/skysynth/artifact/ first (scripts/harvest_skysynth.sh)"
        )
    with open(_ROUTERS_JSON) as fh:
        raw = json.load(fh)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def _load_class(spec: str):
    """Resolve "common.TenantARouter" against the artifact directory."""
    module_name, _, class_name = spec.rpartition(".")
    if not module_name:
        raise RuntimeError(f"routers.json entry {spec!r} is not <module>.<Class>")
    if _IMPL not in sys.path:
        sys.path.insert(0, _IMPL)
    return getattr(importlib.import_module(module_name), class_name)


class _TenantDispatcher(Router):
    """Both specialists live at once; each request goes to its tenant's own.

    Every hook forwards to the same instance that decided the request, so each
    specialist's internal state stays coherent -- the specialists are independent
    policies competing for one fleet, which is the point of the merged replay.
    """

    def __init__(self):
        self._routers = {t: _load_class(spec)() for t, spec in _tenant_map().items()}

    def _for(self, req):
        tenant = (req.features or {}).get("tenant")
        if tenant is None:
            # trace rows set session_id to "<tenant>-<task>" (make_tenant_traces.py)
            tenant = str(getattr(req, "session_id", "")).split("-")[0]
        router = self._routers.get(tenant)
        if router is None:
            raise RuntimeError(
                f"no synthesized router for tenant {tenant!r}; "
                f"routers.json declares {sorted(self._routers)}"
            )
        return router

    def decide(self, req, now_ms, fleet_view):
        return self._for(req).decide(req, now_ms, fleet_view)

    def on_error(self, req, now_ms, kind, retry_after_ms):
        return self._for(req).on_error(req, now_ms, kind, retry_after_ms)

    def on_complete(self, req, now_ms):
        return self._for(req).on_complete(req, now_ms)


def build_router(tenant: str):
    if tenant in ("A", "B"):
        return _load_class(_tenant_map()[tenant])()
    return _TenantDispatcher()
