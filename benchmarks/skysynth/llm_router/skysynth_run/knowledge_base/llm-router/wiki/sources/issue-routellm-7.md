---
kind: issue
id: issue-routellm-7
domain: llm-router
tags: [crash, model-selection, validation, reproducibility]
url: https://github.com/lm-sys/RouteLLM/issues/7
repo: lm-sys/RouteLLM
number: 7
failure: server startup dies with a KeyError when the configured strong model is absent from the matrix factorization router's fixed model id table
---

# KeyError gpt-4o when the routed model is missing from MODEL_IDS

Starting the server with `gpt-4o` as the strong model crashed during the lifespan hook at `self.strong_model_id = MODEL_IDS[strong_model]` in `routellm/routers/routers.py`, because the released matrix factorization checkpoint was trained on an older arena snapshot whose model id table stops at the `gpt-4-1106-preview` era. The maintainer clarified that the pair used to train the router, set in the config, is a different thing from the pair a query is actually dispatched to, set by the strong model and weak model flags, and that the learned policy transfers to newer pairs. A router built from scratch must decide whether the model identity inside its scoring function is bound to the identity of the endpoint it dispatches to, since binding them makes every new deployable model a retraining event and turns an unknown name into a startup crash rather than a validation error. This touches model selection.
