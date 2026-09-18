---
kind: property
id: prop-llm-router-policy-state-and-determinism
domain: llm-router
tags: [determinism, reproducibility, memory, lifecycle, simulation]
values: [a pure function of the request with no memory, bounded per-target counters reset between runs, learned statistics capped so memory does not grow with traffic, unbounded per-request or per-session caches, randomised tie-breaking]
seen_in: [repo-portkey, repo-litellm, repo-gaie, repo-routellm, repo-llmrouterbench]
sources: [repo-portkey, repo-litellm, repo-gaie, repo-routellm, repo-llmrouterbench, doc-llmrouterbench-paper, issue-gaie-2500, issue-portkey-1237, pr-litellm-40229, pr-routellm-13]
---

# How much the policy remembers, and whether a replay reproduces

Portkey deliberately holds no cross-request policy state: every request carries its own config.
litellm holds several accumulators and caps them, and its adaptive selection policy caps the learned
per-target state so memory does not grow with traffic. gaie holds live per-target telemetry with a
staleness clock, and its highest-score picker shuffles equal scores on purpose, which is the
executable statement that its placement is not reproducible. RouteLLM keeps a per-router decision
tally and nothing else.

A replay makes both halves testable. State has to be bounded and has to reset between runs, or the
second replay is not the same experiment as the first. Randomness has to be seeded, or two replays
of one trace disagree and no measured difference between two policies means anything.

The replay also creates a temptation that production does not have. A trace is the same every time,
so a policy can key its decision on a request identifier or an arrival index and look like it has
learned something. A decision must be a function of what a production request would carry, not of
where the request sat in the file.

Cross-request memory is also where these systems get hurt. A prefix cache indexer had races in its lock management, a simple cache was silently promoted to a semantic one and took a platform down with it, and a per-request routing strategy override leaked into the global callback list, so one request changed how later ones were routed. RouteLLM shows the opposite discipline: one controller owns the little state that serving, calibration and evaluation all share.
