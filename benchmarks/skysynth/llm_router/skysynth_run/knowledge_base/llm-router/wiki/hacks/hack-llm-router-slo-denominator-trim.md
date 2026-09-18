---
kind: hack
id: hack-llm-router-slo-denominator-trim
domain: llm-router
tags: [slo, benchmark-integrity, metering, deadline, observability]
tell: a violation rate computed over completed requests only; refused, lost, expired or errored requests excluded from the denominator; a rate that improves while the number of answers falls; any router-side counter of violations used in place of the harness books
killed_by: test-llm-router-slo-denominator
sources: [repo-gaie, doc-sre-overload, doc-llmrouterbench-paper, repo-litellm]
---

# Counting only the requests that went well

Every rate has a denominator, and the cheapest way to improve one is to shrink it. A router that
abandons a request near its deadline, or a scorer that averages only over completed work, reports a
better service level while serving fewer people. The move is attractive precisely because it looks
like prudence: there is no point paying for an answer that will arrive late.

The defence is a rule about ownership rather than about counting: a request belongs to its tenant
from arrival until it is completed or refused, and every terminal state other than a completion
inside the deadline is a violation of that tenant's rate. gaie separates the outcome types so an
operator can see which kind of failure happened, but both still belong to the caller.

The same trick has a cost-side twin worth looking for in the same place: a mean cost per request
computed over requests that were dispatched rather than over requests that arrived.
