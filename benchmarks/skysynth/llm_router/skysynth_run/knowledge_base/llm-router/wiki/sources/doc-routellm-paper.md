---
kind: doc
id: doc-routellm-paper
domain: llm-router
tags: [model-selection, quality, cost, calibration, paper]
url: https://arxiv.org/abs/2406.18665
publisher: arXiv, Ong et al., LMSYS
---

# RouteLLM: Learning to Route LLMs with Preference Data

Routing between a strong and a weak model on a per-query predicted win rate recovers most of the
strong model's quality on a fraction of its calls. The paper's operational point matters more than
its models: the knob is the share of traffic sent to the expensive model, not a quality target, and
the trade-off is reported as a curve over that share rather than a single number. A router that
claims a quality gain has to say what share of expensive calls bought it.
