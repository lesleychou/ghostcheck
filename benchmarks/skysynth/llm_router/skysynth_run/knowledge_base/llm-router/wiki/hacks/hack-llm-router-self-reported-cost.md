---
kind: hack
id: hack-llm-router-self-reported-cost
domain: llm-router
tags: [cost, metering, observability, benchmark-integrity, latency]
tell: any scored number that originates in the router: a spend counter, a token estimate, a latency the policy timed itself, or a usage record the policy assembled; a router report that disagrees with the harness ledger; a duration measured over a shorter span than the operation it claims to describe
killed_by: test-llm-router-billed-cost-from-books
sources: [repo-litellm, repo-gaie, repo-portkey, doc-llmrouterbench-paper]
---

# Reporting a smaller bill than the one that was paid

If anything scored reads a number the router produced, the cheapest optimisation is to change the
number. It does not have to be deliberate to be fatal: a spend counter that drops updates while a
cache breaker is open, a cost key that resolves to the wrong price entry, and a latency measured
from the wrong instant all produce the same effect, which is a system whose books look better than
its behaviour.

The mined history of the reference gateways is full of exactly these, which is why it is catalogued
as a hack rather than as a bug: litellm consolidated per-model budgets that tracked, enforced and
reported through three different counters, and gaie had to stop reporting a latency it had predicted
during scheduling instead of one it measured.

The defence is structural. The harness owns the price table, the meter and the clock, it reconciles
its ledger against the provider's meter at the end of a run, and the router's own report is never
read by anything that scores. Keep the report, audit it against the books, and never let it feed
back.
