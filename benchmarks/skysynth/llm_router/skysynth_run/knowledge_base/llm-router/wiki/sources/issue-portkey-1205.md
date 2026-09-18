---
kind: issue
id: issue-portkey-1205
domain: llm-router
tags: [retry, correctness, validation, quality]
url: https://github.com/Portkey-AI/gateway/issues/1205
repo: Portkey-AI/gateway
number: 1205
failure: the configured retry budget was skipped entirely when an output guardrail denied the response, returning 446 on the first attempt
---

# Retry settings not respected when guardrail fails

With an output guardrail set to deny, a denied response returned status 446 to the caller immediately even though a retry block with a non zero attempt count was present in the same config, on both the hosted and the open source gateway. The reporter expected the request to be attempted again until the guardrail passed or the attempt budget was exhausted, which is the whole point of pairing a deny guardrail with retries. A router built from scratch must decide which failure classes consume the retry budget: a transport error and a policy rejection are both failures, but only one of them is plausibly transient, and the answer has to be explicit in the config rather than implied by where in the pipeline the failure was raised. This is retry and fallback, with admission and policy state.
