---
kind: pr
id: pr-litellm-40225
domain: llm-router
tags: [cost, routing, observability, consistency, load-balancing]
url: https://github.com/BerriAI/litellm/pull/40225
repo: BerriAI/litellm
number: 40225
changed_paths: [litellm/router_strategy/lowest_cost.py, tests/test_litellm/router_strategy/test_lowest_cost.py]
---

# fix(router): give cost-based routing its own cache key so it stops overwriting latency samples

Cost-based routing and latency-based routing both wrote their whole state dict to the same per-model-group Redis entry, so a proxy on the cost strategy erased the latency samples a sibling proxy on the latency strategy had just recorded. The latency router then saw every deployment as never measured, and the merged change moves cost counters under a distinct prefixed key so the two strategies cannot alias each other. A router must treat each routing strategy's accumulated statistics as private state with its own namespace, and must never write a read-modify-write of a whole shared blob when another writer owns part of it. The axis is policy state and determinism, feeding model selection.
