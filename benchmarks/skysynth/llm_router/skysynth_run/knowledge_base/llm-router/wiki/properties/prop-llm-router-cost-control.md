---
kind: property
id: prop-llm-router-cost-control
domain: llm-router
tags: [cost, budget, metering, quality, correctness]
values: [no cost awareness, soft price preference inside the ranking, weighted quality versus price objective, a hard spend cap that removes a target once crossed, a target share of expensive calls fixed in advance]
seen_in: [repo-litellm, repo-routellm, repo-llmrouterbench, repo-portkey]
sources: [repo-litellm, repo-routellm, repo-llmrouterbench, repo-portkey, doc-routellm-paper, doc-frugalgpt, doc-llmrouterbench-paper, pr-litellm-40225]
---

# Whether spend is bounded by anything other than the traffic

The reference systems split into soft and hard. LLMRouterBench's balanced baseline is soft: one
objective weighting quality against price, at default weights 0.7 and 0.3, so a large enough quality
gain always justifies a larger bill. litellm is hard: a provider or deployment spend cap that
removes those targets from selection once reached, end to end, while its siblings keep serving.
Portkey ships the seam rather than the policy: a pre-request validator that is a no-op when nothing
is installed and can short-circuit the request with its own answer when something is.

RouteLLM contributes the third form, which is neither a preference nor a cap: calibration fixes the
share of traffic that may go to the expensive model, and the threshold is derived from that share
rather than from a quality target. That is the form that survives contact with a scored benchmark,
because it states the price of the quality up front.

Whatever form is chosen, the number that counts is the one the harness's own books produce. The
provider's meter and an independent ledger are reconciled at the end of a run, a bill is never
negative and never below the all-cached floor, and what the router reports about its own spend is
for the operator, not for the score.

A caution from the same history: cost-based routing had to be given its own cache key because it was overwriting the latency samples another strategy depended on, so one price-aware path quietly degraded a latency-aware one.
