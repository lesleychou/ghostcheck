---
kind: pr
id: pr-gaie-2415
domain: llm-router
tags: [validation, crash, recovery, correctness, placement]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2415
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2415
changed_paths: [pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/prediction.go, pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/preparedata_hooks.go, pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/requestcontrol_hooks.go, pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/latencypredictor_helper.go, pkg/epp/framework/interface/scheduling/types.go]
---

# fix(predicted-latency-scorer): prevent nil pointer panic for non-completions API types

The predicted-latency scorer read request fields that only the text completions body shape populated, so a chat completions request reached prediction generation with a nil body and the whole endpoint picker process died on a nil pointer dereference rather than degrading to a fallback score. The merged change makes the request type accessors safe across API shapes and has the scorer handle a body it cannot read instead of dereferencing it. A router with pluggable scorers must decide what a scorer returns when its required input is absent for this request shape, and must contain a scorer fault to that scorer rather than to the process. This is the placement axis with a fallback and health consequence.
