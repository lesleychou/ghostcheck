# Citation verification — llmrouterbench

Checked 2026-09-13T19:01:35. Source pin: read at cloned HEAD.

## Counts

| Verdict | Count |
|---|---|
| CONFIRMED | 19 |
| **total** | **19** |

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
| `baselines/aggregators.py` | 6 |
| `baselines/data_loader.py` | 4 |
| `baselines/AvengersPro/simple_cluster_router.py` | 2 |
| `baselines/schema.py` | 2 |
| `baselines/AvengersPro/balance_cluster_router.py` | 1 |
| `baselines/FrugalGPT/train_router_from_results.py` | 1 |
| `baselines/GraphRouter/model/multi_task_graph_router.py` | 1 |
| `config/data_collector_proprietary_model_config.yaml` | 1 |
| `generators/generator.py` | 1 |

