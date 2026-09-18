---
kind: issue
id: issue-routellm-9
domain: llm-router
tags: [compute, latency, memory, model-selection]
url: https://github.com/lm-sys/RouteLLM/issues/9
repo: lm-sys/RouteLLM
number: 9
failure: the per-query scoring model spends parameters and compute on a chain of linear stages that collapses into one matrix multiply
---

# Matrix factorization router forward pass can collapse to a single matrix multiply

A maintainer filed this against `MFModel`, which per query embeds the model id, L2 normalizes that embedding, projects the prompt embedding through a bias-free linear layer, takes an element-wise product and feeds a bias-free linear classifier. No activation sits between those stages, so the whole chain is one linear map and can be precomputed to a single flattened vector per model, which the issue demonstrates for `mixtral-8x7b-instruct-v0.1`. Folding it would cut parameter count and per-query work without changing any routing decision. A router built from scratch must budget the compute its scorer is allowed on the critical path, because that scorer runs before every request and its latency is paid even on queries that end up at the cheap model. This touches model selection with a latency consequence.
