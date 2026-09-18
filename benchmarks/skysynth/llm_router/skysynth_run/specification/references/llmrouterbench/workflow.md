# llmrouterbench — ynulihao/LLMRouterBench @ c77cb0506949d8f959e97967d2fefca0e8ff1b05

The benchmark whose measured per-prompt per-model scores and per-request dollars are the ground
truth behind this task's quality and cost numbers.

## Purpose
Compare LLM routing policies offline on a frozen (prompt x model) matrix of measured correctness
and measured dollars, with no live serving of any kind (`baselines/schema.py:42`).

## Public interface
A router is plugged in as an *adaptor* under `baselines/adaptors/`; it is fitted on a train split
and asked for one model per held-out prompt, and the aggregator reports accuracy and USD cost
tables side by side (`baselines/aggregators.py:709`).

## Module map
| Path | Role |
|---|---|
| `baselines/schema.py` | the per-record schema |
| `baselines/data_loader.py` | split construction and the leakage guard |
| `baselines/aggregators.py` | the reporting layer: accuracy and cost tables, reference rows |
| `baselines/adaptors/` | ten routing policies behind one interface |
| `baselines/AvengersPro/`, `baselines/FrugalGPT/`, `baselines/GraphRouter/` | the policies themselves |
| `generators/generator.py` | the one-time measurement pass that produced the dollars |

## Execution spine of ONE evaluation
1. Records are parsed into the fixed schema: dataset_id, split, model_name, record_index,
   origin_query, prompt, prediction, raw_output, ground_truth, score, prompt_tokens,
   completion_tokens, cost (`baselines/schema.py:42`, parsed at `baselines/data_loader.py:255`).
2. The split is built **per prompt, not per record**, so every model's row for a given prompt lands
   on the same side; out-of-distribution datasets go entirely to test; `train_ratio=0.8`, `seed=42`
   (`baselines/data_loader.py:336`, `:405`, `:411`).
3. A policy is fitted on train only.
4. For each held-out prompt the policy emits one model; scoring reads only test rows
   (`baselines/AvengersPro/simple_cluster_router.py:597`).
5. The aggregator reports accuracy and cost, with `cost_metric` one of `total_cost` or
   `avg_cost_per_record` (`baselines/aggregators.py:881`), against reference rows for a random
   router, the single best model, and an oracle (`baselines/aggregators.py:939`, `:950`, `:970`).

## Data / cost model
Dollars are list price per million tokens per model declared in the collector config
(`config/data_collector_proprietary_model_config.yaml:146`), applied as
`prompt_tokens/1e6*prompt_price + completion_tokens/1e6*completion_price`, overridden by the
provider's own reported cost when it supplies one (`generators/generator.py:177`), then frozen per
record and replayed offline.

## The load-bearing absence
**There is no latency, deadline or SLO term anywhere in this benchmark.** The record schema has no
time field (`baselines/schema.py:59`) and `latency` appears only as an unscored passthrough inside
a vendored dependency (`baselines/FrugalGPT/src/FrugalGPT/llmvanilla.py:139`). Likewise there is no
fleet: no rate limit, quota, queue, capacity, throttle or availability concept in any baseline.
Every baseline is a single-attempt argmax over a static table.
