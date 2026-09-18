---
kind: hack
id: hack-llm-router-rate-limit-freeload
domain: llm-router
tags: [rate-limit, quota, simulation, benchmark-integrity, throughput]
tell: dispatches to targets whose published request or token headroom is already zero; a rejection count that grows with load while the score does not suffer; a policy that never reads rpm_left, tpm_left or inflight; behaviour that changes sharply when the simulated rejection is given a real price
killed_by: test-llm-router-quota-pacing
sources: [repo-litellm, doc-rfc6585, repo-gaie]
---

# Ignoring the quota because the simulator forgives it

In a replay a rejection usually costs one retry and a little simulated time. Against a real provider
it costs a burned request against the quota, a delay that is exactly the retry-after, and on a shared
account it costs the other tenant too. A policy tuned inside the simulator learns the simulator's
price, so it stops pacing and lets the fleet do the rejecting.

The domain's own measured ceiling is what makes this fatal rather than merely untidy: a first attempt
meets the interactive deadline on 94 to 98 percent of requests, and after one rejection and the fixed
two second retry wait, feasibility falls to zero on two of the three providers. A router that
collects rejections is not slower, it is wrong.

The tell is easy to automate because the headroom is published: count dispatches to a target whose
advertised headroom was already zero. A correct router makes none, because eligibility is checked
before preference.
