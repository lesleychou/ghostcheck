---
kind: property
id: prop-llm-router-quota-pacing
domain: llm-router
tags: [rate-limit, quota, capacity-bound, throughput, routing]
values: [ignore quota and learn from rejections, track a local counter and pre-subtract this request's own cost, read the published remaining headroom before dispatch, hold back a reserve of headroom for urgent traffic]
seen_in: [repo-litellm, repo-portkey, repo-gaie]
sources: [repo-litellm, repo-portkey, repo-gaie, doc-rfc6585, roof-llm-router-shared-fleet, pr-gaie-2802, pr-gaie-2848, pr-gaie-2819]
---

# How the router stays inside an upstream's request and token quota

litellm keeps per-deployment request and token counters and excludes an exhausted deployment from
the candidate set before dispatch, rather than dispatching and being rejected. Portkey does not pace
at all by default: a provider rate limit arrives as a status code and is handled by the retry and
fallback config. gaie paces against a live utilisation estimate and treats a target whose state is
missing or stale as fully saturated.

The choice is not cosmetic on a shared fleet. Measured on this run's traces, peak one-minute demand
is 1.8 to 2.1 times the strongest single provider's request quota while the three providers together
are under 40 percent utilised, so a router that ignores headroom does not merely collect rejections:
it concentrates them on the provider it likes and turns a spread-out burst into a wall of refusals.
The build must decide whether an estimate of this request's own token cost is subtracted before
dispatch or only after the answer comes back, because under a burst the difference is the whole
error.

Whatever counter the pacing reads has to survive the path that maintains it. gaie fixed an in-flight concurrency counter that drifted on decrement, a prefill token counter that could go negative, and an in-flight load structure that was shared by reference where a copy was needed. A pacing rule is only as good as the arithmetic under it.
