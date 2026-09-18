---
kind: pr
id: pr-gaie-2583
domain: llm-router
tags: [correctness, placement, slo, load-balancing]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2583
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2583
changed_paths: [pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/selection.go, pkg/epp/framework/plugins/scheduling/scorer/predictedlatency/scorer_test.go]
---

# fix(epp): correct composite-least strategy in negative headroom selection

When every candidate endpoint had negative SLO headroom, the selector dispatched on the configured strategy but the composite-least branch passed composite-most down to the scoring helper, so a deployment asking for the least-loaded endpoint under overload got the most-loaded one and the two configurations were indistinguishable in behaviour. The merged change passes the matching strategy constant and adds a test that asserts the two strategies pick different endpoints for the same candidate set. A router with more than one tie-break or overload strategy must decide how it proves the configured strategy is the one executed, because a copy-paste in the dispatch switch produces no error and no log. This is the placement axis under deadline and priority pressure.
