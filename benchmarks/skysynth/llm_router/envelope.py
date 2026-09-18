"""Is this workload inside the deployment SkySynth declared, or outside it?

The split has to survive a hostile reading, because the whole argument rests on it:
an in-envelope witness is a failure on the deployment they SPECIFIED, so "just re-run
SkySynth on your workload" is no answer to it. An out-of-envelope witness is reported
as a degradation curve, never as a failure. Mislabel one and the claim collapses.

So the line is drawn at ONE question: did SkySynth declare this quantity as varying?

Only the ARRIVAL PROCESS did. make_tenant_traces.py generates arrivals from a seeded
random process, and the workload cards publish the peak that process produces
(tenantA.card.yaml: peak_rps_10s 7.7 against mean_rps 0.940, i.e. 8.2x). Re-drawing
that process, up to the concentration they themselves measured, is a different sample
of a declared distribution.

Everything else is FROZEN in their published files, so the declared value is the only
in-envelope value:
  - token counts are ground-truth measurements bound to committed prompt ids
    (data/manifests/), not a distribution we may rescale;
  - SLOs, equiv-class width: fixed per tenant in the cards;
  - fleet capacity, error rates, outage shape: fixed in env_card.yaml, which its own
    header calls "FROZEN at first scored replay".

NOTE on a tempting mistake: tenant A's prompt p50->p99 spans 28 -> 190648 tokens, which
looks like licence for a ~6800x token multiplier. It is not. That is the spread ACROSS
requests already present in the trace; it says nothing about how far a UNIFORM multiplier
on every request may go. Different quantities. Hence (1.0, 1.0) below.

This is deliberately conservative — it moves findings out of the "unanswerable" bucket
and into the weaker "degradation curve" one. That is the right trade: under-claiming is
recoverable, over-claiming that gets challenged is not.
"""

DECLARED_ENVELOPE: dict[str, tuple[float, float]] = {
    # -- the one declared random process: arrivals ----------------------------
    # burst concentration, up to the 8.2x peak-over-mean the cards publish
    "burst_factor": (1.0, 8.0),
    # time compression; 8x faster arrivals is that same peak seen as a rate
    "arrival_scale": (0.125, 4.0),
    # -- everything below is frozen in their published files ------------------
    "prompt_token_scale": (1.0, 1.0),
    "output_token_scale": (1.0, 1.0),
    "ttft_ms": (2500, 2500),            # tenantA.card.yaml slo.ttft_ms
    "deadline_ms": (600000, 600000),    # tenantB.card.yaml slo.latency_ms
    "equiv_class_width": (12, 12),      # the full 12-model fleet
    "rate_limit_scale": (1.0, 1.0),     # env_card.yaml: "FROZEN at first scored replay"
    "error_rate_scale": (1.0, 1.0),
    "outage_count": (0, 2),             # exactly two declared val windows
    "outage_duration_scale": (1.0, 1.0),
    "outage_shift_ms": (0, 0),
}


def classify(w: dict) -> dict:
    outside = []
    for knob, (lo, hi) in DECLARED_ENVELOPE.items():
        if knob not in w:
            continue
        try:
            value = float(w[knob])
        except (TypeError, ValueError):
            continue
        if value < lo or value > hi:
            outside.append(knob)
    return {"in_envelope": not outside, "outside": sorted(outside)}
