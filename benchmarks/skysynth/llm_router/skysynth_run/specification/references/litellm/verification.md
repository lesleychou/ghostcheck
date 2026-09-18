# Citation verification — litellm

Checked 2026-09-13T19:01:35. Source pin: read at cloned HEAD.

## Counts

| Verdict | Count |
|---|---|
| CONFIRMED | 36 |
| **total** | **36** |

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
| `litellm/constants.py` | 6 |
| `litellm/router.py` | 6 |
| `litellm/router_strategy/lowest_cost.py` | 3 |
| `litellm/router_strategy/lowest_tpm_rpm_v2.py` | 3 |
| `litellm/utils.py` | 3 |
| `litellm/router_strategy/budget_limiter.py` | 2 |
| `litellm/router_strategy/simple_shuffle.py` | 2 |
| `litellm/router_utils/cooldown_handlers.py` | 2 |
| `litellm/router_utils/handle_error.py` | 2 |
| `litellm/scheduler.py` | 2 |
| `litellm/__init__.py` | 1 |
| `litellm/proxy/hooks/parallel_request_limiter_v3.py` | 1 |
| `litellm/router_strategy/adaptive_router/bandit.py` | 1 |
| `litellm/router_strategy/adaptive_router/config.py` | 1 |
| `litellm/router_strategy/lowest_latency.py` | 1 |

