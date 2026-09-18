---
kind: pr
id: pr-litellm-39675
domain: llm-router
tags: [fallback, health, model-selection, routing, recovery]
url: https://github.com/BerriAI/litellm/pull/39675
repo: BerriAI/litellm
number: 39675
changed_paths: [litellm/router_strategy/complexity_router/complexity_router.py, litellm/types/utils.py, tests/test_litellm/router_strategy/test_complexity_router.py]
---

# fix(complexity_router): fall back to a live peer when the decided tier model is fully cooled down

A complexity tier can list several models, but the tier pick ignored deployment health, so once one tier model's deployments went into cooldown roughly half the traffic was routed to it and answered 429, and a session pinned to that model failed every remaining turn until the pin expired about an hour later. The merged change adds one health gate at the hook's exits, swaps a model group with no capacity for a live peer in the same tier through the normal tier pick so plugins still apply, and fails open when health is uncertain. The decision this forces is where the health filter sits relative to the semantic pick: a router that chooses a model by request class and only then checks liveness must be able to re-pick within the class, and session affinity must be revocable when the pinned target is down. The axis is model selection crossed with outage and health.
