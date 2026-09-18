---
kind: issue
id: issue-litellm-39309
domain: llm-router
tags: [rate-limit, quota, admission, metering, correctness]
url: https://github.com/BerriAI/litellm/issues/39309
repo: BerriAI/litellm
number: 39309
failure: a request rejected by the concurrency limit still increments the rpm counter and the increment is never refunded, so rejected work consumes quota it never used
---

# [Bug]: Requests rejected by max_parallel_requests still consume RPM quota

The parallel request limiter increments the rpm counter before it checks the concurrency limit, so a request refused for lack of a concurrency slot never executes yet permanently spends one unit of rpm quota. With an rpm limit of one and a concurrency limit of one, the rejected request pushes the counter to two and the next legitimate request is refused on rate limit even after the concurrency slot is free. A router that reserves quota ahead of admission must make the reservation part of the same atomic decision as every other admission check, and must release it on any rejection path, otherwise rejections themselves become a source of self-inflicted throttling that compounds under load. The axis is admission and overload crossed with rate limit pacing.
