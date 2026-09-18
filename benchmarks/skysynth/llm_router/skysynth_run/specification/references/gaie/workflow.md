# gaie — kubernetes-sigs/gateway-api-inference-extension

**Pin, and a warning.** The run cloned HEAD, `2711ff86a50ae23c5d32387779df8d3db9ca28e4`. At that
commit `pkg/epp` **no longer exists**: the Endpoint Picker was deleted in `a70292c` ("Cleanup EPP
and Latency Predictor", #2967, 481 files, -90903 lines) and `main` now holds only `pkg/lwepp`, a
thin proxy shim with no scheduler and no flow control. Every citation below is therefore read at
`1748e829d1161147aaf35e76699ec86fd88406d2` (= `a70292c^`), the last commit containing the Endpoint
Picker, and was re-verified there by `git show <sha>:<path>` during this run. Read them with
`git -C specification/sources/gaie show 1748e829d1161147aaf35e76699ec86fd88406d2:<path>`.

## Purpose
A proxy sidecar that picks one model-server pod per inference request from a pool, with
priority-aware admission, per-workload queueing and plugin-based scoring
(`pkg/epp/requestcontrol/director.go:106`).

## Public interface
- Entry: a gRPC external-processing stream (`pkg/epp/handlers/server.go:162`), handed to the
  director (`pkg/epp/handlers/server.go:326`).
- Request: an OpenAI-shaped body plus headers, carrying an objective key, an optional
  `x-slo-ttft-ms`, and an endpoint-subset metadata filter
  (`pkg/epp/requestcontrol/director.go:173`).
- Response: mutated body plus an `x-gateway-destination-endpoint` metadata value, or a typed error
  rendered as 400/401/403/404/429/500/503 (`pkg/common/error/error.go:62`).
- Config: an `EndpointPickerConfig` YAML plus about 35 flags (`pkg/epp/server/options.go:120`),
  with defaults injected for any role left empty (`pkg/epp/config/loader/defaults.go:123`).

## Module map
| Path | Role |
|---|---|
| `pkg/epp/handlers` | the stream, request and response lifecycle |
| `pkg/epp/requestcontrol` | the director, the admission controller, endpoint candidates |
| `pkg/epp/scheduling` | the scheduler and its profiles: filter, score, pick |
| `pkg/epp/flowcontrol` | the controller (shards), the registry (flows, bands, capacity), eviction |
| `pkg/epp/framework/plugins` | scorers, filters, pickers, fairness, ordering, saturation policies |
| `pkg/epp/datalayer`, `pkg/epp/datastore` | per-endpoint metric collectors and the pool cache |
| `pkg/epp/metrics` | the exported metric surface |

## Execution spine of ONE request
1. Stream opens (`pkg/epp/handlers/server.go:162`), headers handled (`:304`), body parsed and the
   director invoked (`:326`).
2. Optional model rewrite by weighted random draw over declared integer weights
   (`pkg/epp/requestcontrol/director.go:276`, draw at `:285`).
3. The workload objective is looked up; **priority defaults to 0**
   (`pkg/epp/requestcontrol/director.go:133`).
4. **Admission runs BEFORE the candidate endpoints are even located** (`:186` versus `:190`).
   - legacy path: refuse only if priority is negative AND mean pool saturation is at least 1.0
     (`pkg/epp/requestcontrol/admission.go:73`).
   - flow-control path: block the caller in a per-flow bounded queue
     (`pkg/epp/requestcontrol/admission.go:169`), with the request's own remaining deadline as its
     time to live (`pkg/epp/flowcontrol/controller/controller.go:383`), shards ranked by this
     workload's queued bytes (`:411`), capacity checked on the shard's single goroutine
     (`pkg/epp/flowcontrol/controller/internal/processor.go:288`), and the outcome mapped to a typed
     caller-visible error (`pkg/epp/requestcontrol/admission.go:216`).
5. Candidates located: **every pod in the datastore**, with no health predicate
   (`pkg/epp/requestcontrol/candidates.go:104`, `pkg/epp/datastore/datastore.go:46`). An empty set
   becomes a 503 (`pkg/epp/requestcontrol/director.go:191`).
6. Best-effort signal enrichment under a 400 ms budget; failures are logged and ignored
   (`pkg/epp/requestcontrol/director.go:55`, `:200`).
7. Scheduling: filters, then a weighted sum of scorers each clamped to [0,1], then the picker
   (`pkg/epp/scheduling/scheduler_profile.go:117`, `:167`, `:194`). An empty set after filtering is
   an error (`:119`), which the director maps to a 429 (`pkg/epp/requestcontrol/director.go:211`).
8. The picker shuffles before a stable sort, so ties resolve at random
   (`pkg/epp/framework/plugins/scheduling/picker/maxscore/picker.go:91`).

## Build / config: the shipped defaults
Scorer weights queue-depth 2.0, KV-cache 2.0, prefix-cache 3.0
(`pkg/epp/config/loader/defaults.go:47`); unweighted scorers 1.0 (`:42`). Metrics refresh every
50 ms (`pkg/epp/server/options.go:102`); state older than **200 ms** is distrusted
(`pkg/epp/framework/plugins/flowcontrol/saturationdetector/utilization/config.go:36`). Per-band
queue capacity 1 GB (`pkg/epp/flowcontrol/registry/config.go:51`). Default fairness policy is
**global-strict, which is not fair** (`pkg/epp/flowcontrol/registry/config.go:43`). Default request
time to live is **0, meaning no limit** (`pkg/epp/flowcontrol/controller/config.go:37`), swept every
1 s (`:28`).

## Two documented defaults that are not implemented
`pkg/epp/flowcontrol/registry/config.go:183` documents a 5000-request per-band cap; no such
constant exists and the defaulting function only fills in the byte cap (`:571`), so the per-band
request count is unlimited. In-flight eviction is fully built
(`pkg/epp/framework/plugins/flowcontrol/eviction/filtering/sheddable.go:56`) but has no production
caller, only tests.
