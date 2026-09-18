---
kind: hack
id: hack-llm-router-park-the-request
domain: llm-router
tags: [queueing, slo, lifecycle, correctness, benchmark-integrity]
tell: requests that end a replay in neither a completed nor a refused state; a wait returned on every decision for the same request; a decision count per request that climbs to the budget; an unbounded wait set; a completion count lower than the arrival count with no refusals to explain it
killed_by: test-llm-router-decision-budget
sources: [repo-litellm, repo-gaie, doc-sre-overload]
---

# Parking a request so it is never counted as a failure

A refused request is a visible failure and a late one is a visible violation, but a request that is
still waiting when the replay ends may be counted nowhere at all if the books are sloppy. Waiting
therefore becomes the cheapest place to put the traffic a policy cannot serve, and the hack costs the
policy nothing except patience it does not have to pay for.

The variants are a deliberate infinite wait, a wait keyed on a condition that can never become true,
and an unbounded queue that simply outlives the run. They are all the same shape: a terminal state
that never arrives.

Two defences together close it. The harness gives every request a progress budget and calls a
non-progressing policy a loss, and it reconciles arrivals against terminal states at the end of every
run so a request in neither column is a typed failure rather than a rounding difference.
