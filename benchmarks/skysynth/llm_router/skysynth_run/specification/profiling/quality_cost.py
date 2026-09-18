#!/usr/bin/env python3
"""Per-model quality/cost landscape, train vs val. Train and val ONLY."""
import json, os, statistics
TASK="/path/to/ghostcheck/benchmarks/skysynth/upstream/skydiscover/synthesize/examples/llm-router"
TR=f"{TASK}/evaluator/benchmark/.data/traces"
def load(p):
    if "test" in os.path.basename(p): raise SystemExit("REFUSED")
    return [json.loads(l) for l in open(p)]
out={}
for t in ("A","B"):
    for s in ("train","val"):
        m=load(f"{TR}/matrix_tenant{t}_{s}.jsonl")
        models=sorted(m[0]["score"])
        rec={}
        for mo in models:
            sc=statistics.fmean(r["score"][mo] for r in m)
            co=statistics.fmean(r["cost"][mo] for r in m)
            rec[mo]={"mean_score":round(sc,4),"mean_cost_usd":round(co,6),
                     "static_utility_no_slo":round(sc-3*co,4)}
        best=max(rec,key=lambda k:rec[k]["static_utility_no_slo"])
        out[f"{t}_{s}"]={"n":len(m),"models":rec,
            "best_static_model":best,"best_static_utility":rec[best]["static_utility_no_slo"],
            "oracle_best_per_request_quality":round(statistics.fmean(max(r["score"].values()) for r in m),4),
            "oracle_argmax_utility_per_request":round(statistics.fmean(
                max(r["score"][mo]-3*r["cost"][mo] for mo in models) for r in m),4),
            "cheapest_model_by_mean_cost":min(rec,key=lambda k:rec[k]["mean_cost_usd"]),
            "cost_spread_max_over_min":round(max(v["mean_cost_usd"] for v in rec.values())/
                                             min(v["mean_cost_usd"] for v in rec.values()),1),
        }
# train -> val rank shift
for t in ("A","B"):
    tr=out[f"{t}_train"]["models"]; va=out[f"{t}_val"]["models"]
    rt=sorted(tr,key=lambda k:-tr[k]["static_utility_no_slo"])
    rv=sorted(va,key=lambda k:-va[k]["static_utility_no_slo"])
    out[f"{t}_rank_shift"]={"train_order":rt,"val_order":rv,
        "top3_train":rt[:3],"top3_val":rv[:3],
        "max_abs_score_shift":max((abs(tr[k]["mean_score"]-va[k]["mean_score"]),k) for k in tr),
        "max_abs_cost_shift":max((round(abs(tr[k]["mean_cost_usd"]-va[k]["mean_cost_usd"]),6),k) for k in tr),
        "max_abs_utility_shift":max((round(abs(tr[k]["static_utility_no_slo"]-va[k]["static_utility_no_slo"]),4),k) for k in tr)}
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"quality_cost.json"),"w"),indent=1)
for k,v in out.items():
    if k.endswith("rank_shift"): print(k,json.dumps(v,indent=1)); continue
    print("="*60);print(k,"n=",v["n"],"best_static=",v["best_static_model"],v["best_static_utility"],
          "oracle_q=",v["oracle_best_per_request_quality"],"oracle_u=",v["oracle_argmax_utility_per_request"],
          "cost_spread=",v["cost_spread_max_over_min"])
    for mo,r in sorted(v["models"].items(),key=lambda kv:-kv[1]["static_utility_no_slo"]):
        print(f"   {mo:32s} q={r['mean_score']:.4f} $={r['mean_cost_usd']:.6f} U={r['static_utility_no_slo']:.4f}")
