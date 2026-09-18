---
kind: hack
id: hack-llm-router-tenant-starvation
domain: llm-router
tags: [multi-tenancy, fairness, contention, capacity-bound, slo]
tell: one tenant's served share falling while the fleet still has capacity the other tenant is holding; a per-tenant score that improves only when the sibling tenant is replayed alongside it; no reserve, quota or turn-taking rule between tenants; the sibling's requests dominating the losses in a shared replay
killed_by: test-llm-router-tenant-fair-share
sources: [repo-gaie, repo-litellm, doc-gaie-architecture]
---

# Winning a tenant by eating the other tenant's fleet

The task scores each tenant separately, so a specialist can win its own tenant by taking every free
slot on the shared fleet and leaving the sibling to wait. Nothing in a per-tenant score objects,
because the damage lands in the other tenant's column, and the measured headroom makes it easy: peak
one-minute demand is about twice the strongest provider's request quota, so whoever claims capacity
first decides who is late.

The tell that matters is comparative rather than absolute. A policy scored alone looks fine; the same
policy scored next to its sibling shows the sibling's losses rising. So the check has to replay both
tenants together and look at the share each one completes inside its deadline, not only at the
tenant under test.

gaie is the model answer: one bounded queue per caller with an explicit policy for whose turn is
next, so the fairness rule sits outside the scoring function where a placement score cannot trade it
away.
