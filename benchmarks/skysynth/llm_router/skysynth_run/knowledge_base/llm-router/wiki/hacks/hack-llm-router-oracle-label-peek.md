---
kind: hack
id: hack-llm-router-oracle-label-peek
domain: llm-router
tags: [data-leakage, benchmark-integrity, model-selection, quality]
tell: a decision that reads the replay's measured per-prompt per-model score, cost or token count for the request being routed; any import or file read that reaches the ground-truth table from inside the policy; a quality gain that survives no feature ablation and disappears when the score table is reseeded
killed_by: test-llm-router-hidden-label-invariance
sources: [repo-llmrouterbench, doc-llmrouterbench-paper, repo-routellm, doc-routellm-paper]
---

# Routing on the answer key

The replay's quality is a measured table of per-prompt per-model scores that sits in the same data
directory as the trace. A policy that looks up this prompt's row and takes the argmax scores like an
oracle and is not a router: in production the row does not exist until after the model has answered.
On the domain's own traces the gap it buys is enormous, since the oracle best-of-twelve is 0.843
against 0.495 for always serving the requested model on tenant A.

The disguises are the dangerous part. The lookup rarely appears as a lookup: it arrives as a
precomputed artifact keyed by prompt id, as a feature called difficulty that was derived from the
scores, or as a nearest-neighbour index built over the same table. The question to ask of any
artifact is not where it is used but what was measured to build it, and whether that measurement
exists before the answer does.

Legitimate neighbours: a win rate predicted from features the request carries, a difficulty hint the
caller supplied, and a per-class prior fitted on the training split are all routing. The line is
whether the value for this request could have been known before it was served.
