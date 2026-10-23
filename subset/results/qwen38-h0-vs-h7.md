# qwen3.8: time budget told (H7) vs not told (H0) — updated 2026-10-21

Model `qwen3.8-flash-next`, 40-task subset × 5 attempts = 200 trials per run. Both arms stop at the same time budget:

- **hidden (H0):** stock terminus-2; the model is told nothing (`harness0-time<B>-attempt5`).
- **shown (H7):** the model is told the budget and sees a clock on every turn (`harness7-time<B>-attempt5`).

Score = harbor Mean (reward averaged over all 200 trials, partial credit included). CIs and paired differences are
bootstraps over the 40 tasks. Plots: `.claude-visuals/qwen38-time-budget-curve.svg` (score vs budget),
`.claude-visuals/qwen38-solved-vs-cost.svg` (solved trials vs total `cost_usd`, one point per run),
`.claude-visuals/qwen38-h0-vs-h7.svg` (each attempt, one circle per run), `.claude-visuals/qwen38-h0-vs-h7-means.svg`.

## Results by budget

| Budget | Arm | Score (95% CI) | Solved | Ran out of time | Tasks solved at least once | `cost_usd` / trial | `cost_usd` total | With prefix caching / trial | With prefix caching, total |
|---|---|---|---|---|---|---|---|---|---|
| 1200 s | hidden | 0.366 (0.242–0.497) | 69 of 200 | 79 of 200 | 20 of 40 | $0.0190 | $3.81 | $0.0077 | $1.54 |
| 1200 s | shown | 0.443 (0.311–0.578) | 81 of 200 | 57 of 200 | 22 of 40 | $0.0183 | $3.67 | $0.0077 | $1.54 |
| 1800 s | hidden | 0.463 (0.333–0.593) | 88 of 200 | 63 of 200 | 24 of 40 | $0.0265 | $5.31 | $0.0096 | $1.91 |
| 1800 s | shown | 0.467 (0.348–0.591) | 87 of 200 | 56 of 200 | 26 of 40 | $0.0263 | $5.26 | $0.0100 | $2.00 |
| 2400 s | hidden | 0.459 (0.325–0.595) | 87 of 200 | 59 of 200 | 22 of 40 | $0.0329 | $6.58 | $0.0117 | $2.35 |
| 2400 s | shown | 0.539 (0.420–0.659) | 99 of 200 | 35 of 200 | 28 of 40 | $0.0316 | $6.32 | $0.0116 | $2.31 |
| 3600 s | hidden | 0.434 (0.311–0.561) | 82 of 200 | 45 of 200 | 24 of 40 | $0.0542 | $10.84 | $0.0163 | $3.26 |
| 3600 s | shown | **0.571** (0.455–0.689) | 104 of 200 | 23 of 200 | 29 of 40 | $0.0454 | $9.09 | $0.0147 | $2.93 |
| 12000 s | hidden | 0.534 (0.412–0.657) | 95 of 200 | 16 of 200 | 27 of 40 | $0.1474 | $29.48 | $0.0337 | $6.73 |

Reference: stock H0 with no budget (ended by harbor's own 2400 s limit, Sep 23) scores 0.445, 84 of 200 solved, at $0.0302
`cost_usd` per trial ($6.04 total; $0.0110 and $2.20 with prefix caching). Totals are over the run's 200 trials.
2400 s is TUA-Bench's official limit.

## Told vs not told

| Budget | Shown − hidden (95% CI) | P(≤ 0) | Hard-stop equivalent (95% CI) |
|---|---|---|---|
| 1200 s | **+0.077** (+0.005 to +0.152) | 0.02 | +0.064 (−0.015 to +0.143), P 0.055 |
| 1800 s | +0.004 (−0.068 to +0.080) | 0.47 | −0.005 (−0.080 to +0.071) |
| 2400 s | **+0.080** (+0.017 to +0.148) | 0.01 | same (already a hard kill) |
| 3600 s | **+0.137** (+0.063 to +0.217) | 0.00 | +0.142 (+0.070 to +0.221) |

Other comparisons:

| Comparison | Difference (95% CI) | P(≤ 0) |
|---|---|---|
| gap at 3600 s − gap at 1800 s | **+0.134** (+0.050 to +0.218) | 0.001 |
| shown 3600 s − shown 1800 s | **+0.104** (+0.051 to +0.156) | 0.00 |
| shown 3600 s − shown 2400 s | +0.033 (−0.010 to +0.077) | 0.07 |
| hidden 1800 s − hidden 1200 s | **+0.097** (+0.037 to +0.162) | 0.00 |
| hidden 3600 s − hidden 2400 s | −0.025 (−0.070 to +0.020) | 0.84 |
| hidden 12000 s − hidden 3600 s | **+0.100** (+0.031 to +0.171) | 0.00 |
| shown 3600 s − hidden 12000 s | +0.037 (−0.041 to +0.115) | 0.17 |

Two identical runs differ by about 0.016, so differences inside about ±0.02 are noise; the CIs above are the real test.

## What we can conclude

1. **Telling the model its time budget helps at every budget except 1800 s, and helps more as the budget loosens:**
   +0.077 at 1200 s, +0.080 at 2400 s, +0.137 at 3600 s. The 1800 s pair is the exception (see caveats).
2. **How: the clock makes long trials finish.** At 3600 s, of the trials still running after 20 minutes, 76 of 92 shown
   trials declare "done" at some point, against 35 of 80 hidden ones. Of the trials that run past 30 minutes, the hidden arm
   lets 45 of 69 run into the stop; the shown arm lets 23 of 68 run into it, finishes 45 itself, and 21 of those solve.
   Stopped trials almost never score (3 of the 45 hidden ones had any reward).
3. **The model reads the clock.** Shown runs mention time left, the budget or wrapping up in 73–92 of 200 trials, and in
   most turns near the end of the budget (209 of 347 turns in the last quarter at 3600 s). Hidden runs almost never do
   (5–16 of 200 trials).
4. **Without the clock, time helps only slowly.** Hidden gains up to 30 minutes (+0.097 from 1200 to 1800 s), nothing from
   30 to 60 minutes (0.463, 0.459, 0.434), then creeps up: 0.534 at 12000 s (3.3 hours). Of its +0.100 over hidden 3600 s,
   about 0.04 is luck (the hidden model never sees its budget, so the two runs behave identically for the first hour, yet the
   12000 s run was already 0.038 ahead at minute 60) and about 0.06 is real: 10 of the 48 trials still running at 60 minutes
   solved by 3.3 hours (tasks 016, 025, 042, 088, 094, 100). 16 of 200 were still running at 12000 s, none solved.
5. **The clock is the cheap route.** Shown at 3600 s (0.571) is level with hidden at 12000 s (0.534; +0.037, inside the
   noise) at $0.0454 against $0.1474 `cost_usd` per trial ($9.09 against $29.48 for the whole run), with about half the agent time
   per trial.

## Would a faster server help H0?

The model's own generation is most of the agent time (median 9.0 of 10.5 minutes per trial in hidden 12000 s; about
16 tok/s), and H0 never sees the clock, so a faster server acts like a bigger budget. Re-timing the hidden 12000 s trials
with model time divided by k, and keeping a trial's reward only if it ended on its own within the budget (stopped trials get
0, so read the change along each row):

| Budget | ×1 | ×2 | ×4 | ×∞ |
|---|---|---|---|---|
| 1200 s | 0.361 | 0.429 | 0.446 | 0.474 |
| 2400 s | 0.441 | 0.459 | 0.479 | 0.512 |
| 3600 s | 0.459 | 0.474 | 0.509 | 0.527 |

A 2× faster server is worth about +0.07 at 1200 s and +0.02 at 2400 s. Nothing exceeds 0.527, the trials that end on their
own at all.

## Caveats

- One run per arm per budget, each on a different day. Server speed was the same (about 16 tok/s) and network dropouts were
  checked against vllmtop's record of the server.
- **1800 s rests on an uneven shown run:** its attempts solved 19, 13, 14, 20 and 21 of 40 tasks. Attempts 2–3 (Oct 11,
  09:00–15:39) wrote more output and failed easy tasks on a healthy server; a spread that wide comes up by chance with
  P 0.02. Hidden 12000 s is also uneven (attempt scores .448 to .639, P 0.05).
- Hidden 1800 s: 71 trials hit by the server's network dropouts on Oct 12 were re-run on Oct 13 and merged (before: 0.433).
- **The stop differs by budget.** At 2400 s harbor kills the trial mid-turn (the official setting). At the other budgets
  the harness stops it after the turn under way finishes (about a minute later). The hard-stop column re-judges the
  soft-stopped trials that scored (trial list in `archive/budget-sweep-findings.md`); no conclusion changes.
- Errors count as 0: one tmux failure in hidden 12000 s (`109`).

## Not run yet

- shown 12000 s (`harness7-time12000-attempt5`, config ready) — does the clock still add anything when time is plentiful?
- the 4800 s pair (`harness7-time4800-attempt5`, `harness0-time4800-attempt5`).
- a second 1800 s pair, both arms at once, to settle the uneven shown run.

Older write-ups (Qwen3.6, other harnesses, cost and turn budgets, leaderboard, run tracker) are in `archive/`.
