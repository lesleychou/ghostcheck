---
kind: test
id: test-llm-router-equiv-class
domain: llm-router
tags: [model-selection, correctness, quality, routing]
enforces: prop-llm-router-model-selection
command: python3 test_equiv_class.py
mutant: OutsideEquivClassMutant in mutants.py, which serves a cheaper model the request never allowed
confidence: verified
sources: [repo-litellm, repo-routellm, repo-llmrouterbench, pr-litellm-40757, issue-routellm-7]
---

# A served model stays inside the request's equivalence class

Substitution is the biggest lever a router has and the easiest one to abuse, so the boundary has to
be executable. The test replays a clean trace with the reference router, checks that every dispatch
named a model from the request's own equivalence class, then replays the same trace with a mutant
that serves an unlisted cheap model and requires the replay to fail with the substitution named.

The reference systems both motivate and complicate this. litellm resolves a model name to a list of
deployments of that same model, so its substitution is of the endpoint and never of the model; its
tiered routers fall back to a different tier only when the chosen one is unusable, which is a
decision the operator configured. A missing entry in a model map is a real failure mode rather than
a theoretical one, as the RouteLLM issue about a routed model absent from the identifier map shows.
