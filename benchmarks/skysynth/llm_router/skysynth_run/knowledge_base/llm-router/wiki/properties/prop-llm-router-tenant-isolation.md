---
kind: property
id: prop-llm-router-tenant-isolation
domain: llm-router
tags: [multi-tenancy, fairness, contention, queueing, capacity-bound]
values: [no isolation and first come first served, per-caller spend or request budgets, one bounded queue per caller with a fairness policy choosing whose turn it is, a reserved share of fleet capacity per tenant]
seen_in: [repo-litellm, repo-gaie, repo-portkey]
sources: [repo-litellm, repo-gaie, repo-portkey, doc-gaie-architecture]
---

# What stops one traffic shape from starving another on a shared fleet

gaie is the only reference system that treats this as a scheduling contract: one bounded queue per
caller and priority band, a swappable fairness policy that decides which queue is served next, and a
test that separates a greedy pick that ignores band boundaries from a starvation-free one. The
capacity check and the enqueue are atomic there, so an over-capacity item is refused rather than
queued.

litellm isolates by money and by quota rather than by turn: per-key, per-team and per-provider
budgets remove a caller's targets from selection once its cap is reached. Portkey has no notion of a
neighbour at all, since each request carries its own config.

On a fleet whose one-minute request quota is exceeded twice over by a single tenant's burst, the
question is unavoidable: two specialised routers that each optimise their own score can be jointly
worse than one compromise, because the burst of one lands exactly in the batch wave of the other. A
build must state what the other tenant is guaranteed while this one is bursting, and a policy that
wins by consuming the shared headroom first has answered that it is guaranteed nothing.
