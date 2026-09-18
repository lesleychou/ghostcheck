"""Pure, in-memory transforms of a frozen LLMRouterBench tenant trace.

One GhostCheck workload dict -> one new list of trace records. The record schema is
SkySynth's own (evaluator/benchmark/data/make_tenant_traces.py:to_request); we only
re-shape values, never invent fields.

Every knob is optional and neutral by default, so `transform_trace(recs, {})` is the
identity. That property is what lets Agent 2 explore one axis at a time.
"""
import copy

_A_SLO_KEY = "ttft_ms"
_B_SLO_KEY = "latency_ms"


def _scale_tokens(value: int, factor: float) -> int:
    return max(1, int(round(value * factor)))


def transform_trace(records: list[dict], w: dict) -> list[dict]:
    out = [copy.deepcopy(r) for r in records]

    tenant = w.get("tenant", "merged")
    if tenant in ("A", "B"):
        out = [r for r in out if r.get("tenant") == tenant]
    if not out:
        return []

    n = w.get("n_requests")
    if n is not None:
        out = out[: max(1, int(n))]

    # Arrival shape. arrival_scale < 1 compresses the span (higher request rate).
    # burst_factor > 1 pulls interior arrivals toward the front of the span without
    # changing the span itself, which concentrates load the way a traffic spike does.
    t0 = out[0]["t_ms"]
    span = max(1, out[-1]["t_ms"] - t0)
    burst = float(w.get("burst_factor", 1.0))
    if burst != 1.0:
        for r in out:
            frac = (r["t_ms"] - t0) / span
            r["t_ms"] = int(round(t0 + span * (frac ** burst)))
    scale = float(w.get("arrival_scale", 1.0))
    if scale != 1.0:
        for r in out:
            r["t_ms"] = int(round(t0 + (r["t_ms"] - t0) * scale))

    p_scale = float(w.get("prompt_token_scale", 1.0))
    o_scale = float(w.get("output_token_scale", 1.0))
    ttft = w.get("ttft_ms")
    deadline = w.get("deadline_ms")
    width = w.get("equiv_class_width")
    downgrade = w.get("downgrade_ok")

    for r in out:
        if p_scale != 1.0:
            r["prompt_tokens"] = _scale_tokens(r["prompt_tokens"], p_scale)
        if o_scale != 1.0:
            r["expected_output_tokens"] = _scale_tokens(r["expected_output_tokens"], o_scale)
            r["max_tokens"] = max(256, 4 * r["expected_output_tokens"])
        if ttft is not None and _A_SLO_KEY in r["slo"]:
            r["slo"] = {_A_SLO_KEY: int(ttft)}
        if deadline is not None and _B_SLO_KEY in r["slo"]:
            r["slo"] = {_B_SLO_KEY: int(deadline)}
        if width is not None:
            keep = [r["model_requested"]]
            keep += [m for m in r["equiv_class"] if m != r["model_requested"]]
            keep = keep[: max(1, int(width))]
            r["equiv_class"] = keep
            r["quality"] = {m: q for m, q in r["quality"].items() if m in keep}
        if downgrade is not None:
            r["downgrade_ok"] = bool(downgrade)

    out.sort(key=lambda r: (r["t_ms"], r["features"]["prompt_id"]))
    for i, r in enumerate(out):
        r["req_id"] = i
    return out
