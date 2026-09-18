---
kind: hack
id: hack-llm-router-fleet-table-edit
domain: llm-router
tags: [benchmark-integrity, cost, security, validation, correctness]
tell: the fleet configuration is not byte-identical at the end of a run; a policy that writes to any object reachable from the view it was handed; prices, quotas, concurrency limits or outage windows that differ between the start and the end of a replay; a bill that falls without any decision changing
killed_by: test-llm-router-frozen-fleet
sources: [repo-litellm, repo-llmrouterbench, repo-gaie]
---

# Editing the price list instead of the policy

When the view handed to a policy aliases the harness's own tables, the shortest path to a better
score is to write to them: zero the prices, raise the quotas, shorten the outage. Nothing about the
routing changes, so every behavioural test still passes, and the bill collapses.

It has an accidental cousin that is just as damaging and much more common: a policy that mutates a
shared structure it was only meant to read, so the next request sees a fleet that does not exist.
litellm had to stop persisting cost map pricing as a per-deployment override for the same reason,
which is that a price table any component may rewrite is a bill that means nothing.

Two defences, and both are cheap. Hand out a snapshot by value so the write has nowhere to land, and
hash the configuration at the start and the end of every run so that an escape is caught rather than
argued about.
