---
kind: pr
id: pr-portkey-3
domain: llm-router
tags: [retry, observability, correctness, rate-limit]
url: https://github.com/Portkey-AI/gateway/pull/3
repo: Portkey-AI/gateway
number: 3
changed_paths: [src/handlers/retryHandler.ts]
---

# fix retry handler error headers and attempt count

The retry handler rebuilt the failure response with a hardcoded JSON content type, discarding the provider's headers including rate limit and retry hints, and it assigned `lastAttempt` on the success and bail paths so the reported attempt count did not reflect the retries actually performed. The merged change captures the provider response headers onto the thrown error and replays them on the synthesised response, and moves `lastAttempt` assignment into the `onRetry` callback so it counts real retry attempts. A router built from scratch must decide that the attempt count and the upstream headers are part of the response contract, not debug output, because callers and outer fallback layers make decisions from them. This touches decision observability, and rate limit pacing.
