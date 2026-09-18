#!/usr/bin/env bash
# The suite entry point (workflow/references/verification.md):
#
#   bash test.sh              run every test
#   bash test.sh <file>...    run only the named tests
#
# Exit 0 iff every test passed. The harness sets SKYDISCOVER_IMPL to the implementation under
# test (a directory here: the delivered routers plus routers.json) and SKYDISCOVER_INTERFACE to
# the interface directory, and runs this from the suite directory.
#
# A test is a top-level `*.py` here, named after the property it checks. `_*.py` are shared
# plumbing, not tests. `vendor/` (the harness, copied from the task) and `fixtures/` (train-split
# trace slices) are data the suite carries so it stays self-contained when it is copied to
# `best/tests/`.
#
# Written for bash 3.2 (the macOS system bash): no `mapfile`, no empty-array expansion under -u.

set -uo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"

if [ "$#" -gt 0 ]; then
  TESTS="$*"
else
  TESTS=""
  for f in *.py; do
    case "$f" in
      _*) continue ;;
      "*.py") continue ;;
    esac
    TESTS="$TESTS $f"
  done
fi

if [ -z "${TESTS// /}" ]; then
  echo "test.sh: no tests to run" >&2
  exit 1
fi

# The suite never reaches out of itself; PYTHONPATH is set so the vendored harness package
# (`evaluator.*`) and the implementation under test both import, from here and from any
# subprocess a test launches.
export PYTHONPATH="$PWD/vendor:${SKYDISCOVER_IMPL:-}${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1

status=0
for t in $TESTS; do
  if [ ! -f "$t" ]; then
    echo "FAIL $t (no such test in $PWD)" >&2
    status=1
    continue
  fi
  if "$PY" "$t"; then
    echo "PASS $t"
  else
    echo "FAIL $t" >&2
    status=1
  fi
done

exit "$status"
