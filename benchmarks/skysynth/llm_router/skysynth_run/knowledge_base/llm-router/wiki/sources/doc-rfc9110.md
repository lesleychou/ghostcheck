---
kind: doc
id: doc-rfc9110
domain: llm-router
tags: [retry, idempotence, correctness, provider-api, validation]
url: https://datatracker.ietf.org/doc/html/rfc9110
publisher: IETF, Fielding, Nottingham and Reschke, June 2022
---

# RFC 9110: HTTP Semantics

Whether a request may be repeated is a property of the method and of the response, not of the
client's convenience. Retrying an attempt that may already have taken effect is a correctness
decision and has to be made deliberately. A router that retries everything is choosing to treat
every request as repeatable; one that carries an explicit retry-safety flag on the request can
decide per request instead.
