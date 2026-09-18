"""Two tenants share one fleet. A policy that takes every free slot for whoever asked first
serves its own tenant by consuming the other's capacity, and the other tenant's requests are
the ones that never finish.
Mutant: HeadroomHogMutant, the reference with the per-tenant reserve removed."""
import scenarios as S
from mutants import HeadroomHogMutant
from routers import FairShareRouter
from sim import Violation, replay


def main():
    a = S.trace(n=30, tenant="A", model="flagship", every_ms=150, deadline_ms=6000)
    b = S.trace(n=10, tenant="B", model="flagship", every_ms=900, deadline_ms=6000,
                first_rid=500, prompt_prefix="b", equiv=("flagship",))
    reqs = sorted(a + b, key=lambda r: (r.t_ms, r.rid))
    gt = S.gt_for(reqs)

    fair = replay(S.fleet(), reqs, gt, FairShareRouter())
    assert not fair.violations, fair.violations
    assert fair.served_share("B") == 1.0, fair.served_share("B")
    assert fair.served_share("A") == 1.0, fair.served_share("A")

    caught, hog_b = "", None
    try:
        hog = replay(S.fleet(), reqs, gt, HeadroomHogMutant())
        hog_b = hog.served_share("B")
    except Violation as err:
        caught, hog_b = str(err), err.run.served_share("B")
        starved = int(caught.split()[1])
        assert starved >= 500, f"the starved request {starved} does not belong to tenant B"
    assert caught or hog_b < fair.served_share("B"), (
        "removing the reserve changed nothing, so the scenario does not show starvation"
    )
    print(
        f"OK test_tenant_fair_share: with a reserve both tenants finish; without it tenant B "
        f"is starved. {caught}"
    )


main()
