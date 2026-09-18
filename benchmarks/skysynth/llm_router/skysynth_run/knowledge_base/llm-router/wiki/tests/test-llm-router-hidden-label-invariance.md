---
kind: test
id: test-llm-router-hidden-label-invariance
domain: llm-router
tags: [data-leakage, benchmark-integrity, model-selection, quality]
enforces: prop-llm-router-model-selection
command: python3 test_hidden_label_invariance.py
mutant: LabelPeekMutant in mutants.py, which picks the argmax of the harness's hidden per-prompt score table
confidence: verified
sources: [repo-llmrouterbench, doc-llmrouterbench-paper, repo-routellm, doc-routellm-paper, pr-routellm-1, issue-routellm-22]
---

# A decision does not change when the answer key changes

The replay's quality comes from a measured table of per-prompt per-model scores. That table is the
answer key, and no production router has it. The test states the consequence as an executable
property: swap the table for one generated from a different seed, and a router that decides from the
request must produce exactly the same dispatches. The reference does. The label peeker does not, and
the test reports the mean quality it bought that way, which on this trace is about a quarter of a
point of pure fiction.

This is the domain's most attractive cheat because the table is right there in the replay data.
RouteLLM's design is the honest version of the same idea: a win rate predicted from features of the
query, trained on data whose provenance is documented, never a lookup of the outcome.
