---
kind: pr
id: pr-gaie-2674
domain: llm-router
tags: [race, concurrency, fairness, queueing, consistency]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2674
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2674
changed_paths: [pkg/epp/flowcontrol/registry/shard.go, pkg/epp/flowcontrol/registry/shard_test.go]
---

# fix: add read lock to AllOrderedPriorityLevels to prevent data race

The flow control shard exposed its cached slice of priority levels by returning the internal backing array with no lock, documented as a lock-free read, while band add and delete rewrote that same slice under the write lock. A dispatch loop iterating the levels could therefore read a torn or half-rebuilt priority order and skip or double-visit a band. The merged change takes the read lock and returns a copy, so every caller iterates a stable snapshot. A router with priority bands must decide what a priority-order read returns under concurrent reconfiguration: a copied snapshot, or a live structure the caller must keep locked. This is the deadline and priority axis, and it decides whether fairness between tenants holds while the band set changes.
