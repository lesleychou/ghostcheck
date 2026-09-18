"""Every dispatch carries a record of where the request went and why, and the record has to
survive a check against the fleet's own tables. A reason nobody checks is decoration.
Mutant: MisreportedReasonMutant, which buys the dearest eligible model and files it as the
cheapest."""
import scenarios as S
from audit import audit_reasons
from mutants import MisreportedReasonMutant
from routers import ReferenceRouter
from sim import replay


def main():
    reqs = S.trace(n=20, every_ms=250, deadline_ms=20000)
    gt = S.gt_for(reqs)
    fl = S.fleet()

    run = replay(fl, reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    assert len(run.reason_log) == len(run.dispatch_log)
    complaints = audit_reasons(run, fl, reqs)
    assert not complaints, complaints

    fl2 = S.fleet()
    bad = replay(fl2, reqs, gt, MisreportedReasonMutant())
    bad_complaints = audit_reasons(bad, fl2, reqs)
    assert bad_complaints, "a dispatch record that contradicts the price table went unnoticed"
    print(f"OK test_decision_record: reference clean, mutant caught {len(bad_complaints)} times. "
          f"First: {bad_complaints[0]}")


main()
