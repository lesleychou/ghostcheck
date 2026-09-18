---
kind: pr
id: pr-litellm-40636
domain: llm-router
tags: [rate-limit, provider-api, validation, cost, production]
url: https://github.com/BerriAI/litellm/pull/40636
repo: BerriAI/litellm
number: 40636
changed_paths: [litellm/proxy/hooks/dynamic_rate_limiter_v3.py, tests/test_litellm/proxy/hooks/test_dynamic_rate_limiter_v3.py]
---

# fix(rate_limiter): skip non-Latin-1 x-litellm-priority header on /v1/messages

The dynamic rate limiter attached the caller's priority value as a response header, and a team whose priority string was not Latin-1 encodable made the HTTP layer raise while serializing the response, turning every Messages API call into a 500. The upstream provider call had already succeeded and was billed, so the customer paid for an error, and the merged change emits the priority header only when its value is encodable and leaves the rate limiter version and the standard ratelimit headers untouched. A router that echoes internal policy state back as response headers must validate that state against the transport's encoding rules at the boundary, and must never let a post-call observability step destroy a response whose cost has already been incurred. The axis is deadline and priority, with decision observability attached.
