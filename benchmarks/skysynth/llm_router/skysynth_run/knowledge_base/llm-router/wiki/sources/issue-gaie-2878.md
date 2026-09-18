---
kind: issue
id: issue-gaie-2878
domain: llm-router
tags: [memory, validation, caching, capacity-bound, placement]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/issues/2878
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2878
failure: an unbounded-low prefix cache block size multiplies indexer entries until the router itself is killed on its memory limit
---

# Enforce a minimum blockSizeTokens to prevent EPP OOMs from oversized prefix cache indexer

Configuring the prefix cache scorer with a very small block size gives every token its own LRU entry at roughly 60 to 70 bytes of overhead, so indexer memory scales as capacity per server times pod count and reaches gigabytes on a large pool, and the router pod is killed on its memory limit under live traffic. The issue asks for a floor of 64 tokens in the autotuning path, a startup warning when a smaller value is configured by hand, and documentation of the precision versus stability trade-off. A router that keeps per-endpoint routing state must decide the bound on that state as a function of pool size and reject or clamp a configuration that exceeds it at startup rather than at OOM time. This is the placement axis constrained by cost control.
