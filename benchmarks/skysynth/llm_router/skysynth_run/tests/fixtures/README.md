# Suite fixtures

`trace_tenantA_fixture.jsonl` and `trace_tenantB_fixture.jsonl` are the FIRST 400 and FIRST 300
rows of `trace_tenantA_train.jsonl` / `trace_tenantB_train.jsonl` respectively, copied byte for
byte with no edit of any kind (`head -n 400` / `head -n 300`).

TRAIN SPLIT ONLY. The val and test splits were not read to build these, and nothing in this suite
ever opens a `*_test.*` trace, matrix or manifest: the test split is sealed for this run.

Why these sizes. Each slice crosses the first `val` outage window (300000-420000 ms on the env
card): tenant A's 400 rows span 0-337826 ms and tenant B's 300 rows span 0-388533 ms, so a replay
of either under `--split val` really does drive the announced-outage path, an empty published
catalogue and the failover off `prime`. Together they are ~0.7 MB, so the suite stays copyable to
`best/tests/` while the full ~20 MB traces stay where they are.

The full train traces are NOT vendored. A test that needs them (the operating-point test) resolves
the trace directory from `$SKYDISCOVER_TRACES_DIR`, falls back to the path recorded in the run's
`synthesis/evaluator/benchmark/traces.json`, and SKIPS cleanly when neither is present, so this
suite runs anywhere.
