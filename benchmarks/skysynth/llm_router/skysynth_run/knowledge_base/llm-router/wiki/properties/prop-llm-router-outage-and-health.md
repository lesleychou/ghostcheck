---
kind: property
id: prop-llm-router-outage-and-health
domain: llm-router
tags: [outage, health, recovery, correctness, routing]
values: [no health memory at all, quarantine after an error-rate threshold over a window, quarantine for a fixed configured duration, trust an explicit unavailability signal with an end time, re-probe a quarantined target before trusting it]
seen_in: [repo-litellm, repo-portkey, repo-gaie]
sources: [repo-litellm, repo-portkey, repo-gaie, doc-sre-overload, pr-litellm-40224]
---

# How long a failing target is avoided, and on what evidence

litellm quarantines a deployment on a failure rate over a window, honours a configured cooldown
duration exactly, and deliberately does not quarantine a group's only target on a single failure so
a lone provider is never taken out of service by a transient error. Portkey remembers health across
requests through a circuit breaker on the config node. gaie has no quarantine: it scores a target
whose telemetry is missing or stale as fully saturated, which removes it from selection for as long
as the silence lasts and restores it automatically when data returns.

The build has to pick the evidence and the exit condition separately. Evidence can be inferred from
failures or announced by the fleet with an end time, and an announced outage is strictly better
information than a failure count, so ignoring it is a decision. The exit condition is a timer, a
probe, or a fresh signal, and a router that only ever counts failures can keep a healthy target out
of service long after it recovered. Continuing to dispatch into an announced outage does not slow a
request down: past the retry grace it loses it.

Health state also has to be shared. litellm had to count a deployment's allowed failures in the shared router cache so that a multi-worker proxy benches a deployment fleet-wide rather than once per worker.
