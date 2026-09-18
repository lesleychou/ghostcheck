---
kind: test
id: test-llm-router-no-free-shed
domain: llm-router
tags: [admission, overload, slo, correctness, quality]
enforces: prop-llm-router-admission-under-overload
command: python3 test_no_free_shed.py
mutant: EagerShedMutant in mutants.py, which refuses as soon as the named model is busy
confidence: verified
sources: [repo-gaie, repo-litellm, doc-sre-overload, issue-litellm-39309, pr-gaie-2126]
---

# A refusal has to be one the fleet forced

Refusing a request is the cheapest way to lift an average: the hard ones cost quality and money, and
a router that drops them looks both better and cheaper unless refusal is priced. The test runs a
saturating trace where the named model is busy but a legally substitutable one has room. The
reference substitutes and completes everything. The mutant refuses, and the replay fails with the
refusal named.

gaie is the reference behaviour here: a request is refused for load only when it is low priority and
a measured saturation signal reports the fleet full. The litellm issue about requests rejected by a
parallelism cap still consuming request quota shows the other side of the same coin, where a refusal
is not free for the next caller either.
