---
kind: pr
id: pr-gaie-2805
domain: llm-router
tags: [determinism, reproducibility, placement, concurrency]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2805
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2805
changed_paths: [pkg/epp/framework/plugins/scheduling/picker/common.go, pkg/epp/framework/plugins/scheduling/picker/weighted_random_picker.go]
---

# fix: stop reseeding picker RNG on every pick

The endpoint shuffle and the weighted random picker each built a fresh PCG generator seeded from the wall clock on every call, so back to back picks inside one scheduling burst drew from near-identical streams and the spread over equal-weight endpoints was measurably skewed. The merged change hoists a single process-wide generator guarded by a mutex and routes both the shuffle and the weighted draw through it, so the picker consumes one continuous stream. A router built from scratch must decide where its randomness lives: one long-lived, explicitly seeded stream owned by the picker, not a generator constructed per decision. This is the policy state and determinism axis, and it is what makes a placement run reproducible under a fixed seed.
