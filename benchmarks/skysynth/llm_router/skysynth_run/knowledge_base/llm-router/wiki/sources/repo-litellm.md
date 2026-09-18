---
kind: repo
id: repo-litellm
domain: llm-router
tags: [routing, placement, cost, rate-limit, production]
url: https://github.com/BerriAI/litellm
sha: 30f33a949b8a2bb890a2baee18e2ab7ab015a4f7
license: MIT (enterprise/ subtree excluded)
following: 58648 stars, the largest following of any open LLM gateway
production: shipped release v1.100.1, deployed as a proxy in front of paid provider accounts, with per-key budgets and spend logs
---

# litellm: a production LLM gateway whose Router picks the deployment

The closest production analogue of a per-tenant LLM router. One `Router` object holds a list of
deployments for each model group and decides which one serves a call, then paces it against the
deployment's requests-per-minute and tokens-per-minute counters, retries it, falls back to a
declared sibling, quarantines a deployment that keeps failing, and books the spend against a key or
team budget. Every axis this domain cares about is a concrete, shipped, separately configurable
policy here, which is why it grounds most of the properties.

Read at commit 30f33a949b8a2bb890a2baee18e2ab7ab015a4f7 from the clone made for this run. The parts
that matter are `litellm/router.py`, `litellm/router_strategy/` (lowest cost, lowest latency, usage
based, adaptive bandit), `litellm/router_utils/` (cooldown handlers, fallbacks, error handling),
and the budget limiter under `litellm/proxy/hooks/`.
