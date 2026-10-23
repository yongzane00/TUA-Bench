# Time budget: why the hidden arm does not grow with time, and what speed would do (2026-10-16; updated 2026-10-21)

Companion to `budget-sweep-findings.md`. Runs: qwen3.8 hidden / shown at 1800, 2400, 3600 s and the old H0 (Sep 23);
Qwen3.6 hidden at 1800, 2400 s, shown at 1800, 2400, 3600 s and the old H0 (the Qwen3.6 hidden 3600 s run is still going).
Read from every trial's `result.json` and `trajectory.json`. Score = harbor Mean; "solved" = reward 1. Qwen3.6 runs have a
32,768-token output cap per call and qwen3.8 runs have none.

## Update 2026-10-21: the hidden 12000 s run

The conclusions below were drawn from runs of at most one hour. A hidden run with a 12000 s budget (3.3 hours) scores
**0.534**, +0.100 (+0.031 to +0.171) over hidden 3600 s. About +0.04 of that is run-to-run luck: both runs behave identically
for the first hour, and the 12000 s run was already 0.038 ahead at minute 60. The other ~+0.06 is real: 10 of the 48 trials
still running at 60 minutes solved by 3.3 hours (016, 025, 042, 088, 094, 100). So "more time does nothing" holds only within
the first hour. Past it, qwen3.8 without the clock does finish some long trials, slowly (3–6% per 10 minutes adds up over two
more hours) and expensively (2.7× the `cost_usd` of hidden 3600 s). H7 at 3600 s still scores as well (0.571, +0.037,
−0.041 to +0.115) at a third of the cost. Section 3 is redone on the 12000 s run below.

## 1. When the score is earned

Score from trials that have **ended** by minute m (reward summed over the 200 trials):

| Run | 5 | 10 | 20 | 30 | 40 | 50 | 60 min | Final | Earned after 20 min |
|---|---|---|---|---|---|---|---|---|---|
| qwen3.8 hidden 1800 s | .170 | .305 | .371 | .421 | .458 | | | 0.463 | +0.092 |
| qwen3.8 hidden 2400 s | .150 | .299 | .386 | .424 | .439 | .459 | | 0.459 | +0.073 |
| qwen3.8 hidden 3600 s | .198 | .289 | .346 | .381 | .396 | .406 | .421 | 0.434 | +0.088 |
| qwen3.8 shown 1800 s | .110 | .250 | .359 | .436 | .467 | | | 0.467 | +0.108 |
| qwen3.8 shown 2400 s | .130 | .259 | .374 | .439 | .515 | .539 | | 0.539 | +0.165 |
| qwen3.8 shown 3600 s | .145 | .270 | .364 | .440 | .480 | .515 | .557 | 0.571 | **+0.207** |
| Qwen3.6 hidden 2400 s | .100 | .140 | .162 | .172 | .200 | .200 | | 0.200 | +0.038 |
| Qwen3.6 shown 3600 s | .110 | .135 | .157 | .171 | .194 | .201 | .208 | 0.208 | +0.051 |

Chance that a trial still running at minute m ends solved within the next 10 minutes:

| Run | 0 | 10 | 20 | 30 | 40 | 50 min |
|---|---|---|---|---|---|---|
| qwen3.8 hidden 3600 s | 27% | 11% | 9% | 4% | 3% | 6% |
| qwen3.8 shown 3600 s | 26% | 15% | 15% | 12% | 12% | 12% |
| qwen3.8 hidden 2400 s | 28% | 16% | 9% | 5% | 7% | |
| qwen3.8 shown 2400 s | 24% | 20% | 15% | 20% | 2% | |
| Qwen3.6, any run | 11–12% | 2–6% | 0–2% | 2–6% | 0–3% | 0–2% |

- The hidden qwen3.8 arm earns the same amount after minute 20 at every budget (+0.07 to +0.09). Past 30 minutes a running
  hidden trial has a 3–6% chance per 10 minutes of finishing solved, so a longer budget mostly adds minutes to trials that will
  not finish.
- The shown arm keeps converting: 12% per 10 minutes up to the end of the 3600 s budget, and its score earned after
  minute 20 grows with the budget (+0.11, +0.17, +0.21).
- The shown − hidden gap is earned almost entirely by trials that ran past 20 minutes: +0.016 / +0.092 / +0.120 at
  1800 / 2400 / 3600 s, against −0.012 / −0.012 / +0.018 from trials that ended earlier. For qwen3.8 the clock changes how
  long trials end, not how short ones go.
- Qwen3.6 solves in the first 10 minutes or almost never. Its small shown − hidden lean comes from trials that ended in under
  20 minutes (+0.015 at 1800 s, +0.032 at 2400 s), not from late finishes.

## 2. What trials still running after 20 minutes do

Turns after t = 1200 s; "claims done" = the trial calls `mark_task_complete` at least once after 20 minutes.

| Run | Trials | Solved | Hit the stop | Turns / 10 min | Repeated commands | Empty waits | Broken JSON | Claims done |
|---|---|---|---|---|---|---|---|---|
| qwen3.8 hidden 2400 s | 75 | 14 | 59 | 5.5 | 1% | 11% | 1% | 25% |
| qwen3.8 shown 2400 s | 88 | 28 | 35 | 4.9 | 0% | 9% | 1% | 68% |
| qwen3.8 hidden 3600 s | 80 | 17 | 45 | 5.3 | 0% | 9% | 1% | 44% |
| qwen3.8 shown 3600 s | 92 | 35 | 23 | 4.9 | 0% | 9% | 1% | **83%** |
| Qwen3.6 hidden 2400 s | 76 | 3 | 55 | 23.1 | **22%** | 18% | 6% | 28% |
| Qwen3.6 shown 2400 s | 85 | 5 | 57 | 22.9 | 22% | 14% | 4% | 40% |
| Qwen3.6 shown 3600 s | 85 | 5 | 39 | 19.9 | 24% | 18% | 5% | 56% |

Trials that hit the stop, last 10 turns:

| Run | Trials | Ever claimed done | Turns (median) | Tokens per reply (median) | Repeated / empty / broken JSON | Any reward at the stop |
|---|---|---|---|---|---|---|
| qwen3.8 hidden 3600 s | 45 | **0%** | 36 | 1,696 | 0% / 7% / 1% | 3 |
| qwen3.8 shown 3600 s | 23 | 30% | 25 | 1,170 | 0% / 11% / 3% | 2 |
| Qwen3.6 hidden 2400 s | 55 | 0% | 98 | 394 | 21% / 21% / 10% | 0 |
| Qwen3.6 shown 3600 s | 39 | 8% | 150 | 225 | **35% / 33% / 17%** | 0 |

- **qwen3.8 without the clock keeps working and never decides to stop.** Its long trials are not loops: no repeated commands,
  about 10% empty waits, 1% broken JSON. They send new commands and write longer replies late (1,700 tokens per reply over the
  last 10 turns of trials that hit the 3600 s stop), but none of those 45 trials ever claimed done, and only 3 had any reward
  when stopped. Work in progress is rarely in a gradeable state, so more time adds turns, not score.
- **With the clock, qwen3.8 finishes.** 83% of the shown 3600 s trials still running after 20 minutes claim done (hidden 44%),
  and 21 of the 45 that finish after 30 minutes solve. The model mentions the clock in 12–13% of all turns, 36–46% of trials,
  and 60–72% of the turns in the last quarter of the budget. Of the trials that solved after 20 minutes, 15 of 19 at 1800 s
  mention the clock in their last 5 turns, ending a median 5 minutes before the budget. At 3600 s they end a median 26 minutes
  early and only 20 of 35 mention the clock at all, so at the loose budget part of the effect is a changed working style, not
  only a last-minute wrap-up.
- **Qwen3.6's long trials are loops.** After 20 minutes it runs 20–25 turns per 10 minutes, and about a fifth of them repeat an
  earlier command exactly. In the last 10 turns of shown 3600 s trials that hit the stop, 35% are repeats, 33% empty waits and
  17% broken JSON, over a median of 150 turns. More time is more loop iterations.
- **Qwen3.6 does not read the clock until it is almost out.** It mentions the clock in 1–3% of turns; its first mention comes at
  92–97% of the budget, and only 6–18% of its last-quarter turns mention it.

Example (`059-make-summary-slide`, 3600 s): the hidden trial spent 47 turns retrying `.uno:SummarySlide` through UNO
dispatch variations and was stopped with no output. The shown trial looked up the real command name (`.uno:SummaryPage`) in
LibreOffice's command registry, dispatched it, verified the file and finished at 1,537 s in 16 turns. Hidden solves 0 of 5 on
this task at 3600 s, shown 3 of 5.

## 3. Does a faster server help?

Share of agent time spent waiting for the model: **qwen3.8 77–84%** (16–17 tok/s per trial), **Qwen3.6 18–22%**
(175–190 tok/s; the rest is commands, waits and harness overhead). For qwen3.8 a faster server works almost like a bigger time
budget; for Qwen3.6 it barely moves the clock.

Simulated speed-up of the hidden arm, redone on 2026-10-21 on the hidden 12000 s run, whose trials ran to their natural end
(184 of 200 ended on their own within 3.3 hours). Each trial is re-timed with model time divided by k (82% of qwen3.8's agent
time is the model) and keeps its reward only if it ended on its own within budget B. The ×1 column is lower than the real
runs because stopped trials get 0 here; read the change along each row.

| Budget | ×1 | ×1.5 | ×2 | ×4 | ×∞ (model time 0) |
|---|---|---|---|---|---|
| 1200 s | 0.361 | 0.411 | 0.429 | 0.446 | 0.474 |
| 1800 s | 0.421 | 0.441 | 0.444 | 0.459 | 0.488 |
| 2400 s | 0.441 | 0.444 | 0.459 | 0.479 | 0.512 |
| 3600 s | 0.459 | 0.474 | 0.474 | 0.509 | 0.527 |
| 7200 s | 0.499 | 0.518 | 0.527 | 0.527 | 0.527 |

- A faster server helps the hidden arm most at tight budgets: 2× speed is worth +0.068 at 1200 s, +0.023 at 1800 s and
  +0.018 at the official 2400 s; 4× is worth +0.038 at 2400 s. The ceiling is 0.527, the trials that end on their own at all.
  The earlier version of this table (from the 3600 s run) capped the ceiling at what finished within an hour, so its "at most
  +0.04" was too low.
- For Qwen3.6 the model is about 20% of agent time, so speed barely moves the clock (simulated on hidden 2400 s: at most
  +0.009 at 1800 s).
- Measured, not simulated: in the old qwen3.8 H0 run, 48 trials without a stalled call ran at half speed (median 8.1 tok/s).
  They scored 0.411 against 0.457 for the same tasks at normal speed (−0.046, with 8 trials worse, 8 better and 32 the same).
  Within the normal range there is no difference: the faster half of each task's hidden trials (17.5 tok/s) scored 0.456, the
  slower half (16.0 tok/s) 0.469.
- So for H0 the curve rises to about 30 minutes, is flat to an hour, then creeps up: hidden 1200 s 0.366, 1800 s 0.463,
  3600 s 0.434, 12000 s 0.534 (part of the last step is run-to-run luck). More speed acts like more time on that curve.
- With the clock (H7), extra time does turn into score (+0.104 from 1800 to 3600 s), so a faster server should help H7 in the
  same way. That is an inference: H7 has not run on a faster server, and the meter's "turns that fit" would change with speed.

## Bottom line

Within the first hour, qwen3.8 without the clock is not short of time or speed: it does not decide to finish, and its
unfinished work is rarely in a state the grader accepts. Given hours, it finishes some of that work anyway (hidden 12000 s:
0.534), so a much faster server would help the hidden arm somewhat (2× speed: +0.02 at 2400 s, +0.07 at 1200 s). The clock
gets there faster and cheaper: H7 at one hour scores as well as hidden at 3.3 hours, at a third of the cost. Qwen3.6 is not
short of time or speed: its long trials are command loops, it ignores the clock until the last few percent of the budget,
and neither more time (H7 4800 s 0.218) nor more speed helps it.
