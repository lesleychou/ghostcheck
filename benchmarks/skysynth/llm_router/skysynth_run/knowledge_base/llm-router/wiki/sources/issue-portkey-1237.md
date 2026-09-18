---
kind: issue
id: issue-portkey-1237
domain: llm-router
tags: [caching, correctness, outage, production, consistency]
url: https://github.com/Portkey-AI/gateway/issues/1237
repo: Portkey-AI/gateway
number: 1237
failure: a simple exact match cache behaved as a semantic cache, driving the hit rate to nearly 100 percent and serving wrong responses until the platform stalled
---

# Bug Report: Simple Cache Incorrectly Converted to Semantic Cache Causing Platform Outage

A production deployment running a simple cache saw its cache mode effectively become semantic, so requests that were merely similar matched existing entries, the hit rate climbed to nearly 100 percent, and the platform became unresponsive to all customers. The reported expectation is that a simple cache keeps exact key matching and that hit rate tracks normal usage, which makes an unexplained jump toward total hit rate an actionable alarm rather than a win. A router built from scratch must decide that cache mode is policy state that cannot change without an explicit config change, and must treat the cache hit rate as a health signal with a ceiling, since a cache that answers everything is indistinguishable from a cache that answers wrongly. This is policy state and determinism, with cost control and decision observability.
