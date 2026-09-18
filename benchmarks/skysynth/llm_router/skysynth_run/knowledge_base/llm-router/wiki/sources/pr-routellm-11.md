---
kind: pr
id: pr-routellm-11
domain: llm-router
tags: [provider-api, model-selection, fallback, cost]
url: https://github.com/lm-sys/RouteLLM/pull/11
repo: lm-sys/RouteLLM
number: 11
changed_paths: [routellm/openai_server.py, routellm/evals/evaluate.py, pyproject.toml, examples/routing_to_local_models.md, README.md]
---

# Add LiteLLM support so the routed pair can span providers

Completions could only be dispatched to OpenAI compatible endpoints, so the strong and weak model both had to come from providers speaking that one wire format. The merged change sends completions through LiteLLM in the server and in the evaluation path, adding Anthropic, Amazon Bedrock and Google AI Studio, while keeping OpenAI compatible endpoints reachable by prefixing the model name with `openai/` and passing alternate base URL and API key flags. A router built from scratch must decide whether the provider adapter sits below the routing decision or above it, because a policy that names concrete provider model strings cannot move a query to a second provider when the first is unreachable. This touches model selection with a direct retry and fallback consequence.
