---
kind: hack
id: hack-llm-router-split-peek
domain: llm-router
tags: [data-leakage, benchmark-integrity, calibration, reproducibility]
tell: a fitted artifact containing prompt ids outside the training split; a threshold or weight selected against the validation split more times than the budget allows; any read of the held-out trace, manifest or score matrix during fitting; a validation score far better than the first test replay
killed_by: test-llm-router-train-split-isolation
sources: [repo-llmrouterbench, doc-llmrouterbench-paper, repo-routellm, issue-routellm-36]
---

# Fitting on the split that was supposed to judge the result

The protocol is fit on train, select on validation within a fixed number of evaluations, and touch
the test split once. Each of those three has a matching shortcut: fit on everything, select on
validation as many times as it takes, and peek at the test split to decide what to submit. All three
produce a number that does not survive the one replay that counts.

The middle one is the one that gets rationalised, because no boundary is formally crossed: every
extra validation evaluation is a bit of the held-out signal spent, and a policy chosen after thirty
of them has been fitted on the validation split by hand. Counting the evaluations is the whole
defence.

The reference benchmark draws its boundary per prompt rather than per row so that no model's score
for a held-out prompt is visible in fitting, and RouteLLM's tracker records the matching caveat for
calibration: a threshold calibrated on one distribution does not carry its expensive-call share to
another. Calibration is fitting, so it lives inside the same boundary.
