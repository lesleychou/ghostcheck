---
kind: test
id: test-llm-router-id-permutation-invariance
domain: llm-router
tags: [reproducibility, benchmark-integrity, data-leakage, determinism]
enforces: prop-llm-router-policy-state-and-determinism
command: python3 test_id_permutation_invariance.py
mutant: IdMemoriseMutant in mutants.py, which memorised the best model per prompt identifier from an earlier replay
confidence: verified
sources: [repo-llmrouterbench, doc-llmrouterbench-paper, repo-routellm, issue-routellm-10, pr-routellm-1]
---

# Relabelling the trace changes nothing a router decides

A fixed trace replays in the same order with the same identifiers every time, so a policy can key on
a request id or an arrival index and appear to have learned something that would evaporate in
production. The test builds the same trace with different request and prompt identifiers and
identical features. The reference produces an identical dispatch sequence. The memoriser does not,
because its table was keyed on the file.

The related discipline in the reference benchmark is the split boundary drawn per prompt rather than
per row, so that no model's row for a held-out prompt is visible during fitting. Memorising the
identifiers of the training trace is the same leak taken one step further: it needs no held-out row
at all, only the promise that the file will not change.
