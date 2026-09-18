"""A replayed trace is the same every time, so a policy can key on a request identifier and
look like it learned something. Relabelling the trace without touching a single feature must
not change one decision.
Mutant: IdMemoriseMutant, which memorised the best model per prompt id from an earlier replay."""
import scenarios as S
from mutants import IdMemoriseMutant
from routers import ReferenceRouter
from sim import replay


def main():
    reqs = S.trace(n=20, every_ms=300, deadline_ms=20000)
    other = S.relabel(reqs)
    gt = S.gt_for(reqs)
    gt.update(S.gt_for(other, seed=7))

    ref_1 = replay(S.fleet(), reqs, gt, ReferenceRouter())
    ref_2 = replay(S.fleet(), other, gt, ReferenceRouter())
    assert not ref_1.violations and not ref_2.violations
    assert S.decisions(ref_1) == S.decisions(ref_2), (
        "the reference changed its dispatches when only the identifiers changed"
    )

    table = {}
    for r in reqs:
        table[r.prompt_id] = max(S.MODELS, key=lambda m: gt[(r.prompt_id, m)])
    memo_1 = replay(S.fleet(), reqs, gt, IdMemoriseMutant(table))
    memo_2 = replay(S.fleet(), other, gt, IdMemoriseMutant(table))
    assert S.decisions(memo_1) != S.decisions(memo_2), (
        "the memoriser survived relabelling, so the test proves nothing"
    )
    print(
        "OK test_id_permutation_invariance: the reference is identical on the relabelled trace; "
        "the memoriser is not, because its table was keyed on the file and not on the request"
    )


main()
