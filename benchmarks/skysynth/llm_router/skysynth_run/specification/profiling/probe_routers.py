"""Ceiling probes for environment mode. Not shipped policy: these exist only to measure
how much of the zero-queue per-request U optimum survives the fleet's rate limits,
queueing and outages when driven through the real replay harness on TRAIN.

ProbeOracleU  reads req.quality (ORACLE, forbidden to the shipped router by
              decision_log 'quality_information_source'); it measures the unreachable bound.
ProbeHeadU    reads only req.features['prompt_id'] through the shipped ridge head, i.e. the
              same observable information the baseline has.
"""
import json, os, sys
import yaml

ROOT = "/path/to/ghostcheck/benchmarks/skysynth/upstream/skydiscover/synthesize/examples/llm-router"
sys.path.insert(0, ROOT)
from evaluator.router_interface import Action, Router  # noqa: E402

CARD = yaml.safe_load(open(os.path.join(ROOT, "evaluator/benchmark/env_card.yaml")))
PRED = json.load(open(os.path.join(ROOT, "evaluator/benchmark/artifacts/generic_predictions.json")))
COST_W, SLO_W = 3.0, 1.0


class _ProbeU(Router):
    oracle = False

    def __init__(self):
        self.spec = {n: (c["ttft_base_ms"], c["prefill_tps"], c["decode_tps"], c["concurrency"])
                     for n, c in CARD["providers"].items()}
        self.decode = {n: {m: float(e.get("decode_tps", c["decode_tps"]))
                           for m, e in c["models"].items()}
                       for n, c in CARD["providers"].items()}
        self.attempts = {}

    def _q(self, req):
        if self.oracle:
            return req.quality or {}
        p = PRED["pred"].get((req.features or {}).get("prompt_id"))
        if p is None:
            return {}
        return {m: p[i] for i, m in enumerate(PRED["fleet"])}

    def _late(self, prov, model, req, now_ms):
        base, prefill, _dec, _c = self.spec[prov]
        ttft = base + req.prompt_tokens / prefill * 1000.0
        elapsed = now_ms - req.t_ms
        if "latency_ms" in req.slo:
            dec = self.decode[prov].get(model, _dec)
            return elapsed + ttft + req.expected_output_tokens / dec * 1000.0 > req.slo["latency_ms"]
        return elapsed + ttft > req.slo["ttft_ms"]

    def decide(self, req, now_ms, fleet_view):
        q = self._q(req)
        allowed = set(req.equiv_class) | {req.model_requested} if req.downgrade_ok \
            else {req.model_requested}
        tokens = req.prompt_tokens + req.expected_output_tokens
        scored = []
        for name, v in fleet_view.items():
            for m, price in v["models"].items():
                if m not in allowed:
                    continue
                c = (req.prompt_tokens * price["in"] + req.expected_output_tokens * price["out"]) / 1e6
                u = q.get(m, 0.0) - COST_W * c - (SLO_W if self._late(name, m, req, now_ms) else 0.0)
                scored.append((-u, name, m, v))
        if not scored:
            return Action("defer", until_ms=now_ms + 1000)
        scored.sort(key=lambda s: (s[0], s[1], s[2]))
        for _u, name, m, v in scored:
            if (v["rpm_left"] > 0 and v["tpm_left"] >= tokens
                    and v["inflight"] < self.spec[name][3]):
                return Action("dispatch", provider=name, model=m)
        k = self.attempts.get(req.req_id, 0)
        self.attempts[req.req_id] = k + 1
        return Action("defer", until_ms=now_ms + min(2000, 100 * (2 ** min(k, 5))))

    def on_error(self, req, now_ms, kind, retry_after_ms):
        self.attempts[req.req_id] = self.attempts.get(req.req_id, 0) + 1

    def on_complete(self, req, now_ms):
        self.attempts.pop(req.req_id, None)
        return None


class ProbeOracleU(_ProbeU):
    oracle = True


class ProbeHeadU(_ProbeU):
    oracle = False
