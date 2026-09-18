---
kind: pr
id: pr-portkey-1030
domain: llm-router
tags: [retry, rate-limit, deadline, provider-api, latency]
url: https://github.com/Portkey-AI/gateway/pull/1030
repo: Portkey-AI/gateway
number: 1030
changed_paths: [src/globals.ts, src/handlers/handlerUtils.ts, src/handlers/retryHandler.ts, src/middlewares/requestValidator/schema/config.ts, src/types/requestBody.ts]
---

# feat: allow retry based on headers and skip expoential backoff

Retries on a 429 used a blind exponential backoff that ignored the provider's own pacing advice, so the gateway either retried too early and burned quota or waited longer than the provider asked. The merged change adds an opt in `useRetryAfterHeader` flag that reads `retry-after-ms`, `x-ms-retry-after-ms` or `retry-after`, zeroes the library's backoff timeouts, sleeps for the advertised interval instead, and keeps a 60 second budget across attempts; if the advised delay exceeds the remaining budget the whole retry sequence is abandoned and a `skip` flag propagates so the caller does not start a fresh recursive retry round and reports the attempt as exhausted. A router built from scratch must decide who owns the wait between attempts, the local backoff policy or the provider header, and it must bound the sum of provider supplied waits against a request level budget. This touches rate limit pacing, retry and fallback, and deadline and priority.
