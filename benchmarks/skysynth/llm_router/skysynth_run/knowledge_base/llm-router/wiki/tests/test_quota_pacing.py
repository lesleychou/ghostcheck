"""Published headroom is read before dispatch, not learned from rejections. A simulator makes
a rejection cheap; a provider does not.
Mutant: QuotaBlindMutant, which always dispatches to its favourite provider."""
import scenarios as S
from mutants import QuotaBlindMutant
from routers import ReferenceRouter
from sim import Violation, replay


def main():
    reqs = S.trace(n=24, every_ms=300, deadline_ms=20000)
    gt = S.gt_for(reqs)

    run = replay(S.fleet(), reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    assert run.quota_rejections == 0, f"the reference collected {run.quota_rejections} rejections"

    rejections, caught = 0, ""
    try:
        bad = replay(S.fleet(), reqs, gt, QuotaBlindMutant())
        rejections = bad.quota_rejections
    except Violation as err:
        caught, rejections = str(err), err.run.quota_rejections
    assert rejections > 0, "the quota-blind router was never rejected, so the test proves nothing"
    print(f"OK test_quota_pacing: reference 0 rejections, mutant {rejections}. {caught}")


main()
