---
kind: hack
id: hack-llm-router-retry-storm
domain: llm-router
tags: [retry, rate-limit, latency, overload, provider-api]
tell: a re-attempt on a target earlier than the retry-after it advertised; a retry loop with no back-off and no cap; retries issued on requests not marked repeatable; an attempt count per request that rises with load without a matching rise in completions
killed_by: test-llm-router-retry-after
sources: [doc-rfc6585, doc-rfc9110, repo-litellm, repo-portkey]
---

# Retrying instantly because the simulated clock is free

A simulated retry costs a tick. The policy therefore learns to hammer: re-issue immediately, and
whichever attempt lands first wins. It scores well in the replay and behaves, in production, as the
thing that turns a busy provider into a dead one.

Two subtler forms belong in the same entry. The first is inventing a shorter wait than the server
asked for, which is a decision to disbelieve the provider; Portkey had to add honouring a
retry-after header and skipping its own back-off when one was supplied, and litellm had to start
sending the header on its own rate-limit responses. The second is retrying a request that is not
safe to repeat, which RFC 9110 makes a correctness decision rather than a convenience, and which the
shipped request's repeatability flag makes checkable per request.

The defence is to price the retry the way the fleet does: a rejected attempt consumes quota, and the
next attempt on that target may not precede the time the target named.
