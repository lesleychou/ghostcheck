---
kind: pr
id: pr-litellm-30098
domain: llm-router
tags: [rate-limit, retry, overload, provider-api, observability]
url: https://github.com/BerriAI/litellm/pull/30098
repo: BerriAI/litellm
number: 30098
changed_paths: [litellm/proxy/common_request_processing.py, tests/test_litellm/proxy/test_common_request_processing.py]
---

# fix(proxy): set Retry-After header on RouterRateLimitError 429 responses

When every deployment in a model group was in cooldown the router answered 429 but sent no Retry-After header, so the client had no signal for when capacity would return and retried on its own schedule, typically immediately and into the same wall. The merged change carries the router's known cooldown remainder into a Retry-After header on those 429 responses. A router that rejects for lack of capacity already knows when capacity is expected back, and a design must decide to publish that number rather than leave every caller to guess, because uncoordinated client retries against a cooling fleet are the mechanism that turns a partial outage into an overload. The axis is admission and overload, feeding the caller's retry and fallback policy.
