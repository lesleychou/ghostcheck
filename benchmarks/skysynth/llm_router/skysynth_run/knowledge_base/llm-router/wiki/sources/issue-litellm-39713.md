---
kind: issue
id: issue-litellm-39713
domain: llm-router
tags: [rate-limit, caching, multi-tenancy, quota, consistency]
url: https://github.com/BerriAI/litellm/issues/39713
repo: BerriAI/litellm
number: 39713
failure: per-customer rpm and tpm limits stop being enforced for every request served from the cached virtual key object, so the configured rate limit is silently inert
---

# [Bug]: Per-customer RPM limits stop applying once the virtual key is cached

A per-customer budget object carrying an rpm limit is enforced only on the first request after the virtual key enters the proxy's in-memory key cache; every subsequent request served from that cache skips the limit entirely, because the end-user rate limit fields are populated during the uncached key lookup and are not part of what the cache stores. Spend limits on the same budget object keep working and the management endpoints read the limit back correctly, so nothing signals that the control is dead, and the only workaround is disabling the key cache and paying a lookup per request. The decision a router must make is which parts of an authorization object are safe to cache: any policy field derived at lookup time must either be cached with the object or recomputed on every request, never silently dropped. The axis is rate limit pacing under tenant isolation, with policy state and determinism behind it.
