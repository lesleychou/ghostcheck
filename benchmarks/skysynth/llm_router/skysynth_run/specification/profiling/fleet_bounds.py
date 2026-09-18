#!/usr/bin/env python3
"""Environment-mode ceiling construction, TRAIN split only.

Builds, per tenant, from the frozen fleet card + the train traces:
  - oracle quality ceiling      (best-quality permitted model per request)
  - cost floor                  (cheapest permitted model/provider per request)
  - oracle per-request U optimum (argmax q - 3*cost, with the zero-queue SLO term)
  - observable-feature U optimum (same, with the ridge head's predicted quality)
  - feature-cell U optimum       (best fixed model per task x difficulty decile)
  - structural SLO floors from prompt size and from the outage windows
Never reads any *_test.* file.
"""
import json, os, sys, collections, bisect
import yaml

ROOT = "/path/to/ghostcheck/benchmarks/skysynth/upstream/skydiscover/synthesize/examples/llm-router"
DATA = os.path.join(ROOT, "evaluator/benchmark/.data/traces")
CARD = yaml.safe_load(open(os.path.join(ROOT, "evaluator/benchmark/env_card.yaml")))
PRED = json.load(open(os.path.join(ROOT, "evaluator/benchmark/artifacts/generic_predictions.json")))
PROV = CARD["providers"]
COST_W = 3.0
SLO_W = 1.0

def cost(p, m, pt, ot):
    e = PROV[p]["models"][m]
    return (pt * e["in"] + ot * e["out"]) / 1e6

def ttft_ms(p, pt):
    c = PROV[p]
    return c["ttft_base_ms"] + pt / c["prefill_tps"] * 1000.0

def total_ms(p, m, pt, ot):
    c = PROV[p]
    dt = float(c["models"][m].get("decode_tps", c["decode_tps"]))
    return ttft_ms(p, pt) + ot / dt * 1000.0

def latency_ok(p, m, r):
    pt, ot = r["prompt_tokens"], r["expected_output_tokens"]
    if "latency_ms" in r["slo"]:
        return total_ms(p, m, pt, ot) <= r["slo"]["latency_ms"]
    return ttft_ms(p, pt) <= r["slo"]["ttft_ms"]

def permitted(r):
    ms = set(r["equiv_class"]) | {r["model_requested"]} if r["downgrade_ok"] else {r["model_requested"]}
    return [(p, m) for p in PROV for m in ms if m in PROV[p]["models"]]

out = {}
for t in "AB":
    rows = [json.loads(l) for l in open(f"{DATA}/trace_tenant{t}_train.jsonl")]
    n = len(rows)
    qmax = qmin_cost = 0.0
    u_oracle = u_head = 0.0
    q_o = c_o = v_o = 0.0
    q_h = c_h = v_h = 0.0
    cheap_cost = cheap_q = cheap_v = 0.0
    slo_floor_any = 0           # no (p,m) meets the SLO at zero queue
    slo_floor_noprime = 0       # no (p,m) outside prime meets it
    head_missing = 0
    picks_o = collections.Counter(); picks_h = collections.Counter()
    cells = collections.defaultdict(list)
    for r in rows:
        pt, ot = r["prompt_tokens"], r["expected_output_tokens"]
        opts = permitted(r)
        q = r["quality"]
        pid = r["features"]["prompt_id"]
        pred = PRED["pred"].get(pid)
        if pred is None:
            head_missing += 1
        qhat = ({m: pred[i] for i, m in enumerate(PRED["fleet"])} if pred
                else {m: 0.0 for m in PRED["fleet"]})
        # ceilings
        qmax += max(q.get(m, 0.0) for _, m in opts)
        qmin_cost += min(cost(p, m, pt, ot) for p, m in opts)
        cb = min(opts, key=lambda pm: cost(pm[0], pm[1], pt, ot))
        cheap_cost += cost(*cb, pt, ot); cheap_q += q.get(cb[1], 0.0)
        cheap_v += 0.0 if latency_ok(*cb, r) else 1.0
        # structural SLO floor
        if not any(latency_ok(p, m, r) for p, m in opts):
            slo_floor_any += 1
        if not any(latency_ok(p, m, r) for p, m in opts if p != "prime"):
            slo_floor_noprime += 1
        # per-request U optimum, oracle and head
        def u(pm, qd):
            p, m = pm
            return qd.get(m, 0.0) - COST_W * cost(p, m, pt, ot) - (0.0 if latency_ok(p, m, r) else SLO_W)
        bo = max(opts, key=lambda pm: u(pm, q))
        bh = max(opts, key=lambda pm: u(pm, qhat))
        picks_o[bo]; picks_o[bo] += 1; picks_h[bh] += 1
        q_o += q.get(bo[1], 0.0); c_o += cost(*bo, pt, ot); v_o += 0.0 if latency_ok(*bo, r) else 1.0
        q_h += q.get(bh[1], 0.0); c_h += cost(*bh, pt, ot); v_h += 0.0 if latency_ok(*bh, r) else 1.0
        cells[(r["features"]["task"], int(min(9, r["features"]["difficulty_hint"] * 10)))].append(r)
    U = lambda q, c, v: q / n - SLO_W * (v / n) - COST_W * (c / n)
    # feature-cell optimum: one fixed (provider, model) per (task, difficulty decile)
    q_c = c_c = v_c = 0.0
    for key, rs in cells.items():
        allopts = sorted({pm for r in rs for pm in permitted(r)})
        best, bestu = None, None
        for pm in allopts:
            tot = 0.0
            for r in rs:
                p, m = pm
                pt, ot = r["prompt_tokens"], r["expected_output_tokens"]
                if m not in PROV[p]["models"]:
                    tot -= 1e9; break
                tot += r["quality"].get(m, 0.0) - COST_W * cost(p, m, pt, ot) - (0.0 if latency_ok(p, m, r) else SLO_W)
            if bestu is None or tot > bestu:
                best, bestu = pm, tot
        for r in rs:
            p, m = best
            pt, ot = r["prompt_tokens"], r["expected_output_tokens"]
            q_c += r["quality"].get(m, 0.0); c_c += cost(p, m, pt, ot)
            v_c += 0.0 if latency_ok(p, m, r) else 1.0
    out[t] = {
        "n": n,
        "quality_ceiling_oracle": round(qmax / n, 4),
        "cost_floor_usd_per_req": round(qmin_cost / n, 6),
        "cheapest_everywhere": {"U": round(U(cheap_q, cheap_cost, cheap_v), 4),
                                "q": round(cheap_q / n, 4), "cost": round(cheap_cost / n, 6),
                                "slo_rate": round(cheap_v / n, 4)},
        "U_opt_oracle_zeroqueue": {"U": round(U(q_o, c_o, v_o), 4), "q": round(q_o / n, 4),
                                   "cost": round(c_o / n, 6), "slo_rate": round(v_o / n, 4)},
        "U_opt_observable_head_zeroqueue": {"U": round(U(q_h, c_h, v_h), 4), "q": round(q_h / n, 4),
                                            "cost": round(c_h / n, 6), "slo_rate": round(v_h / n, 4)},
        "U_opt_feature_cell_zeroqueue": {"U": round(U(q_c, c_c, v_c), 4), "q": round(q_c / n, 4),
                                         "cost": round(c_c / n, 6), "slo_rate": round(v_c / n, 4)},
        "slo_floor_prompt_size_rate": round(slo_floor_any / n, 4),
        "slo_floor_without_prime_rate": round(slo_floor_noprime / n, 4),
        "head_missing_prompt_ids": head_missing,
        "top_oracle_picks": [[f"{p}/{m}", c] for (p, m), c in picks_o.most_common(6)],
        "top_head_picks": [[f"{p}/{m}", c] for (p, m), c in picks_h.most_common(6)],
    }
print(json.dumps(out, indent=2))
