"""Pin the adapter to SkySynth's own published numbers.

Needs the LLMRouterBench traces; skipped when they are not built.
"""
import importlib.util
import sys

import pytest

sys.path.insert(0, "benchmarks/skysynth/llm_router")
import paths  # noqa: E402
import run_workload as rw  # noqa: E402


def _traces_built():
    try:
        root = paths.llm_router_root()
    except RuntimeError:
        return False
    return (root / "evaluator/benchmark/.data/traces/trace_merged_val.jsonl").is_file()


pytestmark = pytest.mark.skipif(
    not _traces_built(), reason="LLMRouterBench traces not built"
)


def _load(path):
    spec = importlib.util.spec_from_file_location("m", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_P = "benchmarks/skysynth/llm_router/initial_program.py"
_PP = "benchmarks/skysynth/llm_router/best/reference/best_program.py"


def test_baseline_merged_reproduces_generic_baseline_results_json():
    """generic_baseline_results.json, val.merged: mean_quality 0.418,
    total_cost_usd 5.2734, slo_violation_rate 0.0414, selected utility 0.3671."""
    m = rw.run_workload(_load(_P), {"tenant": "merged"})
    assert m["requests"] == 1665
    assert m["mean_quality"] == pytest.approx(0.418, abs=5e-4)
    assert -m["neg_cost_usd_per_request"] == pytest.approx(5.2734 / 1665, rel=2e-3)
    assert -m["neg_slo_violation_rate"] == pytest.approx(0.0414, abs=5e-4)
    assert m["utility_U"] == pytest.approx(0.3671, abs=1e-3)


def test_reference_router_matches_direct_replay_so_fleet_order_is_preserved():
    """The regression guard for the env-card round trip. yaml.safe_dump sorts mapping
    keys by default, which reorders the fleet from [value, prime, courier] to
    [courier, prime, value]. ReferenceRouter takes the FIRST provider stocking a model,
    so the reorder changes every placement: cost/req 0.01820 -> 0.01499,
    svr 0.1800 -> 0.2788. GenericPolicy ranks by price and does not notice, which is
    why only a first-fit router can catch this."""
    m = rw.run_workload(_load(_PP), {"tenant": "A"})
    assert -m["neg_cost_usd_per_request"] == pytest.approx(0.01820, abs=2e-4)
    assert -m["neg_slo_violation_rate"] == pytest.approx(0.1800, abs=2e-3)
    assert m["utility_U"] == pytest.approx(0.2767, abs=2e-3)


def test_tenant_a_alone_is_easier_than_tenant_a_in_the_merged_trace():
    """Not a regression guard -- a recorded property. Tenant A's SLO-violation rate is
    0.0412 replayed alone and 0.071 inside the merged trace: it nearly doubles once
    tenant B competes for the same rate-limited fleet. This is the cross-tenant
    interference the campaigns hunt, and it is present in the BASELINE."""
    alone = rw.run_workload(_load(_P), {"tenant": "A"})
    assert -alone["neg_slo_violation_rate"] == pytest.approx(0.0412, abs=1e-3)
    assert -alone["neg_slo_violation_rate"] < 0.071
