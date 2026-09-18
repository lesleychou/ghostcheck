---
kind: test
id: test-llm-router-slo-denominator
domain: llm-router
tags: [slo, deadline, benchmark-integrity, metering, quality]
enforces: prop-llm-router-deadline-and-priority
command: python3 test_slo_denominator.py
mutant: DoomedDropMutant in mutants.py, which gives up on a request whose deadline already passed
confidence: verified
sources: [repo-gaie, repo-litellm, doc-sre-overload, doc-llmrouterbench-paper, issue-litellm-39309]
---

# A refused or lost request stays in the denominator

The test has two halves. First it takes the whole fleet down, so the reference router's refusals are
ones the fleet really forced, and checks the books: the violation rate is 1.0 and the mean quality is
0.0, so a refusal is counted and earns nothing. Then it saturates the fleet until the reference is
late on fourteen of forty requests and replays a mutant that abandons any request whose deadline has
already passed. The mutant does not lower the violation rate; it is stopped for refusing while the
fleet still had room.

The rule this pins is the one that makes the whole score meaningful. gaie already separates a
deadline-expired outcome from a capacity rejection so the two cannot be confused in a caller's
metrics. The point here is stronger: both belong to the tenant that owns the request, so no policy
can improve its rate by choosing which requests to stop counting.
