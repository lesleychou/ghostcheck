---
kind: doc
id: doc-llmrouterbench-paper
domain: llm-router
tags: [benchmark-integrity, quality, cost, reproducibility, paper]
url: https://arxiv.org/abs/2601.07206
publisher: arXiv, Li et al., accepted to Findings of ACL 2026
---

# LLMRouterBench: a massive benchmark and unified framework for LLM routing

The paper behind the measured score and cost tables this domain replays. It fixes the unit of
evidence: one row per prompt per model, carrying a measured score, token counts and a dollar cost,
with no timing field at all. Two consequences follow for anything built here. A routing result is
only meaningful next to the share of expensive calls that produced it, and the per-prompt scores
that make the replay possible are exactly the labels a production router would not have, so reading
them at decision time is not routing.
