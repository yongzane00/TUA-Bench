# Qwen3.6-35B-A3B: H2 (reasoning kept) vs H0 — findings

Runs: `qwen36-35b-a3b/harness0-attempt5/2026-10-02__21-45-56` vs `qwen36-35b-a3b/harness2-attempt5/2026-10-03__23-40-43`, 40 tasks × 5 attempts each.

| | H0 | H2 |
|---|---|---|
| Score (harbor Mean) | 0.197 (0.107–0.301) | 0.208 (0.115–0.307) |
| Paired difference | | +0.011 (−0.044 to +0.063), P(≤0) = 0.35 |
| Reward = 1 | 15.5% | 16.5% |
| Tasks up / down / same | | 8 / 6 / 26 |
| Timeouts | 54 | 67 |
| Trials that summarized | 4 | 4 (one 85 times) |
| Cost / trial (with caching) | $0.0927 | $0.0958 |

- **No measurable accuracy gain.** Keeping Qwen3.6's reasoning in history (the mode its model card recommends for agents) changes accuracy by +1 point, inside run-to-run noise. Only two tasks moved by 2 or more attempts: `099-professor-contact-info` 1 → 4 and `050-mri-png-slices` 5 → 2.
- **More timeouts.** Longer contexts make each turn slower, and 13 more attempts hit the 40-minute cap.
- **Slightly higher cost**, from the reasoning re-sent every turn.
- The failure modes found in H0 (answers saved in a form the grader can't read, working outside the task's own browser) are not addressed by keeping reasoning; they need harness support at completion time (see the cost/accuracy proposals of 2026-10-04).
- Mechanism check: `preserve_thinking: true` was verified to reach the model (turn-2 prompt 89 → 454 tokens in a probe through harbor's chat code).
