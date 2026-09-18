---
kind: test
id: test-llm-router-quota-pacing
domain: llm-router
tags: [rate-limit, quota, capacity-bound, throughput, simulation]
enforces: prop-llm-router-quota-pacing
command: python3 test_quota_pacing.py
mutant: QuotaBlindMutant in mutants.py, which always dispatches to its favourite provider and lets the fleet reject
confidence: verified
sources: [repo-litellm, repo-gaie, doc-rfc6585, pr-litellm-28805, issue-litellm-39309, issue-litellm-39713, roof-llm-router-shared-fleet]
---

# Headroom is read before dispatch, not learned from rejections

A simulator makes a rejection cheap: it costs a retry and nothing else. A provider does not, and the
measured ceiling for this domain says a first attempt can meet the interactive deadline on almost
every request while a retried one cannot meet it at all. The test asserts the reference collects
zero quota rejections on a trace it can pace, and that the quota-blind mutant collects many and then
burns its progress budget.

litellm excludes a deployment whose request or token counter is exhausted from the candidate set
before dispatch, which is the behaviour this test pins. Its own history shows how fragile the
counter is: a token-per-minute floor for requests without a declared maximum had to be capped at the
smallest configured limit, and per-customer limits stopped applying once a key was cached.
