---
kind: pr
id: pr-litellm-40202
domain: llm-router
tags: [latency, observability, calibration, routing, streaming]
url: https://github.com/BerriAI/litellm/pull/40202
repo: BerriAI/litellm
number: 40202
changed_paths: [litellm/router_strategy/lowest_latency.py, tests/test_litellm/router_strategy/test_lowest_latency.py, tests/local_testing/test_lowest_latency_routing.py]
---

# fix(router): rank streaming latency routing by raw TTFT, not TTFT per token

Latency-based routing recorded time-to-first-token divided by the completion token count, so a deployment that took three seconds to start streaming but then wrote a long answer scored better than one that started in one second, and the router systematically preferred the slowest deployment to begin streaming. The merged change stores time to first token as plain seconds measured from request start in both the sync and async success handlers, leaving the non-streaming per-output-token metric unchanged. A router must decide what quantity its selection policy actually optimizes and record exactly that: normalizing a latency sample by a variable the policy does not care about inverts the ranking. The axis is decision observability feeding model selection.
