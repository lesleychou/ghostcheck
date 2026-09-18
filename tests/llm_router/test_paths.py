import sys
import pytest

sys.path.insert(0, "benchmarks/skysynth/llm_router")
import paths  # noqa: E402


def test_llm_router_root_reads_env(tmp_path, monkeypatch):
    (tmp_path / "evaluator").mkdir()
    (tmp_path / "task.md").write_text("x")
    monkeypatch.setenv("LLM_ROUTER_ROOT", str(tmp_path))
    assert paths.llm_router_root() == tmp_path


def test_llm_router_root_defaults_to_the_in_repo_clone(tmp_path, monkeypatch):
    """When the vendored tree does not validate, fall back to the upstream clone."""
    monkeypatch.delenv("LLM_ROUTER_ROOT", raising=False)
    monkeypatch.setattr(paths, "_VENDOR_ROOT", tmp_path / "no-vendor-here")
    root = paths.llm_router_root()
    assert root.name == "llm-router"
    assert (root / "task.md").is_file()


def test_vendored_tree_is_preferred_over_the_clone(monkeypatch):
    """The vendored copy is what we publish results against, so it must win when no
    explicit override is set."""
    monkeypatch.delenv("LLM_ROUTER_ROOT", raising=False)
    root = paths.llm_router_root()
    assert root.name == "vendor"
    assert (root / "evaluator" / "generic_policy.py").is_file()


def test_env_var_still_overrides_the_vendored_tree(tmp_path, monkeypatch):
    (tmp_path / "evaluator").mkdir()
    (tmp_path / "task.md").write_text("x")
    monkeypatch.setenv("LLM_ROUTER_ROOT", str(tmp_path))
    assert paths.llm_router_root() == tmp_path


def test_sealed_test_split_is_absent_from_the_vendored_tree():
    """task.md seals the test split. Not shipping it is the cheapest proof we never
    replayed it."""
    root = paths.llm_router_root()
    traces = root / "evaluator" / "benchmark" / ".data" / "traces"
    assert not list(traces.glob("*test*")), "sealed test split must not be vendored"


def test_llm_router_root_errors_when_not_a_checkout(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_ROUTER_ROOT", str(tmp_path))
    with pytest.raises(RuntimeError, match="does not look like"):
        paths.llm_router_root()


def test_bind_upstream_wins_over_a_shadowing_evaluator_module(tmp_path, monkeypatch):
    """The regression this module exists for: an evaluator.py on sys.path must not
    shadow SkySynth's namespace-package evaluator/ directory."""
    root = tmp_path / "llm-router"
    (root / "evaluator").mkdir(parents=True)
    (root / "task.md").write_text("x")
    (root / "evaluator" / "router_interface.py").write_text("MARKER = 'upstream'\n")

    shadow = tmp_path / "appdir"
    shadow.mkdir()
    (shadow / "evaluator.py").write_text("MARKER = 'shim'\n")
    monkeypatch.syspath_prepend(str(shadow))

    monkeypatch.setenv("LLM_ROUTER_ROOT", str(root))
    monkeypatch.delitem(sys.modules, "evaluator", raising=False)
    paths.bind_upstream()

    from evaluator.router_interface import MARKER

    assert MARKER == "upstream"


def test_bind_upstream_is_idempotent(tmp_path, monkeypatch):
    root = tmp_path / "llm-router"
    (root / "evaluator").mkdir(parents=True)
    (root / "task.md").write_text("x")
    monkeypatch.setenv("LLM_ROUTER_ROOT", str(root))
    paths.bind_upstream()
    first = sys.modules["evaluator"]
    paths.bind_upstream()
    assert sys.modules["evaluator"] is first
