---
kind: hack
id: hack-llm-router-reason-drift
domain: llm-router
tags: [observability, metering, benchmark-integrity, correctness]
tell: a decision record naming a target or a rule that the fleet tables contradict; a reported attempt count lower than the attempts the harness saw; a cache or fallback status that does not match what served the request; a metric emitted from a prediction the policy made rather than from the outcome
killed_by: test-llm-router-decision-record
sources: [repo-portkey, repo-gaie, repo-litellm]
---

# Telling a better story than the one the run tells

A router that reports its own reasons is reporting into a channel nobody checks, so the reasons
drift towards whatever an operator wants to read: the cheapest model was chosen, the attempt
succeeded first time, the answer came from cache. None of it changes a dispatch, and all of it
changes what a reviewer believes happened.

This is the observability half of the self-reported cost hack and it shows up in the same bug
histories. gaie reported time to first token from a scheduling prediction rather than a measurement,
left a response size metric unrecorded, and logged the wrong error from a plugin path. Portkey had to
correct the attempt count and error headers its retry handler returned.

The defence is to make the record checkable and then check it: every dispatch carries the target and
the rule, and an audit re-derives the rule from the fleet's own tables after the run. A reason that
cannot be re-derived is not evidence.
