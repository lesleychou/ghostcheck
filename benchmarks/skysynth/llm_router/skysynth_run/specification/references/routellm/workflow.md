# routellm — lm-sys/RouteLLM @ 0b64fdafe049e596a3f5657c219329f24af24198

## Purpose
Cut LLM serving cost by sending each prompt to a *strong* or a *weak* model according to a
predicted strong-model win rate, with the strong/weak split governed by one scalar threshold
(`routellm/routers/routers.py:41`).

## Public interface
- `Controller(routers=[...], strong_model=..., weak_model=...)`, then `.chat.completions.create(
  model="router-<name>-<threshold>", ...)` — the router and its threshold are encoded in the
  OpenAI `model` string and parsed out (`routellm/controller.py:93`).
- An OpenAI-compatible HTTP server wraps the same controller (`routellm/openai_server.py:63` for
  the request model, `:127` for the only rejection path, `:143` for `/health`).

## Module map
| Path | Role |
|---|---|
| `routellm/controller.py` | model-string parsing, routing entry, call dispatch to litellm |
| `routellm/routers/routers.py` | the router implementations and the threshold comparison |
| `routellm/routers/matrix_factorization/model.py` | the embedding-backed win-rate predictor |
| `routellm/calibrate_threshold.py` | offline threshold calibration against a target strong-call fraction |
| `routellm/evals/evaluate.py` | the evaluation metrics (APGR, CPT) |
| `routellm/evals/benchmarks.py` | benchmark drivers and threshold binning |

## Execution spine of ONE routed request
1. `model` string split into router name and threshold (`routellm/controller.py:93`).
2. Only the LAST message is scored; earlier turns are discarded (`routellm/controller.py:110`).
3. The router predicts a strong-win-rate and compares it to the threshold; `>=` selects the strong
   model (`routellm/routers/routers.py:41`).
4. The chosen model name is counted in a process-global tally (`routellm/controller.py:113`).
5. The call is handed to litellm with one global `api_base`/`api_key` and the result returned
   unwrapped (`routellm/controller.py:153`, `:170`).

## Build / config
Python package; the only per-request configuration is the threshold in the model string. Threshold
calibration is a separate offline script whose target is a *fraction of calls sent to strong*, not a
quality target (`routellm/calibrate_threshold.py:55`).
