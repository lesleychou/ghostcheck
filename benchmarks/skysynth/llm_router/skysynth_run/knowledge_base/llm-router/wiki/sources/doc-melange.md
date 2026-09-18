---
kind: doc
id: doc-melange
domain: llm-router
tags: [placement, cost, latency, capacity-bound, paper]
url: https://arxiv.org/abs/2404.14527
publisher: arXiv, Griggs et al., UC Berkeley
---

# Melange: cost efficient LLM serving by exploiting heterogeneity

Serving cost is set by the match between a request's size, its arrival rate, its latency target and
the hardware it lands on, so allocation across a heterogeneous pool beats picking one best endpoint
type. For a router the transferable claim is that placement is a function of the live state of the
target, not only of the model's published quality, and that request size and rate belong in the
decision. Its specific signals do not all exist here: the fleet this domain routes on publishes
in-flight counts and remaining request and token quota, but no queue depth.
