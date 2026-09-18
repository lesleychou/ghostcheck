---
kind: pr
id: pr-gaie-2126
domain: llm-router
tags: [queueing, admission, routing, lifecycle]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2126
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2126
changed_paths: [pkg/epp/requestcontrol/locator.go, pkg/epp/requestcontrol/locator_test.go, cmd/epp/runner/runner.go, pkg/epp/server/options.go]
---

# fix: optionally disable endpoint subset filtering while dispatching requests

A request admitted into the flow control queue carried the endpoint subset metadata it was tagged with at arrival, and when the pool scaled from zero the queued request was still filtered against that stale subset, so it never dispatched even though fresh endpoints existed. The merged change makes subset filtering at dispatch time optional through a runner flag, so the locator can re-resolve candidates against the current pool instead of the snapshot taken at admission. A router that queues requests must decide whether a routing constraint captured at admission is still binding at dispatch, or whether the queue re-evaluates candidates from live state. This sits on the admission and overload axis and touches outage and health recovery.
