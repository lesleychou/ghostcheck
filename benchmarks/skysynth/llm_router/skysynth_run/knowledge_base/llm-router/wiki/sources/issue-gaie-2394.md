---
kind: issue
id: issue-gaie-2394
domain: llm-router
tags: [crash, validation, recovery, placement, health]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/issues/2394
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2394
failure: a scorer dereferences a request field absent for one API shape and takes the whole endpoint picker down with a nil pointer panic
---

# predicted-latency-scorer crashes on /v1/chat/completions requests

With the predicted-latency scorer enabled, any chat completions request reached prediction generation with a nil body field and the endpoint picker process died on a segmentation violation, so a single unsupported request shape removed routing for every tenant on that gateway. The reporter expected the scorer to serve both the completions and chat completions shapes, or at minimum to degrade rather than crash. A router built from scratch must decide the blast radius of a scorer fault: a scorer that cannot evaluate a request should abstain and let the remaining scorers decide, and no plugin should be able to panic the router. This is the placement axis with a direct outage and health consequence.
