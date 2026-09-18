---
kind: pr
id: pr-litellm-37736
domain: llm-router
tags: [cost, budget, metering, multi-tenancy, correctness]
url: https://github.com/BerriAI/litellm/pull/37736
repo: BerriAI/litellm
number: 37736
changed_paths: [litellm/proxy/hooks/model_max_budget_limiter.py, litellm/proxy/auth/user_api_key_auth.py, litellm/proxy/auth/auth_utils.py, litellm/proxy/litellm_pre_call_utils.py, litellm/proxy/management_endpoints/key_management_endpoints.py, litellm/proxy/_types.py]
---

# fix(proxy): make per-model budgets track spend, enforce, and report the same counter

Per-model budgets were enforced against one counter key, incremented under another, and reported from a third, so a cap on a model could show zero usage forever while spend accrued, and a Bedrock deployment id never matched a budget keyed on the bare family name. The merged change gives the counter a single owner, the configured budget model, shared by the admission check, the post-call increment, and the info endpoints, resolves provider-specific ids to their cost-map family name, and extends enforcement to the user scope and to native passthrough routes that previously counted nothing. A router built from scratch must decide on one canonical identity for a spend counter and derive every read, write, and enforcement decision from that same identity, because a budget enforced against a key nobody increments is a cap that does not exist. The axis is cost control, with tenant isolation riding on it.
