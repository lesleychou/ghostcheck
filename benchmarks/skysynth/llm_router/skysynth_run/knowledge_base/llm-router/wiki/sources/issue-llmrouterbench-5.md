---
kind: issue
id: issue-llmrouterbench-5
domain: llm-router
tags: [benchmark-integrity, reproducibility, validation, cost]
url: https://github.com/ynulihao/LLMRouterBench/issues/5
repo: ynulihao/LLMRouterBench
number: 5
failure: the released per-instance score and cost records carried no stated license, so it was unclear whether routers could be trained or evaluated on them
---

# License clarification for repository code versus the released benchmark records

The released `bench-release.tar.gz` holds exactly the per-instance records routing research needs, with prompt, score, token counts and cost per model and per query, but the README license badge linked to a `LICENSE` file absent from the repository, the GitHub API detected no license, and the Hugging Face dataset card carried none either. The only MIT statement was inside the `baselines/AvengersPro` subdirectory, which plausibly covers that baseline alone, leaving the reporter unable to tell whether the score and cost tables could be used to train or evaluate routing models or to publish derived aggregate statistics. The maintainer confirmed MIT is intended for the top-level source and that the benchmark data may be used for non-commercial academic research and reproduction of results, and committed to adding license files and a dataset card. A router built from scratch must decide whether the cost and score table it fits its policy on can travel with that policy, because the trained router embeds the prices and quality labels it was fit to. This touches cost control.
