"""A served model must be inside the request's declared equivalence class.
Mutant: OutsideEquivClassMutant, which serves a cheaper model nobody allowed."""
import scenarios as S
from mutants import OutsideEquivClassMutant
from routers import ReferenceRouter
from sim import Violation, replay


def main():
    reqs = S.trace(n=12)
    gt = S.gt_for(reqs)

    run = replay(S.fleet(), reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    assert all(e.status == "completed" for e in run.entries.values())
    assert all(m in S.MODELS for _r, _p, m in run.dispatch_log)

    caught = ""
    try:
        replay(S.fleet(), reqs, gt, OutsideEquivClassMutant())
    except Violation as err:
        caught = str(err)
    assert "equivalence class" in caught, "substitution outside the equivalence class went unnoticed"
    print("OK test_equiv_class:", caught)


main()
