import sys

sys.path.insert(0, "benchmarks/skysynth/llm_router")
import envelope  # noqa: E402


def test_empty_workload_is_in_envelope():
    r = envelope.classify({})
    assert r["in_envelope"] is True
    assert r["outside"] == []


def test_neutral_values_are_in_envelope():
    r = envelope.classify({"burst_factor": 1.0, "arrival_scale": 1.0, "rate_limit_scale": 1.0})
    assert r["in_envelope"] is True


def test_mild_burst_stays_in_envelope():
    # tenant A's card reports peak_rps_10s 7.7 against mean_rps 0.94, so roughly
    # 8x concentration is inside what they measured and published.
    assert envelope.classify({"burst_factor": 2.0})["in_envelope"] is True


def test_extreme_burst_leaves_envelope():
    r = envelope.classify({"burst_factor": 20.0})
    assert r["in_envelope"] is False
    assert "burst_factor" in r["outside"]


def test_shrinking_the_fleet_leaves_envelope():
    # env_card.yaml is FROZEN; any capacity change is outside the declared deployment.
    r = envelope.classify({"rate_limit_scale": 0.5})
    assert r["in_envelope"] is False
    assert "rate_limit_scale" in r["outside"]


def test_any_token_rescaling_leaves_envelope():
    """Token counts are ground-truth measurements bound to committed prompt ids, not a
    distribution we may rescale. The p50->p99 spread across requests is NOT a licence
    for a uniform multiplier — different quantities."""
    assert envelope.classify({"prompt_token_scale": 3.0})["in_envelope"] is False
    assert envelope.classify({"output_token_scale": 2.0})["in_envelope"] is False
    assert envelope.classify({"prompt_token_scale": 1.0})["in_envelope"] is True


def test_token_scaling_far_past_p99_leaves_envelope():
    assert envelope.classify({"prompt_token_scale": 500.0})["in_envelope"] is False


def test_tightening_an_slo_leaves_envelope():
    """The regression this guards: with ttft_ms absent from DECLARED_ENVELOPE, cutting
    tenant A's SLO from 2500ms to 800ms was silently labelled in-envelope."""
    r = envelope.classify({"ttft_ms": 800})
    assert r["in_envelope"] is False
    assert "ttft_ms" in r["outside"]
    assert envelope.classify({"ttft_ms": 2500})["in_envelope"] is True


def test_shortening_the_batch_deadline_leaves_envelope():
    r = envelope.classify({"deadline_ms": 60000})
    assert r["in_envelope"] is False
    assert "deadline_ms" in r["outside"]


def test_narrowing_the_equiv_class_leaves_envelope():
    r = envelope.classify({"equiv_class_width": 3})
    assert r["in_envelope"] is False
    assert "equiv_class_width" in r["outside"]
    assert envelope.classify({"equiv_class_width": 12})["in_envelope"] is True


def test_more_outages_than_declared_leaves_envelope():
    r = envelope.classify({"outage_count": 5})
    assert r["in_envelope"] is False
    assert "outage_count" in r["outside"]


def test_multiple_violations_are_all_reported():
    r = envelope.classify({"burst_factor": 20.0, "rate_limit_scale": 0.5})
    assert sorted(r["outside"]) == ["burst_factor", "rate_limit_scale"]


def test_unknown_knobs_are_ignored():
    assert envelope.classify({"tenant": "A", "nonsense": 99})["in_envelope"] is True
