---
kind: issue
id: issue-portkey-1142
domain: llm-router
tags: [streaming, correctness, fallback, provider-api, observability]
url: https://github.com/Portkey-AI/gateway/issues/1142
repo: Portkey-AI/gateway
number: 1142
failure: a provider error returned inside a 200 streaming response was not raised as an error, so the failure was reported as a successful attempt
---

# Bedrock streaming mode fails to throw exceptions correctly

A streaming chat request to a Bedrock hosted Claude model was rejected by the provider for a malformed thinking block, but the rejection arrived with HTTP status 200 and the error payload embedded in the stream body, and the gateway did not translate it into a thrown error. Because the status line said success, every layer above treated the attempt as good: no retry consumed the budget and no fallback target was tried, and the caller got a stream that contained an error message instead of content. A router built from scratch must decide that the success predicate for a streamed attempt is the parsed stream content, not the status of the response headers, and that a mid stream provider error has a defined mapping onto retry and failover decisions. This is retry and fallback, with decision observability.
