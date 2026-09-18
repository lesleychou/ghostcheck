#!/usr/bin/env python3
"""Workload-mode characterization of the two tenant traces.

HARD PROTOCOL CONSTRAINT: this script opens ONLY *_train.jsonl and *_val.jsonl.
Any path containing "test" is refused before opening. The test split is out of
bounds for every tuning phase (decision_log row `split-protocol`).
"""
import json, math, os, statistics, sys
from collections import Counter, defaultdict

TASK = "/path/to/ghostcheck/benchmarks/skysynth/upstream/skydiscover/synthesize/examples/llm-router"
TR = f"{TASK}/evaluator/benchmark/.data/traces"


def load(path):
    if "test" in os.path.basename(path):
        raise SystemExit(f"REFUSED: test split is out of bounds: {path}")
    with open(path) as f:
        return [json.loads(l) for l in f]


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]


def stats(xs):
    return {
        "n": len(xs), "min": min(xs), "p50": q(xs, .50), "p90": q(xs, .90),
        "p99": q(xs, .99), "max": max(xs), "mean": round(statistics.fmean(xs), 2),
        "sum": sum(xs),
    }


def window_peaks(ts_ms, widths_s):
    """max requests in any sliding window of each width (event-anchored)."""
    ts = sorted(ts_ms)
    out = {}
    for w in widths_s:
        wm = w * 1000.0
        best, j = 0, 0
        for i, t in enumerate(ts):
            while ts[j] < t - wm:
                j += 1
            best = max(best, i - j + 1)
        out[w] = best
    return out


def window_peak_tokens(rows, w_s, key):
    """max sum(key) over any sliding w_s window, anchored at each arrival."""
    rs = sorted(rows, key=lambda r: r["t_ms"])
    ts = [r["t_ms"] for r in rs]
    vals = [key(r) for r in rs]
    pre = [0]
    for v in vals:
        pre.append(pre[-1] + v)
    wm = w_s * 1000.0
    best, j = 0, 0
    for i, t in enumerate(ts):
        while ts[j] < t - wm:
            j += 1
        best = max(best, pre[i + 1] - pre[j])
    return best


def idle_gaps(ts_ms):
    ts = sorted(ts_ms)
    return [(b - a) / 1000.0 for a, b in zip(ts, ts[1:])]


def fano(ts_ms, bin_s):
    ts = sorted(ts_ms)
    span = (ts[-1] - ts[0]) / 1000.0
    nb = max(1, int(span / bin_s))
    c = Counter(int((t - ts[0]) / 1000.0 / bin_s) for t in ts)
    counts = [c.get(k, 0) for k in range(nb + 1)]
    m = statistics.fmean(counts)
    v = statistics.pvariance(counts)
    return {"bin_s": bin_s, "mean_per_bin": round(m, 3),
            "var_per_bin": round(v, 3), "fano": round(v / m, 3) if m else None}


def diurnal(ts_ms, period_s=1200.0, nb=12):
    ts = sorted(ts_ms)
    span = (ts[-1] - ts[0]) / 1000.0
    c = Counter(int(((t / 1000.0) % period_s) / period_s * nb) for t in ts)
    # normalize by how much wall time each phase bin got
    per_bin_time = span / nb  # approx (whole periods)
    return {str(k): round(c.get(k, 0) / max(per_bin_time, 1e-9), 4) for k in range(nb)}


def profile(rows, name):
    ts = [r["t_ms"] for r in rows]
    span_s = (max(ts) - min(ts)) / 1000.0
    n = len(rows)
    pk = window_peaks(ts, [1, 5, 10, 30, 60])
    gaps = idle_gaps(ts)
    out = {
        "name": name,
        "n": n,
        "t_first_ms": min(ts), "t_last_ms": max(ts),
        "span_sec": round(span_s, 1),
        "mean_rps": round(n / span_s, 4),
        "peak_rps": {f"{w}s": round(c / w, 3) for w, c in pk.items()},
        "peak_count": {f"{w}s": c for w, c in pk.items()},
        "burstiness_ratio_10s_over_mean": round((pk[10] / 10) / (n / span_s), 2),
        "fano_10s": fano(ts, 10.0),
        "fano_60s": fano(ts, 60.0),
        "interarrival_sec": {
            "p50": round(q(gaps, .5), 4), "p90": round(q(gaps, .9), 4),
            "p99": round(q(gaps, .99), 4), "max": round(max(gaps), 2),
        },
        "idle_gaps_over_5s": sum(1 for g in gaps if g > 5),
        "idle_gaps_over_30s": sum(1 for g in gaps if g > 30),
        "frac_in_busiest_10pct_of_10s_bins": None,
        "diurnal_rps_by_phase_1200s": diurnal(ts),
        "prompt_tokens": stats([r["prompt_tokens"] for r in rows]),
        "expected_output_tokens": stats([r["expected_output_tokens"] for r in rows]),
        "max_tokens": stats([r["max_tokens"] for r in rows]),
        "admission_tokens": stats([r["prompt_tokens"] + r["expected_output_tokens"] for r in rows]),
        "cls_mix": {k: round(v / n, 4) for k, v in Counter(r["class"] for r in rows).most_common()},
        "cls_counts": dict(Counter(r["class"] for r in rows).most_common()),
        "model_requested_mix": {k: round(v / n, 4) for k, v in Counter(r["model_requested"] for r in rows).most_common()},
        "equiv_class_sizes": dict(Counter(len(r["equiv_class"]) for r in rows)),
        "equiv_class_distinct_sets": len({tuple(sorted(r["equiv_class"])) for r in rows}),
        "stream_mix": {str(k): round(v / n, 4) for k, v in Counter(r["stream"] for r in rows).items()},
        "slo_fields": {json.dumps(r_, sort_keys=True): c for r_, c in
                       [(json.loads(k), v) for k, v in Counter(json.dumps(r["slo"], sort_keys=True) for r in rows).items()]},
        "downgrade_ok": dict(Counter(r["downgrade_ok"] for r in rows)),
        "retry_safe": dict(Counter(r["retry_safe"] for r in rows)),
        "quality_floor_nonzero": sum(1 for r in rows if r["quality_floor"] > 0),
        "prefix_tokens_nonzero": sum(1 for r in rows if r["prefix_tokens"] > 0),
        "prefix_ids": dict(Counter(r["prefix_id"] for r in rows)),
        "session_ids": dict(Counter(r["session_id"] for r in rows)),
        "temperature": sorted({r["temperature"] for r in rows}),
        "difficulty_hint": {
            "p10": q([r["features"]["difficulty_hint"] for r in rows], .10),
            "p50": q([r["features"]["difficulty_hint"] for r in rows], .50),
            "p90": q([r["features"]["difficulty_hint"] for r in rows], .90),
            "max": max(r["features"]["difficulty_hint"] for r in rows),
            "distinct": len({r["features"]["difficulty_hint"] for r in rows}),
        },
        "feature_keys": sorted(rows[0]["features"].keys()),
        "distinct_prompt_ids": len({r["features"]["prompt_id"] for r in rows}),
        # oracle quality, for reference only (routers may not read it)
        "oracle_quality_best_of_12_mean": round(statistics.fmean(max(r["quality"].values()) for r in rows), 4),
        "oracle_quality_requested_mean": round(statistics.fmean(r["quality"][r["model_requested"]] for r in rows), 4),
        "rows_where_all_12_zero": sum(1 for r in rows if max(r["quality"].values()) == 0.0),
        "rows_where_all_12_one": sum(1 for r in rows if min(r["quality"].values()) == 1.0),
    }
    # frac in busiest 10% of 10s bins
    c = Counter(int((t - min(ts)) / 10000) for t in ts)
    vals = sorted(c.values(), reverse=True)
    k = max(1, int(0.10 * math.ceil(span_s / 10)))
    out["frac_in_busiest_10pct_of_10s_bins"] = round(sum(vals[:k]) / n, 4)
    # offered-load peaks in 60s sliding windows (what rpm/tpm windows see)
    out["peak_60s_requests"] = pk[60]
    out["peak_60s_admission_tokens"] = window_peak_tokens(
        rows, 60, lambda r: r["prompt_tokens"] + r["expected_output_tokens"])
    out["peak_10s_admission_tokens"] = window_peak_tokens(
        rows, 10, lambda r: r["prompt_tokens"] + r["expected_output_tokens"])
    return out


def waves(rows, thresh_gap_s=20.0):
    ts = sorted(r["t_ms"] for r in rows)
    groups, cur = [], [ts[0]]
    for a, b in zip(ts, ts[1:]):
        if (b - a) / 1000.0 > thresh_gap_s:
            groups.append(cur); cur = []
        cur.append(b)
    groups.append(cur)
    return [{"start_s": round(g[0] / 1000, 1), "end_s": round(g[-1] / 1000, 1),
             "dur_s": round((g[-1] - g[0]) / 1000, 1), "n": len(g),
             "rps": round(len(g) / max((g[-1] - g[0]) / 1000, 1e-9), 2)} for g in groups]


def bursts_A(rows, bin_s=10.0, factor=3.0):
    ts = sorted(r["t_ms"] for r in rows)
    t0 = ts[0]
    c = Counter(int((t - t0) / 1000.0 / bin_s) for t in ts)
    nb = int((ts[-1] - t0) / 1000.0 / bin_s) + 1
    counts = [c.get(k, 0) for k in range(nb)]
    base = statistics.median([x for x in counts if x > 0]) or 1
    hot = [(k, v) for k, v in enumerate(counts) if v >= factor * base]
    return {"median_per_10s": base, "n_hot_bins": len(hot),
            "hot_bin_frac": round(len(hot) / nb, 4),
            "requests_in_hot_bins": sum(v for _, v in hot),
            "frac_requests_in_hot_bins": round(sum(v for _, v in hot) / len(ts), 4),
            "max_per_10s": max(counts),
            "peak_over_median_factor": round(max(counts) / base, 2),
            "hot_bins": [{"t_s": k * bin_s, "n": v} for k, v in hot][:40]}


def main():
    env = {}
    out = {}
    for t in ("A", "B"):
        for split in ("train", "val"):
            rows = load(f"{TR}/trace_tenant{t}_{split}.jsonl")
            p = profile(rows, f"tenant{t}_{split}")
            p["waves_gap20s"] = waves(rows)[:40]
            p["n_waves_gap20s"] = len(waves(rows))
            p["burst_bins"] = bursts_A(rows)
            out[f"{t}_{split}"] = p
        # train/val prompt-id disjointness
        a = {r["features"]["prompt_id"] for r in load(f"{TR}/trace_tenant{t}_train.jsonl")}
        b = {r["features"]["prompt_id"] for r in load(f"{TR}/trace_tenant{t}_val.jsonl")}
        out[f"{t}_split_overlap"] = {"train": len(a), "val": len(b), "shared": len(a & b)}
    # merged trace: tenant interleaving
    for split in ("train", "val"):
        m = load(f"{TR}/trace_merged_{split}.jsonl")
        ts = [r["t_ms"] for r in m]
        out[f"merged_{split}"] = {
            "n": len(m),
            "by_tenant": dict(Counter(r["tenant"] for r in m)),
            "span_sec": round((max(ts) - min(ts)) / 1000, 1),
            "peak_60s_requests": window_peaks(ts, [60])[60],
            "peak_10s_requests": window_peaks(ts, [10])[10],
            "peak_60s_admission_tokens": window_peak_tokens(
                m, 60, lambda r: r["prompt_tokens"] + r["expected_output_tokens"]),
        }
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trace_profile.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if not k.endswith("_val") and not k.endswith("_train")}, indent=1))


if __name__ == "__main__":
    main()
