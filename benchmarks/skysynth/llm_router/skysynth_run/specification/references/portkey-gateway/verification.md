# Citation verification — portkey-gateway

Checked 2026-09-13T19:01:35. Source pin: read at cloned HEAD.

## Counts

| Verdict | Count |
|---|---|
| CONFIRMED | 66 |
| **total** | **66** |

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
| `src/handlers/retryHandler.ts:174` | +1 line(s) | `retryCount` |
| `src/middlewares/requestValidator/index.ts:111` | +2 line(s) | `requestHeaders` |

## Files cited

| File | Citations |
|---|---|
| `src/handlers/handlerUtils.ts` | 28 |
| `src/handlers/retryHandler.ts` | 9 |
| `src/globals.ts` | 5 |
| `src/handlers/services/requestContext.ts` | 5 |
| `src/middlewares/cache/index.ts` | 3 |
| `src/services/conditionalRouter.ts` | 3 |
| `src/handlers/services/logsService.ts` | 2 |
| `src/handlers/services/responseService.ts` | 2 |
| `src/handlers/services/cacheService.ts` | 1 |
| `src/handlers/services/hooksService.ts` | 1 |
| `src/handlers/services/preRequestValidatorService.ts` | 1 |
| `src/index.ts` | 1 |
| `src/middlewares/hooks/index.ts` | 1 |
| `src/middlewares/log/index.ts` | 1 |
| `src/middlewares/requestValidator/index.ts` | 1 |
| `src/middlewares/requestValidator/schema/config.ts` | 1 |
| `src/shared/services/cache/utils/rateLimiter.ts` | 1 |

