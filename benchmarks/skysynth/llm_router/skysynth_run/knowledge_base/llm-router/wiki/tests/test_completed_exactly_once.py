"""Every request ends completed once or refused once. A second dispatch of a request that
already finished is a second bill for one answer.
Mutant: ResubmitAfterCompletionMutant, which re-dispatches on the completion callback."""
import scenarios as S
from mutants import ResubmitAfterCompletionMutant
from routers import ReferenceRouter
from sim import Violation, replay


def main():
    reqs = S.trace(n=14, every_ms=400, deadline_ms=20000)
    gt = S.gt_for(reqs)

    run = replay(S.fleet(), reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    served = [rid for rid, _p, _m in run.dispatch_log]
    assert len(served) == len(set(served)) == len(reqs), served
    assert all(e.status == "completed" for e in run.entries.values())

    caught = ""
    try:
        replay(S.fleet(), reqs, gt, ResubmitAfterCompletionMutant())
    except Violation as err:
        caught = str(err)
    assert "after completing" in caught, "a request was served twice and nobody noticed"
    print("OK test_completed_exactly_once:", caught)


main()
