---
kind: test
id: test-llm-router-frozen-fleet
domain: llm-router
tags: [benchmark-integrity, cost, validation, security, correctness]
enforces: prop-llm-router-cost-control
command: python3 test_frozen_fleet.py
mutant: PriceEditMutant in mutants.py, which zeroes every price in the view it was handed
confidence: verified
sources: [repo-litellm, pr-litellm-38344, pr-litellm-37736, repo-llmrouterbench, doc-llmrouterbench-paper]
---

# The router does not edit the fleet it is routing on

The fleet's prices, quotas and limits belong to the harness. The test hashes them before and after a
replay. The reference leaves them byte-identical. The mutant reaches through the view it was handed,
zeroes every price, and bills nothing at all while making exactly the same decisions, which the
checksum catches.

The simulation here deliberately aliases the price table into the view so that the attack can be
written down; a harness that hands out a snapshot by value removes it at the source. litellm's own
history is the production version of the same hazard: it had to stop persisting cost map pricing as
a per-deployment override, and had to fix a cost key that resolved to the wrong entry. A price table
that any component may rewrite is a bill that means nothing.
