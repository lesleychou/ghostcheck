"""Exercises the real P' once a SkySynth artifact has been harvested; skipped until then."""
import importlib.util
import os
import sys

import pytest

sys.path.insert(0, "benchmarks/skysynth/llm_router")

_PP = "benchmarks/skysynth/llm_router/best/skysynth/best_program.py"
_ARTIFACT = "benchmarks/skysynth/llm_router/best/skysynth/artifact/routers.json"

pytestmark = pytest.mark.skipif(
    not os.path.isfile(_ARTIFACT), reason="no harvested SkySynth artifact yet"
)


def _load():
    spec = importlib.util.spec_from_file_location("pp", _PP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_each_tenant_gets_its_own_specialist():
    pp = _load()
    a, b = pp.build_router("A"), pp.build_router("B")
    assert type(a) is not type(b), "the two tenants must get different specialists"


def test_merged_returns_a_dispatcher_holding_both():
    pp = _load()
    d = pp.build_router("merged")
    assert set(d._routers) == {"A", "B"}


def test_dispatcher_routes_by_tenant_feature():
    pp = _load()
    d = pp.build_router("merged")

    class Req:
        features = {"tenant": "B"}
        session_id = "B-hle"

    assert d._for(Req()) is d._routers["B"]


def test_dispatcher_falls_back_to_session_id():
    pp = _load()
    d = pp.build_router("merged")

    class Req:
        features = {}
        session_id = "A-simpleqa"

    assert d._for(Req()) is d._routers["A"]
