# Citation verification — routellm

Checked 2026-09-13T19:01:35. Source pin: read at cloned HEAD.

## Counts

| Verdict | Count |
|---|---|
| CONFIRMED | 18 |
| **total** | **18** |

## Method

Every file:line in this system's spec.json, properties.json, design_principles.json and decisions.json was re-read from the pinned source. The asserted line number was ignored: the most distinctive identifier or numeric literal on that line was extracted and the whole file grepped for it. CONFIRMED = the symbol really is on that line; OFF_BY = it is elsewhere in the file (corrected line given); WRONG = it is not in the file at all; UNVERIFIABLE = the file or line does not exist, or the line carries no distinctive symbol (a brace, a comment marker).

The check is mechanical (`specification/profiling/verify_citations.py`), not an agent's
opinion: the asserted line number is thrown away and the file is searched for the line's
own leading symbol.

## Corrections applied

None. Every citation landed on the line it claimed.
## Files cited

| File | Citations |
|---|---|
| `routellm/controller.py` | 5 |
| `routellm/openai_server.py` | 5 |
| `routellm/evals/evaluate.py` | 4 |
| `routellm/routers/routers.py` | 3 |
| `routellm/calibrate_threshold.py` | 1 |

