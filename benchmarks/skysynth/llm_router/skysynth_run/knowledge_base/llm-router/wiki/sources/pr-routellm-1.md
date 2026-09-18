---
kind: pr
id: pr-routellm-1
domain: llm-router
tags: [model-selection, reproducibility, paper, quality]
changed_paths: [routellm/routers/matrix_factorization/train_matrix_factorization.py]
url: https://github.com/lm-sys/RouteLLM/pull/1
repo: lm-sys/RouteLLM
number: 1
---

# Add matrix factorization router training code

The matrix factorization router could be loaded and served from a published checkpoint but not retrained, so the paper's strongest router was a fixed artifact. The merged change adds `train_matrix_factorization.py`, which reads battle records keyed by `idx`, `model_a`, `model_b` and `winner`, drops rows whose winner is a tie and rows where both sides are the same model, then shuffles and cuts a 95 to 5 train and test split before fitting the model embedding and text projection. A router built from scratch must decide whether its preference model is a frozen checkpoint or a retrainable one, because a frozen checkpoint pins the routable model pool to the snapshot the battles were collected from. This touches model selection and the train and test boundary that any later quality claim rests on.
