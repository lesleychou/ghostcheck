"""An announced outage is better evidence than a failure count. Dispatching into one past the
retry grace does not slow the request down, it loses it.
Mutant: OutageBlindMutant, which reads headroom but not the outage window."""
import scenarios as S
from mutants import OutageBlindMutant
from routers import ReferenceRouter
from sim import Violation, replay

OUT = {"prime": [(0, 60_000)], "courier": [(0, 60_000)]}


def main():
    reqs = S.trace(n=12, every_ms=500, deadline_ms=20000)
    gt = S.gt_for(reqs)

    run = replay(S.fleet(outages=OUT), reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    assert all(e.status == "completed" for e in run.entries.values())
    assert all(p == "value" for _r, p, _m in run.dispatch_log), run.dispatch_log[:5]

    caught = ""
    try:
        replay(S.fleet(outages=OUT), reqs, gt, OutageBlindMutant())
    except Violation as err:
        caught = str(err)
    assert "announced outage" in caught, "dispatching into an announced outage went unnoticed"
    print("OK test_outage_grace:", caught)


main()
