"""Locate the read-only upstream skydiscover llm-router checkout and bind its
`evaluator` namespace package before anything else can claim that name.

Why this exists: SkySynth's `evaluator` is a package DIRECTORY; GhostCheck requires a
FILE named evaluator.py in the app dir. Both want `sys.modules["evaluator"]`. The
harness execs run_workload.py before loading the program (harness.py:_worker), so we
bind their package first and our evaluator.py shim stays what it is: text Agent 1 reads.
"""
import importlib.machinery
import importlib.util
import os
import sys
from pathlib import Path

_ENV_VAR = "LLM_ROUTER_ROOT"


# Resolution order: explicit override always wins; otherwise prefer the vendored tree
# (what we publish results against) and fall back to the upstream clone (setup cloned
# it here, so it is a fallback, not a requirement).
_VENDOR_ROOT = Path(__file__).resolve().parent / "vendor"
_CLONE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "skysynth/upstream/skydiscover/synthesize/examples/llm-router"
)


def _looks_like_checkout(path: Path) -> bool:
    return (path / "evaluator").is_dir() and (path / "task.md").is_file()


def llm_router_root() -> Path:
    raw = os.environ.get(_ENV_VAR)
    if raw:
        root = Path(raw).expanduser().resolve()
    elif _looks_like_checkout(_VENDOR_ROOT):
        root = _VENDOR_ROOT.resolve()
    else:
        root = _CLONE_ROOT.resolve()
    if not _looks_like_checkout(root):
        raise RuntimeError(
            f"{root} does not look like the llm-router example "
            "(expected an evaluator/ directory and task.md). Set "
            f"{_ENV_VAR} to override, or re-clone into benchmarks/skysynth/upstream."
        )
    return root


def bind_upstream() -> None:
    """Make `import evaluator...` resolve to SkySynth's package. Idempotent.

    We register the package in sys.modules BY HAND rather than plain `import
    evaluator`, and that is not optional. SkySynth's evaluator/ has no __init__.py,
    so it is a PEP 420 namespace package -- and Python only falls back to a namespace
    package after scanning every sys.path entry for a regular module. Our app dir holds
    a file named evaluator.py, so a plain import would find the file and shadow their
    package no matter which path entry comes first. Binding __path__ explicitly makes
    `from evaluator.benchmark.replay_tenants import TenantReplay` resolve correctly
    regardless of sys.path order.
    """
    root = llm_router_root()
    pkg_dir = root / "evaluator"

    cached = sys.modules.get("evaluator")
    if cached is not None and str(pkg_dir) in list(getattr(cached, "__path__", [])):
        return  # already bound
    for name in [n for n in sys.modules if n == "evaluator" or n.startswith("evaluator.")]:
        del sys.modules[name]

    spec = importlib.machinery.ModuleSpec("evaluator", None, is_package=True)
    spec.submodule_search_locations = [str(pkg_dir)]
    module = importlib.util.module_from_spec(spec)
    sys.modules["evaluator"] = module

    # generic_policy.py does its own sys.path.insert(0, <root>); keep the root
    # importable so their relative imports and data paths resolve too.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
