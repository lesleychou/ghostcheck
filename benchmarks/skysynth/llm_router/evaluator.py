# benchmarks/skysynth/llm_router/evaluator.py
"""Workload grammar for the SkySynth llm-router benchmark.

READ, NEVER IMPORTED. GhostCheck' Agent 1 reads this file's source to infer the
workload schema (schema_infer.py, param_extractor.py). The real scoring lives in
SkySynth's evaluator/ package, which we import read-only at replay time.

Every parameter below is a plain number consumed by run_workload.py. Defaults are
neutral: the empty workload {} replays SkySynth's frozen val trace unchanged.

DECLARED ranges come from SkySynth's own published files (tenantA/B.card.yaml,
env_card.yaml). Values inside them describe the deployment they specified; values
outside are robustness probes. envelope.py tags which is which.
"""

# --- which traffic -----------------------------------------------------------
TENANT = "merged"          # "A" (interactive, 2.5s TTFT) | "B" (batch, 10min) | "merged"
SPLIT = "val"              # "val" only. task.md: the test split is out of bounds.
N_REQUESTS = 1665          # val rows: A=972, B=693, merged=1665

# --- arrival shape -----------------------------------------------------------
ARRIVAL_SCALE = 1.0        # <1 compresses the span = higher request rate. Declared 0.125-4.0
BURST_FACTOR = 1.0         # >1 concentrates arrivals at the front. Declared 1.0-8.0
                           # (tenantA.card.yaml: peak_rps_10s 7.7 vs mean_rps 0.94)

# --- request size ------------------------------------------------------------
PROMPT_TOKEN_SCALE = 1.0   # FROZEN at 1.0: token counts are ground-truth measurements
OUTPUT_TOKEN_SCALE = 1.0   # bound to committed prompt ids; rescaling is a robustness probe

# --- service-level terms -----------------------------------------------------
TTFT_MS = 2500             # tenant A's SLO, FROZEN in tenantA.card.yaml
DEADLINE_MS = 600000       # tenant B's deadline, FROZEN in tenantB.card.yaml
EQUIV_CLASS_WIDTH = 12     # the full declared fleet; narrowing is a robustness probe
DOWNGRADE_OK = True        # may the router substitute within equiv_class

# --- the fleet (env_card.yaml is FROZEN: 1.0 is the only declared value) ------
RATE_LIMIT_SCALE = 1.0     # scales every provider's rpm, tpm, concurrency
ERROR_RATE_SCALE = 1.0     # scales every provider's 429/503 rate

# --- outages (env_card.yaml declares exactly two val windows) ----------------
OUTAGE_COUNT = 2           # Declared 0-2
OUTAGE_DURATION_SCALE = 1.0
OUTAGE_SHIFT_MS = 0
