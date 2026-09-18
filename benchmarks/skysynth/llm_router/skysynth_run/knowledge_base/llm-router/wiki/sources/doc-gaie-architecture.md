---
kind: doc
id: doc-gaie-architecture
domain: llm-router
tags: [placement, admission, fairness, queueing, routing]
url: https://gateway-api-inference-extension.sigs.k8s.io/
publisher: Kubernetes SIG Network, Gateway API Inference Extension project
---

# Gateway API Inference Extension: the scheduling architecture

The reference architecture behind the gaie clone states the shape this domain keeps borrowing: a
router in front of a pool of inference endpoints is a scheduling problem made of filters, scorers
and a picker, with a separate flow control layer that bounds queue occupancy and enforces fairness
between workloads. The split matters because it puts admission and fairness outside the scoring
function, where a placement score cannot silently trade them away. The documented shape is the
starting point; the specifics are read from the code under `pkg/epp/scheduling` and
`pkg/epp/flowcontrol`.
