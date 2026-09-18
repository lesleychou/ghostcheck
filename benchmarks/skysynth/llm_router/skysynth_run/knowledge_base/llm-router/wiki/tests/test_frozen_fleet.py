"""The fleet's prices, quotas and limits belong to the harness. A router that reaches through
the view it was handed and edits them cuts its bill without changing a single decision.
Mutant: PriceEditMutant, which zeroes every price it can see."""
import scenarios as S
from mutants import PriceEditMutant
from routers import ReferenceRouter
from sim import replay


def main():
    reqs = S.trace(n=12, every_ms=500, deadline_ms=20000)
    gt = S.gt_for(reqs)

    fl = S.fleet()
    run = replay(fl, reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    assert run.fleet_checksum_before == run.fleet_checksum_after
    assert run.billed_total() > 0

    fl2 = S.fleet()
    bad = replay(fl2, reqs, gt, PriceEditMutant())
    assert "fleet_mutated" in bad.violations, (
        "the fleet tables were edited by the router and the harness did not notice"
    )
    assert bad.billed_total() < run.billed_total(), "the edit bought nothing, so nothing is proven"
    print(
        f"OK test_frozen_fleet: the reference leaves the tables byte-identical; the mutant bills "
        f"{bad.billed_total():.4f} against {run.billed_total():.4f} and is caught by the checksum"
    )


main()
