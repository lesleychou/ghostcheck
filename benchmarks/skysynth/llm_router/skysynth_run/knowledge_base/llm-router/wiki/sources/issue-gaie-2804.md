---
kind: issue
id: issue-gaie-2804
domain: llm-router
tags: [determinism, reproducibility, placement, benchmark-integrity]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/issues/2804
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2804
failure: the weighted random picker reseeds a fresh RNG from the wall clock on every pick, so repeated sampling is timing-dependent and biased
---

# WeightedRandomPicker reseeds per pick and makes picker tests flaky

The picker constructed a new generator seeded from the current nanosecond on each Pick call, so the endpoint distribution over many picks depended on how fast the calls were issued rather than on the configured weights, and the uniformity assertion drifted to 0.280 against an expected 0.333. The report is explicit that the fix is a stable RNG stream owned by the picker, not a per-call seed, and that the test flake was only the visible symptom of a biased production distribution. A router built from scratch must decide up front that its randomness is a single long-lived seeded stream, and must be able to replay a routing run from that seed. This is the policy state and determinism axis, and it is the difference between a benchmark number that means something and one that does not.
