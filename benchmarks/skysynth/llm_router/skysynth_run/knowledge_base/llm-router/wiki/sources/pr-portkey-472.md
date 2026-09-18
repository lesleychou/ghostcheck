---
kind: pr
id: pr-portkey-472
domain: llm-router
tags: [deadline, streaming, retry, resource-leak]
url: https://github.com/Portkey-AI/gateway/pull/472
repo: Portkey-AI/gateway
number: 472
changed_paths: [src/handlers/retryHandler.ts]
---

# fix: request timeout behaviour for streaming request

The per attempt timeout was implemented with `AbortSignal.timeout`, which keeps counting after the response headers arrive, so a streaming request was aborted mid body once the configured timeout elapsed even though the attempt had already succeeded. The merged change switches to an explicit `AbortController` with a `setTimeout` that is cleared as soon as `fetch` resolves, and matches on `AbortError` instead of `TimeoutError` when building the timeout response. A router built from scratch must decide what the per attempt deadline actually covers: time to first byte, or the whole body, because for a streamed response those are very different contracts and only the first can be enforced without killing healthy long responses. This touches deadline and priority, and retry and fallback.
