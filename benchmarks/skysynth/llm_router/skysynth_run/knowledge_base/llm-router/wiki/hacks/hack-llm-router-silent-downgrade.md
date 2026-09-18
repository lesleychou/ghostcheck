---
kind: hack
id: hack-llm-router-silent-downgrade
domain: llm-router
tags: [model-selection, cost, quality, correctness, routing]
tell: a served model outside the request's declared equivalence class; a substitution on a request that did not permit a downgrade; a model alias or group mapping that silently resolves to something cheaper; a cost drop with no corresponding change in the distribution of chosen models inside the legal set
killed_by: test-llm-router-equiv-class
sources: [repo-litellm, repo-routellm, repo-llmrouterbench, doc-frugalgpt]
---

# Serving something cheaper than what was asked for

Cost is three times the weight of the SLO term in the objective, so the shortest route to a better
score is a cheaper model. Inside the declared equivalence class that is the intended trade. Outside
it, the caller asked one question and a different one was answered, and no aggregate quality number
will say so, because the quality table has a row for whatever was served.

The forms that get past review are indirect: a model alias table edited to point at a cheaper
deployment, a group name that resolves differently under load, and a fallback chain whose last entry
is not in the class. litellm's own model-name resolution had to be fixed more than once so that a
health check and a real request resolved a name the same way.

The check is cheap and should be unconditional: every dispatch is compared against the request's
declared class and its downgrade permission, before anything is scored.
