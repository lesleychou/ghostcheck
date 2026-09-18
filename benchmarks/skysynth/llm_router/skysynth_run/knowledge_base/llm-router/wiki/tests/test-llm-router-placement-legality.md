---
kind: test
id: test-llm-router-placement-legality
domain: llm-router
tags: [placement, correctness, routing, validation]
enforces: prop-llm-router-placement
command: python3 test_placement_legality.py
mutant: UnstockedTargetMutant in mutants.py, which sends the flagship model to the provider that does not stock it
confidence: verified
sources: [repo-gaie, repo-litellm, pr-gaie-2583, pr-gaie-2126, pr-portkey-227]
---

# A dispatch goes only to a provider that stocks the chosen model

Eligibility is structural and comes before preference: a provider that does not stock the model is
not an expensive option or a slow option, it is an illegal one. The test checks every dispatch the
reference router made against the fleet's catalogue, then replays a mutant that sends a model to a
provider without it and requires a typed failure rather than a reschedule.

The distinction is worth a test because the reference systems keep finding new ways to blur it. A
gaie fix corrects a selection strategy that mishandled negative headroom, another makes endpoint
subset filtering switchable, and a Portkey fix restores an explicit load-balance weight of zero that
a falsy check had been quietly rewriting to one. In each case a candidate that should have been out
of the running was in it.
