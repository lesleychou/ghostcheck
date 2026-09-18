---
kind: issue
id: issue-portkey-1206
domain: llm-router
tags: [crash, streaming, recovery, resource-leak, correctness]
url: https://github.com/Portkey-AI/gateway/issues/1206
repo: Portkey-AI/gateway
number: 1206
failure: an error thrown inside the stream transform generator became an unhandled rejection that crashed the gateway and left the writer open
---

# Unhandled rejection in stream transform generator function is crashing the gateway

Once the HTTP stream response had begun, the chunk transforming generator was driven by a floating async IIFE with no catch, so any error raised while transforming a chunk surfaced as an unhandled promise rejection and took the process down instead of terminating that one response. The writer was never closed on the error path either, so the client saw a hung stream while the shared process died for every other in flight request. A router built from scratch must decide that a per request streaming failure is contained to that request: the transform pipeline needs a terminal error handler that closes or aborts the writer, and the outcome must be recorded so the attempt is not silently counted as a success. This is outage and health, with tenant isolation, since one request's error path took down the whole gateway.
