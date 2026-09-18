---
kind: property
id: prop-llm-router-placement
domain: llm-router
tags: [placement, latency, load-balancing, cost, routing]
values: [first target that stocks the model, cheapest eligible target, lowest observed latency, least in-flight or least loaded, affinity to a previously used target]
seen_in: [repo-litellm, repo-portkey, repo-gaie]
sources: [repo-litellm, repo-portkey, repo-gaie, doc-gaie-architecture, doc-melange, pr-gaie-2415, issue-gaie-2394, pr-gaie-2823, pr-litellm-40202, pr-routellm-11]
---

# Which provider serves the chosen model

Once the model is fixed, several providers may stock it and they differ in price, speed and current
load. Every reference system ships more than one answer and lets an operator pick, which is the
clearest sign that no single rule dominates.

gaie states the shape most explicitly: placement is exclusion, then ranking, then selection, with
exclusion short-circuiting when it eliminates every target. litellm ships first-listed, cheapest,
lowest observed latency and usage-based strategies as interchangeable objects, and applies price
ranking only to targets that still have request and token headroom. Portkey resolves placement by
walking a config tree of weighted targets and fallback nodes.

Two things separate a placement rule from a scoring hack. The eligible set is structural and comes
first: a provider that does not stock the model is not a cheap option, it is an illegal one.
Ranking inside that set is soft and may trade price against expected time to answer, but it may not
put back a candidate that eligibility removed.

The mined fixes show where a placement score goes wrong in practice. A latency predictor panicked on a request shape it did not expect and had to be made safe on that path, a prefix-affinity hash turned every request carrying a long media reference into one hotspot, and a streaming latency ranking had to be corrected to rank by raw time to first token instead of time to first token per output token. The RouteLLM gateway integration is the reminder that the candidate set can span providers at all, which is what makes placement a separate question from model choice.
