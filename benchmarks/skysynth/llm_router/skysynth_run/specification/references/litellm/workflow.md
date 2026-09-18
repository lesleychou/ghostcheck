# litellm — BerriAI/litellm @ 30f33a949b8a2bb890a2baee18e2ab7ab015a4f7

The closest production analogue of the system under specification: a Python LLM gateway whose
`Router` places each call on one of several deployments of a named model group, under rate limits,
budgets, cooldowns, retries and fallbacks.

## Purpose
Serve a request naming a *model group* by choosing one healthy deployment of that group, retrying
and falling back on failure, while staying inside per-deployment quotas and per-caller budgets
(`litellm/router.py:7907` for the retry predicate, `litellm/router_utils/handle_error.py:75` for the
no-deployment path).

## Public interface
- `Router(model_list=[...], routing_strategy=..., num_retries=..., fallbacks=...)`; callers use
  `router.completion(model=<group>, ...)`.
- Defaults that matter: `num_retries` falls back to the OpenAI client default
  (`litellm/router.py:1003`), `ROUTER_MAX_FALLBACKS = 5` (`litellm/constants.py:11`),
  `DEFAULT_COOLDOWN_TIME_SECONDS = 5` (`litellm/constants.py:76`), `allowed_fails = 3`
  (`litellm/__init__.py:539`).

## Module map
| Path | Role |
|---|---|
| `litellm/router.py` | the router: deployment selection pipeline, retries, fallbacks, priority queue |
| `litellm/router_strategy/simple_shuffle.py` | the default placement strategy |
| `litellm/router_strategy/lowest_latency.py`, `least_busy.py`, `lowest_cost.py`, `lowest_tpm_rpm_v2.py` | the alternative placement strategies |
| `litellm/router_strategy/budget_limiter.py` | hard spend caps that filter candidates pre-call |
| `litellm/router_strategy/adaptive_router/` | optional online model-group selection |
| `litellm/router_utils/cooldown_handlers.py` | when a deployment is quarantined and for how long |
| `litellm/router_utils/handle_error.py` | the overload path |
| `litellm/proxy/hooks/parallel_request_limiter_v3.py` | per-caller sliding-window quotas |
| `litellm/scheduler.py` | the optional priority queue |
| `litellm/utils.py` | the back-off calculation |

## Execution spine of ONE request
1. Resolve the model group to its deployment list.
2. Drop deployments currently in cooldown (`litellm/router.py:12747`). **Surprising:** if that
   leaves nothing AND health-check routing is on with an explicit allowed-fails policy, the filter
   is deliberately bypassed and a known-bad deployment is served (`litellm/router.py:12755`).
3. Drop blocked deployments, then run the async callback filters, which is where budget caps
   remove over-spent candidates (`litellm/router.py:12760`, `litellm/router_strategy/budget_limiter.py:243`).
4. Apply the placement strategy. Default is a weighted random pick by `weight`/`rpm`/`tpm`
   (`litellm/router_strategy/simple_shuffle.py:58`), falling through to a uniform random pick
   (`:70`).
5. If nothing survives, raise a 429 immediately (`litellm/router_utils/handle_error.py:91`). There
   is no wait unless the caller supplied a priority, in which case the request polls a heap every
   30 ms (`litellm/constants.py:449`, `litellm/scheduler.py:47`) until `self.timeout`
   (`litellm/router.py:4207`).
6. On failure: up to `num_retries` in-group retries, sleeping **0 s** when a healthy sibling
   deployment exists (`litellm/router.py:8054`); otherwise honour a server `Retry-After` when it is
   in (0, 60] s, else exponential back-off capped at the maximum retry delay, plus up to 0.75 s of
   jitter (`litellm/utils.py:6886`, `:6898`, `:6902`, `:6907`).
7. Then up to 5 cross-group fallback hops (`litellm/constants.py:11`).
8. Post-call, real usage is charged to the TPM counters and to the budget ledger
   (`litellm/router_strategy/lowest_tpm_rpm_v2.py:284`, `litellm/router_strategy/budget_limiter.py:407`).
9. The decision is surfaced to the caller as response headers (`x-litellm-model-id`,
   `x-litellm-attempted-retries`, `x-litellm-attempted-fallbacks`, `x-litellm-response-cost`).

## Build / config
YAML/dict `model_list` plus a routing strategy name; nearly every threshold is an environment
variable with a shipped default (`litellm/constants.py:11`, `:70`, `:76`, `:129`, `:132`, `:449`).
