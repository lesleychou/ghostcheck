---
kind: property
id: prop-llm-router-model-selection
domain: llm-router
tags: [model-selection, quality, cost, routing]
values: [serve exactly the model the caller named, substitute freely inside a declared equivalent set, substitute only when the caller allows a downgrade, start on the cheap model and escalate on a confidence signal]
seen_in: [repo-litellm, repo-portkey, repo-routellm, repo-llmrouterbench]
sources: [repo-litellm, repo-portkey, repo-routellm, repo-llmrouterbench, doc-routellm-paper, doc-frugalgpt, doc-llmrouterbench-paper, issue-routellm-9]
---

# Which model actually serves a request that named one

A request names a model. The router decides whether that name is an instruction or a hint, and the
answer is the single largest lever on both quality and spend.

litellm treats the name as a group and resolves it to one of several deployments that all serve that
same model, so the model is honoured and only the endpoint varies. Portkey treats the name as one
field of a config node, and a fallback node may name a different model entirely, so substitution is
possible but only where an operator wrote it down. RouteLLM makes substitution the whole point: a
predicted win rate is compared against a calibrated threshold and everything below it goes to the
weak model. LLMRouterBench's baselines pick one model per prompt by argmax of a learned per-prompt
quality score.

The decision a build must make is where substitution is legal and what makes it legal: an
equivalence set declared on the request, a per-request permission to downgrade, or nothing at all. A
substitution outside the declared set is not a cheaper answer, it is a different question answered.
The second decision is what evidence the choice may use. A predicted score built from features the
request carries is routing; a measured per-prompt score for this exact prompt is the answer key, and
no production router has it.

A predictor is also a component that can quietly stop predicting: RouteLLM's own tracker records that the matrix factorisation router's forward pass could collapse into a single matrix multiply, which would make the selection rule constant without changing its shape.
