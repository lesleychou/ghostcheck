---
kind: roof
id: roof-llm-router-shared-fleet
domain: llm-router
tags: [capacity-bound, rate-limit, quota, contention, throughput]
box: the frozen 3-provider fleet of the two-tenant replay (value, prime, courier), measured against the generated train and val traces; the replay itself is simulated time on one host core, so no local resource binds it
commands: python3 specification/profiling/characterize_traces.py and python3 specification/profiling/headroom.py, run in this run's specification directory against the train and val splits only
bound: provider request-per-minute quota at the burst peak, and provider concurrency for the batch tenant; not host CPU, not memory, not the model's own speed
ceiling: peak one-minute demand reaches 1.82x the strongest provider's rpm quota for tenant A and 2.11x for tenant B, while all three providers together sit at 0.34 and 0.40 of their combined 702 rpm; tenant B's requested model needs 306 to 678 concurrent slots at peak against provider limits of 32 to 96
confidence: source-reported
sources: [repo-llmrouterbench, doc-llmrouterbench-paper, repo-gaie]
---

# What actually limits this fleet: a burst that fits only if it is spread

The binding resource is not the host and not any single model. It is the per-provider request quota
during a burst, and for the batch tenant the per-provider concurrency limit.

The measurement is the offered load of each trace against the published capacity of each provider.
At tenant A's one-minute peak of 240 requests, utilisation is 1.82 on prime and 1.60 on courier but
only 0.57 on value, and the whole fleet is at 0.34. Tenant B peaks at 278 requests per minute, which
is 2.11 of prime and 1.85 of courier, with the fleet at 0.40. Token quota is never the binder: peak
token utilisation stays at 0.67 or below on every provider for both tenants.

Concurrency is the second wall, and it is specific to tenant B. Its requested model takes 91 to 146
seconds of service time per request depending on provider, so Little's law puts peak concurrency
demand at 306 to 678 against provider limits of 32, 48 and 96. No single provider can absorb that
wave.

The consequence for a design is a ceiling rather than a target. There is enough aggregate capacity
for both tenants, and there is nowhere near enough on the provider each tenant would naively prefer,
so the whole achievable gain lives in spreading and in timing, not in picking one best provider. A
second measured fact narrows it further: for tenant A, a first attempt can meet the 2.5 second time
to first token on 94 to 98 percent of requests, but after a single rejection and the fixed 2 second
retry wait, feasibility falls to zero on two of the three providers. On this fleet a retry is not a
recovery, it is a missed deadline, so pacing has to prevent the rejection rather than absorb it.

The numbers above were produced by this run's profiling scripts on the train and val splits; the
scripts refuse any path containing "test". They are recorded here as measured once, not re-measured
by the wiki checker.
