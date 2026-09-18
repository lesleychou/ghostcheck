---
kind: doc
id: doc-frugalgpt
domain: llm-router
tags: [cost, quality, budget, model-selection, paper]
url: https://arxiv.org/abs/2305.05176
publisher: arXiv, Chen, Zaharia and Zou, Stanford
---

# FrugalGPT: cascading cheap models under an explicit dollar budget

Cost falls when a cheap model is tried first and the answer is escalated only when a scorer judges
it unreliable, with the whole cascade held under a stated per-query budget. The idea is the origin
of budget-as-a-constraint rather than budget-as-a-preference. It does not transfer unchanged to a
fleet that bills every completed attempt: there a first cheap attempt is paid for in full, so a
cascade costs more than it saves unless the escalation rate is very low.
