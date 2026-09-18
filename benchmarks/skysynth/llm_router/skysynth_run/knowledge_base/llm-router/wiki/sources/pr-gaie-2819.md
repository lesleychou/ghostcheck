---
kind: pr
id: pr-gaie-2819
domain: llm-router
tags: [validation, consistency, admission, placement]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2819
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2819
changed_paths: [pkg/epp/framework/plugins/flowcontrol/saturationdetector/concurrency/detector.go, pkg/epp/framework/plugins/requestcontrol/requestdataproducer/inflightload/producer.go, pkg/epp/framework/plugins/scheduling/scorer/tokenload/token_load.go]
---

# fix: fix DAG validation by using value types for InFlightLoad

The in-flight load attribute was declared as a pointer type by its producer and by the token load scorer, and the concurrency saturation detector declared no dependency on it at all, so the plugin dependency graph could not match producer to consumer and the detector was wired without its input. The merged change normalises the attribute declarations to value types on both sides and adds an explicit Consumes entry to the saturation detector, so the graph validates and the detector is fed real concurrency data. A router with pluggable scorers and a saturation gate must decide how a plugin declares the data it produces and consumes, and must fail startup rather than run a detector whose input silently never arrives. This is the admission and overload axis.
