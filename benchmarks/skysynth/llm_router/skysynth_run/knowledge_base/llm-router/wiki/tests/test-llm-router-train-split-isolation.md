---
kind: test
id: test-llm-router-train-split-isolation
domain: llm-router
tags: [data-leakage, benchmark-integrity, reproducibility, calibration]
enforces: prop-llm-router-policy-state-and-determinism
command: python3 test_train_split_isolation.py
mutant: fit_best_model_leaky in audit.py, the same fit with the split boundary removed
confidence: verified
sources: [repo-llmrouterbench, doc-llmrouterbench-paper, repo-routellm, pr-routellm-1, issue-routellm-36, issue-routellm-22]
---

# A fitted artifact knows only the prompts it was allowed to see

Everything a router carries into a replay was fitted somewhere, and the only thing keeping that fit
honest is the boundary of the split. The test fits a per-prompt table on the training prompts and
asserts the artifact contains none of the held-out ones, then fits the same table with the boundary
removed and asserts it contains all of them. It checks the artifact, not the intention.

The boundary is drawn per prompt rather than per row in the reference benchmark, so no model's row
for a held-out prompt is ever visible in fitting. RouteLLM contributes the second half: a threshold
is calibrated to a target share of expensive calls on data that was split for the purpose, and its
own issue tracker records that a threshold calibrated on one distribution does not guarantee the
same expensive-call share on another. Calibration is part of the fit, so it lives inside the same
boundary.
