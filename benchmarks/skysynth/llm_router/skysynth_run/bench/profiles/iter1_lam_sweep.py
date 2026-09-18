#!/usr/bin/env python3
"""Iteration 1 profile: the LAM cost-quality frontier of candidate C0.

DIAGNOSTIC ONLY -- nothing here is a score. It replays the candidate's own policy shape at a
range of LAM (the dollars-to-quality shadow price in the soft rank, common.py:196) at the exact
scored operating point (TRAIN trace, --split val outages, full trace, fresh instance), to find
where the three-clause pass condition's COST clause becomes feasible and what U survives there.

The implementation is NOT modified: each point is a one-line subclass overriding LAM.
"""
import json, os, sys

ROOT = "/path/to/ghostcheck/benchmarks/skysynth/upstream"
EX = os.path.join(ROOT, "skydiscover/synthesize/examples/llm-router")
RUN = os.path.join(ROOT, ".skydiscover/llm-router")
sys.path.insert(0, EX)
sys.path.insert(0, os.path.join(RUN, "synthesis/impl"))

from evaluator.benchmark.replay_tenants import TenantReplay  # noqa: E402
import common  # noqa: E402

ENV = os.path.join(EX, "evaluator/benchmark/env_card.yaml")
TRACE = os.path.join(EX, "evaluator/benchmark/.data/traces/trace_tenant%s_train.jsonl")
BASE = {"A": {"q": 0.6212, "cpr": 0.004362, "slo": 0.0386, "U": 0.5695},
        "B": {"q": 0.3907, "cpr": 0.001746, "slo": 0.0000, "U": 0.3855}}
CLS = {"A": common.TenantARouter, "B": common.TenantBRouter}
LAMS = [3, 5, 8, 12, 18, 25, 40, 60, 100, 200, 400]


def point(tenant, lam):
    sub = type("L%s" % lam, (CLS[tenant],), {"LAM": float(lam)})
    r = TenantReplay(ENV, split="val").run(TRACE % tenant, sub())
    b = r["tenants"][tenant]
    n = b["requests"]
    cpr = b["cost_usd"] / n
    U = b["mean_quality"] - b["slo_violation_rate"] - 3 * cpr
    base = BASE[tenant]
    slo_ok = b["slo_violation_rate"] < base["slo"] if base["slo"] > 0 else b["slo_violation_rate"] <= base["slo"]
    return {
        "lam": lam, "q": round(b["mean_quality"], 4), "cpr": round(cpr, 6),
        "slo": b["slo_violation_rate"], "U": round(U, 4),
        "cost_ratio_vs_baseline": round(cpr / base["cpr"], 3),
        "throttles_429": b["throttles_429"], "shed": b["shed"],
        "violations": r["violation_count"], "kinds": r["violation_kinds"],
        "gate_q": b["mean_quality"] >= base["q"], "gate_cost": cpr <= base["cpr"], "gate_slo": slo_ok,
        "gate": "PASS" if (b["mean_quality"] >= base["q"] and cpr <= base["cpr"] and slo_ok) else "FAIL",
        "U_margin_vs_baseline": round(U - base["U"], 4),
    }


out = {}
for t in ("A", "B"):
    rows = []
    print("tenant %s  lam     q      $/req    x_base   slo     U      dU     gate  429" % t)
    for lam in LAMS:
        p = point(t, lam)
        rows.append(p)
        print("          %5d  %.4f  %.6f  %6.3f  %.4f  %.4f %+.4f  %-4s  %d"
              % (p["lam"], p["q"], p["cpr"], p["cost_ratio_vs_baseline"], p["slo"],
                 p["U"], p["U_margin_vs_baseline"], p["gate"], p["throttles_429"]))
    out[t] = rows
    print()

dest = os.path.join(RUN, "synthesis/bench/profiles/iter1_lam_sweep.json")
json.dump({"note": __doc__.strip(), "baseline": BASE, "sweep": out}, open(dest, "w"), indent=2)
print("wrote", dest)
