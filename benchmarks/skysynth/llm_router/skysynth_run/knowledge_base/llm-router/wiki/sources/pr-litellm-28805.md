---
kind: pr
id: pr-litellm-28805
domain: llm-router
tags: [rate-limit, quota, admission, capacity-bound, correctness]
url: https://github.com/BerriAI/litellm/pull/28805
repo: BerriAI/litellm
number: 28805
changed_paths: [litellm/proxy/hooks/parallel_request_limiter_v3.py, tests/test_litellm/proxy/hooks/test_tpm_concurrent.py]
---

# fix(v3 limiter): cap no-max_tokens TPM floor at smallest configured limit

A request that did not set max_tokens had its token reservation estimated with a default output allowance, so against a small per-model TPM limit the estimate alone exceeded the whole limit and the request was rejected with 429 on every attempt while the counter still reported the full quota as remaining. The merged change caps that no-max_tokens floor at the smallest configured limit so such a request can be admitted instead of being permanently unservable. A router that reserves tokens before it knows the real output length must bound the reservation by the limit it is checking against, otherwise its own pessimism becomes a permanent admission failure rather than back pressure. The axis is rate limit pacing and admission.
