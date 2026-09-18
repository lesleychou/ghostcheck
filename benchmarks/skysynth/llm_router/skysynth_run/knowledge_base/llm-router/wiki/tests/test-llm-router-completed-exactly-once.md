---
kind: test
id: test-llm-router-completed-exactly-once
domain: llm-router
tags: [correctness, idempotence, atomicity, cost, lifecycle]
enforces: prop-llm-router-admission-under-overload
command: python3 test_completed_exactly_once.py
mutant: ResubmitAfterCompletionMutant in mutants.py, which re-dispatches on the completion callback
confidence: verified
sources: [doc-rfc9110, repo-litellm, repo-portkey, issue-portkey-1142, pr-portkey-3, pr-portkey-991]
---

# Every request ends completed once or refused once

The test checks the reference's ledger: one dispatch per request, every request completed, no
duplicates. Then it replays a mutant that re-dispatches a request from the completion callback, and
requires the replay to fail with the second dispatch named. One answer, one bill.

The failure this guards against is what happens when an error classifier is wrong rather than when a
router is greedy. A Portkey issue reports a provider error arriving inside a successful stream and
being counted as a success, and a merged fix had to make the retry handler detect all errors rather
than the obvious ones. The mirror image is retrying something that already took effect, which RFC
9110 makes a correctness decision rather than a convenience.
