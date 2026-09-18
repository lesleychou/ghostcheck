---
kind: issue
id: issue-litellm-40095
domain: llm-router
tags: [budget, race, concurrency, cost, multi-tenancy]
url: https://github.com/BerriAI/litellm/issues/40095
repo: BerriAI/litellm
number: 40095
failure: concurrent first requests for an unknown end user all bypass the default budget because no enforceable budget exists until the first successful request creates the customer row
---

# [Bug]: Concurrent first requests for an unknown end user bypass the default budget

A fleet-wide default end-user budget is loaded into the end-user parameters during auth, but the helper that copies those parameters onto the request token omits the budget field, so an end user with no persisted customer row has no enforceable cap. Eight simultaneous first requests for one unknown end user all reached the provider and returned 200, recording spend hundreds of thousands of times the configured limit, and only the next request after the customer row existed was correctly refused with 429. A router must decide how a tenant's first request is admitted when the tenant's accounting record is created lazily by that same request: either the default policy is materialized before admission or the cold-start window is an unmetered hole that concurrency widens arbitrarily. The axis is cost control and tenant isolation, decided at admission.
