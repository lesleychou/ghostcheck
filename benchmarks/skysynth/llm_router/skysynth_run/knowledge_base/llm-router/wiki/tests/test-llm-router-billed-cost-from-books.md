---
kind: test
id: test-llm-router-billed-cost-from-books
domain: llm-router
tags: [cost, metering, benchmark-integrity, observability, correctness]
enforces: prop-llm-router-cost-control
command: python3 test_billed_cost_from_books.py
mutant: CostUnderReportMutant in mutants.py, which buys the flagship model and reports the cheap price
confidence: verified
sources: [repo-litellm, repo-llmrouterbench, pr-litellm-37736, pr-litellm-38344, issue-routellm-5, doc-llmrouterbench-paper]
---

# The bill is the harness ledger, not the router's account of itself

The test replays one trace twice with routers that make identical dispatches and differ only in what
they say they spent. The books charge the same amount both times, the score does not move, and the
liar's self-report is an order of magnitude below what it actually spent. A router's report is an
operator convenience; nothing scored may read it.

Mis-costing is a real and recurring bug, not a hypothetical. litellm had to make per-model budgets
track, enforce and report one single counter instead of three that could disagree, and had to fix a
cost lookup that resolved the wrong key when a model alias contained a slash. RouteLLM's reported
savings were challenged because the embedding model's own cost had been left out of the total. In
every case the system's story about its spending drifted from the spending.
