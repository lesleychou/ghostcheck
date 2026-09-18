import copy
import sys

sys.path.insert(0, "benchmarks/skysynth/llm_router")
import trace_transform as tt  # noqa: E402


def test_neutral_workload_is_identity(trace_records):
    assert tt.transform_trace(trace_records, {}) == trace_records


def test_does_not_mutate_input(trace_records):
    # deep copy: a shallow one shares the nested slo/equiv_class/quality/features
    # objects, so an in-place nested mutation would compare equal and escape the test
    before = copy.deepcopy(trace_records)
    tt.transform_trace(trace_records, {"prompt_token_scale": 4.0, "equiv_class_width": 1})
    assert trace_records == before


def test_tenant_filter_keeps_one_tenant(trace_records):
    out = tt.transform_trace(trace_records, {"tenant": "A"})
    assert {r["tenant"] for r in out} == {"A"}
    assert len(out) == 3


def test_n_requests_truncates_and_renumbers(trace_records):
    out = tt.transform_trace(trace_records, {"n_requests": 2})
    assert len(out) == 2
    assert [r["req_id"] for r in out] == [0, 1]


def test_arrival_scale_compresses_time(trace_records):
    out = tt.transform_trace(trace_records, {"arrival_scale": 0.5})
    assert [r["t_ms"] for r in out] == [0, 500, 1000, 1500, 2000, 2500]


def test_burst_factor_pulls_arrivals_toward_the_front(trace_records):
    out = tt.transform_trace(trace_records, {"burst_factor": 2.0})
    spans = [r["t_ms"] for r in out]
    assert spans[0] == 0
    assert spans[-1] == 5000  # span preserved
    assert spans[1] < 1000  # interior arrivals pulled earlier


def test_token_scaling_updates_max_tokens(trace_records):
    out = tt.transform_trace(trace_records, {"output_token_scale": 2.0})
    assert out[0]["expected_output_tokens"] == 740
    assert out[0]["max_tokens"] == max(256, 4 * 740)


def test_token_scaling_never_goes_below_one(trace_records):
    out = tt.transform_trace(trace_records, {"prompt_token_scale": 0.001})
    assert all(r["prompt_tokens"] >= 1 for r in out)


def test_slo_overrides_apply_per_tenant_key(trace_records):
    out = tt.transform_trace(trace_records, {"ttft_ms": 800, "deadline_ms": 60000})
    a = [r for r in out if r["tenant"] == "A"][0]
    b = [r for r in out if r["tenant"] == "B"][0]
    assert a["slo"] == {"ttft_ms": 800}
    assert b["slo"] == {"latency_ms": 60000}


def test_equiv_class_width_narrows_and_keeps_requested_model(trace_records):
    out = tt.transform_trace(trace_records, {"equiv_class_width": 1})
    for r in out:
        assert len(r["equiv_class"]) == 1
        assert r["model_requested"] in r["equiv_class"]
        assert set(r["quality"]) == set(r["equiv_class"])


def test_ordering_is_stable_by_time(trace_records):
    out = tt.transform_trace(trace_records, {"burst_factor": 3.0})
    assert [r["t_ms"] for r in out] == sorted(r["t_ms"] for r in out)
