---
kind: pr
id: pr-portkey-1163
domain: llm-router
tags: [outage, health, fallback, routing, observability]
url: https://github.com/Portkey-AI/gateway/pull/1163
repo: Portkey-AI/gateway
number: 1163
changed_paths: [src/handlers/handlerUtils.ts, src/types/requestBody.ts]
---

# feat: base integration for circuit breaker

Before this change the recursive target walker had no notion of a target being out of service, so a provider that had already tripped its breaker was still attempted on every request and every fallback chain paid its failure latency first. The merged change filters targets carrying `isOpen` out of the candidate list before the strategy switch runs, keeps the surviving list only when it is non empty, and threads an `originalIndex` through fallback, loadbalance, conditional and single modes so the reported target path still points at the position in the user's config. A router built from scratch must decide where health state is applied: filtering candidates before strategy selection is a different system than letting the strategy pick and then skipping, because the first changes the loadbalance weight denominator and the second does not. This touches outage and health, and decision observability, since the reported target index has to survive the filtering.
