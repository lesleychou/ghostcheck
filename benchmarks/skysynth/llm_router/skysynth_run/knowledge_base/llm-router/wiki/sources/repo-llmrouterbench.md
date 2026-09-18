---
kind: repo
id: repo-llmrouterbench
domain: llm-router
tags: [benchmark-integrity, quality, cost, data-leakage, paper]
url: https://github.com/ynulihao/LLMRouterBench
sha: c77cb0506949d8f959e97967d2fefca0e8ff1b05
license: MIT, declared in the README badge; the commit ships no LICENSE file
following: 104 stars, small but the accompanying artifact of an ACL Findings 2026 paper
production: peer-reviewed paper (Findings of ACL 2026) with a released dataset of measured per-prompt per-model scores and costs
---

# LLMRouterBench: measured per-prompt per-model quality and price

The source of the ground truth this domain is scored against: for each prompt and each model, a
measured score, the prompt and completion token counts, and the dollar cost. Because the scores are
measured rather than sampled live, a routing experiment is a replay, which is what makes both
reproducibility and leakage first-class concerns here. Its `baselines/data_loader.py` draws the
train and test boundary per prompt so that no model's row for a test prompt is ever visible during
training, and fixes the split ratio and seed.

Its baselines are also the simplest executable statements of a selection rule: one model per prompt
by argmax of a learned quality score, and a soft quality-versus-price objective with default weights
0.7 and 0.3. Read at commit c77cb0506949d8f959e97967d2fefca0e8ff1b05 from the clone made for this
run.
