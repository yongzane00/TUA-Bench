# qwen3.8 H6 "Turn budget" (40 turns, counter shown): findings

Run: `qwen38-flash-next/harness6-turns40-attempt5/2026-10-07__17-45-47` vs H0 `harness0-attempt5/2026-09-23__14-45-40`
(40 tasks × 5 attempts, 200/200 trials, no infrastructure errors). H6 = stock terminus-2 with `max_turns: 40`, a
budget sentence in the task, and "[Turn N of 40]" on every update. Qwen3.6 results: `qwen36-harness6-findings.md`.

## Score and cost

| | H0 | H6 | Change |
|---|---|---|---|
| Score (harbor Mean, 95% CI) | 0.445 (0.314–0.575) | 0.476 (0.344–0.610) | +0.031 (−0.015 to +0.085), P(≤0) 0.11 |
| Leak-adjusted | 0.365 | 0.426 | |
| Cost / trial (prefix-caching proxy) | $0.0110 | $0.0120 | +9% |
| Agent time / trial (median) | 13.4 min | 13.3 min | |
| Model time / trial (median) | 11.2 min | 9.0 min | server 13.5 → 16.9 tok/s |
| Turns (median / mean) | 11 / 14.8 | 13 / 16.2 | |
| Timeouts (2400 s) | 64 | 53 | |
| Trials that reached turn 40 | 2 went past 40 | 5 stopped at 40 | |

**Inside the noise, leaning positive.** Two caveats make it weaker than it looks:
- The gain comes mostly from tasks where H0 is the low outlier among all qwen3.8 runs. 054 prostate-label-obj
  (H0 0 solved; H1–H6: 2, 2, 3, 2, 1, 3) and 059 make-summary-slide (H0 0; others 0–3). 021 (3 → 5) is within
  the 3–5 range of the other runs.
- The model server was faster during this run (16.9 vs 13.5 tok/s; H3 and H5 also ran at ~16.7). qwen3.8 is
  timeout-bound, so a faster server alone lowers timeouts: H3 also had 53. The timeout drop 64 → 53 cannot
  be credited to the counter.

The cap itself almost never binds: qwen3.8 rarely takes more than 40 turns (H0: 2 trials of 200). Its limit is
the 2400 s clock, not turns.

## Does the model know its budget? Yes, from early on, unlike Qwen3.6

Every reply was searched for budget language ("turn 16 of 40", "26 left", "limited turns", "turn budget", ...),
excluding back-references such as "from turn 4".

| | qwen3.8 H0 | qwen3.8 H6 | Qwen3.6 H6 |
|---|---|---|---|
| Trials that show budget awareness | 12 / 200 | **56 / 200** | 14 / 200 |
| Median turn of the first mention | 21 | **12** | 38 |
| Replies mentioning any turn number, turns 11–30 | 0.9% | **12%** | 0.7% |

1. **It plans with the counter.** Examples:
   - 038, turn 9: "UI date pickers consume many turns. I have 40 turns, used 9. Let me attempt URL approach
     first (1 turn), inspect (1 turn)." It solved the task.
   - 003, turn 19: "I should keep an eye on turn budget: 40 turns, at turn 19 now... Turn ~20-22: analyze image →
     room rectangles. Turn ~23: write OSM builder ruby script. Turn ~24: translate + run simulation."
   - 003 and 005: "Given limited turns, I should be pragmatic: build a reasonable model... partial credit likely".
     It lowers its ambition on hard tasks.
2. **But it watches the wrong budget.** Of the 56 budget-aware trials, **38 timed out** at a median of 25 turns,
   with about 15 of its 40 turns still unused. Of the 53 timeouts in the run, 38 are in these trials.
   Budget awareness concentrates on the hardest, slowest tasks (003, 005, 007, 033, 088, 100, 109). There the
   turn counter is misleading, because the 2400 s clock runs out first and the model never sees the clock.
3. **Awareness is not linked to doing better.** On the 20 tasks with both budget-aware and other attempts, the
   aware attempts score 0.46 vs 0.51.
4. **At the cap it wraps up cleanly.** Of the 5 trials that reached turn 40, 4 claimed done on the last reply and
   3 of those were right (034, 038, 042): "This is the last turn, so I'll finalize with task_complete true"
   (038). Qwen3.6's last-turn claims were mostly wrong (mean reward 0.13).

## Bottom line

On qwen3.8 the 40-turn cap is free (it rarely binds) and the score is within noise of H0 (+0.031, P(≤0) 0.11),
with a faster server as a likely contributor. The more interesting result is behavioural. qwen3.8 does
read and plan with a budget it is shown, whereas Qwen3.6 does not. But it is shown turns while what runs out
is time. That is the direct case for H7 (time budget with a clock): show qwen3.8 the budget that actually ends
its trials.

## Next

- H7 `harness7-time2400-attempt5` on qwen3.8: does showing the clock turn the 38 "aware but timed out" trials
  into earlier, pragmatic finishes?
- Compare server tok/s when reading H7–H9: the meter's pace forecast depends on it, and so do timeouts.
