"""A request parked in a wait loop is never completed, never refused and never counted, which
makes waiting the cheapest way to hide a request the policy cannot serve. A progress budget
turns it back into a loss.
Mutant: StallMutant, which always waits."""
import scenarios as S
from mutants import StallMutant
from routers import ReferenceRouter
from sim import MAX_DECISIONS, Violation, replay


def main():
    reqs = S.trace(n=10, every_ms=500, deadline_ms=20000)
    gt = S.gt_for(reqs)

    run = replay(S.fleet(), reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    worst = max(e.decisions for e in run.entries.values())
    assert worst < MAX_DECISIONS, f"the reference needed {worst} decisions"

    caught = ""
    try:
        replay(S.fleet(), reqs, gt, StallMutant())
    except Violation as err:
        caught = str(err)
        assert all(e.status != "completed" for e in err.run.entries.values())
    assert "decision budget" in caught, "an endless wait was never noticed"
    print(f"OK test_decision_budget: the reference needs at most {worst} decisions; {caught}")


main()
