---
kind: issue
id: issue-litellm-40564
domain: llm-router
tags: [budget, overflow, capacity-bound, recovery, scalability]
url: https://github.com/BerriAI/litellm/issues/40564
repo: BerriAI/litellm
number: 40564
failure: the end-user budget reset builds one unbounded IN-list per shared budget, exceeds the database bind-variable ceiling, and the atomic cascade then fails forever so budgets are never reset
---

# [Bug]: End-user budget reset exceeds PostgreSQL's 32,767 bind-variable limit and never completes

The scheduled budget reset zeroes the spend of every end user attached to a shared budget with a single update carrying one bind variable per user id, which exceeds the database's cap of 32767 once the shared budget has more dependents than that. The cascade is atomic, so nothing commits, the budget stays due, and the job retries on every tick forever for a population that cannot shrink on its own: this is a permanent stall rather than a crash, and the earlier release that batched per-user upserts did not have it. A router must bound every piece of per-tenant work by a chunk size the backing store can accept, and must decide what a partially applied reset means before making the whole cascade one transaction that can only ever fail. The axis is cost control, with unbounded per-request work and recovery behind it.
