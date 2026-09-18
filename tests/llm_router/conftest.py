import pytest

_FLEET = ["gpt-5", "qwen3-235b-a22b-2507", "deepseek-r1-0528"]


def _record(req_id, t_ms, tenant, task, prompt_tokens, out_tokens, slo):
    return {
        "req_id": req_id,
        "t_ms": t_ms,
        "session_id": f"{tenant}-{task}",
        "class": task,
        "tenant": tenant,
        "model_requested": "gpt-5" if tenant == "A" else "deepseek-r1-0528",
        "equiv_class": list(_FLEET),
        "prompt_tokens": prompt_tokens,
        "prefix_id": f"{tenant}-{task}",
        "prefix_tokens": 0,
        "expected_output_tokens": out_tokens,
        "max_tokens": max(256, 4 * out_tokens),
        "stream": tenant == "A",
        "slo": dict(slo),
        "downgrade_ok": True,
        "retry_safe": True,
        "temperature": 0.0,
        "quality": {m: 0.5 for m in _FLEET},
        "quality_floor": 0.0,
        "features": {
            "tenant": tenant,
            "task": task,
            "prompt_id": f"{tenant}-{task}-{req_id}",
            "difficulty_hint": min(1.0, prompt_tokens / 2000.0),
        },
    }


@pytest.fixture
def trace_records():
    a_slo = {"ttft_ms": 2500}
    b_slo = {"latency_ms": 600000}
    return [
        _record(0, 0, "A", "simpleqa", 28, 370, a_slo),
        _record(1, 1000, "B", "hle", 284, 2648, b_slo),
        _record(2, 2000, "A", "gpqa", 81, 934, a_slo),
        _record(3, 3000, "B", "livecodebench", 745, 8072, b_slo),
        _record(4, 4000, "A", "simpleqa", 28, 370, a_slo),
        _record(5, 5000, "B", "hle", 284, 2648, b_slo),
    ]


@pytest.fixture
def env_card():
    return {
        "providers": {
            "value": {
                "models": {m: {"in": 0.3, "out": 0.4, "cached": 0.3} for m in _FLEET},
                "rpm": 420, "tpm": 12000000, "concurrency": 96,
                "ttft_base_ms": 700, "prefill_tps": 25000, "decode_tps": 70,
                "cache_speedup": 8, "cache_entries": 500, "error_rate": 0.008,
            },
            "prime": {
                "models": {m: {"in": 1.5, "out": 14.0, "cached": 1.5} for m in _FLEET},
                "rpm": 180, "tpm": 4000000, "concurrency": 48,
                "ttft_base_ms": 400, "prefill_tps": 40000, "decode_tps": 90,
                "cache_speedup": 8, "cache_entries": 500, "error_rate": 0.01,
            },
        },
        "retry_after_ms": 2000,
        "outages": {
            "provider": "prime",
            "retry_grace": 8,
            "val": [[300000, 420000], [780000, 930000]],
            "test_seed": 20260820,
        },
    }
