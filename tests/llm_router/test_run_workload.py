import sys

import pytest

sys.path.insert(0, "benchmarks/skysynth/llm_router")
import run_workload as rw  # noqa: E402


@pytest.fixture
def replay_result():
    """A REAL GenericPolicy replay of trace_merged_val, verified to match
    evaluator/benchmark/baseline/generic_baseline_results.json exactly.

    Two shape traps this fixture exists to pin down:
      - the GLOBAL "slo_violations" is a DICT keyed by SLO class, not an int;
      - each tenant book carries int "slo_violations" plus "shed" and "lost_or_dead".
    """
    return {
        "trace": "trace_merged_val.jsonl",
        "router": "GenericPolicy",
        "requests": 1665,
        "total_cost_usd": 5.2734,
        "slo_violations": {"critical": 0, "tolerant": 69},
        "mean_quality": 0.418,
        "shed": 0,
        "completed": 1665,
        "violations": [],
        "violation_count": 0,
        "violation_kinds": {},
        "tenants": {
            "A": {"requests": 972, "completed": 972, "shed": 0, "lost_or_dead": 0,
                  "mean_quality": 0.5195, "cost_usd": 4.0194, "slo_violations": 69,
                  "slo_violation_rate": 0.071, "p95_latency_ms": 2832.7},
            "B": {"requests": 693, "completed": 693, "shed": 0, "lost_or_dead": 0,
                  "mean_quality": 0.2756, "cost_usd": 1.254, "slo_violations": 0,
                  "slo_violation_rate": 0.0, "p95_latency_ms": 185046},
        },
    }


def test_all_numeric_fields_are_higher_is_better(replay_result):
    m = rw._metrics_from_replay(replay_result, "merged")
    for key, value in m.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            assert not key.startswith("cost"), f"{key} is lower-is-better; negate it"
            assert "violation_rate" not in key or key.startswith("neg_")
            assert key != "shed"


def test_merged_slo_rate_matches_their_published_number(replay_result):
    """generic_baseline_results.json reports val.merged.slo_violation_rate = 0.0414.
    Reproducing it is the proof the aggregation is theirs, not ours: a plain mean of
    the two tenant rates would give 0.0355 and silently differ."""
    m = rw._metrics_from_replay(replay_result, "merged")
    assert -m["neg_slo_violation_rate"] == pytest.approx(0.0414, abs=5e-5)


def test_utility_matches_their_published_selected_utility(replay_result):
    """task.md: U = mean_quality - 1.0*slo_violation_rate - 3.0*cost_usd_per_request.
    generic_baseline_results.json reports selected.utility = 0.3671."""
    m = rw._metrics_from_replay(replay_result, "merged")
    assert m["utility_U"] == pytest.approx(0.3671, abs=5e-5)


def test_cost_is_negated_and_per_request(replay_result):
    m = rw._metrics_from_replay(replay_result, "merged")
    assert m["neg_cost_usd_per_request"] == pytest.approx(-5.2734 / 1665)
    assert m["neg_shed"] == 0


def test_tenant_scope_reports_that_tenants_own_book(replay_result):
    m = rw._metrics_from_replay(replay_result, "A")
    assert m["mean_quality"] == pytest.approx(0.5195)
    assert m["neg_cost_usd_per_request"] == pytest.approx(-4.0194 / 972, abs=1e-7)
    assert -m["neg_slo_violation_rate"] == pytest.approx(0.071)
    assert m["requests"] == 972


def test_violations_raise_so_the_correctness_oracle_fires(replay_result):
    replay_result["violation_count"] = 2
    replay_result["violation_kinds"] = {"outage_lost": 2}
    with pytest.raises(RuntimeError, match="outage_lost"):
        rw._metrics_from_replay(replay_result, "merged")


def test_router_from_module_uses_build_router():
    class Mod:
        @staticmethod
        def build_router(tenant):
            return f"router-for-{tenant}"

    assert rw._router_from_module(Mod, "A") == "router-for-A"


def test_router_from_module_errors_without_build_router():
    class Mod:
        pass

    with pytest.raises(RuntimeError, match="build_router"):
        rw._router_from_module(Mod, "A")


def test_module_source_execs_in_a_bare_namespace_like_the_harness():
    """Regression: harness.py:_worker runs this file as `exec(source, {})`, a namespace with
    no __file__. A module-level reference to __file__ raises NameError there and every
    oracle call fails with 'name __file__ is not defined' -- which is exactly what happened.
    The other ADRS apps never referenced __file__, so nothing else covers this."""
    import pathlib

    source = pathlib.Path("benchmarks/skysynth/llm_router/run_workload.py").read_text()
    namespace: dict = {}
    exec(compile(source, "run_workload.py", "exec"), namespace)  # noqa: S102
    assert callable(namespace["run_workload"])
