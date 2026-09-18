---
kind: pr
id: pr-gaie-2512
domain: llm-router
tags: [observability, correctness, validation]
url: https://github.com/kubernetes-sigs/gateway-api-inference-extension/pull/2512
repo: kubernetes-sigs/gateway-api-inference-extension
number: 2512
changed_paths: [pkg/epp/requestcontrol/director.go]
---

# fix: log correct error from Prepare Data Plugins

The director called the prepare-data plugin runner, discarded its return value, and then logged a stale error variable left over from an earlier step, so a prepare-data failure was reported under the wrong cause and operators chasing a bad routing decision were pointed at the wrong plugin. The merged change captures the returned error and logs that. A router with a plugin pipeline must decide that every stage's error is captured and attributed to the stage that raised it, since a mislabelled error costs nothing at runtime and everything during an incident. This is the decision observability axis.
