"""A request may be refused only when the fleet really could not serve it. Refusing the hard
or the expensive ones while a legal substitute has room is the cheapest way to lift an average.
Mutant: EagerShedMutant, which refuses as soon as the named model is busy."""
import scenarios as S
from mutants import EagerShedMutant
from routers import ReferenceRouter
from sim import Violation, replay


def main():
    reqs = S.trace(n=30, every_ms=200, deadline_ms=20000)
    gt = S.gt_for(reqs)

    run = replay(S.fleet(), reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    assert all(e.status == "completed" for e in run.entries.values())

    caught = ""
    try:
        bad = replay(S.fleet(), reqs, gt, EagerShedMutant())
        caught = "" if not bad.violations else str(bad.violations)
    except Violation as err:
        caught = str(err)
    assert "refused while the fleet had room" in caught, "a free refusal went unnoticed"
    print("OK test_no_free_shed:", caught)


main()
