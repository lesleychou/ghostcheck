"""Two replays of one trace must produce one set of decisions, or no measured difference
between two policies means anything.
Mutant: UnseededTieBreakMutant, which breaks ties with unseeded randomness."""
import scenarios as S
from mutants import UnseededTieBreakMutant
from routers import ReferenceRouter
from sim import replay


def main():
    reqs = S.trace(n=24, every_ms=250, deadline_ms=20000)
    gt = S.gt_for(reqs)

    a = replay(S.fleet(), reqs, gt, ReferenceRouter())
    b = replay(S.fleet(), reqs, gt, ReferenceRouter())
    assert not a.violations and not b.violations
    assert S.decisions(a) == S.decisions(b), "the reference is not reproducible"
    assert abs(a.utility() - b.utility()) < 1e-12

    runs = [S.decisions(replay(S.fleet(), reqs, gt, UnseededTieBreakMutant())) for _ in range(4)]
    assert len({tuple(r) for r in runs}) > 1, (
        "the unseeded router repeated itself four times, so the test proves nothing"
    )
    print(f"OK test_replay_determinism: reference identical twice, mutant gave "
          f"{len({tuple(r) for r in runs})} different decision sequences in 4 replays")


main()
