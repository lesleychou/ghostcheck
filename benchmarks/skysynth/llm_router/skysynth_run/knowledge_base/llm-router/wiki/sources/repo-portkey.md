---
kind: repo
id: repo-portkey
domain: llm-router
tags: [routing, fallback, retry, health, production]
url: https://github.com/Portkey-AI/gateway
sha: 669825cbe89ee51569918b8f78a9db486fd69dd4
license: MIT
following: 12982 stars, the second largest following among open AI gateways
production: shipped release v1.15.2, run as the open core of a commercial hosted gateway
---

# Portkey gateway: the config-driven contrast to litellm

A gateway written in TypeScript where routing is a declarative config tree rather than a strategy
object: a request names a config, and the config lists targets, weights, a fallback chain, a retry
budget with the status codes that trigger it, per-attempt timeouts, a circuit breaker and cache
behaviour. It is the contrasting design point on almost every axis: retries are off unless asked
for, a target's health is remembered across requests, and the response carries the address of the
config node that served it.

Read at commit 669825cbe89ee51569918b8f78a9db486fd69dd4 from the clone made for this run. The parts
that matter are `src/handlers/handlerUtils.ts` and the services under `src/handlers/services/`
(request context, response service, cache service, hooks service, pre-request validator).
