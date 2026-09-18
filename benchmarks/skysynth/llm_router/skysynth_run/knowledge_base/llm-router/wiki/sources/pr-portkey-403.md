---
kind: pr
id: pr-portkey-403
domain: llm-router
tags: [deadline, routing, latency, observability]
url: https://github.com/Portkey-AI/gateway/pull/403
repo: Portkey-AI/gateway
number: 403
changed_paths: [src/globals.ts, src/handlers/handlerUtils.ts]
---

# feat: support x-portkey-request-timeout header

Request timeout could only come from the target's config, so a caller had no way to shorten or lengthen the deadline for a single request. The merged change registers an `x-portkey-request-timeout` header key and resolves the effective timeout in `tryPost` as header first, then the target's `requestTimeout`, then null, passing the resolved value to the retry handler instead of the config value. A router built from scratch must fix the precedence order between a per request deadline and a per target default, and decide whether the per request value may relax the target's limit or only tighten it. This touches deadline and priority, and policy state and determinism.
