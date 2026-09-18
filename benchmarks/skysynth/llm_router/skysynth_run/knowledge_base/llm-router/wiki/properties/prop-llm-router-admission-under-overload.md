---
kind: property
id: prop-llm-router-admission-under-overload
domain: llm-router
tags: [admission, overload, queueing, slo, correctness]
values: [wait indefinitely for capacity, wait inside a bounded queue and then refuse, refuse immediately with an overload status, refuse only when a measured saturation signal says the fleet is full]
seen_in: [repo-litellm, repo-portkey, repo-gaie]
sources: [repo-litellm, repo-portkey, repo-gaie, doc-sre-overload, doc-gaie-architecture]
---

# What happens when nothing can serve the request right now

This is the axis the reference systems disagree on most. Portkey never queues: if no target accepts,
the caller gets the failure. litellm refuses immediately unless the caller supplied a priority, in
which case the request joins an ordered wait set polled until the router timeout, and a waiter that
gives up is removed so the wait set cannot grow without bound. gaie queues with a per-workload
bound, and refuses for load only when the request's priority is negative and a measured saturation
signal reports the fleet full.

Both mistakes are typed failures. Waiting forever loses the request: it ends neither completed nor
refused, and nobody is told. Refusing while some provider still had request, token and concurrency
headroom for a legally substitutable model is a refusal the fleet did not force, which is the
cheapest way to make an average look good. A build has to state which measurement authorises a
refusal, and it has to be a measurement of the fleet rather than of the request's difficulty.
