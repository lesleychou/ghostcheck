---
kind: pr
id: pr-portkey-1239
domain: llm-router
tags: [fallback, correctness, routing, outage]
url: https://github.com/Portkey-AI/gateway/pull/1239
repo: Portkey-AI/gateway
number: 1239
changed_paths: [src/handlers/handlerUtils.ts]
---

# onStatusCodes is respected during fallbacks

The fallback loop stopped only when the response was `ok` and its status was not in the configured `onStatusCodes`, so a configuration that asked to fail over on a specific non error status never triggered the next target, and a target returning a failure status outside the list kept the chain running. The merged change makes the stop condition explicit: when `onStatusCodes` is present it is the sole authority and the chain stops on any status not listed, when it is absent the chain stops on a successful response, and a gateway exception always stops the chain. A router built from scratch must decide whether the failover predicate is the transport success flag or an operator supplied status set, and it cannot silently intersect the two. This touches retry and fallback, and outage and health.
