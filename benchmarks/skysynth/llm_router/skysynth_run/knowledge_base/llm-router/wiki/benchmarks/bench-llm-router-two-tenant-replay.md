---
kind: bench
id: bench-llm-router-two-tenant-replay
domain: llm-router
tags: [benchmark-integrity, quality, cost, slo, simulation]
workload: two per-tenant arrival traces replayed in simulated time against one shared 12-model 3-provider fleet with rate-limit tiers and scheduled outages
metric: U = mean_quality - 1.0 * slo_violation_rate - 3.0 * cost_usd_per_request, computed per tenant from the harness books
baseline: a single generic policy fitted on the merged traffic of both tenants and scored separately on each; a specialist wins a tenant only when quality is at least the baseline AND cost is at most the baseline AND the SLO violation rate is strictly below it
sources: [repo-llmrouterbench, doc-llmrouterbench-paper, doc-routellm-paper, issue-llmrouterbench-1, issue-llmrouterbench-2, issue-llmrouterbench-5]
---

# Two tenants, one rate-limited fleet, replayed

The workload is two traces with genuinely different shapes, which is the point of the benchmark: a
single compromise policy cannot serve both well.

Tenant A is interactive: measured on this run's train split, 2899 requests over 3084 seconds, mean
0.94 requests per second with a 10 second peak of 8.2, a burstiness ratio of 8.7 against the mean,
median prompt 28 tokens with a 99th percentile of 190648, and a single service level field, a 2500
millisecond time to first token. Tenant B is batch reasoning: 1940 requests over 2529 seconds, mean
0.77 per second, arriving in waves, with a 600000 millisecond deadline and far heavier prompts. Both
tenants name one model and both carry an equivalence class of all 12 fleet models, so every request
is substitutable and the whole spread of quality and price is reachable.

Quality is ground truth from measured per-prompt per-model scores, so no live model is called and a
full replay finishes in seconds. Two measured reference points bound what any policy can do on
tenant A train: always serving the requested model scores 0.495 mean quality, and an oracle that
picks the best of the 12 models per prompt scores 0.843. The same pair for tenant B is 0.386 and
0.650. A reported quality outside that band is a bug in the measurement, not a result.

The three books the score is read from are the harness's, not the router's: billed dollars, token
counts and SLO accounting all come from the harness ledger. Correctness is pass or fail and sits
outside the score, so a replay that violates an invariant does not score badly, it does not score.

Protocol: fit on train, select on val within a five-evaluation budget, and leave the test split
alone until the win criteria are registered. A measured ceiling is a valid result.

The benchmark that supplies the ground truth has conventions of its own, recorded in its tracker: a quick-start step that named the wrong collection config, a submitted baseline held back until the router behind it had a paper, and a licence question that separates the repository code from the released measurement records. The last one matters here, because what this domain reuses is the measurements.
