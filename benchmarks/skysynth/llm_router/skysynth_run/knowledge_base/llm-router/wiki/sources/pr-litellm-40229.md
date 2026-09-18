---
kind: pr
id: pr-litellm-40229
domain: llm-router
tags: [resource-leak, determinism, rate-limit, routing, multi-tenancy]
url: https://github.com/BerriAI/litellm/pull/40229
repo: BerriAI/litellm
number: 40229
changed_paths: [litellm/router.py, tests/test_litellm/router_strategy/test_router_routing_groups.py]
---

# fix(router): keep per-request routing_strategy override selectors out of global callbacks

A single request carrying a per-request routing strategy override built a selector that registered itself into the process-wide callback lists and stayed there for the life of the worker, so every later request on that worker ran the overriding strategy's pre-call check as well: with usage-based routing that meant unrelated traffic on a simple-shuffle proxy started getting rpm 429s. The merged change builds override selectors without registering global callbacks and runs the override selector's own pre-call check only for the request that asked for it, keeping the existing caching and reinit behavior of the override selectors. A router that lets a request override policy must scope both the selector and its side effects to that request, or per-request policy silently becomes sticky process state that leaks across tenants. The axis is policy state and determinism, with tenant isolation at stake.
