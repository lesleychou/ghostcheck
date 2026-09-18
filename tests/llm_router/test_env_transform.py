import sys

sys.path.insert(0, "benchmarks/skysynth/llm_router")
import env_transform as et  # noqa: E402


def test_neutral_workload_is_identity(env_card):
    assert et.transform_env(env_card, {}) == env_card


def test_does_not_mutate_input(env_card):
    before = et.transform_env(env_card, {})
    et.transform_env(env_card, {"rate_limit_scale": 0.1})
    assert env_card == before


def test_rate_limit_scale_shrinks_every_provider(env_card):
    out = et.transform_env(env_card, {"rate_limit_scale": 0.5})
    assert out["providers"]["value"]["rpm"] == 210
    assert out["providers"]["value"]["tpm"] == 6000000
    assert out["providers"]["value"]["concurrency"] == 48
    assert out["providers"]["prime"]["rpm"] == 90


def test_rate_limits_never_reach_zero(env_card):
    out = et.transform_env(env_card, {"rate_limit_scale": 0.0001})
    for p in out["providers"].values():
        assert p["rpm"] >= 1 and p["tpm"] >= 1 and p["concurrency"] >= 1


def test_error_rate_scale_is_clamped_to_one(env_card):
    out = et.transform_env(env_card, {"error_rate_scale": 1000.0})
    assert out["providers"]["value"]["error_rate"] == 1.0


def test_outage_count_truncates(env_card):
    out = et.transform_env(env_card, {"outage_count": 1})
    assert out["outages"]["val"] == [[300000, 420000]]


def test_outage_count_zero_removes_all(env_card):
    out = et.transform_env(env_card, {"outage_count": 0})
    assert out["outages"]["val"] == []


def test_outage_duration_scale_extends_the_window_end(env_card):
    out = et.transform_env(env_card, {"outage_duration_scale": 2.0})
    assert out["outages"]["val"][0] == [300000, 540000]


def test_outage_shift_moves_windows_and_clamps_at_zero(env_card):
    out = et.transform_env(env_card, {"outage_shift_ms": -500000})
    assert out["outages"]["val"][0][0] == 0
