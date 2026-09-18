"""Fixed per-app run_workload for the SkySynth llm-router benchmark.

One GhostCheck workload dict -> one TenantReplay of P or P' -> flat metrics.

Order matters: the harness execs this file BEFORE loading the program
(harness.py:_worker), so bind_upstream() here is what makes `evaluator` resolve to
SkySynth's package rather than our Agent-1 shim of the same name.

TenantReplay takes FILE PATHS for both the trace and the env card, so each call writes
its transformed copies to a temp dir and deletes them afterwards. A val trace is a few
thousand JSON lines; this costs milliseconds.

Oracle mapping:
  correctness  -- we raise on any typed violation, crash, or timeout
  optimality   -- mean_quality, neg_cost_usd_per_request, neg_slo_violation_rate, utility_U
  scalab_time  -- wall clock, measured by the harness
  scalab_mem   -- tracemalloc peak, measured by the harness

EVERY numeric field returned must be higher-is-better: oracle.py:_check_optimality
treats all numeric non-time fields that way and fires when P > P'.
"""
import json
import os
import sys
import tempfile

# The harness runs this file as `exec(source, {})` (harness.py:_worker), a bare namespace
# with NO __file__ -- so referencing it raises NameError and every oracle call fails. The
# harness has already put the app dir (and, for a program in best/<x>/, the app root via
# extra_path) on sys.path before the exec, so there is nothing to add in that case.
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:  # exec'd by the harness
    _HERE = None
if _HERE and _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import yaml  # noqa: E402

import env_transform  # noqa: E402
import envelope  # noqa: E402
import paths  # noqa: E402
import trace_transform  # noqa: E402

# NOTE: bind_upstream() is deliberately NOT called at import time. Importing this
# module must work with no LLMRouterBench checkout so the unit tests stay fast and
# data-free. The programs (initial_program.py / best_program.py) bind on their own
# import, and run_workload() binds again defensively; both are idempotent.

_TRACE_DIR = "evaluator/benchmark/.data/traces"
_ENV_CARD = "evaluator/benchmark/env_card.yaml"


def _base_trace_path(tenant: str, split: str) -> str:
    root = paths.llm_router_root()
    name = "trace_merged" if tenant == "merged" else f"trace_tenant{tenant}"
    path = root / _TRACE_DIR / f"{name}_{split}.jsonl"
    if not path.is_file():
        raise RuntimeError(
            f"trace not found: {path}\nBuild it once with:\n"
            f"  cd {root} && python evaluator/benchmark/data/make_tenant_traces.py"
        )
    return str(path)


def _router_from_module(mod, tenant: str):
    build = getattr(mod, "build_router", None)
    if build is None:
        raise RuntimeError(
            f"{getattr(mod, '__name__', mod)} defines no build_router(tenant); "
            "both P and P' must expose it so the differential is fair"
        )
    return build(tenant)


def _metrics_from_replay(result: dict, tenant: str) -> dict:
    """Flatten a TenantReplay result. Raises on any typed violation so GhostCheck'
    correctness oracle sees a hard failure rather than a silently worse number."""
    if result.get("violation_count"):
        kinds = result.get("violation_kinds") or {}
        raise RuntimeError(
            f"correctness violation ({result['violation_count']}): {json.dumps(kinds)}; "
            f"first: {json.dumps(result.get('violations', [])[:3])}"
        )

    if tenant in ("A", "B"):
        book = (result.get("tenants") or {}).get(tenant) or {}
        requests = book.get("requests") or 0
        quality = book.get("mean_quality") or 0.0
        cost = book.get("cost_usd") or 0.0
        svr = book.get("slo_violation_rate") or 0.0
        shed = book.get("shed") or 0
    else:
        quality = result.get("mean_quality") or 0.0
        cost = result.get("total_cost_usd") or 0.0
        shed = result.get("shed") or 0
        # Aggregate the per-tenant books rather than the global one. Two reasons:
        # the GLOBAL "slo_violations" is a dict keyed by SLO class (not an int), and a
        # plain mean of the two tenant rates would weight a 693-request tenant like a
        # 972-request one -- paying a router to drop its smaller tenant. Summing
        # (violations + shed + lost) over summed requests reproduces the 0.0414 that
        # generic_baseline_results.json publishes for val.merged; a mean gives 0.0355.
        books = list((result.get("tenants") or {}).values())
        requests = sum(b.get("requests") or 0 for b in books) or (result.get("requests") or 0)
        missed = sum(
            (b.get("slo_violations") or 0) + (b.get("shed") or 0) + (b.get("lost_or_dead") or 0)
            for b in books
        )
        svr = missed / requests if requests else 0.0

    cost_per_req = cost / requests if requests else 0.0
    return {
        # higher-is-better quality terms
        "mean_quality": round(quality, 6),
        "neg_cost_usd_per_request": round(-cost_per_req, 8),
        "neg_slo_violation_rate": round(-svr, 6),
        "neg_shed": -int(shed),
        "completed": int(result.get("completed") or 0),
        # task.md's own tuning metric, so a regression is stated in their units
        "utility_U": round(quality - 1.0 * svr - 3.0 * cost_per_req, 6),
        # context, not scored (strings and bools are ignored by the optimality oracle)
        "requests": int(requests),
        "tenant_scope": str(tenant),
    }


def run_workload(program_module, workload: dict):
    paths.bind_upstream()
    tenant = str(workload.get("tenant", "merged"))
    split = str(workload.get("split", "val"))
    if split != "val":
        raise RuntimeError(
            f"split={split!r} refused; task.md puts the test split out of bounds "
            "for every tuning phase"
        )

    root = paths.llm_router_root()
    with open(_base_trace_path(tenant, split)) as fh:
        records = [json.loads(line) for line in fh if line.strip()]
    records = trace_transform.transform_trace(records, workload)
    if not records:
        raise RuntimeError(f"workload selected zero requests: {json.dumps(workload)}")

    with open(root / _ENV_CARD) as fh:
        env = yaml.safe_load(fh)
    env = env_transform.transform_env(env, workload)

    from evaluator.benchmark.replay_tenants import TenantReplay

    tmp = tempfile.mkdtemp(prefix="ghostcheck_llm_router_")
    try:
        trace_path = os.path.join(tmp, "trace.jsonl")
        with open(trace_path, "w") as fh:
            for rec in records:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
        env_path = os.path.join(tmp, "env_card.yaml")
        with open(env_path, "w") as fh:
            # sort_keys=False is LOAD-BEARING, not style. The default sorts mapping keys,
            # which reorders the fleet from [value, prime, courier] to [courier, prime,
            # value]. env_card.yaml's own header says "order matters, routers that take
            # the first stocking provider get `value` for open-weight models and `prime`
            # for the closed ones" -- so the default silently changes every placement a
            # first-fit router makes. Measured on ReferenceRouter over trace_tenantA_val:
            # sorted gives cost/req 0.01499, svr 0.2788, U 0.1875; unsorted reproduces the
            # real card exactly at 0.01820 / 0.1800 / 0.2767. A price-ranking router like
            # GenericPolicy masks the bug completely, which is how it nearly shipped.
            yaml.safe_dump(env, fh, sort_keys=False)

        router = _router_from_module(program_module, tenant)
        result = TenantReplay(env_path, split=split).run(trace_path, router)
    finally:
        for name in os.listdir(tmp):
            os.unlink(os.path.join(tmp, name))
        os.rmdir(tmp)

    metrics = _metrics_from_replay(result, tenant)
    tag = envelope.classify(workload)
    metrics["in_envelope"] = tag["in_envelope"]
    metrics["outside_envelope_knobs"] = ",".join(tag["outside"])
    return metrics
