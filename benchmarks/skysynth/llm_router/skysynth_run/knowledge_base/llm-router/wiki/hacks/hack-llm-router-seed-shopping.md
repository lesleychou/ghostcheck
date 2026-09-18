---
kind: hack
id: hack-llm-router-seed-shopping
domain: llm-router
tags: [determinism, reproducibility, benchmark-integrity, calibration]
tell: unseeded randomness anywhere in the policy; a score reported as the best of several replays; a configuration that differs between the reported run and the committed one; two replays of one trace producing different decisions; a result that cannot be reproduced from the recorded seed and configuration
killed_by: test-llm-router-replay-determinism
sources: [repo-gaie, repo-llmrouterbench, doc-llmrouterbench-paper]
---

# Replaying until the dice fall well

A policy with unseeded randomness gives a distribution of scores rather than a score, and reporting
its best replay is a free gain that survives no repetition. The same shape appears without any
explicit randomness whenever a run is repeated and only the good one is written down, or when the
number reported came from a configuration slightly different from the one committed.

The domain has an honest version of the underlying practice: gaie shuffles equal-scoring targets on
purpose to spread load, and a merged fix stopped its weighted picker reseeding on every pick. Spread
is a legitimate goal; the seed just has to be configuration, so the run reproduces.

The defences are procedural and cheap. Seed everything from the configuration, replay twice and
require identical decisions, and record the evaluation count against the budget so that a selection
made over many replays cannot be presented as a single measurement.
