---
kind: pr
id: pr-gaie-2372
domain: llm-router
tags: [observability, calibration, latency, correctness, placement]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2372
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2372
changed_paths: [pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/prediction.go, pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/requestcontrol_hooks.go, pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/scorer.go, pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/latencypredictor_helper.go, pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/preparedata_helper.go]
---

# fix: reuse scheduling predictions for TTFT and first TPOT reporting

Predictions made during scheduling were held in a flat slice that could not be looked up by endpoint, so the pre-request and first-token paths issued a second prediction call for the endpoint that had already been scored, and the TTFT and first TPOT figures reported afterwards came from that later, differently conditioned call rather than from the prediction the placement decision actually used. The merged change keys stored predictions by endpoint name and has the reporting hooks read the stored value instead of re-predicting. A router that scores on a predicted latency must decide that the prediction attached to a decision is the one carried forward for reporting and calibration, and must keep the measured value distinct from the predicted one. This is the decision observability axis.
