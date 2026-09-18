"""After a target rejects a request it states when it will be ready. Re-attempting that same
target sooner is a decision to ignore it, and on this fleet a burst of early retries is what
turns a rejection into a missed deadline.
Mutant: ImpatientRetryMutant, which re-attempts the rejecting target on the next tick."""
import scenarios as S
from mutants import ImpatientRetryMutant
from routers import ReferenceRouter
from sim import Violation, replay


def main():
    reqs = S.trace(n=24, every_ms=250, deadline_ms=20000)
    gt = S.gt_for(reqs)

    run = replay(S.fleet(), reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    assert run.early_retries == 0, f"the reference retried early {run.early_retries} times"

    early, caught = 0, ""
    try:
        bad = replay(S.fleet(), reqs, gt, ImpatientRetryMutant())
        early = bad.early_retries
    except Violation as err:
        caught, early = str(err), err.run.early_retries
    assert early > 0, "the impatient router never retried early, so the test proves nothing"
    print(f"OK test_retry_after: reference 0 early retries, mutant {early}. {caught}")


main()
