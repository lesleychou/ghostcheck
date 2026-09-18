# Citation verification — gaie

Checked 2026-09-13T19:01:35. Source pin: read at commit 1748e829d1161147aaf35e76699ec86fd88406d2 (a70292c^), because pkg/epp was deleted before cloned HEAD.

## Counts

| Verdict | Count |
|---|---|
| CONFIRMED | 73 |
| **total** | **73** |

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
| `pkg/epp/framework/plugins/flowcontrol/saturationdetector/concurrency/config.go:89` | +1 line(s) | `defaultMaxConcurrency` |

## Files cited

| File | Citations |
|---|---|
| `pkg/epp/requestcontrol/director.go` | 14 |
| `pkg/epp/flowcontrol/registry/config.go` | 5 |
| `pkg/epp/scheduling/scheduler_profile.go` | 5 |
| `pkg/epp/config/loader/defaults.go` | 4 |
| `pkg/epp/flowcontrol/controller/controller.go` | 4 |
| `pkg/epp/flowcontrol/controller/internal/processor.go` | 4 |
| `pkg/epp/framework/plugins/flowcontrol/saturationdetector/utilization/detector.go` | 4 |
| `pkg/epp/metrics/metrics.go` | 4 |
| `pkg/epp/framework/plugins/flowcontrol/saturationdetector/utilization/config.go` | 3 |
| `pkg/epp/framework/plugins/requestcontrol/dataproducer/approximateprefix/types.go` | 3 |
| `pkg/epp/requestcontrol/admission.go` | 3 |
| `pkg/epp/flowcontrol/controller/config.go` | 2 |
| `pkg/epp/framework/plugins/scheduling/picker/common.go` | 2 |
| `pkg/epp/server/options.go` | 2 |
| `pkg/common/error/error.go` | 1 |
| `pkg/epp/datastore/datastore.go` | 1 |
| `pkg/epp/framework/plugins/flowcontrol/eviction/filtering/sheddable.go` | 1 |
| `pkg/epp/framework/plugins/flowcontrol/fairness/globalstrict/global_strict.go` | 1 |
| `pkg/epp/framework/plugins/flowcontrol/fairness/roundrobin/roundrobin.go` | 1 |
| `pkg/epp/framework/plugins/flowcontrol/ordering/fcfs/fcfs.go` | 1 |
| `pkg/epp/framework/plugins/flowcontrol/ordering/slodeadline/slo_deadline.go` | 1 |
| `pkg/epp/framework/plugins/flowcontrol/saturationdetector/concurrency/config.go` | 1 |
| `pkg/epp/framework/plugins/flowcontrol/usagelimits/usagelimitpolicy.go` | 1 |
| `pkg/epp/framework/plugins/scheduling/picker/maxscore/picker.go` | 1 |
| `pkg/epp/handlers/server.go` | 1 |
| `pkg/epp/requestcontrol/candidates.go` | 1 |
| `pkg/epp/server/runserver.go` | 1 |
| `pkg/epp/util/request/sheddable.go` | 1 |

