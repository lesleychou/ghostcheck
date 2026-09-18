---
kind: issue
id: issue-llmrouterbench-1
domain: llm-router
tags: [crash, reproducibility, validation, benchmark-integrity]
url: https://github.com/ynulihao/LLMRouterBench/issues/1
repo: ynulihao/LLMRouterBench
number: 1
failure: the documented quick start command handed the baseline adaptor config to the data collector and the first step crashed
---

# Quick start data collection step used the wrong config file

The first quick start command, `python -m data_collector.cli run config/baseline_config.yaml`, failed on a fresh checkout, so nobody could produce the per-model response records the baselines read. The maintainer confirmed the README pointed the collector at the adaptor config: collection needs `config/data_collector_small_model_config.yaml`, which names the model pool to be measured, while `config/baseline_config.yaml` configures the baseline data loader and its filters, and the README was corrected. The two files are both YAML with overlapping keys, so the mismatch surfaced only at run time rather than at load. A router built from scratch must decide whether the description of the model pool being measured and the description of the routing policy live in one config or two, and validate the file against the role before it runs. This touches policy state and determinism.
