# Vendored copy of SkySynth's `llm-router` example

This directory is a **read-only, point-in-time copy** of the `llm-router` example from
the `skydiscover` upstream repository. It exists so that the code and data we actually
execute — including `P` (`GenericPolicy`) itself, the traces we replay, and the
published baseline we pin the golden tests to — are recorded in this repository and
survive if upstream moves, rewrites history, or disappears.

- **Upstream repository:** https://github.com/skydiscover-ai/skydiscover
- **Vendored from commit:** `c30ca1907b0084c7ef2d2ed4b6398d181a3fad0c`
- **Upstream path:** `skydiscover/synthesize/examples/llm-router/`
- **Vendored on:** 2026-09-13

## What was copied

Per the Task 8b copy manifest:

| Copied | Why |
|---|---|
| `task.md`, `README.md` | the spec we are held to; also what `paths.llm_router_root()` validates against |
| `evaluator/router_interface.py` | the `Router`/`Request`/`Action` contract |
| `evaluator/generic_policy.py` | **`P` itself** |
| `evaluator/reference_router.py` | the stand-in `P'` |
| `evaluator/benchmark/replay.py`, `replay_tenants.py` | the harness that produces every number |
| `evaluator/benchmark/env_card.yaml` | the frozen fleet |
| `evaluator/benchmark/artifacts/` | `generic_predictions.json` + `generic_heads.npz` — `GenericPolicy` cannot construct without them |
| `evaluator/benchmark/baseline/` | `generic_baseline_results.json`, the published numbers the golden test pins to |
| `evaluator/benchmark/data/` | cards, manifests, `fleet_flagship.json`, the `make_*.py` builders |
| `evaluator/benchmark/.data/traces/trace_*_train.jsonl`, `trace_*_val.jsonl` | the traces we replay (~13 MB) |

## What was deliberately NOT copied

- `evaluator/benchmark/.data/lrb/` — the 7.7 GB extracted LLMRouterBench source. The
  traces in this vendor tree are derived from it deterministically (frozen seed,
  sha256s printed by the builder), so the derived traces are the reproducible
  artifact; the multi-gigabyte source is not vendored.
- `trace_*_test.jsonl` / `matrix_*_test.jsonl` — `task.md` seals the test split. Not
  copying it is the cheapest possible proof we never replayed it.
- `evaluator/benchmark/data/manifests/tenant{A,B}_test.manifest.json` — although the
  Task 8b copy manifest lists "manifests" as part of `evaluator/benchmark/data/`, these
  two manifests enumerate the `prompt_id`s that belong to the sealed test split (i.e.
  they reveal test-split membership even without the request/response bodies). They
  were copied and then deleted before commit, per the sealed-split check in Task 8b
  Step 1/4. Only the `train` and `val` manifests for each tenant remain.
- `matrix_*_train.jsonl` / `matrix_*_val.jsonl` — intermediates the replay never reads.

## Rules for this directory

**Nothing under `vendor/` is ever edited.** It is a read-only snapshot used to
reproduce the published baseline numbers (`generic_baseline_results.json`, merged
`mean_quality` 0.418, `slo_violation_rate` 0.0414, `utility_U` 0.3671). Any local
change to these files would silently invalidate that comparison. If upstream changes,
re-vendor by re-running the Task 8b copy steps against the new commit and update the
commit SHA above — do not hand-edit files in place.
