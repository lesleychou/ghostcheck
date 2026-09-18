---
kind: issue
id: issue-routellm-5
domain: llm-router
tags: [cost, metering, paper, benchmark-integrity]
url: https://github.com/lm-sys/RouteLLM/issues/5
repo: lm-sys/RouteLLM
number: 5
failure: the reported cost savings metric counts only strong model calls and omits the router's own embedding spend
---

# Embedding cost was excluded from the reported cost savings

A reader asked whether the cost of `text-embedding-3-small`, which the matrix factorization and similarity weighted routers call on every query, was included when the paper computed router monetary cost. The maintainer answered that cost savings were calculated from the number of GPT-4 calls only, justified by the price gap: roughly 20 dollars per million tokens for GPT-4 against roughly 0.20 for Mixtral 8x7B and 0.02 for the embedding model, so the omitted terms are under one percent. That approximation is a property of this particular pair and collapses when the strong and weak models are close in price or when the scoring model is a larger one. A router built from scratch must decide whether the cost of making the decision is inside its cost accounting or outside it, and must publish which, so the savings number can be checked. This is the cost control axis with a metering consequence.
