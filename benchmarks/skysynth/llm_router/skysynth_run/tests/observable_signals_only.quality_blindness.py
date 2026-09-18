"""observable_signals_only.quality_blindness

THE PROPERTY (cards/properties.json). From a fresh router instance, the router's decision stream
is a function of the observable request fields, `now_ms` and the fleet view ALONE. `req.quality`
is the harness's own answer key -- the measured per-prompt per-model ground truth it grades with,
which no deployed router has. Rewriting it, and nothing else, must change nothing the router does.

THE PROBE. The same fixture trace is replayed three ways, each through a FRESH candidate instance:

  ORIGINAL   the rows verbatim;
  PERMUTED   each row's `quality` dict with its VALUES shuffled among the 12 model keys under a
             fixed seed (random.Random(7)); keys, ordering and every other field identical;
  STRIPPED   each row's `quality` set to {} -- the Request dataclass defaults it, and the harness
             then books q=1.0 for every completion.

NON-VACUITY, and the one place this test departs from the letter of the probe sketch. The sketch
asks that the permutation move the per-row argmax on >= 90% of ROWS. That bar is not reachable on
this data and never was: 544 of tenant A's 2899 train rows and 896 of tenant B's 1940 carry a
CONSTANT quality vector (every model 0.0, or every model 1.0), and no permutation of a constant
vector can move anything. The requirement is therefore asserted where it has meaning -- on the
rows a permutation can move at all -- and backed by a floor on how many of those there are:

    (a) >= 90% of the NON-CONSTANT rows have a different argmax after the permutation
        (the permutation is rejection-resampled under the same seeded RNG until it moves the
        argmax, so this is ~100% in practice, and it is still exactly a permutation of the
        row's own values);
    (b) non-constant rows are >= 40% of the fixture (measured: 81.5% of tenant A's 400 rows,
        52.7% of tenant B's 300).

Together those make the PERMUTED leg a real question: an oracle router reading `req.quality`
demonstrably decides differently on a large majority of the trace.

THE ORACLE. Three independent harness-side observables, all three required, and every one of them
read from the harness's own books or from the candidate's own public return values -- never from
the candidate's source, counters or state:

  (a) the three decision logs are equal element for element;
  (b) the three books are equal after deleting ONLY the quality-derived keys (`mean_quality`,
      `quality_floor_misses`, `tenants[*].mean_quality`) -- so `total_cost_usd`,
      `cost_by_class_usd`, `slo_violations`, `shed`, `completed`, `decides`, `p95_latency_ms`,
      `prefix_cache_hit_token_fraction`, `leading_indicators` and every other `tenants[*]` count
      must be identical;
  (c) `violation_count == 0` on all three, which additionally catches a router that reads
      `req.quality` unguarded and raises a typed `router_exception` on the STRIPPED trace.

The three traces are written into three scratch directories under the SAME basename, because the
harness reports `trace: basename(path)` in its books and a differing filename would be a false
difference.
"""

import copy
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support as S

SEED = 7
MIN_MOVED_FRACTION_OF_NONCONSTANT = 0.90
MIN_NONCONSTANT_FRACTION = 0.40
RESHUFFLE_TRIES = 64

# Deleted before the books are compared, and nothing else: these are the only fields the harness
# derives from the answer key.
QUALITY_KEYS = ("mean_quality", "quality_floor_misses")
TENANT_QUALITY_KEYS = ("mean_quality",)


def argmax(quality):
    """Deterministic argmax over a quality dict: highest value, name as the tie-break."""
    return max(quality, key=lambda model: (quality[model], model))


def permute_quality(records):
    """Each row's quality values shuffled among its own keys under random.Random(7).

    Rejection-resampled: if a shuffle leaves the argmax where it was and the row COULD move
    (its values are not all equal), reshuffle, up to RESHUFFLE_TRIES times, from the same seeded
    stream. The result is still a permutation of the row's own values and is fully deterministic.
    """
    rnd = random.Random(SEED)
    out, moved, nonconstant = [], 0, 0
    for rec in records:
        rec = copy.deepcopy(rec)
        quality = rec["quality"]
        keys = sorted(quality)
        values = [quality[k] for k in keys]
        can_move = len(set(values)) > 1
        nonconstant += 1 if can_move else 0
        before = argmax(quality)
        shuffled = dict(quality)
        for _ in range(RESHUFFLE_TRIES):
            rnd.shuffle(values)
            shuffled = dict(zip(keys, values))
            if not can_move or argmax(shuffled) != before:
                break
        if argmax(shuffled) != before:
            moved += 1
        rec["quality"] = {k: shuffled[k] for k in quality}  # original key order, new values
        out.append(rec)
    return out, moved, nonconstant


def strip_quality(records):
    out = []
    for rec in records:
        rec = copy.deepcopy(rec)
        rec["quality"] = {}
        out.append(rec)
    return out


def books_without_quality(books):
    books = copy.deepcopy(books)
    for key in QUALITY_KEYS:
        books.pop(key, None)
    for tenant_book in books.get("tenants", {}).values():
        for key in TENANT_QUALITY_KEYS:
            tenant_book.pop(key, None)
    return books


def log_difference(left, right):
    for i, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return "decision %d of %d: %r != %r" % (i, min(len(left), len(right)), a, b)
    if len(left) != len(right):
        return "decision stream lengths differ: %d != %d" % (len(left), len(right))
    return None


def run():
    classes = S.candidate_classes()
    work = S.scratch("quality-blindness-")
    try:
        for tenant in S.TENANTS:
            records = S.rows(S.FIXTURE[tenant])
            permuted, moved, nonconstant = permute_quality(records)

            if nonconstant < MIN_NONCONSTANT_FRACTION * len(records):
                S.fail(
                    "tenant %s: only %d of %d fixture rows have a non-constant quality vector "
                    "(need >= %.0f%%); the permutation leg could not be meaningful"
                    % (tenant, nonconstant, len(records), 100 * MIN_NONCONSTANT_FRACTION)
                )
            if moved < MIN_MOVED_FRACTION_OF_NONCONSTANT * nonconstant:
                S.fail(
                    "tenant %s: the seeded permutation moved the argmax on only %d of the %d "
                    "non-constant rows (need >= %.0f%%); a quality-reading router would barely "
                    "notice, so the probe would prove nothing"
                    % (tenant, moved, nonconstant, 100 * MIN_MOVED_FRACTION_OF_NONCONSTANT)
                )

            variants = (
                ("original", records),
                ("permuted", permuted),
                ("stripped", strip_quality(records)),
            )
            results = {}
            for name, rows_out in variants:
                # same basename in three directories: `trace` in the books must not differ
                path = S.write_rows(os.path.join(work, tenant, name, "trace.jsonl"), rows_out)
                results[name] = S.replay_recorded(path, tenant, classes)

            for name, (books, _log) in results.items():
                if books["violation_count"] != 0:
                    S.fail(
                        "tenant %s, %s trace: the router took %d typed violation(s) %s -- a "
                        "router that reads req.quality unguarded raises router_exception here"
                        % (tenant, name, books["violation_count"], books["violation_kinds"])
                    )

            base_books, base_log = results["original"]
            for name in ("permuted", "stripped"):
                books, log = results[name]
                diff = log_difference(base_log, log)
                if diff:
                    S.fail(
                        "tenant %s: the decision stream changed when ONLY the ground-truth "
                        "quality changed (original vs %s) -- %s. The router is reading the "
                        "harness's answer key, which no deployed router has."
                        % (tenant, name, diff)
                    )
                diff = S.first_difference(
                    books_without_quality(base_books), books_without_quality(books)
                )
                if diff:
                    S.fail(
                        "tenant %s: a non-quality harness book changed between the original and "
                        "the %s trace -- %s. Cost, dispatches, throttles, latency and the "
                        "leading indicators cannot depend on the answer key."
                        % (tenant, name, diff)
                    )

            S.ok(
                "quality_blindness tenant %s: %d rows, identical decision stream (%d decisions) "
                "and identical non-quality books across original / permuted / stripped; the "
                "seeded permutation moved the argmax on %d of %d non-constant rows"
                % (tenant, len(records), len(base_log), moved, nonconstant)
            )
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(S.main(run))
