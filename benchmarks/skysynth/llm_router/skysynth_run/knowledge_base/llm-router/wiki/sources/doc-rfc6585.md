---
kind: doc
id: doc-rfc6585
domain: llm-router
tags: [rate-limit, retry, overload, provider-api, validation]
url: https://datatracker.ietf.org/doc/html/rfc6585
publisher: IETF, Nottingham and Fielding, April 2012
---

# RFC 6585: Additional HTTP Status Codes

Section 4 defines 429 Too Many Requests: an overloaded server says so explicitly and may send a
Retry-After hint, and a client is expected to honour it rather than to guess. This is the contract
behind every rate-limit path in the reference gateways, and the reason a router that retries
immediately on a 429 is making a decision rather than following the protocol. It also fixes what
"the provider refused" means: a refusal is a signal carrying a time, not an opaque failure.
