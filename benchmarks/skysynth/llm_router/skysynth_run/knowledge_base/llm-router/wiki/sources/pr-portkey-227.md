---
kind: pr
id: pr-portkey-227
domain: llm-router
tags: [load-balancing, routing, validation, correctness]
url: https://github.com/Portkey-AI/gateway/pull/227
repo: Portkey-AI/gateway
number: 227
changed_paths: [src/handlers/handlerUtils.ts]
---

# Fix: allow loadbalance zero weight

The loadbalance strategy defaulted a missing weight to 1 using a falsy check, so an operator who set a weight of zero to drain a target had that zero rewritten to 1 and the target kept receiving its share of traffic. The merged change tests for `undefined` instead, so an explicit zero stays zero and only an absent weight gets the default. A router built from scratch must decide that zero is a valid, meaningful weight and reserve the default only for the unset case, otherwise operators have no way to take a target out of rotation without deleting it from the config. This touches placement and policy state, since weights are the operator's only lever on target selection.
