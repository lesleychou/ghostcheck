---
kind: issue
id: issue-gaie-2500
domain: llm-router
tags: [race, concurrency, atomicity, caching, consistency]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/issues/2500
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2500
failure: the prefix cache indexer drops and re-acquires its lock mid-update, leaving hash entries that point at pods already removed
---

# Race conditions in prefix cache indexer lock management

Add and RemovePod in the prefix cache indexer each released the mutex partway through and took it again, so a concurrent removal could land in the gap and the hash-to-pods map kept entries referencing a pod that no longer existed in the per-pod LRU. The prefix affinity scorer then scored a dead endpoint as a cache hit and steered requests at it. A router with a shared affinity index must decide that one logical index mutation holds one lock for its whole duration, or else define a reconciliation pass that prunes references whose target is gone. This is the placement axis, and the failure is stale policy state masquerading as a routing signal.
