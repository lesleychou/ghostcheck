---
kind: test
id: test-llm-router-decision-budget
domain: llm-router
tags: [lifecycle, correctness, queueing, slo, resource-leak]
enforces: prop-llm-router-policy-state-and-determinism
command: python3 test_decision_budget.py
mutant: StallMutant in mutants.py, which always waits
confidence: verified
sources: [repo-litellm, repo-gaie, doc-sre-overload, issue-gaie-2878, issue-litellm-40564]
---

# Waiting forever is losing the request, not being patient

A request parked in a wait loop is never completed, never refused, and never counted, which makes
waiting the cheapest way to hide a request a policy cannot serve. The test measures how many
decisions the reference needs per request, which is one on an unloaded fleet, and then replays a
router that always waits and requires the progress budget to stop it with nothing completed.

Both reference systems bound this somewhere. litellm removes a waiter that gives up from its wait
set so the set cannot grow, and gaie waits for capacity for exactly a request's own time to live
before returning a distinct expired outcome. The unbounded version shows up in their bug histories
as a resource problem: an oversized prefix cache index that could exhaust memory, and a budget reset
job that exceeded a database parameter limit and never completed at all.
