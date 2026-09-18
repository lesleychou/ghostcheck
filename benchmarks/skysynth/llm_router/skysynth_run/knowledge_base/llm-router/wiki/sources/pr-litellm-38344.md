---
kind: pr
id: pr-litellm-38344
domain: llm-router
tags: [cost, metering, budget, correctness, streaming]
url: https://github.com/BerriAI/litellm/pull/38344
repo: BerriAI/litellm
number: 38344
changed_paths: [litellm/cost_calculator.py, tests/test_litellm/test_cost_calculator.py]
---

# fix(cost_calculator): resolve real cost key when model_name alias contains '/'

When a deployment was published under a public alias that itself contained a slash, the cost lookup prefixed the provider again and produced a cost key no price table entry carried, so streamed requests were logged with real token counts and a spend of exactly zero. Budgets never tripped, dashboards under-counted, and nothing raised. The merged change resolves the prefixed alias to the first registered cost key, leaves custom-priced router ids that already resolve untouched, and keeps prior behavior for aliases that still do not resolve. The decision a router must make here is what a failed price lookup means: silently pricing an unpriceable request at zero turns a metering gap into free capacity, so the design axis is cost control and the safe default is to treat an unresolved price as an error, not as zero.
