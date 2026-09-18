---
kind: repo
id: repo-gaie
domain: llm-router
tags: [placement, admission, fairness, queueing, production]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension
sha: 2711ff86a50ae23c5d32387779df8d3db9ca28e4
license: Apache-2.0
following: 767 stars, small in absolute terms but the reference implementation of a Kubernetes SIG standard
production: shipped release v1.6.1, a kubernetes-sigs project implementing the Gateway API Inference Extension standard
---

# gaie: scheduling requests onto a live inference fleet

The strongest reference for placement under live load. Its endpoint picker is an explicit pipeline
of filters, scorers and a picker, with a separate flow control layer that bounds queue occupancy,
detects saturation and enforces fairness between workload bands. It is the only reference system
that treats admission as a decision in its own right: a request is refused for load only when the
fleet reports itself saturated, and a caller-visible status distinguishes an empty candidate set
from a placement failure.

Read at commit 2711ff86a50ae23c5d32387779df8d3db9ca28e4 from the clone made for this run; the
scheduler evidence cited by this domain's tests was read at 1748e829d1161147aaf35e76699ec86fd88406d2.
The parts that matter are `pkg/epp/scheduling/`, `pkg/epp/flowcontrol/`, `pkg/epp/requestcontrol/`
and the plugins under `pkg/epp/framework/plugins/`.
