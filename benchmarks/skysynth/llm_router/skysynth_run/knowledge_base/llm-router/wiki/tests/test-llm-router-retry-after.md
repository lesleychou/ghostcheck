---
kind: test
id: test-llm-router-retry-after
domain: llm-router
tags: [retry, rate-limit, latency, provider-api, recovery]
enforces: prop-llm-router-retry-and-fallback
command: python3 test_retry_after.py
mutant: ImpatientRetryMutant in mutants.py, which re-attempts the rejecting target on the next tick
confidence: verified
sources: [doc-rfc6585, doc-rfc9110, repo-litellm, repo-portkey, pr-litellm-30098, pr-portkey-1030, pr-portkey-1010]
---

# A rejected target is not re-attempted before it said it would be ready

A provider that refuses states when it will be ready. Re-attempting it sooner is a decision to
ignore that, and under a burst it converts one rejection into a storm of them. The test counts
re-attempts made before the advertised retry-after has elapsed: the reference makes none because it
reads headroom first, and the impatient mutant makes hundreds.

The reference systems agree that the wait belongs to the server. litellm had to start setting a
Retry-After header on its own rate-limit responses so that its callers could honour one. Portkey
added honouring a retry-after header and skipping its own exponential back-off when the server
supplied a time, and separately stopped applying default retry status codes when no retry budget was
configured at all, which is the opposite mistake: retrying something nobody asked to have retried.
