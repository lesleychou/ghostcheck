# Citation verification — task-evaluator

Checked 2026-09-13T19:01:35. Source pin: shipped with the task, read from the working tree.

## Counts

| Verdict | Count |
|---|---|
| CONFIRMED | 80 |
| **total** | **80** |

## Method

Every file:line in this system's spec.json, properties.json, design_principles.json and decisions.json was re-read from the pinned source. The asserted line number was ignored: the most distinctive identifier or numeric literal on that line was extracted and the whole file grepped for it. CONFIRMED = the symbol really is on that line; OFF_BY = it is elsewhere in the file (corrected line given); WRONG = it is not in the file at all; UNVERIFIABLE = the file or line does not exist, or the line carries no distinctive symbol (a brace, a comment marker).

The check is mechanical (`specification/profiling/verify_citations.py`), not an agent's
opinion: the asserted line number is thrown away and the file is searched for the line's
own leading symbol.

## Corrections applied


No citation was wrong. The following point at the opening line of a multi-line
statement, so the check followed the statement to its first distinctive token:

| Citation | Followed to | Symbol |
|---|---|---|
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/env_card.yaml:138` | +1 line(s) | `300000` |
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/replay_tenants.py:79` | +1 line(s) | `models` |
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/replay_tenants.py:202` | +2 line(s) | `requests` |
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/replay_tenants.py:277` | +1 line(s) | `concurrency` |
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/replay_tenants.py:412` | +1 line(s) | `model_requested` |
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/replay_tenants.py:503` | +1 line(s) | `trace_path` |

## Files cited

| File | Citations |
|---|---|
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/replay_tenants.py` | 49 |
| `skydiscover/synthesize/examples/llm-router/evaluator/router_interface.py` | 14 |
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/env_card.yaml` | 8 |
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/replay.py` | 4 |
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/data/cards/tenantA.card.yaml` | 2 |
| `skydiscover/synthesize/examples/llm-router/evaluator/benchmark/data/cards/tenantB.card.yaml` | 2 |
| `skydiscover/synthesize/examples/llm-router/evaluator/generic_policy.py` | 1 |

