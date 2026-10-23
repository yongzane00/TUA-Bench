# H7 "Time budget" (2400 s, clock on every update): findings

Runs (40 tasks × 5 attempts, 200/200 trials each):
- qwen3.8: `qwen38-flash-next/harness7-time2400-attempt5/2026-10-08__15-37-09` vs H0 `harness0-attempt5/2026-09-23__14-45-40`
- Qwen3.6: `qwen36-35b-a3b/harness7-time2400-attempt5/2026-10-08__15-36-41` vs H0 `harness0-attempt5/2026-10-02__21-45-56`
  (`2026-10-08__15-32-36` next to it is an empty start with no trials; ignore it)

H7 = stock terminus-2, plus one sentence in the task ("You have a time budget of 2400 seconds…") and a meter line
at the top of every terminal update, e.g. `[Time 1000 of 2400 s, 1400 s left | last reply 41 s at 38 tok/s | about
17 turns fit]` (`terminus_2_harness7.py`, `budget_meter.py`).

## Score and cost

| | qwen3.8 H0 | qwen3.8 H7 | Qwen3.6 H0 | Qwen3.6 H7 |
|---|---|---|---|---|
| Score (harbor Mean, 95% CI) | 0.445 (0.314–0.575) | **0.539 (0.414–0.664)** | 0.197 (0.108–0.300) | 0.227 (0.131–0.334) |
| Paired difference vs H0 | | **+0.094 (+0.040 to +0.151), P(≤0) 0.00** | | +0.030 (−0.013 to +0.074), P(≤0) 0.08 |
| Paired difference vs H6 (40-turn counter) | | +0.062 (+0.007 to +0.121), P 0.014 | | +0.053 (+0.006 to +0.108), P 0.014 |
| Leak-adjusted | 0.365 | 0.499 | 0.187 | 0.222 |
| Reward = 1 / pass@5 | 42.0% / 57.5% | 49.5% / 70.0% | 15.5% / 35.0% | 18.0% / 35.0% |
| Cost / trial (prefix-caching proxy) | $0.0110 | $0.0116 | $0.0937 | $0.0939 |
| Timeouts (2400 s) | 64 | **35** | 54 | 57 |
| Outcomes solved / wrong / timeout | 81 / 55 / 64 | 98 / 67 / 35 | 30 / 116 / 54 | 35 / 107 / 57 (+1 tmux error) |
| Server speed | 13.5 tok/s | 16.4 tok/s | 178 tok/s | 164 tok/s |

**qwen3.8: the first harness gain in this project that clears the noise.** H7 beats H0 by 0.094, six times the
0.016 difference between two identical runs, and every attempt column but the first is above H0's best attempt.
It costs nothing extra.

The server was faster than during H0 (16.4 vs 13.5 tok/s), and a faster server alone lowers timeouts. But H6 ran at
the same speed (16.9 tok/s) and H7 still beats it by 0.062 (CI clears 0). H6 showed a turn counter. H7 shows the
clock. So most of the gain is the clock, not the server.

**Qwen3.6: inside the noise, leaning positive** (P 0.08), at the same cost and the same number of timeouts.

## qwen3.8: how the clock helps: timeouts turn into finishes

| | H0 | H7 |
|---|---|---|
| Trials that finish (not timed out) | 136 | 165 |
| ... of which finish after 1800 s, in the last 10 min | 4 | **34** (mean reward 0.50) |
| Timeouts | 64 | 35 |
| Mean reward of finished trials | 0.632 | 0.636 |

Without a clock, qwen3.8 keeps working until harbor kills it at 2400 s and almost never finishes late. With the
clock, 30 more trials stop and hand in their work in the last 10 minutes, and half of that work scores (34 × 0.50
≈ 17 reward points over 200 trials ≈ +0.085, most of the +0.094). Finished trials score as well as before (0.636
vs 0.632), so it does not rush good work. Timeouts fall most on 094 (5 → 0), 088 (5 → 1), 059 (5 → 1), 052, 089
and 033 (5 → 2).

Did the model know? Yes, increasingly as time ran down:

| Time left on the meter | 1800–2400 s | 1200–1800 s | 600–1200 s | 300–600 s | 0–300 s |
|---|---|---|---|---|---|
| qwen3.8 replies that talk about time | 2.4% | 13.4% | 35.4% | 59.2% | 65.6% |
| Qwen3.6 replies that talk about time | 0.0% | 0.2% | 0.6% | 2.8% | 27.9% |
| qwen3.8 "done" claims | 177 | 54 | 47 | 26 | 40 |

- 80 of 200 qwen3.8 trials talk about the clock (H0: 11), first at a median of 1,570 s left. It plans with it:
  "Time budget: 1265s left, ~9 turns. Be efficient. Let me write one script that does everything" (059).
  "Budget: ~2100s left, ~35 turns. Turns are limited! … fewer, larger commands" (007).
  "785s left, ~6 turns. Do it in one turn: write script, run, render PNG, verify… Then complete" (009).
- It uses the "turns fit" forecast and its own reply speed: "my last reply took 283s? … ~13 turns fit, so I must be
  efficient" (016).
- The clock is the right budget for qwen3.8. H6 showed turns, the model planned with them, and 38 of 56 budget-aware
  trials still timed out. In H7, 33 of the 35 timeouts did talk about the clock. Those are trials where even a
  planned finish did not fit: 003, 005 and 007 time out in every run of every harness.

## Qwen3.6: reads the clock only at the end

- 55 of 200 trials talk about time, but the first mention comes at a median of turn 78 with **254 s left**
  (qwen3.8: 1,570 s). Typical: "I've tried every possible approach… Given that I have about 100 seconds left and I
  can't seem to recover the terminal" (007); "With only 252 seconds left in the budget, I need to be efficient.
  Plan: Wait for the script to finish" (038).
- 45 of the 57 timeouts mention the clock, mostly in a stuck terminal or a script that does not return. The pattern
  is the same as with H6's turn counter: it notices the budget only when it is already stuck, and too late to change
  course.
- It does not slow down or batch more: replies stay ~350–400 output tokens and ~2 commands at every time-left
  level. Qwen3.6 takes ~50 turns of a few seconds each, so a time budget gives it many chances to react but it does
  not use them.

## Harness notes

- **The harness's own stop never fired** (0 of 400 trials). The budget is 2400 s and harbor's agent limit is also
  2400 s, measured from slightly earlier, so harbor always ends the trial first. Every H7 "timeout" is harbor's
  `AgentTimeoutError`, exactly as in H0. In 24 of qwen3.8's 35 timeouts the last meter the model saw already said
  "about 0 turns fit". For budgets below 2400 s (e.g. `time1200`) the harness stop will be the one that fires.
- The meter is shown after each reply. A single qwen3.8 reply can take 100–460 s, so the model can only react at
  turn boundaries, and its forecast is coarse near the end.
- One Qwen3.6 trial (007) ended with a `RuntimeError` from tmux ("failed to send non-blocking keys") after 109
  turns in a frozen Slicer terminal. It is an environment failure, not the meter. It scored 0 and is counted.

## Per-task movers (qwen3.8)

Up: 054 (0 → 3 solved), 012, 052, 059, 100 (+2 each). 054 and 059 are the tasks where H0 is the low outlier among all
qwen3.8 runs (H6 also gained on them), so part of this is H0's bad luck. 052, 100 and 012 gained by at most 1 in
H6. They are long tasks that time out in H0 (052 5 of 5, 100 4 of 5). Down: 016 (1 → 0), 030 (2 → 1), 119 (5 → 4),
all within normal swings.

## Bottom line

Showing qwen3.8 the clock that actually ends its trials raises the score from 0.445 to 0.539 at no extra cost. It
converts timeouts into late, pragmatic finishes, half of which score. This is the best qwen3.8 result so far and the
first one outside the noise. Qwen3.6 reads the clock only in its last few minutes and gains little (+0.030, within
noise). The meter helps a model that already plans (qwen3.8 also planned with H6's counter); it does not make a model
plan that otherwise doesn't.

## Next

- H7 at a tighter budget (`harness7-time1200-attempt5`) on qwen3.8, where the harness stop actually fires. That
  shows whether the clock can cut time/cost the way H6's cap did for Qwen3.6 without losing score.
- H9 (clock + spend + turn number) on qwen3.8, to see whether the cost line adds anything on top of the clock.
- Replicate qwen3.8 H7 once before writing it up as the headline result. +0.094 is far outside the run-to-run noise,
  but it is one run on a faster server day.
