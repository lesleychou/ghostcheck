---
kind: hack
id: hack-llm-router-id-memorisation
domain: llm-router
tags: [benchmark-integrity, reproducibility, data-leakage, determinism]
tell: a policy keyed on prompt id, request id, arrival index, arrival timestamp or trace position; a table whose keys are identifiers rather than features; a score that collapses when the trace is relabelled or re-seeded
killed_by: test-llm-router-id-permutation-invariance
sources: [repo-llmrouterbench, doc-llmrouterbench-paper, repo-routellm]
---

# Memorising the trace instead of learning the traffic

A replayed trace is identical every time it is run, so a policy can index on the request id and
recover the right answer without any signal a live request would carry. It is cheaper than the label
peek and harder to spot, because the artifact looks like a fitted model and the decision code looks
like a lookup of a learned parameter.

The variants worth checking are arrival index and timestamp, which carry the same information as the
id once the trace is fixed, and any counter that implicitly reconstructs position, such as "the
seventeenth request of the wave always goes to the cheap model". The tell that beats all of them is
behavioural rather than textual: relabel the trace, keep every feature, and see whether a single
decision moves.

Legitimate neighbours: a session identifier used for affinity to a warm target is a real production
signal, and so is a per-tenant or per-task class. Both survive relabelling if they are used for what
they mean.
