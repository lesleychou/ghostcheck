---
kind: test
id: test-llm-router-outage-grace
domain: llm-router
tags: [outage, health, recovery, correctness, fallback]
enforces: prop-llm-router-outage-and-health
command: python3 test_outage_grace.py
mutant: OutageBlindMutant in mutants.py, which reads headroom but not the announced outage window
confidence: verified
sources: [repo-litellm, repo-portkey, repo-gaie, issue-portkey-1289, pr-portkey-1163, pr-litellm-40025, pr-litellm-39675]
---

# An announced outage is believed, and a request is not lost to it

The fleet announces its outages with an end time, which is better evidence than any failure count a
router could accumulate. The test takes both flagship providers down for a minute. The reference
substitutes onto the provider that is still up and completes every request. The mutant, which reads
every other field of the view but not the outage, keeps dispatching into the dark and the replay
fails with the request lost.

This is the failure the reference gateways keep re-fixing. A Portkey issue reports requests not
routed to the secondary target immediately when the breaker is open, and the breaker integration that
followed filters open targets out before the strategy runs. litellm gave cooldowns their own cache so
a sibling worker sees a benched deployment in about a second, and made a tiered router fall back to a
live peer when the tier it decided on is fully cooled down.
