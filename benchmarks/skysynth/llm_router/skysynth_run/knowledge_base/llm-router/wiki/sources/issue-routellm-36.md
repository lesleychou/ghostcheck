---
kind: issue
id: issue-routellm-36
domain: llm-router
tags: [calibration, benchmark-integrity, cost, model-selection]
url: https://github.com/lm-sys/RouteLLM/issues/36
repo: lm-sys/RouteLLM
number: 36
failure: a calibrated threshold names a strong model percentage that only holds on the calibration distribution, not on the user's traffic
---

# Threshold value does not guarantee the calibrated strong model percentage

A user asked what `threshold=0.4066` for the bert router means and whether the accompanying note about 50 percent strong model calls implies that five of any ten queries go to the strong model. The maintainer answered that the number is the quantile of the router win rate distribution over the Chatbot Arena calibration set, so 50 percent of those queries routed strong, and that the realized percentage on other inputs is larger or smaller depending on how similar they are to the arena data. The repository computes it exactly that way, as `thresholds_df[router].quantile(q=1 - strong_model_pct)`, with no feedback from live traffic. A router built from scratch must decide whether its cost knob is a static score cutoff or a closed loop on the observed strong call rate, because only the second holds a budget under distribution shift. This is the cost control axis resting on the calibration knob.
