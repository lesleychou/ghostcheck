#!/usr/bin/env python3
"""Scored benchmark runner for the two-tenant LLM router.

One replay, one tenant, one JSON line. Wraps the vendored `replay_tenants.py` (the harness
that owns the clock, the fleet, the billing and every typed correctness violation) so that a
candidate can be measured from the run directory without reaching into the task root for
anything except the traces themselves.

    python3 synthesis/evaluator/benchmark/score.py --tenant A --split train \
        --router impl.common.TenantARouter

Layout
------
  vendor/evaluator/                       the harness package, copied verbatim from the task
      router_interface.py                 (byte-identical to ../interface/router_interface.py)
      generic_policy.py                   the registered baseline
      benchmark/replay.py, replay_tenants.py, env_card.yaml
      benchmark/artifacts/generic_predictions.json
  traces.json                             absolute path of the trace directory (never copied)

`replay_tenants.py` inserts its own grandparent on sys.path and imports
`evaluator.benchmark.replay`, so the vendor tree must keep exactly that shape.

Operating point
---------------
The scored configuration (cards/requirements.json operating_point) is the TRAIN trace replayed
with `--split val`, i.e. the env card's two literal prime outage windows applied to the train
timeline. Here those are two separate flags, because they are two separate things:

  --split      WHICH TRACE (train | val).  Never `test`: the test split is out of bounds for
               this entire run and this script refuses it loudly.
  --outages    WHICH OUTAGE SCHEDULE the harness imposes (val | none). Default `val`, the
               operating point. `none` is a diagnostic, not a score.

U = mean_quality - 1.0 * slo_violation_rate - 3.0 * (cost_usd / requests), per tenant, from the
harness's own tenant books and nothing the router reports.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "vendor")
if VENDOR not in sys.path:
    sys.path.insert(0, VENDOR)

# The candidate is resolved off $SKYDISCOVER_IMPL, the same way every kept test resolves it
# (decision row `routers-json`); default to this run's impl directory.
IMPL = os.environ.get("SKYDISCOVER_IMPL") or os.path.abspath(
    os.path.join(HERE, os.pardir, os.pardir, "impl")
)
if os.path.isdir(IMPL) and IMPL not in sys.path:
    sys.path.insert(0, IMPL)

from evaluator.benchmark.replay_tenants import TenantReplay  # noqa: E402

ENV_CARD = os.path.join(VENDOR, "evaluator", "benchmark", "env_card.yaml")
TRACES_CFG = os.path.join(HERE, "traces.json")

ALLOWED_SPLITS = ("train", "val")
ALLOWED_OUTAGES = ("val", "none")

# The registered bar to beat: GenericPolicy(lam=40, placement="latency") on each tenant's TRAIN
# trace under the val outage windows, as re-measured in environment mode and carried on
# cards/requirements.json operating_point.pass_condition. Reported for reference; `--baseline`
# (on by default) additionally re-measures it in the same process, which is the number that
# actually governs the pass condition.
REGISTERED_BASELINE = {
    ("A", "train", "val"): {
        "U": 0.5695,
        "mean_quality": 0.6212,
        "cost_usd_per_request": 0.004362,
        "slo_violation_rate": 0.0386,
    },
    ("B", "train", "val"): {
        "U": 0.3855,
        "mean_quality": 0.3907,
        "cost_usd_per_request": 0.001746,
        "slo_violation_rate": 0.0,
    },
}
BASELINE_ROUTER = "evaluator.generic_policy.GenericPolicy"


class OutOfBoundsSplit(SystemExit):
    pass


def _refuse(split):
    raise OutOfBoundsSplit(
        "score.py REFUSES split %r.\n"
        "  Only %s are in bounds. The TEST split is sealed for this entire run: it is\n"
        "  replayed once, by the harness owner, after the win criteria are registered\n"
        "  (task.md 'Data protocol'). Reading it here would invalidate the run."
        % (split, " / ".join(ALLOWED_SPLITS))
    )


def trace_path(tenant, split):
    if split not in ALLOWED_SPLITS:
        _refuse(split)
    cfg = json.load(open(TRACES_CFG))
    root = os.environ.get(cfg["env_var"]) or cfg["traces_dir"]
    name = cfg["files"][tenant][split]
    if "test" in name:  # belt and braces: the config itself may not smuggle test in
        _refuse(split)
    path = os.path.join(root, name)
    if not os.path.exists(path):
        raise SystemExit(
            "trace not found: %s\n  set %s to the directory holding the tenant traces"
            % (path, cfg["env_var"])
        )
    return path


def load_router(path):
    import importlib

    mod, cls = path.rsplit(".", 1)
    return getattr(importlib.import_module(mod), cls)()


def utility(book):
    n = book["requests"]
    if not n or book["mean_quality"] is None:
        return None
    return round(
        book["mean_quality"] - 1.0 * book["slo_violation_rate"] - 3.0 * (book["cost_usd"] / n), 4
    )


def row(result, tenant):
    book = result["tenants"][tenant]
    n = book["requests"]
    return {
        "mean_quality": book["mean_quality"],
        "cost_usd_per_request": round(book["cost_usd"] / n, 6) if n else None,
        "slo_violation_rate": book["slo_violation_rate"],
        "U": utility(book),
        "requests": n,
        "completed": book["completed"],
        "shed": book["shed"],
        "lost_or_dead": book["lost_or_dead"],
        "throttles_429": book["throttles_429"],
        "outage_rejects": book["outage_rejects"],
        "p95_latency_ms": book["p95_latency_ms"],
    }


def replay(tenant, split, outages, router_class, max_wall_ms=None, max_decides=None):
    result = TenantReplay(ENV_CARD, split=outages).run(
        trace_path(tenant, split),
        load_router(router_class),
        max_wall_ms=max_wall_ms,
        max_decides=max_decides,
    )
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tenant", required=True, choices=["A", "B"])
    ap.add_argument(
        "--split",
        required=True,
        help="which trace: train | val. `test` is refused; it is sealed for this run.",
    )
    ap.add_argument(
        "--outages",
        default="val",
        help="outage schedule the harness imposes: val (the operating point) | none (diagnostic)",
    )
    ap.add_argument("--router", required=True, help="dotted path to the router class")
    ap.add_argument("--no-baseline", action="store_true", help="skip the baseline re-measurement")
    ap.add_argument("--max-wall-ms", type=float, default=None)
    ap.add_argument("--max-decides", type=int, default=None)
    ap.add_argument("--indent", type=int, default=None)
    args = ap.parse_args()

    if args.split not in ALLOWED_SPLITS:
        _refuse(args.split)
    if args.outages not in ALLOWED_OUTAGES:
        raise SystemExit(
            "--outages must be one of %s; the test outage schedule is derived from the sealed "
            "card seed and is never run here." % (" / ".join(ALLOWED_OUTAGES),)
        )

    result = replay(
        args.tenant, args.split, args.outages, args.router, args.max_wall_ms, args.max_decides
    )
    out = row(result, args.tenant)
    out.update(
        {
            "tenant": args.tenant,
            "split": args.split,
            "outages": args.outages,
            "router": args.router,
            "violation_count": result["violation_count"],
            "violation_kinds": result["violation_kinds"],
            "violations": result["violations"],
            "decides": result["decides"],
            "aborted": result["aborted"],
            "outage_windows_ms": result["outage_windows_ms"],
            "accounted_exactly_once": out["requests"] == out["completed"] + out["shed"],
            "registered_baseline": REGISTERED_BASELINE.get(
                (args.tenant, args.split, args.outages)
            ),
        }
    )
    if args.no_baseline:
        out["baseline"] = None
    else:
        b = replay(args.tenant, args.split, args.outages, BASELINE_ROUTER)
        out["baseline"] = row(b, args.tenant)
        out["baseline"]["router"] = BASELINE_ROUTER + "(lam=40, placement='latency')"
        out["baseline"]["violation_count"] = b["violation_count"]
    print(json.dumps(out, indent=args.indent))


if __name__ == "__main__":
    main()
