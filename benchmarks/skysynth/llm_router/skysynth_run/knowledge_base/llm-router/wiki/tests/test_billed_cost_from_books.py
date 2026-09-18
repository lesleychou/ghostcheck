"""The bill is the harness ledger, never what the router says it spent. A router that
under-reports changes its story and not its spending.
Mutant: CostUnderReportMutant, which buys the flagship and reports the cheap price."""
import scenarios as S
from mutants import CostUnderReportMutant
from routers import ReferenceRouter
from sim import replay


def main():
    reqs = S.trace(n=12, every_ms=600, deadline_ms=20000)
    gt = S.gt_for(reqs)

    honest = ReferenceRouter()
    ref = replay(S.fleet(), reqs, gt, honest)
    assert not ref.violations, ref.violations
    assert abs(honest.reported_cost_usd - ref.billed_total()) < 1e-9, "the reference misreports"

    liar = CostUnderReportMutant()
    bad = replay(S.fleet(), reqs, gt, liar)
    assert not bad.violations, bad.violations

    assert abs(bad.billed_total() - ref.billed_total()) < 1e-9, (
        "the two routers made the same dispatches, so the books must agree"
    )
    drift = bad.billed_total() - liar.reported_cost_usd
    assert drift > 1e-6, "the mutant did not under-report, so the test proves nothing"
    assert abs(bad.utility() - ref.utility()) < 1e-9, "the score moved with the router's story"
    print(
        f"OK test_billed_cost_from_books: books charge {bad.billed_total():.4f} either way; "
        f"the mutant claims {liar.reported_cost_usd:.4f}, a gap of {drift:.4f}, and the score "
        "does not move"
    )


main()
