---
kind: pr
id: pr-gaie-2802
domain: llm-router
tags: [race, concurrency, correctness, capacity-bound, admission]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2802
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2802
changed_paths: [pkg/epp/framework/plugins/requestcontrol/requestdataproducer/inflightload/producer.go]
---

# fix: concurrencyTracker.dec drift

The in-flight concurrency tracker decremented by looking the endpoint counter up under a read lock, dropping the lock, and only then applying the decrement, so a concurrent delete of that endpoint between the two steps lost the decrement and left the per-endpoint count permanently high. An inflated count makes the endpoint look busier than it is forever, biasing least-load placement and tripping saturation detection early. The merged change routes the decrement through the same add path that already handles creation and locking atomically. A router that tracks in-flight work per endpoint must decide that increment, decrement, and entry removal are one atomic operation on the same lock, and must have a reconciliation path for drift. This is the admission and overload axis, with placement as the downstream victim.
