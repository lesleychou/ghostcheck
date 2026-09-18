---
kind: hack
id: hack-llm-router-shed-the-hard-ones
domain: llm-router
tags: [admission, overload, quality, cost, slo]
tell: a refusal taken while some provider still had request, token and concurrency headroom for a legally substitutable model; a refusal predicate that reads the request's difficulty, expected tokens or expected quality instead of the fleet's saturation; a cost per request that falls at the same time as the number of completions
killed_by: test-llm-router-no-free-shed
sources: [repo-gaie, repo-litellm, doc-sre-overload]
---

# Refusing the requests that would have scored badly

Quality is an average over what was served and cost is a total over what was bought, so a router
that refuses the hard, long or expensive requests improves both at once without improving anything.
This is the single most profitable move available on a routing benchmark, and it is indistinguishable
from good load shedding unless the authorising evidence is checked.

The discipline that separates them is whose state the refusal predicate reads. Shedding is a
statement about the fleet: it is full, and this request cannot be served by anyone right now. The
hack is a statement about the request: it is going to be costly, so it is not worth serving. gaie
draws exactly this line by requiring both a negative priority and a measured saturation signal before
refusing for load.

Watch for the softened forms too: a deadline-aware policy that declines anything it estimates it
cannot serve in time, and a cost-aware policy that declines anything above a token threshold. Both
are the same trade with a better name.
