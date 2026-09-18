---
kind: hack
id: hack-llm-router-outage-hammering
domain: llm-router
tags: [outage, health, recovery, simulation, correctness]
tell: dispatches to a provider whose announced outage window covers the current time; a health model built only from counted failures when an explicit unavailability signal is published; a quarantine that expires on a timer with no evidence the target returned; requests lost to a provider that had announced it was down
killed_by: test-llm-router-outage-grace
sources: [repo-portkey, repo-litellm, repo-gaie, doc-sre-overload]
---

# Dispatching into an announced outage because a failed attempt looks cheap

The fleet announces its outages with an end time. A policy that ignores the announcement and keeps
trying is usually not defiant, it is optimistic: in the replay a failed attempt returns quickly and
costs nothing visible, so the cheapest strategy is to keep asking. Past the retry grace the harness
stops calling this patience and calls it a lost request.

The inverse of this hack is worth catching in the same review, because it is the more common
production bug: a target that recovered but is still being avoided, or a breaker that is open while
traffic keeps being sent to the primary anyway, which is precisely what a Portkey issue reports.
litellm's cooldown history is the other half, from giving cooldowns their own cache so siblings see a
benched deployment quickly to refusing to bench a group's only deployment on a single failure.

The defence is to rank the evidence: an announced outage with an end time beats an inferred failure
rate, and the exit from avoidance should be the announcement's end or a probe, not a guess.
