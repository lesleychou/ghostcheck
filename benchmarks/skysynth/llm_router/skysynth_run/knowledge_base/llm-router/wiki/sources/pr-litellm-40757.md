---
kind: pr
id: pr-litellm-40757
domain: llm-router
tags: [routing, fallback, health, model-selection, recovery]
url: https://github.com/BerriAI/litellm/pull/40757
repo: BerriAI/litellm
number: 40757
changed_paths: [litellm/router.py, litellm/router_strategy/adaptive_router/adaptive_router.py, litellm/router_strategy/complexity_router/complexity_router.py, litellm/types/utils.py, tests/test_litellm/test_router.py]
---

# fix(router): fall back from unhealthy auto-router tier

The auto-router classified a request into a tier and then committed to that tier even when its only deployment could not serve, returning the upstream failure instead of using the configured default model, and a tier whose budget was exhausted or whose tag filters matched nothing read as live so the recovery path never ran. The merged change routes to the healthy default model when the selected tier has no capacity and treats budget exhaustion and empty tag matches as a no-capacity verdict rather than a healthy one. A router that picks a tier or class before it picks a deployment must decide whether that classification is binding, and must make every filter that can empty a candidate set report the same no-capacity signal, otherwise one filter silently disables the fallback path. The axis is retry and fallback, driven by outage and health.
