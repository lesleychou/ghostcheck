#!/usr/bin/env python3
"""Outage exposure (the val schedule applied to each timeline, which is what
replay_tenants.py --split val does) and wave-drain arithmetic. Train/val ONLY."""
import json, os, statistics, yaml
TASK="/path/to/ghostcheck/benchmarks/skysynth/upstream/skydiscover/synthesize/examples/llm-router"
TR=f"{TASK}/evaluator/benchmark/.data/traces"
ENV=yaml.safe_load(open(f"{TASK}/evaluator/benchmark/env_card.yaml")); P=ENV["providers"]
W=[(int(s),int(e)) for s,e in ENV["outages"]["val"]]
def load(p):
    if "test" in os.path.basename(p): raise SystemExit("REFUSED")
    return [json.loads(l) for l in open(p)]
out={"val_windows_ms":W,"outage_provider":ENV["outages"]["provider"],
     "retry_grace":ENV["outages"]["retry_grace"]}
for t in ("A","B"):
    for s in ("train","val"):
        rows=load(f"{TR}/trace_tenant{t}_{s}.jsonl")
        n=len(rows); span=max(r["t_ms"] for r in rows)
        ex=[sum(1 for r in rows if a<=r["t_ms"]<b) for a,b in W]
        out[f"{t}_{s}"]={"n":n,"span_ms":span,
            "arrivals_in_window":ex,"total":sum(ex),"frac":round(sum(ex)/n,4),
            "windows_inside_span":[ (a<span) for a,b in W ]}
# fleet decode capacity and wave drain, tenant B
cap={}
for m in ("deepseek-r1-0528","deepseek-v3-0324","qwen3-235b-a22b-2507","qwen3-235b-a22b-thinking-2507","deepseek-v3.1-terminus"):
    tot=0
    for p,cfg in P.items():
        if m not in cfg["models"]: continue
        dt=float(cfg["models"][m].get("decode_tps",cfg["decode_tps"]))
        tot+=cfg["concurrency"]*dt
    cap[m]={"fleet_decode_tokens_per_sec":int(tot)}
out["fleet_decode_capacity"]=cap
for s,wave_n,wave_dur in (("train",388,89.5),("val",347,89.7)):
    rows=load(f"{TR}/trace_tenantB_{s}.jsonl")
    mean_out=statistics.fmean(r["expected_output_tokens"] for r in rows)
    wave_tokens=wave_n*mean_out
    out[f"B_{s}_wave_drain"]={"requests_per_wave":wave_n,"wave_submit_window_sec":wave_dur,
        "mean_output_tokens":round(mean_out,1),"output_tokens_per_wave":int(wave_tokens),
        "drain_sec_whole_fleet":{m:round(wave_tokens/v["fleet_decode_tokens_per_sec"],1) for m,v in cap.items()},
        "deadline_sec":600,
        "rpm_needed_to_admit_wave_in_its_window":round(wave_n/wave_dur*60,1),
        "fleet_rpm":sum(c["rpm"] for c in P.values())}
# tenant A: the retry arithmetic
out["A_ttft_arithmetic"]={
  "slo_ttft_ms":2500,"retry_after_ms_429":ENV["retry_after_ms"],"retry_after_ms_503":ENV["retry_after_ms"]//2,
  "ttft_base_ms":{p:P[p]["ttft_base_ms"] for p in P},
  "budget_left_after_one_429_ms":2500-ENV["retry_after_ms"],
  "providers_still_feasible_after_one_429":[p for p in P if P[p]["ttft_base_ms"]<=2500-ENV["retry_after_ms"]],
  "max_prompt_tokens_on_prime_after_one_429":int((2500-ENV["retry_after_ms"]-P["prime"]["ttft_base_ms"])/1000*P["prime"]["prefill_tps"]),
  "max_prompt_tokens_on_prime_first_try":int((2500-P["prime"]["ttft_base_ms"])/1000*P["prime"]["prefill_tps"]),
  "max_prompt_tokens_on_value_first_try":int((2500-P["value"]["ttft_base_ms"])/1000*P["value"]["prefill_tps"]),
  "max_prompt_tokens_on_courier_first_try":int((2500-P["courier"]["ttft_base_ms"])/1000*P["courier"]["prefill_tps"]),
}
for s in ("train","val"):
    rows=load(f"{TR}/trace_tenantA_{s}.jsonl")
    lim=out["A_ttft_arithmetic"]
    out["A_ttft_arithmetic"][f"frac_{s}_over_prime_first_try_limit"]=round(
        sum(1 for r in rows if r["prompt_tokens"]>lim["max_prompt_tokens_on_prime_first_try"])/len(rows),4)
    out["A_ttft_arithmetic"][f"frac_{s}_over_prime_after_429_limit"]=round(
        sum(1 for r in rows if r["prompt_tokens"]>lim["max_prompt_tokens_on_prime_after_one_429"])/len(rows),4)
    out["A_ttft_arithmetic"][f"frac_{s}_over_courier_first_try_limit"]=round(
        sum(1 for r in rows if r["prompt_tokens"]>lim["max_prompt_tokens_on_courier_first_try"])/len(rows),4)
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"outage_and_drain.json"),"w"),indent=1)
print(json.dumps(out,indent=1))
