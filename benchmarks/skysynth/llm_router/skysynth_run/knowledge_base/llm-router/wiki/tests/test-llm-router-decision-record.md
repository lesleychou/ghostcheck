---
kind: test
id: test-llm-router-decision-record
domain: llm-router
tags: [observability, metering, correctness, benchmark-integrity]
enforces: prop-llm-router-decision-observability
command: python3 test_decision_record.py
mutant: MisreportedReasonMutant in mutants.py, which buys the dearest eligible model and files it as the cheapest
confidence: verified
sources: [repo-portkey, repo-gaie, pr-gaie-2372, pr-gaie-2719, pr-gaie-2512, pr-portkey-3]
---

# A decision record has to survive a check against the fleet's own tables

Every dispatch carries a record naming the target and the rule that chose it. The test audits those
records against the price table: the record must name the target actually used, and a record
claiming the cheapest choice must be the cheapest legal one on that provider. The reference passes
clean. The mutant buys the dearest eligible model twenty times while filing each as the cheapest,
and is caught twenty times.

An unaudited reason is decoration, and the mined history shows which direction it drifts. gaie had to
stop reporting time to first token from a prediction made during scheduling rather than from the
measurement, had to start accumulating a response size that was silently never recorded, and had to
fix a path that logged the wrong error. Portkey had to correct the attempt count and error headers a
retry handler returned. In each case the number the system published was not the number that
happened.
