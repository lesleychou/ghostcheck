---
kind: property
id: prop-llm-router-retry-and-fallback
domain: llm-router
tags: [retry, fallback, recovery, idempotence, latency]
values: [no retry unless configured, retry the same target after a back-off, divert immediately to a healthy sibling, honour the server supplied retry-after, gate the retry on the request being repeatable]
seen_in: [repo-litellm, repo-portkey, repo-gaie]
sources: [repo-litellm, repo-portkey, repo-gaie, doc-rfc6585, doc-rfc9110, issue-portkey-1205, pr-portkey-1239]
---

# What is attempted after an attempt fails, and when

litellm diverts: a rate-limit rejection is retried immediately against a healthy sibling rather than
waited out, the retry loop still honours the overall timeout when every sibling is also limited, and
a declared fallback target serves the request when the primary fails. Portkey makes retries opt in:
with no retry block the budget is zero attempts on an empty status list, and exhausting a configured
budget is reported as a distinct attempt count rather than as a success. gaie neither retries nor
diverts inside the scheduler: a failed placement is returned to the caller as a typed status.

Two sub-decisions decide whether a burst recovers or amplifies. The first is whether the wait comes
from the server or from the client: a provider that answers with a retry-after has stated when it
will be ready, and inventing a shorter interval is a choice to ignore it. The second is whether
every request may be repeated at all. Repeating a request that may already have taken effect is a
correctness decision, so a router that carries an explicit retry-safety flag can decide per request
instead of assuming.

What counts as a failure worth retrying is itself a decision. A Portkey issue reports retry settings ignored entirely when a content check fails, and a merged change makes the configured status list govern failover and not only retry, so the same list decides both.
