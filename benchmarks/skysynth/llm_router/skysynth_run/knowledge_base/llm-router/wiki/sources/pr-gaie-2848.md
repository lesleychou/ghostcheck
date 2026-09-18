---
kind: pr
id: pr-gaie-2848
domain: llm-router
tags: [race, correctness, recovery, overflow, placement]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2848
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2848
changed_paths: [pkg/epp/framework/plugins/requestcontrol/requestdataproducer/predictedlatency/plugin.go, pkg/epp/framework/plugins/requestcontrol/requestdataproducer/predictedlatency/prediction.go, pkg/epp/framework/plugins/requestcontrol/requestdataproducer/predictedlatency/preparedata_hooks.go, pkg/epp/framework/plugins/requestcontrol/requestdataproducer/predictedlatency/requestcontrol_hooks.go]
---

# fix(predictedlatency): keep prefillTokensInFlight from drifting negative

The predicted-latency producer decremented its prefill token in-flight counter on completion paths that could fire without a matching increment, so the counter drifted deeply negative and every subsequent bulk prediction call was rejected by the sidecar's non-negative validation with HTTP 422, which killed latency-prediction scheduling until the process was restarted, and restarting did not help because the same race re-armed on startup. The merged change makes the increment and decrement symmetric across the prepare-data and request-control hooks and clamps the counter so it cannot go below zero. A router that feeds a predictor from counters it maintains itself must decide where the counter is clamped and how it re-syncs after a lost decrement, rather than trusting paired hooks to always pair. This is the placement axis, and the failure mode is a scheduler that goes silently blind.
