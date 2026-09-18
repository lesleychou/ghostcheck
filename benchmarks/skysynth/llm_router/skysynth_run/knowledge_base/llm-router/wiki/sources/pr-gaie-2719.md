---
kind: pr
id: pr-gaie-2719
domain: llm-router
tags: [observability, correctness, metering, capacity-bound]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2719
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2719
changed_paths: [pkg/epp/metrics/metrics.go, pkg/epp/datalayer/logger/logger.go, pkg/epp/backend/metrics/logger.go, pkg/epp/metrics/metrics_test.go]
---

# fix: expose pool-level average running requests metric and fix integer truncation

Running request counts were scraped from every model server pod and consumed by the scorers, but were never exported as a pool-level gauge, so the signal the placement decisions relied on was invisible to operators; separately the existing average queue size gauge computed float64(total/count) with integer operands and silently floored, reporting 1 for per-pod queues of 1 and 2. The merged change registers an average running requests gauge and converts both averages to floating point division before dividing. A router must decide which internal load signals it is obliged to export, and must treat an aggregate whose arithmetic differs from the value the scheduler used as a reporting bug. This is the decision observability axis feeding admission and overload.
