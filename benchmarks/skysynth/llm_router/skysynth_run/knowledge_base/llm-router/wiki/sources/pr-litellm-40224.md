---
kind: pr
id: pr-litellm-40224
domain: llm-router
tags: [health, outage, concurrency, consistency, scalability]
url: https://github.com/BerriAI/litellm/pull/40224
repo: BerriAI/litellm
number: 40224
changed_paths: [litellm/router.py, litellm/router_utils/cooldown_handlers.py, tests/test_litellm/router_utils/test_cooldown_handlers.py, tests/test_litellm/router_utils/test_health_check_allowed_fails_integration.py]
---

# fix(router): count allowed_fails in the shared router cache so multi-worker proxies bench a deployment fleet-wide

Cooldown state was shared through Redis but the allowed_fails counter that triggers a cooldown was kept in a per-process in-memory cache, so with four workers and a threshold of five a dead deployment kept serving errors until one single worker had independently observed six failures, multiplying the user-visible failures by the worker count. The merged change increments the counter through the router's shared dual cache under a per-deployment key with the cooldown TTL, drops the per-process store, and degrades to the local tier if the Redis increment raises rather than failing the request. A router must decide whether the evidence that trips a circuit is per-process or fleet-wide, and keeping the trigger local while the verdict is global makes the effective threshold scale with replica count. The axis is outage and health under concurrency.
