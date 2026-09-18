---
kind: issue
id: issue-llmrouterbench-2
domain: llm-router
tags: [benchmark-integrity, reproducibility, validation, model-selection]
url: https://github.com/ynulihao/LLMRouterBench/issues/2
repo: ynulihao/LLMRouterBench
number: 2
failure: an unreviewed router with self-measured cost and accuracy numbers would have entered the benchmark's comparison table
---

# Baseline submission declined until the router has an associated paper

A third party asked to add the A3M router to the benchmark's baselines, citing figures measured on its own harness: 67 percent exact tier accuracy, 96 percent within one tier, 62.9 percent cost savings against all-premium routing, and a cost per thousand queries roughly five times below the RouteLLM row in its own table. The maintainer declined at this stage, stating that the benchmark admits baselines described in peer-reviewed papers so that comparisons stay reproducible and aligned with established baselines, and invited a pull request carrying the paper, the implementation and an evaluation script once one exists. The companion pull request was closed without merging. A router built from scratch must decide what evidence lets a candidate policy into its comparison set, because numbers a policy reports about itself on its own traces are not commensurable with numbers the harness computes from the shared cost and score tables. This touches model selection through benchmark integrity.
