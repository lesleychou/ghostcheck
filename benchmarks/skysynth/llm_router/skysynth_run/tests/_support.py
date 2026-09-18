"""Shared plumbing for the suite. Not a test (test.sh skips `_*.py`).

The suite is self-contained by contract: it is copied to `best/tests/` at delivery and run from
there, so a test may depend ONLY on

  * `$SKYDISCOVER_IMPL`       the implementation under test (a directory here),
  * `$SKYDISCOVER_INTERFACE`  the interface directory,
  * this suite directory      (the vendored harness under `vendor/`, `fixtures/`),
  * scratch files it writes itself.

Nothing here ever opens a project file by relative path, and nothing here ever opens a `*_test.*`
trace, matrix or manifest: the test split is sealed for this run.
"""

from __future__ import annotations

import copy
import importlib
import json
import os
import random
import shutil
import sys
import tempfile

SUITE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(SUITE, "vendor")
FIXTURES = os.path.join(SUITE, "fixtures")
ENV_CARD = os.path.join(VENDOR, "evaluator", "benchmark", "env_card.yaml")

# `replay_tenants.py` inserts its own grandparent (== VENDOR) on sys.path and imports
# `evaluator.benchmark.replay`, so the vendored tree must keep exactly that shape.
if VENDOR not in sys.path:
    sys.path.insert(0, VENDOR)

from evaluator.benchmark.replay_tenants import TenantReplay  # noqa: E402
from evaluator.router_interface import Request, Router  # noqa: E402

FIXTURE = {
    "A": os.path.join(FIXTURES, "trace_tenantA_fixture.jsonl"),
    "B": os.path.join(FIXTURES, "trace_tenantB_fixture.jsonl"),
}
TENANTS = ("A", "B")


# ---------------------------------------------------------------- reporting


class Skip(Exception):
    """Raised by a test that cannot run here for a declared, benign reason."""


def ok(msg):
    print("OK " + msg)


def fail(msg):
    raise AssertionError(msg)


def main(fn):
    """Run one test body: 0 pass, 0 + a SKIP line for a declared skip, 1 failure."""
    try:
        fn()
    except Skip as exc:
        print("SKIP %s: %s" % (os.path.basename(sys.argv[0]), exc))
        return 0
    return 0


# ---------------------------------------------------------------- the candidates


def impl_dir():
    impl = os.environ.get("SKYDISCOVER_IMPL")
    if not impl:
        raise SystemExit("SKYDISCOVER_IMPL is not set; the harness sets it before test.sh runs")
    impl = os.path.abspath(impl)
    if not os.path.isdir(impl):
        raise SystemExit("SKYDISCOVER_IMPL is not a directory: %s" % impl)
    if impl not in sys.path:
        sys.path.insert(0, impl)
    return impl


def candidate_classes():
    """{tenant: class} for the delivered routers, resolved exactly as decision-log row
    `routers-json` fixes it: `$SKYDISCOVER_IMPL/routers.json` = {"A": "<module>.<Class>",
    "B": "<module>.<Class>"} relative to the implementation directory, with a `TENANT` class
    attribute as the fallback for a directory that ships no such file."""
    impl = impl_dir()
    cfg = os.path.join(impl, "routers.json")
    if os.path.exists(cfg):
        with open(cfg) as fh:
            spec = json.load(fh)
        out = {}
        for tenant in TENANTS:
            dotted = spec.get(tenant)
            if not dotted:
                raise SystemExit("%s names no router for tenant %s" % (cfg, tenant))
            mod, cls = dotted.rsplit(".", 1)
            out[tenant] = getattr(importlib.import_module(mod), cls)
        return out

    found = {}
    for entry in sorted(os.listdir(impl)):
        if not entry.endswith(".py") or entry.startswith("_"):
            continue
        module = importlib.import_module(entry[:-3])
        for name in sorted(vars(module)):
            obj = getattr(module, name)
            tenant = getattr(obj, "TENANT", None)
            if isinstance(obj, type) and tenant in TENANTS and callable(getattr(obj, "decide", None)):
                found.setdefault(tenant, obj)
    missing = [t for t in TENANTS if t not in found]
    if missing:
        raise SystemExit(
            "no routers.json in %s and no class with TENANT in %s; see decision-log row "
            "`routers-json`" % (impl, missing)
        )
    return found


def fresh(tenant, classes=None):
    """A brand-new router instance for `tenant`. Zero-argument construction is the delivery
    contract (the replay CLI builds routers that way)."""
    classes = classes or candidate_classes()
    return classes[tenant]()


# ---------------------------------------------------------------- observing a replay


class RecordingProxy(Router):
    """A Router the test owns, wrapping the candidate. It records only what the candidate
    RETURNS from the public entry point; it never touches candidate state, reads a candidate
    counter, or looks at candidate source."""

    def __init__(self, inner):
        self.inner = inner
        self.log = []

    def decide(self, req, now_ms, fleet_view):
        action = self.inner.decide(req, now_ms, fleet_view)
        self.log.append(
            (
                req.req_id,
                now_ms,
                getattr(action, "kind", None),
                getattr(action, "provider", None),
                getattr(action, "model", None),
                getattr(action, "until_ms", None),
            )
        )
        return action

    def on_error(self, req, now_ms, kind, retry_after_ms):
        return self.inner.on_error(req, now_ms, kind, retry_after_ms)

    def on_complete(self, req, now_ms):
        return self.inner.on_complete(req, now_ms)


def replay(trace_path, router, env_card=None, split="val"):
    """One replay through the vendored harness at the scored outage schedule."""
    return TenantReplay(env_card or ENV_CARD, split=split).run(trace_path, router)


def replay_recorded(trace_path, tenant, classes=None, env_card=None, split="val"):
    """(books, decision_log) for a FRESH candidate instance on `trace_path`."""
    proxy = RecordingProxy(fresh(tenant, classes))
    books = replay(trace_path, proxy, env_card=env_card, split=split)
    return books, proxy.log


# ---------------------------------------------------------------- scratch + traces


def scratch(prefix="skysynth-test-"):
    """A scratch directory the test owns. Callers pass it to `shutil.rmtree`."""
    return tempfile.mkdtemp(prefix=prefix)


def rows(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_rows(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return path


def full_train_trace(tenant):
    """Path of the FULL train trace for `tenant`, for the operating-point test.

    The ~20 MB traces are deliberately not vendored into the suite. Resolution order:
      1. `$SKYDISCOVER_TRACES_DIR`;
      2. the directory recorded in `$SKYDISCOVER_RUN/synthesis/evaluator/benchmark/traces.json`,
         when that variable points at a run directory.
    Neither present, or the file missing -> `Skip`, so `best/tests/` still runs anywhere.

    Only `train` is ever resolved here. The val split is the harness owner's, and the TEST split
    is sealed for this whole run; this function refuses to name one.
    """
    name = "trace_tenant%s_train.jsonl" % tenant
    root = os.environ.get("SKYDISCOVER_TRACES_DIR")
    if not root:
        run = os.environ.get("SKYDISCOVER_RUN")
        cfg = (
            os.path.join(run, "synthesis", "evaluator", "benchmark", "traces.json") if run else None
        )
        if cfg and os.path.exists(cfg):
            with open(cfg) as fh:
                root = json.load(fh).get("traces_dir")
    if not root:
        raise Skip(
            "the full train traces are not vendored into the suite; set SKYDISCOVER_TRACES_DIR "
            "to the directory holding trace_tenant{A,B}_train.jsonl to run this leg"
        )
    path = os.path.join(root, name)
    if not os.path.exists(path):
        raise Skip("no %s under %s" % (name, root))
    return path


# ---------------------------------------------------------------- hand-built fixtures


def env_card():
    import yaml

    with open(ENV_CARD) as fh:
        return yaml.safe_load(fh)


def healthy_fleet_view(card=None, down=()):
    """A fleet view shaped exactly as the harness publishes one (replay_tenants.py
    TenantReplay.fleet_view): every key it sets, and nothing else. Providers named in `down`
    publish the announced-outage form: empty catalogue, no headroom, an `outage_until` ETA."""
    card = card or env_card()
    view = {}
    for name, cfg in card["providers"].items():
        if name in down:
            view[name] = {
                "models": {},
                "inflight": 0,
                "rpm_left": 0,
                "tpm_left": 0,
                "error_rate": float(cfg.get("error_rate", 0.0)),
                "outage_until": 420000,
                "has_prefix": (lambda pid: False),
            }
            continue
        view[name] = {
            "models": {m: dict(price) for m, price in cfg["models"].items()},
            "inflight": 0,
            "rpm_left": int(cfg["rpm"]),
            "tpm_left": int(cfg["tpm"]),
            "error_rate": float(cfg.get("error_rate", 0.0)),
            "has_prefix": (lambda pid: False),
        }
    return view


def request_from(record, **overrides):
    """A Request built the way the harness builds one, with named overrides."""
    rec = copy.deepcopy(record)
    rec.update(overrides)
    return Request.from_json(rec)


def case_table(seed=11, n=12):
    """A seeded table of (label, Request, fleet_view) probes for the direct-entry-point tests:
    healthy fleets, a down `prime`, and downgrade_ok=False requests, drawn from both tenants'
    fixture rows. Deterministic: same seed, same table, every run."""
    card = env_card()
    pool = rows(FIXTURE["A"])[:60] + rows(FIXTURE["B"])[:60]
    rnd = random.Random(seed)
    table = []
    for i in range(n):
        rec = pool[rnd.randrange(len(pool))]
        if i % 3 == 0:
            label, down, over = "healthy", (), {}
        elif i % 3 == 1:
            label, down, over = "prime-down", ("prime",), {}
        else:
            label, down, over = "no-downgrade", (), {"downgrade_ok": False}
        table.append(
            (
                "%s#%d %s/%s" % (label, i, rec["class"], rec["model_requested"]),
                request_from(rec, **over),
                healthy_fleet_view(card, down=down),
                100_000 + 1000 * i,
            )
        )
    return table


def first_difference(left, right, path="books"):
    """The first place two harness books (or any two JSON-shaped values) disagree, as a path
    plus the two values, so a failure names the field instead of dumping two dicts."""
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                return "%s.%s present in only one run" % (path, key)
            diff = first_difference(left[key], right[key], "%s.%s" % (path, key))
            if diff:
                return diff
        return None
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return "%s has %d vs %d entries" % (path, len(left), len(right))
        for i, (a, b) in enumerate(zip(left, right)):
            diff = first_difference(a, b, "%s[%d]" % (path, i))
            if diff:
                return diff
        return None
    if left != right:
        return "%s: %r != %r" % (path, left, right)
    return None


def strip_callables(view):
    """A fleet view compared by VALUE: the harness publishes a fresh `has_prefix` closure per
    call, which is not data, so it is not part of the comparison."""
    return {
        name: {k: v for k, v in entry.items() if not callable(v)}
        for name, entry in view.items()
    }


__all__ = [
    "ENV_CARD",
    "FIXTURE",
    "SUITE",
    "TENANTS",
    "VENDOR",
    "RecordingProxy",
    "Request",
    "Router",
    "Skip",
    "TenantReplay",
    "candidate_classes",
    "case_table",
    "env_card",
    "fail",
    "first_difference",
    "fresh",
    "full_train_trace",
    "healthy_fleet_view",
    "impl_dir",
    "main",
    "ok",
    "replay",
    "replay_recorded",
    "request_from",
    "rows",
    "scratch",
    "strip_callables",
    "write_rows",
    "shutil",
]
