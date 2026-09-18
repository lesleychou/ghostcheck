"""A dispatch may only go to a provider that stocks the chosen model.
Mutant: UnstockedTargetMutant, which sends the flagship model to the provider without it."""
import scenarios as S
from mutants import UnstockedTargetMutant
from routers import ReferenceRouter
from sim import Violation, replay


def main():
    reqs = S.trace(n=10)
    gt = S.gt_for(reqs)
    fl = S.fleet()

    run = replay(fl, reqs, gt, ReferenceRouter())
    assert not run.violations, run.violations
    for _rid, provider, model in run.dispatch_log:
        assert fl.providers[provider].stocks(model), (provider, model)

    caught = ""
    try:
        replay(S.fleet(), reqs, gt, UnstockedTargetMutant())
    except Violation as err:
        caught = str(err)
    assert "does not stock" in caught, "a dispatch to a provider without the model went unnoticed"
    print("OK test_placement_legality:", caught)


main()
