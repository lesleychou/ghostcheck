---
kind: pr
id: pr-portkey-991
domain: llm-router
tags: [retry, recovery, correctness, observability]
url: https://github.com/Portkey-AI/gateway/pull/991
repo: Portkey-AI/gateway
number: 991
changed_paths: [src/handlers/retryHandler.ts]
---

# fix: add handling to detect all errors in retry handler

The retry handler's catch block only converted a `TypeError` into a synthetic response, so any other thrown value that carried no status fell through without producing a usable last response for the caller. The merged change keys on the absence of `error.status` in addition to the `TypeError` check, on the invariant that the handler always attaches a status to errors it raises itself, and defaults a missing cause. A router built from scratch must decide on one representation for a failed attempt, with a status always present, so that fallback and reporting can classify an attempt without knowing which layer threw. This touches outage and health, and decision observability.
