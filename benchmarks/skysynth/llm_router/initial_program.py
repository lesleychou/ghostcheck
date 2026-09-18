# benchmarks/skysynth/llm_router/initial_program.py
"""P, the reference GhostCheck compares against: the generic baseline from task.md,
one tenant-blind policy trained on the merged traffic.

    "against the generic baseline
     evaluator.generic_policy.GenericPolicy(lam=40, placement='latency'),
     trained on the merged traffic"   -- task.md, Score
"""
import paths

paths.bind_upstream()

from evaluator.generic_policy import GenericPolicy  # noqa: E402


def build_router(tenant: str):
    """The baseline is tenant-blind on purpose; `tenant` is accepted and ignored."""
    return GenericPolicy(lam=40.0, placement="latency")
