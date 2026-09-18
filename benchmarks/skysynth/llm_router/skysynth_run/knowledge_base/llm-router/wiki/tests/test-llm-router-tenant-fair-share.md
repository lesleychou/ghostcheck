---
kind: test
id: test-llm-router-tenant-fair-share
domain: llm-router
tags: [multi-tenancy, fairness, contention, capacity-bound, queueing]
enforces: prop-llm-router-tenant-isolation
command: python3 test_tenant_fair_share.py
mutant: HeadroomHogMutant in mutants.py, the reference with the per-tenant reserve removed
confidence: verified
sources: [repo-gaie, repo-litellm, doc-gaie-architecture, pr-gaie-2674, issue-litellm-39713, issue-litellm-40095, roof-llm-router-shared-fleet]
---

# One tenant's burst may not consume the other tenant's capacity

Two tenants share one fleet: a bursty one that can substitute freely and a batch one that cannot.
With a reserve of half of each provider's concurrency per tenant, both finish everything. With the
reserve removed, the bursty tenant holds every slot and a batch request is starved until it burns
its progress budget, which the test requires the replay to catch and attributes to the starved
tenant.

gaie is the only reference system that treats this as a contract: one bounded queue per caller and
priority band with a policy deciding whose turn it is, and a concurrency accounting path careful
enough that a missing read lock on the ordered priority levels was worth a fix. litellm isolates by
money instead, and its issues show how quickly that leaks: per-customer limits stopped applying once
the key was cached, and concurrent first requests for an unknown end user bypassed the default
budget entirely.
