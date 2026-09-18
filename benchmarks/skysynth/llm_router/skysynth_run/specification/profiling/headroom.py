#!/usr/bin/env python3
"""Offered load vs published fleet capacity, and deadline feasibility.
Train and val ONLY; any path containing "test" is refused."""
import json, os, statistics, yaml
from collections import Counter

TASK = "/path/to/ghostcheck/benchmarks/skysynth/upstream/skydiscover/synthesize/examples/llm-router"
TR = f"{TASK}/evaluator/benchmark/.data/traces"
ENV = yaml.safe_load(open(f"{TASK}/evaluator/benchmark/env_card.yaml"))
P = ENV["providers"]
RETRY = ENV["retry_after_ms"]
OUT_VAL = ENV["outages"]["val"]


def load(p):
    if "test" in os.path.basename(p):
        raise SystemExit("REFUSED: test split")
    return [json.loads(l) for l in open(p)]


def slide_max(rows, w_s, key):
    rs = sorted(rows, key=lambda r: r["t_ms"]); ts=[r["t_ms"] for r in rs]
    pre=[0]
    for r in rs: pre.append(pre[-1]+key(r))
    wm=w_s*1000.0; best=0; j=0
    for i,t in enumerate(ts):
        while ts[j] < t-wm: j+=1
        best=max(best, pre[i+1]-pre[j])
    return best


def slide_max_n(rows, w_s):
    return slide_max(rows, w_s, lambda r: 1)


def svc_ms(prov, model, r):
    cfg = P[prov]; e = cfg["models"][model]
    dt = float(e.get("decode_tps", cfg["decode_tps"]))
    ttft = cfg["ttft_base_ms"] + r["prompt_tokens"]/cfg["prefill_tps"]*1000
    return ttft, ttft + r["expected_output_tokens"]/dt*1000


res = {}
for t, split in [("A","train"),("A","val"),("B","train"),("B","val")]:
    rows = load(f"{TR}/trace_tenant{t}_{split}.jsonl")
    key = "A" if t=="A" else "B"
    tok = lambda r: r["prompt_tokens"]+r["expected_output_tokens"]
    peak_n60 = slide_max_n(rows, 60)
    peak_tok60 = slide_max(rows, 60, tok)
    span = (max(r["t_ms"] for r in rows)-min(r["t_ms"] for r in rows))/1000.0
    mean_n60 = len(rows)/span*60
    mean_tok60 = sum(tok(r) for r in rows)/span*60
    entry = {
        "peak_requests_per_60s": peak_n60,
        "mean_requests_per_60s": round(mean_n60,1),
        "peak_admission_tokens_per_60s": peak_tok60,
        "mean_admission_tokens_per_60s": int(mean_tok60),
        "rpm_utilisation_at_peak": {p: round(peak_n60/P[p]["rpm"],3) for p in P},
        "rpm_utilisation_at_mean": {p: round(mean_n60/P[p]["rpm"],3) for p in P},
        "tpm_utilisation_at_peak": {p: round(peak_tok60/P[p]["tpm"],4) for p in P},
        "rpm_sum_all_three": P["value"]["rpm"]+P["prime"]["rpm"]+P["courier"]["rpm"],
        "rpm_utilisation_at_peak_whole_fleet": round(peak_n60/(P["value"]["rpm"]+P["prime"]["rpm"]+P["courier"]["rpm"]),3),
    }
    # concurrency demand: Little's law on the requested model at each provider
    req_model = rows[0]["model_requested"]
    for p in P:
        if req_model not in P[p]["models"]: continue
        tot = [svc_ms(p, req_model, r)[1] for r in rows]
        # peak concurrency demand over the busiest 60s window, Little's law
        entry.setdefault("concurrency_demand_requested_model", {})[p] = {
            "model": req_model,
            "mean_service_sec": round(statistics.fmean(tot)/1000,1),
            "p90_service_sec": round(sorted(tot)[int(.9*(len(tot)-1))]/1000,1),
            "peak_concurrency_little": round(peak_n60/60.0*statistics.fmean(tot)/1000,1),
            "mean_concurrency_little": round(len(rows)/span*statistics.fmean(tot)/1000,1),
            "provider_concurrency_limit": P[p]["concurrency"],
        }
    # cheapest-fast alternative concurrency (deepseek-v3-0324, fast decode, no override)
    for p in P:
        alt = "deepseek-v3-0324"
        tot = [svc_ms(p, alt, r)[1] for r in rows]
        entry.setdefault("concurrency_demand_cheap_alt", {})[p] = {
            "model": alt,
            "mean_service_sec": round(statistics.fmean(tot)/1000,1),
            "peak_concurrency_little": round(peak_n60/60.0*statistics.fmean(tot)/1000,1),
            "provider_concurrency_limit": P[p]["concurrency"],
        }
    # deadline feasibility
    if t=="A":
        lim = 2500
        for p in P:
            ok0 = sum(1 for r in rows if svc_ms(p,"gpt-5",r)[0] <= lim) if "gpt-5" in P[p]["models"] else None
            okc = sum(1 for r in rows if svc_ms(p,"deepseek-v3-0324",r)[0] <= lim)
            entry.setdefault("ttft_feasible_first_try",{})[p] = {
                "gpt-5": None if ok0 is None else round(ok0/len(rows),4),
                "deepseek-v3-0324": round(okc/len(rows),4)}
            # after one 429 (2000 ms burned)
            okr = sum(1 for r in rows if svc_ms(p,"deepseek-v3-0324",r)[0] <= lim-RETRY)
            entry.setdefault("ttft_feasible_after_one_429",{})[p] = round(okr/len(rows),4)
        entry["prompt_tokens_too_big_for_prime_ttft"] = sum(
            1 for r in rows if P["prime"]["ttft_base_ms"]+r["prompt_tokens"]/P["prime"]["prefill_tps"]*1000 > lim)
        entry["prompt_tokens_too_big_for_courier_ttft"] = sum(
            1 for r in rows if P["courier"]["ttft_base_ms"]+r["prompt_tokens"]/P["courier"]["prefill_tps"]*1000 > lim)
        entry["prompt_tokens_too_big_for_value_ttft"] = sum(
            1 for r in rows if P["value"]["ttft_base_ms"]+r["prompt_tokens"]/P["value"]["prefill_tps"]*1000 > lim)
    else:
        lim = 600000
        for p in P:
            for m in ("deepseek-r1-0528","deepseek-v3-0324"):
                if m not in P[p]["models"]: continue
                ok = sum(1 for r in rows if svc_ms(p,m,r)[1] <= lim)
                entry.setdefault("e2e_feasible_solo",{}).setdefault(p,{})[m]=round(ok/len(rows),4)
        # queueing slack: how long a request can wait and still finish
        tot = [svc_ms("value","deepseek-r1-0528",r)[1] for r in rows]
        entry["queue_slack_sec_p50_p90_min"] = [round((lim-q)/1000,1) for q in
            (sorted(tot)[len(tot)//2], sorted(tot)[int(.9*(len(tot)-1))], max(tot))]
    # outage exposure (val schedule is literal; train has no declared schedule)
    if split=="val":
        ex = sum(1 for r in rows if any(s<=r["t_ms"]<e for s,e in OUT_VAL))
        entry["val_outage_windows_ms"] = OUT_VAL
        entry["requests_arriving_during_prime_outage"] = ex
        entry["frac_arriving_during_prime_outage"] = round(ex/len(rows),4)
        # per-window
        entry["per_window"] = [{"window_ms":[s,e],
                                "n": sum(1 for r in rows if s<=r["t_ms"]<e)} for s,e in OUT_VAL]
    res[f"{t}_{split}"] = entry

# fleet reachability
reach = {}
for t in ("A","B"):
    rows = load(f"{TR}/trace_tenant{t}_val.jsonl")
    ec = set(rows[0]["equiv_class"])
    pairs = [(p,m) for p in P for m in ec if m in P[p]["models"]]
    reach[t] = {"equiv_class_size": len(ec),
                "distinct_equiv_sets": len({tuple(sorted(r["equiv_class"])) for r in rows}),
                "legal_provider_model_pairs": len(pairs),
                "pairs_by_provider": dict(Counter(p for p,_ in pairs)),
                "models_missing_on_value": sorted(ec - set(P["value"]["models"])),
                "requested_model": rows[0]["model_requested"],
                "providers_stocking_requested": [p for p in P if rows[0]["model_requested"] in P[p]["models"]]}
res["fleet_reachability"] = reach
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"headroom.json"),"w"), indent=1)
print(json.dumps(res, indent=1))
