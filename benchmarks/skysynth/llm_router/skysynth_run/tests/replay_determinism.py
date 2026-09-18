"""replay_determinism

THE PROPERTY (cards/properties.json). Two replays of the same trace, with the same env card and
the same split, each from a FRESH router instance, emit the identical decision sequence and the
identical harness books to full precision -- including across processes whose string-hash
randomisation differs. If a policy does not repeat itself, no measured difference between two
policies means anything: the difference could be the dice.

THE PROBE, three runs per tenant on the vendored fixture trace at the scored outage schedule
(`--split val`):

  runs 1 and 2   IN-PROCESS, from two freshly constructed candidate instances, with a test-side
                 recording proxy capturing each decision as it is returned;
  runs 3 and 4   SUBPROCESS, `python3 evaluator/benchmark/replay_tenants.py <trace> <class>
                 --env <card> --split val --json`, launched twice with PYTHONHASHSEED=0 and
                 PYTHONHASHSEED=12345 in the child environment.

The hash-seed leg is the one the scored replay can never run, and it is what catches the defect
class the card names: iteration over an UNORDERED set of provider or model names, and unseeded
randomness in placement -- both of which ship in the reference systems (litellm
simple_shuffle.py:70, portkey handlerUtils.ts:704). The harness itself is seeded (`sim_seed: 11`
on the env card) and iterates its own dicts in insertion order, so any difference between two runs
is the router's.

THE ORACLE, from the candidate's public return values and the harness's own books only:
  * decision_log(run 1) == decision_log(run 2), element for element;
  * books(run 1) == books(run 2) field for field, including `mean_quality`, `total_cost_usd`,
    `slo_violations`, `p95_latency_ms`, `decides` and every `leading_indicators` counter;
  * the two subprocess JSON documents are byte-identical, with nothing removed.

Nothing here reads the candidate's source, its counters or its state, and nothing here asserts
WHICH decisions a correct router makes -- only that it makes the same ones twice. A router that
wants randomness may have it; the seed has to be part of its configuration, not of the wall clock
or of the interpreter's hash seed.
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support as S

HASH_SEEDS = ("0", "12345")
REPLAY_CLI = os.path.join("evaluator", "benchmark", "replay_tenants.py")
SUBPROCESS_TIMEOUT_S = 120


def dotted(cls):
    """`<module>.<Class>` for the CLI, taken from the class object the suite already resolved,
    so it works whether the directory shipped routers.json or a TENANT attribute."""
    return "%s.%s" % (cls.__module__, cls.__qualname__)


def subprocess_replay(trace, class_path, hash_seed):
    """One replay in a child interpreter with a named PYTHONHASHSEED. Run from the vendored
    root so `evaluator/benchmark/replay_tenants.py` is exactly the path the harness documents;
    the child sees only the suite's vendor tree and $SKYDISCOVER_IMPL on its path."""
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = hash_seed
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join([S.VENDOR, S.impl_dir()])
    proc = subprocess.run(
        [
            sys.executable,
            REPLAY_CLI,
            trace,
            class_path,
            "--env",
            S.ENV_CARD,
            "--split",
            "val",
            "--json",
        ],
        cwd=S.VENDOR,
        env=env,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT_S,
    )
    if proc.returncode != 0:
        S.fail(
            "the replay CLI exited %d for %s under PYTHONHASHSEED=%s:\n%s"
            % (proc.returncode, class_path, hash_seed, (proc.stderr or proc.stdout)[-1500:])
        )
    return proc.stdout


def run():
    classes = S.candidate_classes()
    for tenant in S.TENANTS:
        trace = S.FIXTURE[tenant]

        books_1, log_1 = S.replay_recorded(trace, tenant, classes)
        books_2, log_2 = S.replay_recorded(trace, tenant, classes)

        # Liveness only, never correctness: this test asserts determinism and nothing else, so
        # a typed violation is left to the test that owns it. An ABORTED replay is different --
        # it stopped early, so the two runs were not the same experiment and comparing their
        # books would mean nothing.
        for run_no, books in ((1, books_1), (2, books_2)):
            if books["aborted"]:
                S.fail(
                    "tenant %s: replay %d did not finish (%s), so there is nothing to compare"
                    % (tenant, run_no, books["aborted"])
                )

        for i, (a, b) in enumerate(zip(log_1, log_2)):
            if a != b:
                S.fail(
                    "tenant %s: two replays of the same trace from two fresh instances diverged "
                    "at decision %d of %d: %r != %r. The router is not reproducible, so no "
                    "measured difference it shows is evidence of anything."
                    % (tenant, i, min(len(log_1), len(log_2)), a, b)
                )
        if len(log_1) != len(log_2):
            S.fail(
                "tenant %s: two replays of the same trace produced %d and %d decisions"
                % (tenant, len(log_1), len(log_2))
            )

        diff = S.first_difference(books_1, books_2)
        if diff:
            S.fail(
                "tenant %s: two replays of the same trace produced different harness books -- %s"
                % (tenant, diff)
            )

        class_path = dotted(classes[tenant])
        out = [subprocess_replay(trace, class_path, seed) for seed in HASH_SEEDS]
        if out[0] != out[1]:
            left, right = json.loads(out[0]), json.loads(out[1])
            diff = S.first_difference(left, right) or "the JSON text differs but the values do not"
            S.fail(
                "tenant %s: %s replayed the same trace differently under PYTHONHASHSEED=%s and "
                "PYTHONHASHSEED=%s -- %s. Something in the router iterates an unordered set of "
                "provider or model names, or draws unseeded randomness."
                % (tenant, class_path, HASH_SEEDS[0], HASH_SEEDS[1], diff)
            )

        S.ok(
            "replay_determinism tenant %s: %d decisions reproduced exactly from a second fresh "
            "instance, identical books, and byte-identical replay output under PYTHONHASHSEED %s"
            % (tenant, len(log_1), " and ".join(HASH_SEEDS))
        )


if __name__ == "__main__":
    raise SystemExit(S.main(run))
