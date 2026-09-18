"""A fitted artifact may only know the prompts of the training split. An artifact that carries
a held-out prompt has answered the question it was going to be asked.
Mutant: fit_best_model_leaky, the same fit with the split boundary removed."""
import scenarios as S
from audit import artifact_leaks, fit_best_model, fit_best_model_leaky


def main():
    reqs = S.trace(n=40)
    gt = S.gt_for(reqs)
    rows = [(p, m, s) for (p, m), s in sorted(gt.items())]
    ids = sorted({r.prompt_id for r in reqs})
    train, held_out = ids[:28], ids[28:]

    honest = fit_best_model(rows, train)
    assert honest, "the honest fit learned nothing, so the test proves nothing"
    assert set(honest) <= set(train)
    assert artifact_leaks(honest, held_out) == [], artifact_leaks(honest, held_out)

    leaky = fit_best_model_leaky(rows, train)
    leaks = artifact_leaks(leaky, held_out)
    assert leaks, "the leaky fit did not leak, so the test proves nothing"
    assert len(leaks) == len(held_out)
    print(f"OK test_train_split_isolation: the honest artifact holds {len(honest)} training "
          f"prompts and none of the {len(held_out)} held out; the leaky one holds all of them")


main()
