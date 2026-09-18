---
kind: property
id: prop-llm-router-decision-observability
domain: llm-router
tags: [observability, metering, correctness, latency, routing]
values: [nothing beyond the answer, a per-decision record naming the target and the reason, distinct caller-visible statuses per failure class, metrics measured after the fact rather than predicted, errors surfaced rather than swallowed]
seen_in: [repo-portkey, repo-gaie, repo-litellm]
sources: [repo-portkey, repo-gaie, repo-litellm, doc-gaie-architecture, issue-portkey-1206]
---

# What the router makes visible about why a request went where it did

Portkey returns the address of the config node that served the request, the trace identifier, the
attempt count, the cache status and the provider name, so a decision can be reconstructed after the
fact from the response alone. gaie separates the failure classes deliberately: an empty candidate
set and a placement failure produce two different caller-visible statuses, and admission runs before
the candidates are located so the two cannot be confused. litellm emits the chosen deployment and
the attempt history through callbacks.

None of the three lets what it reports change the outcome, and that separation is the point. When a
harness bills and scores from its own books, a self-reported number is an operator convenience, and
a router whose report disagrees with the books is either wrong or fishing. Two shapes of bug show up
repeatedly in the mined history: a duration that was measured over the wrong span, and a metric
reported from a prediction the router made rather than from what actually happened. Both make a
policy look better than it is without changing a single dispatch.

The failure mode at the far end of this axis is not a wrong number but no number: an unhandled rejection inside a stream transform crashed the gateway instead of surfacing as an error the caller could see.
