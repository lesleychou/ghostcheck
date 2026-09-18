# task-evaluator — the shipped contract (`skydiscover/synthesize/examples/llm-router/evaluator/`)

Not a clone: the task ships this directory as the interface, the trusted-correct reference, the
baseline to beat and the scoring harness. It is cited here because it is the *only* authority on
what a legal router action is; the five cloned systems ground the design space around it. Every
path below is repo-relative from the project root.

## Purpose
A discrete-event replay of a per-tenant arrival trace through a `Router` policy against a frozen,
simulated fleet of 3 providers x 12 models. The harness owns the clock, the fleet, the billing and
every correctness/SLO book; the router owns only placement policy
(`skydiscover/synthesize/examples/llm-router/evaluator/router_interface.py:1`).

## Public interface
- `Router.decide(req, now_ms, fleet_view) -> Action` — the one required method
  (`.../evaluator/router_interface.py:79`).
- `Router.on_error(req, now_ms, kind, retry_after_ms) -> None` — informational after a 429/503;
  `decide()` is re-invoked afterwards (`.../evaluator/router_interface.py:82`).
- `Router.on_complete(req, now_ms) -> Optional[Action]` — informational; **a correct router returns
  `None`**, and the docstring names returning an Action as the double-bill mutant
  (`.../evaluator/router_interface.py:85`).
- `Action(kind, provider, model, until_ms)` with `kind in {"dispatch","defer","shed"}`
  (`.../evaluator/router_interface.py:63`, kinds at `:67`).
- `Request` is a frozen trace row: `equiv_class` (`:18`), `slo` (`:23`), `downgrade_ok` (`:24`),
  `retry_safe` (`:25`), ground-truth per-model `quality` (`:31`), `quality_floor` (`:32`) and
  observable `features` (`:35`).
- `fleet_view[provider] = {models, inflight, rpm_left, tpm_left, error_rate, has_prefix}`, and
  `outage_until` while that provider is down
  (`.../evaluator/router_interface.py:74`; built at `.../evaluator/benchmark/replay_tenants.py:140`).

## Module map
| File | Role |
|---|---|
| `.../evaluator/router_interface.py` | `Request`, `Action`, `Router` — the contract |
| `.../evaluator/reference_router.py` | trusted-correct oracle: requested model, first provider that stocks it, defer 1000 ms otherwise (`:9`) |
| `.../evaluator/generic_policy.py` | the tenant-blind baseline to beat, `GenericPolicy(lam=40, placement="latency")` (`:31`) |
| `.../evaluator/benchmark/replay.py` | base discrete-event replay, all typed violations, liveness budgets |
| `.../evaluator/benchmark/replay_tenants.py` | the SCORED harness: adds outages, per-model decode, per-tenant books |
| `.../evaluator/benchmark/env_card.yaml` | the frozen fleet: 3 providers, 12 models, prices, quotas, outages |
| `.../evaluator/benchmark/data/cards/tenant{A,B}.card.yaml` | the two measured workloads |

## Execution spine of ONE request (scored harness)
1. Arrival pushed as an `arrive` event at `req.t_ms` (`.../replay_tenants.py:178`).
2. Liveness budgets checked: 512 decide() calls per request (`.../replay.py:35`, applied at
   `.../replay_tenants.py:224`, enforced `:382`) and 600 000 ms wall clock (`.../replay.py:34`,
   enforced `.../replay_tenants.py:389`); exceeding either aborts with `harness_hang`
   (`.../replay_tenants.py:446`).
3. `decide()` is called on a **copy** of the request with a freshly built `fleet_view`
   (`.../replay_tenants.py:399`, copy at `:229`, view at `:140`).
4. The copy is diffed against harness truth; any edited trace field is `req_mutation` and is rolled
   back (`.../replay_tenants.py:235`). Any exception out of a callback is `router_exception`
   (`:247`).
5. The Action is executed (`.../replay_tenants.py:260`): shed (`:265`), defer (`:289`), dispatch
   (`:310`).
6. Dispatch: substitution legality (`:312`), provider exists (`:316`), model stocked (`:320`), then
   `TenantProvider.admit` (`:324` -> `:71`).
7. `admit` refuses with `503` while the provider is down (`:72`), with `429` on model-absent /
   concurrency / rpm / tpm exhaustion (`:79`), and with `503` at the provider's `error_rate` (`:87`);
   otherwise it charges the bill and schedules a `complete` event (`:110`, `:370`).
8. On completion the harness books quality from the **served** model (`:412`), latency against the
   request's own SLO field (`:422`), and the per-tenant books (`:433`).

## Build / config
Pure Python + PyYAML, no network. Scored entry point:
`python evaluator/benchmark/replay_tenants.py TRACE.jsonl <RouterClassPath> --split val|test|none`
(`.../replay_tenants.py:538`). The env card is frozen (`.../env_card.yaml:2`).
