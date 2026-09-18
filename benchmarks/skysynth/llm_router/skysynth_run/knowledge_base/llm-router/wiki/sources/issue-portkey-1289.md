---
kind: issue
id: issue-portkey-1289
domain: llm-router
tags: [outage, health, fallback, routing, observability]
url: https://github.com/Portkey-AI/gateway/issues/1289
repo: Portkey-AI/gateway
number: 1289
failure: an open circuit did not remove the failing target from the fallback chain, so every request still paid its failure latency first
---

# Circuit breaker: requests not routed to secondary target immediately when circuit is open

A self hosted deployment configured a fallback strategy with circuit breaker thresholds of five minimum requests and three failures, and after the breaker should have opened the gateway still attempted the first provider on every subsequent request; the reporter measured total latency equal to the first provider's failure time plus the second provider's response time. Fallback worked, but the breaker never filtered the unhealthy target out of the candidate list, so the breaker bought nothing except bookkeeping, and the reporter also had no way to read the breaker's current state or how often it had opened. A router built from scratch must decide that health state is consulted at candidate selection time, before the first attempt, not only as an after the fact record, and must expose the breaker state as part of the decision trace. This is outage and health, with decision observability.
