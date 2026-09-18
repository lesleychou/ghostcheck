---
kind: test
id: test-llm-router-replay-determinism
domain: llm-router
tags: [determinism, reproducibility, simulation, benchmark-integrity]
enforces: prop-llm-router-policy-state-and-determinism
command: python3 test_replay_determinism.py
mutant: UnseededTieBreakMutant in mutants.py, which breaks ties with unseeded randomness
confidence: verified
sources: [repo-gaie, pr-gaie-2805, issue-gaie-2804, repo-llmrouterbench, doc-llmrouterbench-paper]
---

# Two replays of one trace produce one set of decisions

If a policy does not repeat itself, no measured difference between two policies means anything: the
difference could be the dice. The test replays the reference twice and requires an identical
dispatch sequence and an identical score, then replays the unseeded mutant four times and requires
that the four disagree.

gaie is the system that pays for this openly. Its highest-score picker shuffles equal scores by
design, and a merged fix had to stop the weighted random picker reseeding its generator on every
pick, with the accompanying issue reporting the symptom that made it visible: flaky picker tests. A
router that wants randomness can have it, but the seed has to be part of the configuration, not of
the wall clock.
