---
kind: repo
id: repo-routellm
domain: llm-router
tags: [model-selection, quality, cost, calibration, paper]
url: https://github.com/lm-sys/RouteLLM
sha: 0b64fdafe049e596a3f5657c219329f24af24198
license: Apache-2.0
following: 5482 stars, the reference implementation of the most cited LLM routing paper
production: peer-reviewed paper behind it, and the LMSYS group's released router checkpoints and evaluation harness
---

# RouteLLM: choosing between a strong and a weak model on a predicted win rate

The reference for quality-versus-price model selection. A router scores each query with a predicted
win rate for the strong model, compares it against a threshold, and sends everything below to the
weak model. The threshold is not a quality target: `calibrate_threshold.py` picks the quantile that
sends a chosen fraction of traffic to the expensive model, so the knob an operator turns is the
expensive-call share. The evaluation code turns a sweep of that share into one comparable number.

The repository is finished rather than abandoned: the last commit is from August 2024 and the code
still runs, so it is read as a stable reference. Read at commit
0b64fdafe049e596a3f5657c219329f24af24198 from the clone made for this run. The parts that matter are
`routellm/routers/routers.py`, `routellm/calibrate_threshold.py`, `routellm/controller.py` and
`routellm/evals/`.
