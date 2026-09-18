---
kind: issue
id: issue-routellm-22
domain: llm-router
tags: [reproducibility, benchmark-integrity, paper, model-selection]
url: https://github.com/lm-sys/RouteLLM/issues/22
repo: lm-sys/RouteLLM
number: 22
failure: the exact corpus behind the released router checkpoint is not published, so its reported numbers cannot be reproduced
---

# Training data format and source for the released matrix factorization router

A user trying to train a router for another language could not find the dataset behind the published `routellm/mf_gpt4_augmented` checkpoint, and noted that the training script expects records with `idx`, `model_a`, `model_b` and `winner` keys. The maintainer confirmed the GPT-4 augmented router was trained on roughly 60k Chatbot Arena battles plus roughly 110k Nectar battles labeled by a GPT-4 judge, and pointed at two published datasets described as close to, rather than identical with, the training corpus. The consequence is that the shipped checkpoint mixes human pairwise votes with LLM judge labels in a ratio a reimplementation cannot recover. A router built from scratch must decide where its preference labels come from and record that choice with the checkpoint, because human votes and judge votes disagree and the threshold is later calibrated against whichever one was used. This touches model selection and the reproducibility of the policy state.
