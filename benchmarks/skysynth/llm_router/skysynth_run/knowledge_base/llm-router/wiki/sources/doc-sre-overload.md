---
kind: doc
id: doc-sre-overload
domain: llm-router
tags: [overload, admission, queueing, slo, production]
url: https://sre.google/sre-book/handling-overload/
publisher: Google, Site Reliability Engineering, chapter 21
---

# Handling overload

Under sustained overload the useful behaviour is to shed the least valuable load early and visibly,
because unbounded queueing turns an overload into a total outage and degrades every request instead
of a few. The chapter is the standard argument for bounded queues, for load shedding driven by a
measured saturation signal, and for making the refusal visible to the caller. The caveat this domain
adds is that shedding is not free when the scoring harness prices it: a refused request can book
zero quality and a violated objective at once, so "shed early" has to be weighed against what the
books charge for it.
