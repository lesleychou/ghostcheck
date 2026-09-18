---
kind: pr
id: pr-gaie-2823
domain: llm-router
tags: [caching, placement, load-balancing, contention]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2823
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2823
changed_paths: [pkg/epp/framework/plugins/requestcontrol/dataproducer/approximateprefix/hashing.go, pkg/epp/framework/plugins/requestcontrol/dataproducer/approximateprefix/plugin_test.go]
---

# fix(prefixcache): hash trailing bytes to prevent multimodal URL hotspotting

The approximate prefix hasher only emitted blocks for whole block-size chunks and dropped the trailing remainder, so multimodal requests whose distinguishing content sat in the tail collapsed onto the same block sequence and prefix-cache affinity steered a large share of distinct traffic onto one endpoint. The merged change hashes the final partial block and gives multimodal URL parts a structured representation so distinct inputs produce distinct keys. A router that routes on a cache-locality key must decide what the key covers and check that the key's distribution matches the traffic's, because a lossy key turns an affinity scorer into a hotspot generator. This is the placement axis, and it trades cache hit rate against load spread.
