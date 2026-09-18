---
kind: pr
id: pr-portkey-1010
domain: llm-router
tags: [retry, determinism, correctness, observability]
url: https://github.com/Portkey-AI/gateway/pull/1010
repo: Portkey-AI/gateway
number: 1010
changed_paths: [src/handlers/handlerUtils.ts]
---

# chore: add default status codes only when retry attempts are configured

`tryPost` normalised the retry config by defaulting `onStatusCodes` to the built in `RETRY_STATUS_CODES` list unconditionally, so a target with zero configured attempts still carried a non empty retriable status set and the surrounding logic treated its failures as retriable, skewing the retry count reported back on the response. The merged change makes the default conditional on `attempts` being set and leaves the list empty otherwise. A router built from scratch must decide that a retry policy is a single object: an attempt budget of zero has to imply an empty retriable status set, or the two halves of the policy disagree and the observable attempt count lies. This touches retry and fallback, and decision observability.
