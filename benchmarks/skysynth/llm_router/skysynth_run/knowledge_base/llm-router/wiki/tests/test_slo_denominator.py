"""A refused, lost or late request belongs to its tenant's violation rate and books zero
quality. Abandoning the requests that are hardest to serve on time therefore cannot improve
the rate: it moves the same failure into another column and gives up the quality too.
Mutant: DoomedDropMutant, which gives up on a request whose deadline already passed."""
import scenarios as S
from mutants import DoomedDropMutant
from routers import ReferenceRouter
from sim import Violation, replay

TIGHT = {"value": 2, "prime": 1, "courier": 1}
LOOSE_RPM = {"value": 60, "prime": 40, "courier": 40}
ALL_DOWN = {p: [(0, 600_000)] for p in ("value", "prime", "courier")}


def main():
    # 1. a refusal the fleet really forced is still counted against the tenant.
    reqs = S.trace(n=8, every_ms=400, deadline_ms=5000)
    gt = S.gt_for(reqs)
    dark = replay(S.fleet(outages=ALL_DOWN), reqs, gt, ReferenceRouter(), horizon_ms=30_000)
    assert not dark.violations, dark.violations
    assert all(e.status == "shed" for e in dark.entries.values())
    assert dark.slo_violation_rate() == 1.0, "a refused request escaped the violation rate"
    assert dark.mean_quality() == 0.0, "a refused request booked quality"

    # 2. under load, the reference is late on some requests and keeps them.
    reqs = S.trace(n=40, every_ms=150, deadline_ms=1500)
    gt = S.gt_for(reqs)
    ref = replay(S.fleet(concurrency=TIGHT, rpm=LOOSE_RPM), reqs, gt, ReferenceRouter())
    assert not ref.violations, ref.violations
    late = sum(1 for e in ref.entries.values() if not e.slo_ok)
    assert late > 0, "the scenario has no late requests, so the test proves nothing"

    caught, rate = "", None
    try:
        bad = replay(S.fleet(concurrency=TIGHT, rpm=LOOSE_RPM), reqs, gt, DoomedDropMutant())
        rate = bad.slo_violation_rate()
    except Violation as err:
        caught, rate = str(err), err.run.slo_violation_rate()
    assert caught or rate >= ref.slo_violation_rate() - 1e-9, (
        f"dropping doomed requests cut the violation rate from {ref.slo_violation_rate():.3f} "
        f"to {rate:.3f}, so the books are not counting them"
    )
    assert caught, "the drop was neither refused nor counted, so nothing stopped it"
    print(
        f"OK test_slo_denominator: 8 forced refusals give rate 1.000 and quality 0.000; under "
        f"load the reference carries {late} late requests at rate "
        f"{ref.slo_violation_rate():.3f} and the mutant is stopped: {caught}"
    )


main()
