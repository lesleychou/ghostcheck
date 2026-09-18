#!/usr/bin/env python3
"""Do the OBSERVABLE per-request signals (class, difficulty_hint, token counts)
separate the models? Train vs val. Train and val ONLY."""
import json, os, statistics
from collections import defaultdict
TASK="/path/to/ghostcheck/benchmarks/skysynth/upstream/skydiscover/synthesize/examples/llm-router"
TR=f"{TASK}/evaluator/benchmark/.data/traces"
def load(p):
    if "test" in os.path.basename(p): raise SystemExit("REFUSED")
    return [json.loads(l) for l in open(p)]
out={}
for t in ("A","B"):
    tr={r["features"]["prompt_id"]:r for r in load(f"{TR}/trace_tenant{t}_train.jsonl")}
    va={r["features"]["prompt_id"]:r for r in load(f"{TR}/trace_tenant{t}_val.jsonl")}
    mx={s:{r["prompt_id"]:r for r in load(f"{TR}/matrix_tenant{t}_{s}.jsonl")} for s in ("train","val")}
    models=sorted(next(iter(mx["train"].values()))["score"])
    def util(rows,cost,pick):
        return statistics.fmean(mx_[pid]["score"][pick(pid)]-3*mx_[pid]["cost"][pick(pid)] for pid in rows)
    res={}
    # per-class landscape
    for s,src in (("train",tr),("val",va)):
        mx_=mx[s]
        byc=defaultdict(list)
        for pid,r in src.items(): byc[r["class"]].append(pid)
        res[f"per_class_{s}"]={}
        for c,pids in sorted(byc.items()):
            tab={m:(round(statistics.fmean(mx_[p]["score"][m] for p in pids),4),
                    round(statistics.fmean(mx_[p]["cost"][m] for p in pids),6)) for m in models}
            best=max(tab,key=lambda m:tab[m][0]-3*tab[m][1])
            res[f"per_class_{s}"][c]={"n":len(pids),"best_model":best,
                "best_utility":round(tab[best][0]-3*tab[best][1],4),
                "best_quality":tab[best][0],"best_cost":tab[best][1],
                "top3":[m for m in sorted(tab,key=lambda m:-(tab[m][0]-3*tab[m][1]))[:3]]}
    # does a per-class policy fit on TRAIN beat the single best model, ON VAL?
    fitted={c:v["best_model"] for c,v in res["per_class_train"].items()}
    mx_=mx["val"]
    val_pids=list(va)
    u_perclass=statistics.fmean(
        mx_[p]["score"][fitted[va[p]["class"]]]-3*mx_[p]["cost"][fitted[va[p]["class"]]] for p in val_pids)
    # single best model fitted on train, scored on val
    mtr=mx["train"]
    gbest=max(models,key=lambda m:statistics.fmean(mtr[p]["score"][m]-3*mtr[p]["cost"][m] for p in mtr))
    u_single=statistics.fmean(mx_[p]["score"][gbest]-3*mx_[p]["cost"][gbest] for p in val_pids)
    res["policy_transfer_train_to_val"]={
        "per_class_policy_fitted_on_train":fitted,
        "per_class_policy_utility_on_val":round(u_perclass,4),
        "single_best_model_fitted_on_train":gbest,
        "single_best_utility_on_val":round(u_single,4),
        "gain_from_class_routing":round(u_perclass-u_single,4)}
    # difficulty_hint: does it predict anything?
    for s,src in (("train",tr),("val",va)):
        mx_=mx[s]
        pids=sorted(src,key=lambda p:src[p]["features"]["difficulty_hint"])
        k=len(pids)//4
        qs=[pids[:k],pids[k:2*k],pids[2*k:3*k],pids[3*k:]]
        res[f"difficulty_quartiles_{s}"]=[{
            "q":i+1,"n":len(g),
            "hint_range":[src[g[0]]["features"]["difficulty_hint"],src[g[-1]]["features"]["difficulty_hint"]],
            "oracle_best_quality":round(statistics.fmean(max(mx_[p]["score"].values()) for p in g),4),
            "best_static_model_here":max(models,key=lambda m:statistics.fmean(mx_[p]["score"][m]-3*mx_[p]["cost"][m] for p in g)),
            "best_static_utility_here":round(max(statistics.fmean(mx_[p]["score"][m]-3*mx_[p]["cost"][m] for p in g) for m in models),4),
            "mean_expected_output_tokens":round(statistics.fmean(src[p]["expected_output_tokens"] for p in g),1),
        } for i,g in enumerate(qs)]
    out[t]=res
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"observable_signal.json"),"w"),indent=1)
print(json.dumps(out,indent=1))
