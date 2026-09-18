---
kind: pr
id: pr-routellm-13
domain: llm-router
tags: [calibration, model-selection, reproducibility, cost]
url: https://github.com/lm-sys/RouteLLM/pull/13
repo: lm-sys/RouteLLM
number: 13
changed_paths: [routellm/controller.py, routellm/calibrate_threshold.py, routellm/routers/routers.py, routellm/evals/evaluate.py, routellm/evals/benchmarks.py, routellm/model_pair.py]
---

# Add unified controller interface shared by serving, calibration and evals

Routing was previously reachable only by launching the OpenAI compatible server, and the threshold calibration script and the evaluation harness each reached the routers through their own path. The merged change adds a `Controller` class that owns the router instances and the model pair, parses a `router-<name>-<threshold>` model string, exposes `route` and `batch_calculate_win_rate`, and becomes the single entry point used by `calibrate_threshold.py` and `evals/evaluate.py` as well as by the server. A router built from scratch must decide that the component scoring a prompt during offline calibration is literally the same component scoring it in production, because a threshold fitted through a second code path silently stops meaning what its calibration said. This touches model selection and policy state and determinism.
