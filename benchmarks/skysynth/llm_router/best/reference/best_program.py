# benchmarks/skysynth/llm_router/best/reference/best_program.py
"""A stand-in P' for pipeline debugging, NOT a finding.

ReferenceRouter is SkySynth's trusted-correct baseline: it always asks for the
requested model on the first provider that stocks it, never sheds, never paces.
Their own docstring calls it "slow and expensive on purpose". That makes it a
known-weak candidate: GhostCheck should flag optimality (cost) and scalab_time
against P, and should NOT flag correctness. Any other verdict means the adapter
is wrong, not that we found something.

Replaced by the real synthesized router in Task 10.
"""
import paths

paths.bind_upstream()

from evaluator.reference_router import ReferenceRouter  # noqa: E402


def build_router(tenant: str):
    return ReferenceRouter()
