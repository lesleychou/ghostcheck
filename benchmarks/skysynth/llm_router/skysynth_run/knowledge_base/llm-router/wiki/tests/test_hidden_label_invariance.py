"""A router decides from what a production request carries. The measured per-prompt per-model
score table is the answer key and no live router has it, so the decisions must not change when
that table is replaced by a different one.
Mutant: LabelPeekMutant, which picks the argmax of the hidden scores."""
import scenarios as S
from mutants import LabelPeekMutant
from routers import ReferenceRouter
from sim import replay


def main():
    reqs = S.trace(n=20, every_ms=300, deadline_ms=20000)
    gt_a = S.gt_for(reqs, seed=7)
    gt_b = S.gt_for(reqs, seed=99)

    ref_a = replay(S.fleet(), reqs, gt_a, ReferenceRouter())
    ref_b = replay(S.fleet(), reqs, gt_b, ReferenceRouter())
    assert not ref_a.violations and not ref_b.violations
    assert S.decisions(ref_a) == S.decisions(ref_b), (
        "the reference changed its dispatches when only the hidden score table changed"
    )

    peek_a = replay(S.fleet(), reqs, gt_a, LabelPeekMutant(gt_a))
    peek_b = replay(S.fleet(), reqs, gt_b, LabelPeekMutant(gt_b))
    assert S.decisions(peek_a) != S.decisions(peek_b), (
        "the label peeker did not react to the swapped table, so the test proves nothing"
    )
    gain = peek_a.mean_quality() - ref_a.mean_quality()
    print(
        f"OK test_hidden_label_invariance: the reference is unchanged under a swapped score "
        f"table; the peeker changes its dispatches and buys {gain:+.3f} mean quality it could "
        "not have in production"
    )


main()
