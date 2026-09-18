---
kind: property
id: prop-llm-router-deadline-and-priority
domain: llm-router
tags: [deadline, slo, latency, ordering, queueing]
values: [deadline blind and rely on fast placement, cap each attempt with a timeout, order pending work by remaining slack, spend more on a request that is close to its deadline, give up on a request whose deadline already passed]
seen_in: [repo-litellm, repo-portkey, repo-gaie]
sources: [repo-litellm, repo-portkey, repo-gaie, doc-sre-overload, pr-portkey-403, pr-portkey-472, pr-litellm-40636]
---

# Whether the time left before the deadline changes the decision

The two tenants in this domain differ by two orders of magnitude in urgency: a 2.5 second
time-to-first-token target against a ten minute deadline. That difference is what makes one
compromise policy fail both.

gaie waits for capacity for exactly the request's own time to live and then returns a distinct
deadline-expired outcome, which keeps a slow request from being confused with a rejected one.
Portkey caps each attempt with a timeout whose precedence is fixed: the request header beats the
target's setting, and there is no timeout when neither supplies one. litellm orders its opt-in wait
set so the more urgent waiter is served first when capacity frees up.

The trap is the accounting. A refused, lost or expired request still belongs to its tenant's
violation rate, so abandoning the requests that are hardest to serve on time cannot improve that
rate: it only moves the same failure into a different column. A build that decides to give up near a
deadline must show the decision helps after those requests are counted.

The plumbing of deadlines is where the mined fixes land: a per-request timeout header that has to take precedence over the target's own setting, a streaming request whose timeout kept counting while the body streamed, and a priority header that was dropped on one endpoint because it was not Latin-1. A deadline that does not reach the decision is not a deadline.
