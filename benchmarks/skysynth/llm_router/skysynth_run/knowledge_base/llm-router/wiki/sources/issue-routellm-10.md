---
kind: issue
id: issue-routellm-10
domain: llm-router
tags: [reproducibility, quality, paper, calibration]
url: https://github.com/lm-sys/RouteLLM/issues/10
repo: lm-sys/RouteLLM
number: 10
failure: the label for a battle where both models give the same outcome is undefined, so the training set can be built two incompatible ways
---

# How ties are labeled when constructing the golden-labeled training data

A user reproducing the paper on additional data asked what `winner_model` should be recorded when the strong and weak model produce the same outcome, both correct or both wrong: a tie label, or an assignment to the weak model. The maintainer did not restate the rule in the thread and referred to an external write-up from Anyscale describing how the golden-labeled dataset was built. The repository's own training script sidesteps the question by filtering out every row whose winner is not `model_a` or `model_b`, so ties are discarded rather than routed to the cheaper model. A router built from scratch must fix the tie rule before training, because assigning ties to the weak model teaches a cheaper policy while discarding them removes exactly the queries where routing is free. This touches model selection and cost control through the calibration set.
