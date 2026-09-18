---
kind: pr
id: pr-litellm-40025
domain: llm-router
tags: [health, outage, caching, consistency, latency]
url: https://github.com/BerriAI/litellm/pull/40025
repo: BerriAI/litellm
number: 40025
changed_paths: [litellm/router_utils/cooldown_cache.py, litellm/constants.py, tests/test_litellm/router_utils/test_cooldown_cache.py, tests/router_unit_tests/test_router_cooldown_per_deployment.py]
---

# fix(router): give cooldowns their own cache so siblings see a bench in ~1s

Cooldowns were stored in the router's general dual cache, whose in-memory tier refreshed from Redis only every ten seconds and whose bounded size could evict a live cooldown entirely, so sibling replicas kept routing to a deployment one replica had already benched. The merged change gives cooldowns a dedicated cache over the same Redis with a one second refresh interval and an in-memory tier that holds only cooldown keys, leaving the router-wide cache at its ten second interval so the cheaper keys do not pay for the freshness. A router must decide per class of shared state how stale it may be, because quarantine state is the one thing whose staleness directly routes traffic into a known-dead backend, and it must never let that state share an eviction budget with high-volume counters. The axis is outage and health.
