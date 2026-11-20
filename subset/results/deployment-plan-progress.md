# Professor's plan: progress log

Source: `Time-Aware_Harness_落地导向下一步工作计划.pdf` (2026-11-01, 12 pages). Work branch `time-aware-plugin` in both
repos (TUA-Bench and the Harbor fork); one commit per version. Nothing is pushed.

## Plan items and status

| Plan item (page) | What is done here | Status |
|---|---|---|
| I0-I3 feedback ablation, 40 tasks x 4 arms x 3 attempts = 480 trials (p6); frozen analysis plan with rounds 4-5 | `feedback` levels in the agent (v1); 4 configs; arms run side by side, 1 trial each; 3 rounds, each started only when the server is quiet | Done 2026-11-16 on a shared server (separate condition, not comparable with the report): solved of 120: I0 46, I1 52, I2 51, I3 49, all inside the noise; ended by time 37, 41, 28, 26 (log 2026-11-18 15:35) |
| Finalize control "P" with a reserve (p4) | `finalize_reserve_sec` (v2): one wrap-up notice when time left <= recent turn length + reserve | Done (batch 2 wrap120 arm): 45 of 60, same as full (+0, -5 to +6); lowest $ per qualified ($0.0208); ended by time 12 of 60 (log 2026-11-19 04:40) |
| Timeliness: overrun past the deadline, P95 target 5 s (p4, p7) | Measured in finished runs (below); `hard_deadline` (v2) cancels a running reply and cuts command waits; v18 makes both waits follow the real-time clock | Met: batch 2 P95 delivery 1.8 to 3.3 s; batch 3 missed in 2 of 4 arms (stops during parallel test runs); fixed in v25 (forced worst case 3.7 to 4.5 s, log 2026-11-20 20:45); batch 4 proxy P95 416 to 457 s from WebFetch sub-requests (fixed by turning web tools off) |
| Latency intervention, +5 s and +20 s per reply (p5) | `extra_reply_delay_sec` (v2); 4 configs `swe-dev-{hidden,full}-delay{5,20}-time900-rounds3` (the pilot configs plus the delay); batch 3 in the frozen analysis plan with its decision rule; `ablation_report.py --did` for the change in the gap | Done 2026-11-19: difference of gaps (+20 s minus 0 s) -6 (-12 to +0): no evidence the clock helps more when replies are slower; at +20 s the full arm loses its timeout advantage (log 2026-11-20 10:20) |
| H1: the clock helps tasks that can be done but run out of time (p5) | Classes from other base runs; gap by class (below) | First result: supported at 2400 s |
| H2: feedback brings the deliverable earlier (p5) | First `mark_task_complete` time from trajectories | Not supported: the clock delays the first "done" and adds more just before the deadline (below) |
| Paired task-level bootstrap, decision routes A and B (p7) | `subset/tools/plan_metrics.py` | Done for both models |
| Cost per qualified delivery, empty-handed timeouts (p7) | same | Done for both models |
| Week-1 items for the next group meeting (p11): task contract, 10 reproducible tasks, data split, budget and logging spec, first configs | `pilot/README.md` (contract, budget, logging), `pilot/tasks.md` (split), `pilot/configs/oracle-week1.yaml` | Contract, split, spec and configs written; oracle check of the 10 tasks running (tmux `pilot`) |
| Event log with run_id, task_id, phase, remaining budget, ... (p11) | `subset/tools/event_log.py`: one JSON line per model call, command batch, stop and grading | Done; tested on a pilot smoke trial and a TUA trial |
| Framework middleware + LangChain adapter (p3) | harbor `packages/time-budget`: framework-free core (state, forecast, texts equal to the Harbor agent's) and `TimeBudgetMiddleware` for LangChain 1.4 (state per run in the agent state, meter per call outside the history, tool timing, stop, async hard deadline) | Done; 11 of 11 tests in a real `create_agent` loop; live check on qwen3.8 passed (wrap-up notice, cut at 20.0 s; the server drops a cancelled reply within 0.5 s). Since v12 also a proxy for agents that cannot be changed: stock terminus-2 in Harbor ran through it with no code change (reward 1 at 300 s and at 90 s, cut at 90.0 s) |
| Second harness (p3; the user's goal of one plugin for every harness) | Batch 4 in the frozen analysis plan: Harbor's claude-code agent (unchanged, version pinned) through the proxy, hidden vs full, 20 dev tasks x 3 rounds; configs `cc-dev-{hidden,full}-time900-rounds3`, launcher `subset/tools/run_cc_batch.sh`; checked live on 1 task (1 trial, and 2 at once on one URL). Since v19 a Bash command running at the deadline is ended by Claude Code itself (its timeout lowered to the time left, background tasks off; scripted self-tests). A third harness, Harbor's Codex agent (responses format), ran unchanged through the proxy on 1 task: wrap-up notice at 231 s of 300 s, answer at 263 s, reward 1 | Done 2026-11-20: Claude Code full 43, hidden 34 of 60, +9 (+2 to +17): carries over by the frozen rule; +11 (+2 to +20) with web-using trials counted as unsolved. Repeat without web tools running (log 2026-11-20 19:00, 21:30) |
| Hosted API replication (p9) | Self-hosted cost instead: server-hours per solved task (`server_hours.py`, section "Self-hosted cost") | Not run: there is no money for hosted APIs (the user, 2026-11-12) |
| Business tasks and pilot (p2, p8, p11) | | Needs a partner team; public-repo technical validation is possible |
| Held-out 80 TUA tasks, full 120 (p6) | | After the configuration is locked |

## Findings so far (finished runs, qwen3.8, 40 tasks x 5 attempts per run)

"Solved" = reward 1, the plan's qualified delivery. Gaps are shown minus hidden at the same budget; 95% CIs from a
paired bootstrap over the 40 tasks (attempts stay with their task), as the plan asks on p7.

| Budget (s) | Solved, hidden | Solved, shown | Gap (95% CI) | $ per solved, hidden | $ per solved, shown | Ratio (95% CI) | Route A | Route B |
|---|---|---|---|---|---|---|---|---|
| 1200 | 69 of 200 | 81 of 200 | +12 (-2 to +27) | $0.0552 | $0.0453 | 0.82 (0.64 to 1.03) | no | pass |
| 1800 | 85 of 200 | 91 of 200 | +6 (-4 to +16) | $0.0666 | $0.0506 | 0.76 (0.61 to 0.94) | no | pass |
| 2400 | 87 of 200 | 99 of 200 | +12 (+0 to +24) | $0.0756 | $0.0638 | 0.84 (0.64 to 1.09) | pass | pass |
| 3600 | 87 of 200 | 104 of 200 | +17 (+5 to +31) | $0.1225 | $0.0874 | 0.71 (0.56 to 0.92) | pass | pass |

Route A (plan p7): at least +10 of 200 solved, CI lower bound above 0, $ per solved at most 5% worse.
Route B: $ per solved at least 15% lower, CI lower bound of the gap above -6 of 200. These are the plan's thresholds
applied to finished runs; they were not frozen before the runs, so they describe, not decide.

**Timeliness.** The old stop fires only between turns, so a slow reply runs on past the budget:

| Budget (s) | Arm | Clock reached the budget | Late by: median / P95 / max (s) | Late by more than 30 s | Solved among those |
|---|---|---|---|---|---|
| 1200 | hidden | 79 of 200 | 60 / 758 / 1200 | 57 of 200 | 1 of 57 |
| 1200 | shown | 58 of 200 | 62 / 1200 / 1202 | 39 of 200 | 3 of 39 |
| 1800 | hidden | 62 of 200 | 68 / 394 / 600 | 50 of 200 | 3 of 50 |
| 1800 | shown | 40 of 200 | 77 / 600 / 600 | 26 of 200 | 0 of 26 |
| 3600 | hidden | 45 of 200 | 85 / 465 / 600 | 37 of 200 | 2 of 37 |
| 3600 | shown | 23 of 200 | 54 / 600 / 600 | 16 of 200 | 0 of 16 |

The maximum is Harbor's own agent limit ending the trial. Late trials almost never solve, and mean agent time is
similar in both arms (768 vs 795 s at 1200 s), so the late stop does not explain the gains; it does mean the
plan's P95 target of 5 s is far off without `hard_deadline`.

**H1.** Task classes come from base runs other than the pair being compared: "capable" = base solved the task at
least once in 5 tries at 12000 s; "time-limited" = base ended by time in at least 3 of 5 tries at 3600 s.

| Budget (s) | Capable, time-limited (6 tasks) | Capable, not time-limited (21 tasks) | Not solved at 12000 s (13 tasks) |
|---|---|---|---|
| 1200 | -1: 5 to 4 of 30 | +15: 62 to 77 of 105 | -2: 2 to 0 of 65 |
| 1800 | +1: 10 to 11 of 30 | +5: 73 to 78 of 105 | +0: 2 to 2 of 65 |
| 2400 | +8: 6 to 14 of 30 | +1: 78 to 79 of 105 | +3: 3 to 6 of 65 |

At 2400 s the gain sits in tasks the base can do but runs out of time on, as H1 predicts. At 1200 s it moves to
tasks that are not time-limited at 3600 s, which become time-limited when the budget is a third as long. Tasks the
base never solves gain almost nothing at any budget.

**H2.** The plan's H2 says feedback brings the deliverable earlier. Counting, over all 200 trials of each run, how
many had declared the task complete (`mark_task_complete`) by a given time:

| Budget (s) | Arm | by 300 s | by 600 s | by 900 s | by 1200 s | by 1800 s | by 2400 s | by 3600 s |
|---|---|---|---|---|---|---|---|---|
| 1200 | hidden | 75 | 101 | 113 | 123 | | | |
| 1200 | shown | 55 | 87 | 102 | 140 | | | |
| 2400 | hidden | 58 | 100 | 121 | 127 | 137 | 141 | |
| 2400 | shown | 55 | 88 | 105 | 113 | 138 | 160 | |
| 3600 | hidden | 68 | 97 | 107 | 119 | 130 | 136 | 153 |
| 3600 | shown | 48 | 86 | 100 | 111 | 133 | 142 | 170 |

The shown arm declares later at first and overtakes only in the last part of the budget, at every budget (1800 s is
the same; full table from `plan_metrics.py qwen38 --h2`). So H2 is not supported; following the plan (p5), the effect
is described as a change in stopping behaviour, not as better planning. Declarations are about as often wrong in
both arms (declared but not solved, 2400 s: 73 of 172 shown, 59 of 144 hidden); the clock adds declarations, right
and wrong, in proportion.

**Speed was the same in both arms.** The arms of each pair ran on different days, so the model's speed could differ.
Median output tokens per second per trial, qwen3.8: 16.8 / 17.0 (1200 s, hidden / shown), 17.5 / 17.4 (1800 s),
16.9 / 16.8 (2400 s), 17.2 / 16.1 (3600 s; here the hidden arm was the faster one). Speed does not explain the
gaps. qwen3.6 is even across pairs except 4800 s (hidden 135, shown 170 tokens per second).

**qwen3.6.** Gaps (shown - hidden, of 200): +2 (600 s), +6 (1800 s), +6 (2400 s), +3 (3600 s), +3 (4800 s); every CI
includes 0, so route A fails everywhere. $ per solved is lower in the shown arm at every budget (ratio 0.77 to 0.93)
but only the 600 s and 1800 s ratios clear route B's 0.85 line, with CIs up to 1.08 and 1.06. Its late stops (P95
up to 600 s) are litellm's 600 s timeout on stalled requests, which `hard_deadline` also cuts.

**Server conditions.** The qwen3.8 server moved to `<qwen38-vllm-host-2>` (used by every qwen3.8 run since 2026-10-23); the
old `<qwen38-vllm-host>` no longer answers. vllmtop history for the last 14 days: the server had requests running in 42 to
67 of every 100 seconds at every hour of the day (quietest 09:00 to 14:00), and busy spells last whole days
(2026-11-05: 91 of 100; 2026-11-11: 98 of 100). Night is not reliably quiet, so each ablation round waits for 10
minutes with no requests from anyone; trials can later be tagged with the load during them from the same history.

## Related work (abstracts, checked 2026-11-11)

| Paper | Finding | Relation to this work |
|---|---|---|
| On the Clock, arXiv 2610.10833 (2026-10-07) | Timing information makes agents keep to the budget "without measurable loss in performance"; trained agents learn when to stop but fill extra time with repeated actions; agents do not turn extra time into better results | Here the clock raises quality at a fixed budget (+12 and +17 of 200 at 2400 and 3600 s, CIs above 0), and the shown arm at 3600 s beats the hidden arm at 12000 s (104 vs 95 of 200 for $9.09 vs $29.48): the "productive" side they call open |
| Timely Machine, arXiv 2601.16486 (2026-01-23) | Tool latency separates time from tokens; the best model and strategy depend on latency; RL training (Timely-RL) | The latency intervention tests the same question without training |

## Pilot task checks (week 1)

A task is reproducible only when the oracle (reference fix) scores 1 and Harbor's nop agent (no change) scores 0
(`pilot/check_tasks.py jobs/pilot`). The nop check was added after a smoke trial scored 1 on
`django__django-7530` without changing any file: its one FAIL_TO_PASS test already passes on the untouched repo.
`django__django-10097` fails the other way: the reference fix scores 0 (438 required tests, 475 s to grade). Of the
first 20 dev tasks, these two are the only failures; with the two replacements, all 20 dev tasks reproduce (`pilot/reproducibility.md`; grading time median 41 s, P90 84 s over 68 trials).
Both are listed in `pilot/excluded.md`; the selection rule then took `django__django-11265` and `-11276` into dev
(being checked) and moved 3 held-out tasks by the same file rule. Grading time over 44 trials: median 40 s, P90
102 s, which supports the plan's 120 s wrap-up reserve (P90 rounded up to the next 30 s).

## Second curve and power (plan p5, p7)

**Does the clock make extra time more useful?** The plan separates two curves: across arms at one budget (done above)
and within an arm as the budget grows. Paired over tasks, qwen3.8, solved of 200:

| Budget step | Shown gains | Hidden gains | Difference (95% CI) |
|---|---|---|---|
| 1200 -> 2400 s | +18 | +18 | +0 (-20 to +19) |
| 2400 -> 3600 s | +5 | +0 | +5 (-7 to +17) |
| 1200 -> 3600 s | +23 | +18 | +5 (-14 to +25) |

No evidence that the shown arm turns extra time into more solved tasks than the hidden arm does. The gain is a higher
level at each fixed budget, not a steeper curve; this agrees with On the Clock's point that keeping to a budget and
using more time well are different things, and the write-up should claim only the first.

**Precision of the ablation.** Resampling 3 of 5 attempts per task from the finished 2400 s runs: the interval for the
full meter against hidden is about +-9 of 120, around an effect of about +7 of 120, and it excluded 0 in 40 of 200
resamples. The plan's 3 rounds will most likely leave I1 and I2 "uncertain". The frozen analysis plan
(`subset/results/analysis-plan.md`, commit `bf1f151`, 11:42, before any ablation trial) therefore fixes rounds 4 and 5
in advance and states every decision rule.

## Quiet-start gate: what each rule costs (2026-11-12)

The ablation has waited since 2026-11-11 09:58 for 10 minutes with no request from anyone. `subset/tools/gate_options.py`
reads vllmtop's per-second samples of the server for the last 7 days (95 of 100 seconds sampled):

| Rule: start when other users' requests are at most k for 10 minutes | Openings in 7 days | Wait from a random moment, median | Moments that waited more than 12 h |
|---|---|---|---|
| k = 0 (the current gate) | 23 | 12.6 h | 4940 of 9615 |
| k = 1 | 70 | 4.4 h | 2801 of 9615 |
| k = 2 | 197 | 0.6 h | 406 of 9615 |

| Requests running | Decode speed per request, median (tok/s) | Against 4 running |
|---|---|---|
| 4 (the ablation alone) | 17 | 1.00 x |
| 5 | 15 | 0.90 x |
| 6 | 18 | 1.08 x (778 seconds only) |

A round lasts about 15 h (40 trials per arm in a row at 22.6 min each, from the finished 2400 s runs), so the start
rule governs only the first minutes of a round; the load during the round is whatever the other users bring, and
batch 1 already plans a sensitivity analysis on trials run while other users' load was below 0.5. The four arms run
side by side, so any load slows all of them alike. Waiting for k = 0 costs a median 12.6 h per round; k = 2 cuts
that to 0.6 h for replies at about 0.9 times the speed per extra request at the start. Changing the rule changes a
frozen protocol item (batch 1, Size), so it is the user's decision; recommendation: k = 2, recorded in the analysis
plan as a change before round 1.

**Does other users' load change the clock? (2026-11-12, the user's question)** No: the budget is real elapsed time,
and load does not change how it is measured. Load changes how much work fits in it, because the server shares its
decode speed among the requests running. Per-request decode speed from vllmtop since 2026-10-23 (all seconds with that
many requests running; the rows for 6 to 8 are rare and uneven):

| Requests running | Seconds | Per-request decode speed, median (tok/s) | Against 1 running |
|---|---|---|---|
| 1 | 345006 | 24.7 | 1.00 |
| 2 | 296429 | 21.8 | 0.88 |
| 3 | 148537 | 18.8 | 0.76 |
| 4 | 167073 | 16.9 | 0.68 |
| 5 | 26479 | 15.0 | 0.61 |

What this means for the ablation:

1. The comparison between arms is protected by the design, not by the gate. The four arms run side by side, one
   trial each, so a load spike slows all four at the same moment.
2. The gate controls only the start. A round lasts about 15 h, and other users come and go during it: the server
   has requests running in 42 to 67 of every 100 seconds at every hour of the day (section "Server conditions").
3. The finished runs behind every result so far (H0 against H7 at 1200 to 3600 s) had no start gate and ran under the
   same shared load; their arms got the same speed (16.9 against 16.8 tok/s at 2400 s).
4. Load during a trial is a condition the shown meter is meant to handle: it reports the last reply's seconds and
   tokens per second, and its forecast uses the recent pace. Batch 3 adds delay on purpose to test this.
5. What load does change is the level. With 1 request from others (5 running) each reply decodes at 0.89 times the
   speed of the ablation alone (15.0 against 16.9 tok/s); 6 running is too rare in the history to measure, and the
   trend from 1 to 5 points to about 0.8 times. All arms then fit fewer turns, so absolute scores are not comparable
   with runs made under other loads. The frozen sensitivity analysis (trials with other users' load below 0.5)
   covers this.

## Clock drift (validity check)

The budget and Harbor's own agent limit run on the monotonic clock, which inside WSL runs slow against real time.
Real seconds per 2400 harness seconds (median per run): 1800 s pair 2519 hidden / 2414 shown; 2400 s pair 2578 /
2483; 3600 s pair 2408 / 2485. At 1800 and 2400 s the hidden arm got more real time, which works against the shown
arm. At 3600 s the shown arm got about 3 in 100 more (about 106 s per hour); the hidden arm gains only +8 of 200
from 3600 s to 12000 s, so 106 s cannot explain +17. For a deadline promised to a person the clock must be real
time: v5 adds `clock: wall`, used by the pilot configs. `subset/tools/event_log.py` scales real time to the budget's
clock per trial, so its `budget_left_s` matches the stop (checked: a 2400 s trial killed at 2506 real seconds shows
2400.0 on the budget clock).

**On the Clock, full paper (arXiv HTML, read 2026-11-11).** What it does and does not cover, and where this work differs:

| Point | On the Clock | This work |
|---|---|---|
| Control | No hidden-budget arm with the same stop; the prompt-only baseline used 161% of its 15-min budget, so "no clock" also meant "more time". With clocks: on budget 15% -> 62% of runs, quality 49.4 -> 42.1 (their Table 2) | Hidden arm with the same stop isolates the information; quality rises (+12 and +17 of 200 at 2400 and 3600 s) |
| Forecast | "the harness provides no remaining-time forecasts" | The meter shows turns that fit at the recent pace; I2 vs I3 tests whether it adds anything |
| Long generations | Stated limitation: feedback only between generations, a long generation can overrun | `hard_deadline` cancels the running reply (live check: 2 s late) |
| Wrap-up | Prompt instructions only; no harness-triggered wrap-up | One notice triggered by the measured pace (arm P, plan H3) |
| Inference-side control | none | `late_effort` |
| Speed regime | 1.4 to 1.8 s per turn (27B), no injected latency | about 17 tok/s, most of the time spent waiting for the model; latency injection planned |

Their "clamp" hook (cut a command's time limit to the deadline) is the same idea as the command-wait cut in
`hard_deadline`; their RL policies fill time with rejected commands, a failure mode to check in our traces too.

## Filler actions near the deadline (checked 2026-11-11)

On the Clock's trained agents filled spare time with repeated actions. The check in the finished qwen3.8 runs: every
agent step in the last 300 s of the budget (by the trajectory's timestamps), 200 trials per arm. Wait-only: every
command in the step is empty, `sleep N`, `wait`, `true`, `:` or a one-word `echo`. Repeated: the same commands as an
earlier step of the same trial.

| Budget (s) | Arm | Steps in the last 300 s | Wait-only | Repeated | Declared complete |
|---|---|---|---|---|---|
| 1200 | hidden | 383 | 32 of 383 | 22 of 383 | 26 of 383 |
| 1200 | shown | 373 | 27 of 373 | 20 of 373 | 108 of 373 |
| 1800 | hidden | 321 | 35 of 321 | 32 of 321 | 18 of 321 |
| 1800 | shown | 204 | 9 of 204 | 9 of 204 | 66 of 204 |
| 2400 | hidden | 229 | 25 of 229 | 23 of 229 | 11 of 229 |
| 2400 | shown | 162 | 11 of 162 | 9 of 162 | 50 of 162 |
| 3600 | hidden | 188 | 8 of 188 | 7 of 188 | 13 of 188 |
| 3600 | shown | 149 | 4 of 149 | 3 of 149 | 43 of 149 |

No filling: at every budget the shown arm has fewer wait-only and repeated steps near the deadline than the hidden
arm. It instead uses the last minutes to declare the task complete (50 of 162 steps at 2400 s vs 11 of 229), which
is the same late declaration seen in H2. Earlier in the trials the arms are close (2400 s: wait-only 139 of 2910
hidden, 106 of 2854 shown). `subset/tools/filler_check.py` makes this table (`--plan-runs qwen38`) and checks the
ablation and pilot runs the same way (`<budget> <label>=<run_dir>,...`).

## Does the clock help more when the model is slow? (natural speed, 2026-11-11)

A free first look at the plan's latency question (p5): server load makes some trials slower than others, and a slow
trial has less model time inside the same budget. `subset/tools/speed_dose.py` takes each trial's speed (output
tokens per second of waiting for the model) relative to the same task's mean over all qwen3.8 runs (z, in log units),
and fits solved = task fixed effects + shown + z + shown x z, bootstrap over tasks.

| Budget (s) | Mean z, hidden / shown | Clock gap on slow trials (z = -0.2), of 200 | On fast trials (z = +0.2) | Slow - fast |
|---|---|---|---|---|
| 1200 | -0.011 / -0.003 | +13 (-6 to +32) | +11 (-9 to +34) | +2 (-28 to +31) |
| 1800 | +0.045 / +0.015 | -6 (-42 to +22) | +17 (-0 to +38) | -23 (-78 to +18) |
| 2400 | +0.012 / -0.001 | +13 (-10 to +36) | +11 (-12 to +36) | +2 (-39 to +42) |
| 3600 | +0.017 / -0.040 | +6 (-11 to +21) | +34 (+12 to +70) | -28 (-74 to -2) |
| pooled | | +9 (-3 to +19) | +15 (+5 to +29) | -6 (-30 to +9) |

- The arms met the same server speed at 1200 to 2400 s (mean z within 0.03). At 3600 s the shown run was slower
  (median 16.2 vs 17.2 tok/s), which works against the shown arm.
- No sign that the clock helps more on slow trials: the pooled gap is not larger on slow trials (-6, CI -30 to +9);
  the one interval that excludes 0 (3600 s) points the other way and comes from the run with unequal speed.
- The test is weak, because natural variation is small. Within a task, speed varies by about +-10% (P10 -7%, P90
  +12%; 93 of 1600 trials are more than 20% off their task's usual speed). Waiting for the model is 80 to 83 of every
  100 seconds of agent time (median over 160 trials at 2400 s), and the median reply takes 33 s (P25 17 s, P75 72 s).
  The plan's +20 s per reply adds about 60% to a median reply, about six times the natural spread. So the injected
  delay arm is still needed; this check only says the effect does not show up within the natural range.

## Turn forecast and wrap-up reserve (plan p4, 2026-11-11)

The meter's "turns that fit" and the wrap-up trigger (time left <= recent turn + reserve) both use the mean of the
last 3 turns. `subset/tools/turn_forecast.py` scores it against other forecasters on every turn after the third in the
finished qwen3.8 runs (17655 turns; turn length median 51 s, P90 151 s), using only earlier turns of the same trial:

| Forecaster | Median abs. error (s) | Turn ran > 30 s past the forecast |
|---|---|---|
| mean of last 3 (in use) | 27 | 3650 of 17655 |
| last turn | 25 | 3869 of 17655 |
| median of last 5 | 25 | 4358 of 17655 |
| longest of last 3 | 40 | 2107 of 17655 |
| 80th percentile of all earlier turns | 31 | 3422 of 17655 |
| same command class (install, build, test, other) | 28 | 4437 of 17655 |

No forecaster predicts a single turn well: the error is about half a median turn whichever is used. The command-class
forecast (idea 3 below) is worse than the plain mean, so it is dropped. What matters for the wrap-up is the time set
aside for one more turn:

| Rule | Next turn finished inside it | Mean time set aside (s) |
|---|---|---|
| mean of last 3 + 60 s | 15671 of 17655 | 139 |
| mean of last 3 + 120 s (pilot setting) | 16856 of 17655 | 199 |
| longest of last 3 + 60 s | 16502 of 17655 | 181 |
| longest of last 3 + 120 s | 17128 of 17655 | 241 |
| mean of last 3 + 2 x SD of last 5 + 30 s | 16405 of 17655 | 189 |
| 2 x mean of last 3 + 30 s | 16540 of 17655 | 187 |
| 3 x mean of last 3 | 16864 of 17655 | 236 |

The rule in use, mean plus a fixed reserve, is as good as the adaptive ones for the time it sets aside: the
scaled and spread-based rules cover fewer turns at about the same cost, and 3 x mean covers the same as mean + 120 s
for 37 s more. With 120 s, about 19 in 20 next turns fit (16856 of 17655), the same reserve the pilot's grading-time
P90 suggested. No code change.

## Cancelling local processes at the deadline (plan p4, p11; 2026-11-11)

The plan's deadline stage asks to stop new calls, cancel local processes and check they exited (p4), and lists
long-tool cancellation among the required engineering checks (p11). The hard deadline (v2) only cut the agent's
wait: a command still running in the terminal kept running while the verifier graded the container, and could still
change files. v7 adds `interrupt_at_stop`: when a budget ends the attempt, the harness lists the processes under the
agent's shell (process tree under the tmux server), sends Ctrl-C to the foreground one (at most twice), lists again,
and records both lists. Background jobs (`&`) are listed but left running, since some tasks need a process the agent
started.

**Self-test without a model server** (`pilot/selftest/`): a scripted model drives the real Harbor pipeline on one
Django task (Docker, tmux with recording, verifier). Budget 20 s; reply 1 edits a file, starts `sleep 900 &` and
`sleep 600`; reply 2 takes 60 s and is cut at the deadline.

| Run | What it showed | Fix |
|---|---|---|
| 1 | Ctrl-C stopped `sleep 600`, but the agent's own shell was counted as a job (`stopped` false, a needless second Ctrl-C), and tmux's pane logger (`cat`) was listed | The process tree printed from inside the task showed why: the recorder starts `sh -c /bin/bash`, so the shell is not where the name rule looked. The agent's shell is now the deepest interactive shell with a terminal under tmux, and jobs are its descendants |
| 2 | Correct lists, 1 Ctrl-C, `stopped` true; cleanup 6.4 s, deliverable final 8.6 s past the budget | Each call into the container costs about 1 s here; Ctrl-C, wait and the second listing now go in one call, and `git diff` and `git status` in one call |
| 3 | Work stopped at 21.7 s, cleanup 2.8 s, deliverable final at 24.5 s: 4.5 s past the 20 s budget, inside the plan's 5 s target; reply cut, diff saved (1 file) | - |

The metadata now has `stopped_at_sec` (work stopped) besides `elapsed_sec` (deliverable final), so lateness can be
reported both ways. `interrupt_at_stop: true` is on in all seven pilot configs (batches 2 and 3), the same in every
arm, recorded as a dated change in the analysis plan before any of their trials. 30 of 30 unit tests pass, with the
process tree from the real container as the test fixture.

## Plugin off = stock agent; concurrent trials (plan p7, p11; 2026-11-11)

The plan's engineering checks ask that switching the plugin off restores the base behaviour (p7) and that concurrent
tasks do not share timing (p11, week 2). `pilot/selftest/selftest-baseline.yaml` runs one scripted conversation
(commands with fixed output) with three agents at once on the same Django task, and
`pilot/selftest/compare_prompts.py` compares every prompt the model was sent, after replacing the container hostname
and collapsing the pane's empty padding lines:

| Agent | Prompts vs stock terminus-2 | Budget clock vs the trial's own run time |
|---|---|---|
| H7, `feedback: hidden` (the off position) | 3 of 3 identical | 20.8 s vs 22.1 s |
| H7, `feedback: full` | Differ only by the budget sentence (prompt 0) and one meter line per update | 20.1 s vs 20.1 s |

The three trials ran at the same time for 13.8 s and each budget clock followed its own trial (the 1.3 s in the hidden
row is Harbor's start time being recorded before the agent's `run` starts). A first attempt used `git status`,
whose progress meter printed at different moments in each container; that was terminal timing, not the plugin, and
the script now uses commands with fixed output.

## The code-repair report (plan p2, p8; 2026-11-11)

The contract asks the agent to deliver, besides the patch, the tests it ran with their real results, a short fix note
and what it could not verify (p2), and the week-4 gate rejects a wrap-up arm that adds false success reports (p8).
The SWE-bench task text is only the issue, so nothing asked for that report. v8 adds `report_request`: one fixed
request appended to the task text in every arm, the hidden one included (`REPORT_REQUEST` in `budget_meter.py`).
`event_log.py` puts the report (the agent's message in its last reply that declared the task complete) in
`agent_end.report`, and the analysis plan gains the report check: a reviewer blind to the arm compares each report
with the trajectory, and the wrap-up arm must not have more false verification claims than the full arm.

**Live check** (`swe-smoke-report-time600`, one trial on `django__django-11099`, 600 s): the agent finished at 436 s
with reward 1 and reported "Fix applied to django/contrib/auth/validators.py (both validators now use
r'\A[\w.@+-]+\Z'), verified by manual check and by auth_tests.test_validators (23 tests, OK), with a regression
test added." The trajectory shows the claimed run ("Ran 23 tests ... OK" at step 12), so the claim checks out. It did
not state what was unverified; the request asks for it, so a missing item is itself something the review records.

## Tasks from a repo's history (plan p2; 2026-11-11)

The plan's business task set is 60 historical fixes ("收集 60 个可运行的历史修复任务"), not new tickets, so a team with
few new tickets can still build it from its git history. `pilot/mine_fixes.py` applies the SWE-bench recipe to any
Python repo on GitHub: a candidate is a commit that changes source and test files and points to an issue (directly or
through the squash-merged pull request); the task text is the issue report, never the fix; features, RFCs and
breaking changes are skipped (labels or title); the environment is the repo at the fix's parent commit as a fresh git
repo (the future fix is not in its history); grading resets the touched test files, applies the fix's test changes and
runs them with pytest. For a company repo, the issue lookup would read the ticket system instead.

First use: 8 tasks from marshmallow fixes since 2024 (e.g. issue #2936 "Update Email validator to support IDNs", #2249
"`fields.Url` does not accept `file` URLs without host"), written to `~/work/datasets/mined-marshmallow`. **Not yet
checked**: the reproducibility check (`pilot/configs/check-mined-marshmallow.yaml`, reference fix must score 1 and no
change 0) runs the cloned project's code and tests in Docker, and the permission system blocked it; it waits for the
user's go-ahead. Issue lookups are cached (`~/.cache/mine_fixes/`), since the unauthenticated GitHub API allows 60
requests an hour.

## LangChain adapter on a live model (2026-11-11)

`packages/time-budget/examples/live_smoke.py` (harbor fork) ran `TimeBudgetMiddleware` in a real `create_agent` loop
on qwen3.8-flash-next with one tool and a small coding task:

| Budget | Setting | Result |
|---|---|---|
| 240 s | effort low | Answer after 26.4 s (2 replies, 1 tool call); no stop |
| 90 s | wrap-up reserve 60 s, effort medium | First reply took 47.9 s on the busy server; wrap-up notice at 48.2 s (41.8 s left); answer at 65.9 s |
| 20 s | effort xhigh | The first reply was cancelled at 20.0 s; stop `time` |

No meter line stayed in the message history in any run. **Does the server stop a cancelled reply?** Three long
non-streaming requests raised the server's running count from 3 to 6; after the client cancelled them at 8.3 s it
read 3 again at 8.8 s and stayed there. So on vLLM the hard deadline also frees the shared server instead of leaving
an orphaned generation. Hosted APIs were not checked and may still bill the cut tokens.

## Any agent through its base URL: the budget proxy (plan p3; 2026-11-11)

The adapters so far need code in the agent (a few `TimeBudget` calls, or LangChain middleware). Most agent
harnesses, though, already let the user set the model server's address. `time_budget.proxy` (harbor fork, v12) is a
small web server placed at that address: it adds the budget sentence and the per-turn meter to each request, times
each reply, and cuts the reply still running at the deadline, then passes the request on to the real server. The
agent's code and logs are untouched. One clock per run id in the URL (`/run/<id>/v1`).

Live checks on qwen3.8-flash-next:

| Agent | Budget | Result |
|---|---|---|
| LangChain `create_agent`, no middleware, streaming | 90 s, reserve 60 s | Wrap-up notice at 19.0 s; answer at 38.2 s; 0 meter lines left in the history |
| Same | 20 s, effort xhigh, 3 runs | Cut at 20.0 s in 3 of 3; each ended on the stop reply |
| Harbor stock terminus-2, `django__django-11099` (`swe-smoke-proxy-stock-time300`) | 300 s, reserve 60 s | 6 replies, wrap-up notice at 203 s, task marked complete at 222 s, reward 1 |
| Same (`swe-smoke-proxy-stock-time90`) | 90 s, reserve 30 s | Wrap-up notice at 75.8 s (14 s left); the agent marked the task complete; its confirmation reply was cut at 90.0 s and the stop reply (terminus-2's own JSON with `task_complete: true`) confirmed it; graded, reward 1 |
| Harbor's Claude Code agent (unchanged, inside the task container), Anthropic messages format, streaming (`pilot/configs/smoke-proxy-claude-code.yaml`) | 300 s, reserve 60 s | 12 replies; wrap-up notice at 193 s (107 s left); the model wrote its answer at 288 s, its next reply was cut at 300.0 s, and Claude Code ended cleanly on the stop reply 0.2 s later; reward 1. No Anthropic API was called |
| Same, 2 trials of the task at once on one base URL with no run id (`--track-conversations`, `-k 2 -n 2`) | 240 s each, reserve 60 s | The proxy found 2 runs, started 3.9 s apart, each matching one trial's own log: one had a 208.7 s first reply on the busy server, got the wrap-up notice at 208.9 s and was cut at 240.0 s; the other got the notice at 160.1 s and answered at 194 s. Reward 1 in both |

The event log records the note each request added (for example `[Time 87 of 90 s, 3 s left | last reply 11 s at
14 tok/s | about 0 turns fit]`), because the agent's own trajectory never shows what the proxy added.

Since v15 it also edits the OpenAI responses format (`/v1/responses`, the default of Codex and the OpenAI Agents
SDK), so the three request formats that agent harnesses use are covered. Since v13 the proxy also edits the Anthropic messages format (`/v1/messages`), so Claude Code and other Anthropic
clients take it through `ANTHROPIC_BASE_URL`; vLLM serves that format too. Claude Code runs inside the task
container: with Docker Desktop the container reaches a proxy on WSL's 127.0.0.1 as `host.docker.internal`, but not
at the WSL eth0 address. The first attempt used that address, and Claude Code retried with no answer until it was
stopped (`smoke-proxy-claude-code/2026-11-11__22-49-37`, not used).

**After the wrap-up notice the model kept working.** In the Claude Code run the notice went out at 193 s; the
model then sent 7 more replies (the last one cut at the deadline). The turn forecast swung with them: "about 1 turn fit" at 205 s and 212 s, then
"about 9 turns fit" at 219 s, after three short turns (7 to 11 s) pulled the 3-turn mean down. A model reading
"9 turns fit" right after a wrap-up notice gets mixed signals. Idea 4 below.

Since v16 a launcher (`python -m time_budget.run ... -- <agent command>`) runs a command-line agent behind the
proxy and, if the agent is still running a grace period after the deadline, stops its whole process group
(SIGINT, SIGTERM, SIGKILL). Live: a 60 s command started by an unchanged openai-SDK agent was stopped at 45.9 s on a
40 s budget with 5 s grace, its child process with it. This covers the proxy's main gap for agents run as local
processes; agents in containers (Harbor's installed agents) still finish their running command first.

What the proxy cannot do: it sees model calls only, so tool calls are timed inside the turn, not one by one, and it
cannot stop a command the agent is running. An agent that raises on an error needs the stop reply in its own answer
format: Harbor skips grading when terminus-2 raises anything but a timeout, so the stop reply there is a
`task_complete` JSON, sent up to 2 times (terminus-2 asks to confirm).

**Two fixes found by the live checks.**

1. **The deadline ran on the wrong clock.** The first 20 s run was cut at 21.6 s, and a 12 s one at 13.6 s.
   `asyncio.wait_for` times out on the event loop's monotonic clock, which runs slower than the wall clock under
   WSL (section "Clock drift"). `TimeBudget.run` now waits in 0.5 s slices and re-reads the budget clock;
   after the change, 3 of 3 runs were cut at 20.0 s. The lateness came and went before the change: of 5 cuts, 3
   were 1.6 s late (a 20 s budget once, 12 s twice) and 2 were on time (8 s and 20 s).
2. **Half a tool call.** In the 21.6 s run the agent sent a request after the cut and got HTTP 400. The likely
   cause (not confirmed) is a stream cut inside a tool call, which leaves the agent half a tool call to run.
   Tool-call pieces are now held until the reply is complete; the 3 later runs ended cleanly.

**The Harbor agent had the same clock problem; fixed in v18 (2026-11-12).** `budget_meter.py` cut a reply with
`asyncio.wait_for(..., timeout=left)`, so with `clock: wall` the cut was late by the drift during the reply. The
"77.0 s on a 75 s budget" first given here as evidence was not: that run used the monotonic clock, and its 2.0 s
included the diff saved after the cut (Harbor's own timestamps read 78.6 s). Clean measurement, the same task with
the pilot settings (90 s, real-time clock, hard deadline, Ctrl-C at the stop, saved diff, report request), 3 trials
on each code, reward 1 in 6 of 6:

| Code | Job | Cuts | Work lateness (s) | Delivery lateness (s) |
|---|---|---|---|---|
| Before v18 | `swe-smoke-wall-time90/2026-11-12__05-36-10` | 3 replies | 2.0, 4.1, 4.0 | 3.4, 5.6, 5.6 |
| v18 | `swe-smoke-wall-time90/2026-11-12__05-26-14` | 1 reply, 2 command waits | 0.5, 0.2, 0.2 | 2.7, 1.2, 2.7 |

Work lateness is `stopped_at_sec` - 90; delivery lateness is `elapsed_sec` - 90, which adds the Ctrl-C and the
saved diff (1.0 to 2.6 s) and equals Harbor's own agent time to 0.1 s in all 6 trials. Two of the three old-code
trials would miss the 5 s target. In v18 both waits re-read the budget clock every 0.5 s, as the package does. In 2 of
3 v18 trials a test command's wait, already shortened to the time left, still ran past the deadline (sending the
keys takes time too) and the new check ended it. The v18 run used the Windows copy's code through `PYTHONPATH`; the
WSL copy, which the ablation imports, stays at the old code until the ablation ends (its arms do not use the hard
deadline). Moving the agent onto the shared core is still to do.

## Commands still running at the deadline under the proxy (plan p4, p11; 2026-11-12)

The proxy sees model calls only, so a command Claude Code runs at the deadline used to run on until it ended or hit
Claude Code's own timeout (120 s by default, up to 600 s if the model asks). Most shell tools take a timeout
argument, so v19 lowers it: `--cap-tool-timeout Bash:timeout:ms:120000` hands each Bash call to Claude Code with a
timeout no longer than the time left minus `--cap-margin`, and later requests carry the model's own value back (in a
hidden arm the time left must not show in the model's own tool calls). What Claude Code does at the timeout was
checked rather than assumed. In this session's own Claude Code (2.1.286), a timed-out command was moved to the
background and kept running; a user report says `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` makes it end the command
instead (exit 143); and Harbor's claude-code agent sets `FORCE_AUTO_BACKGROUND_TASKS=1` and `ENABLE_BACKGROUND_TASKS=1`.

Self-tests with Harbor's claude-code agent 2.1.322 in the `django__django-7530` container and a scripted model
(`pilot/selftest/scripted_messages.py`: its first answer is one Bash loop that appends the time to
`/logs/agent/probe-ticks` every second for 90 s; no model server is used). Budget 40 s:

| Job | Background tasks | Margin | Command | Claude Code |
|---|---|---|---|---|
| `jobs/pilot/selftest-cc-timeout/2026-11-12__06-09-02` | on (as Harbor runs it) | 0 s | "Moved to the background" at 40 s; ran all 90 ticks | Stop reply at 44.7 s; then waited for the command, sent 6 more requests (HTTP 400) and exited with an error at 100.8 s (`NonZeroAgentExitCodeError`, graded) |
| `jobs/pilot/selftest-cc-timeout-nobg/2026-11-12__06-12-19` | off | 0 s | "Exit code 143, timed out after 39s"; 40 ticks | Stop reply at 44.5 s; clean exit at 46.5 s |
| `jobs/pilot/selftest-cc-timeout-nobg/2026-11-12__06-17-13` | off | 3.5 s | Ended at its 36.5 s timeout, last tick at 38.1 s | Next request at 39.0 s (before the deadline; a real model's reply would be cut at 40.0 s); clean exit at 39.0 s |

Without a margin the stop came 4.5 s late, all of it Claude Code's own: it starts a command about 2 s after the
reply arrives, its timeout counts from there, and ending the command and sending the next request take about 1.5 s.
Batch 4 now uses the cap with a 3.5 s margin and background tasks off in both arms (change entry in the analysis
plan, before any of its trials). The same self-tests were the first live use of batch 4's way of passing the proxy
address (the config's `env:`; the smoke runs used the shell environment): requests reached the proxy with the model
name `qwen3.8-flash-next`. On that route Harbor does not set the model aliases for Claude Code's other model roles
(`ANTHROPIC_DEFAULT_HAIKU_MODEL` and the rest), so the configs now set them to qwen3.8, as Harbor does on the shell
route. A side request under a Claude model name would have reached vLLM, which serves only qwen3.8.
`subset/tools/proxy_report.py` now counts the lowered calls per trial (batch 4's new secondary; on the first two
self-tests: 2 calls, in 2 of 2 trials).

## Self-hosted cost: server hours per solved task (plan p9; 2026-11-12)

The plan asks for GPU occupancy hours on a self-hosted model rather than token-equivalent dollars, since the
dollars in the earlier tables use API prices nobody paid. The vllmtop history (from 2026-10-13) records the server's
running requests every second and its token counters about every 30 s. `subset/tools/server_hours.py` charges each
run the server's busy hours in the run's window times the run's share of the server's output tokens (decoding takes
most of the time of these long replies). The 2400 s pair ran before the history starts.

| Budget (s) | Arm | Solved | Window (h) | Run's share of the server's output tokens | Server-hours | Server-hours per solved |
|---|---|---|---|---|---|---|
| 1200 | hidden | 69 of 200 | 15.1 | 0.90 | 12.9 | 0.187 |
| 1200 | shown | 81 of 200 | 15.9 | 0.90 | 13.5 | 0.166 |
| 1800 | hidden | 85 of 200 | 17.8 | 0.95 | 16.1 | 0.190 |
| 1800 | shown | 91 of 200 | 17.6 | 0.88 | 14.8 | 0.162 |
| 3600 | hidden | 87 of 200 | 26.0 | 0.94 | 23.6 | 0.271 |
| 3600 | shown | 104 of 200 | 24.3 | 0.91 | 21.1 | 0.203 |
| 12000 | hidden (H0, long limit) | 95 of 200 | 43.0 | 0.95 | 40.0 | 0.421 |

The history covered 99 to 100 of every 100 seconds of each window. The shown arm used 0.89, 0.85 and 0.75 times the
hidden arm's server-hours per solved task at 1200, 1800 and 3600 s. The API-price ratios were 0.82, 0.76 and 0.71, so
the direction holds in server time too. During these runs the 4 concurrent trials made 88 to 95 of every 100 output
tokens the server generated: the shared server was close to being ours, and a run's cost was close to its wall
time. So a solved task cost about 0.16 to 0.27 server-hours at 4 trials at a time. To get dollars, multiply by the
server's GPU count and a price per GPU-hour. Two prices fit the plan: the marginal running cost of the existing
machine, or rental or depreciation. Both need numbers from the server's owner. A batch run with more trials at once
would share the server's time among more trials; this was not measured.

## Minimum engineering checks and handover package (plan p11; 2026-11-12)

The plan lists eight checks the plugin must pass and eight items a handover must contain. Where each one stands:

| Check (p11) | Evidence | State |
|---|---|---|
| Concurrent tasks isolated | Harbor agent: 3 concurrent scripted trials kept separate clocks; proxy: 2 Claude Code trials on one URL kept separate clocks (`--track-conversations`) | Passed |
| Retry timing | v20: a failed model call is logged and counted (`failed_calls`) but is not a turn; its time goes into the turn of the retry. Before, the retry closed a turn of a few seconds and the meter showed the failure as the last reply, so the turns that fit read too high. Tests: plain loop, proxy with HTTP 500 and a retry (both fail on the old code). The Harbor agent retries inside one model call (LiteLLM), so its turns already included retries | Fixed in v20 |
| Process recovery | `TimeBudget` state is a plain dict that resumes the same budget (test); proxy `--state-dir` keeps each run's budget across a proxy restart (test) | Passed (tests only) |
| Long tool cancellation | Harbor agent: hard deadline waits (v2, v18) and Ctrl-C to the running command (v7); package: `TimeBudget.run` cancels a tool at the deadline; proxy: the agent's own tool timeout lowered to the time left (v19); launcher: the agent's process group (v16) | Passed (live checks) |
| Tool failure | v20 test: a failing LangChain tool, sync and async: the error goes back to the model as the tool's result, logged with status `error`, the budget counts on | Passed (test) |
| Saved deliverable when the budget runs out | `save_diff_of` (v3): `git diff` and status at the stop; live in every smoke run | Passed |
| Complete tool-call protocol | Proxy: tool-call pieces held until whole, never half a call after a cut (tests in three formats, live with the openai SDK and Claude Code) | Passed |
| Plugin off = baseline | H7 hidden sends exactly what stock terminus-2 sends (3 of 3 prompts) | Passed |
| Acceptance tests cannot be replaced by the model | SWE-bench grading resets every test file the test patch touches to the base commit and applies the patch before running (`tests/test.sh`), so edits to those files are discarded; the tests directory enters the container only at grading | Holds for SWE-bench tasks; a business task needs the same reset |

| Handover item (p11) | What exists | Missing |
|---|---|---|
| 1. Installable plugin, version locked | `packages/time-budget` (`pip install ./packages/time-budget[proxy,langchain]`); experiments pin by commit | The package version is still 0.1.0 (unchanged since v6); a release number per frozen batch |
| 2. Harbor and framework examples | Harbor agent `terminus_2_harness7`; proxy configs for stock terminus-2 and Claude Code; LangChain `examples/live_smoke.py`; launcher for command-line agents | A business framework example (needs the partner team) |
| 3. Budget, wrap-up and stop semantics | Package README: each part, settings, limits, and the table "The same method in each framework" (core, plain loop, LangChain, proxy and Harbor agent side by side; updated for v19 and v20); `budget_meter.py` docstring for the Harbor agent | |
| 4. Task and environment list | `pilot/tasks.md`, `pilot/excluded.md`, task images from SWE-bench | |
| 5. One full success and one timeout trajectory | Candidates in the smoke jobs | Picked from batch 2 when it has run |
| 6. Analysis scripts and configs | `plan_metrics.py`, `ablation_report.py`, `pilot/pilot_report.py`, `proxy_report.py`, `event_log.py`; all configs in the repo | |
| 7. Real cost report | Self-hosted: server-hours per solved task from the vllmtop history (section "Self-hosted cost"; `server_hours.py`) | The server's GPU count and a price per GPU-hour for dollars; no hosted API bill (no money for hosted APIs, the user, 2026-11-12) |
| 8. Known failure modes, scope, how to turn it off | Package README "Known failure modes, where it helps, how to turn it off" (harbor `6a7198c6`): 9 failure modes seen in the runs, each with its numbers and its guard; the scope from the finished runs; `feedback: hidden` keeps only the stop | Batch 2's report check will add the false-claim rate |

## Ideas to test (new, beyond the plan)

1. **Effort that follows the clock.** About four fifths of the time goes to waiting for the model. Near the
   deadline the harness lowers `reasoning_effort` instead of only telling the model (v4, `late_effort`). This
   changes the inference, not the prompt, so it also works in the hidden arm. Checked first that the server
   honours it: the same coding question used 88 and 90 reasoning tokens at `low` vs 241 and 236 at `xhigh` (14 to
   16 s vs 25 s per reply). To run as its own arm after the wrap-up comparison.
2. **Natural latency experiment.** Server load changes the model's speed from trial to trial. Tagging each trial
   with its measured tokens per second (from the agent's own request times) and the vllmtop load gives a free
   dose-response check of H1 before paying for injected delays. Done (section above): no dose-response within the
   natural +-10% speed range, which is too narrow to replace the injected +5 s / +20 s arms.
3. **Turn-length forecast by command type** (plan p4): keep durations per command class (install, build, test,
   GUI action) instead of the mean of the last 3 turns. Checked on 17655 turns: worse than the plain mean (late
   turns 4437 vs 3650 of 17655); dropped (section "Turn forecast and wrap-up reserve").
4. **A forecast that does not swing back up after the wrap-up notice.** Once the notice is out, show the turns that
   fit at the slowest of the recent turns (or drop the count), so short checking turns do not turn "1 turn fits"
   into "9 turns fit" (seen in the Claude Code proxy run). Checked on the meter lines the H7 models saw
   (`subset/tools/forecast_rebound.py`, 4 budgets): after the count first read 1 or 0 (median 182 s left), it read
   3 or more again in 13 of 219 trials (5 of 219 if it used the longest of the last 3 turns), and those trials did
   not time out more often (2 of 13, against 29 of 206 where it stayed low). Rare and with no sign of harm, so the
   display stays as it is. The H7 runs had no wrap-up notice; recheck on the pilot's wrap-up arm when it has run.

## Versions

| Version | Repo | Commit | What changed |
|---|---|---|---|
| v1 | harbor | `ac7c6ba3` | `feedback` kwarg: `hidden` (I0), `once` (I1), `clock` (I2), `full` (I3, same text as the finished H7 runs, checked against a trajectory). 9 of 9 unit tests pass |
| v1 | TUA-Bench | `409ae90`, `55b16b4` | First ablation configs and launcher; server address fix; `.146` added to the local redact filter as `<qwen38-vllm-host-2>` |
| v2 | harbor | `82c207e1` | `hard_deadline`, `finalize_reserve_sec`, `extra_reply_delay_sec` (all off by default). 17 of 17 unit tests pass |
| v2 | TUA-Bench | `ca2bae1` | Ablation as 3 quiet-start rounds (`run_parallel.sh`, `run_gate.sh`, `run_one.sh`); `-rounds3` configs replace the `-attempt3` ones; `plan_metrics.py` |
| v3 | harbor | `397eb68e`, `2c6683db` | `save_diff_of`: saves `git diff` and status of the deliverable at the stop. 20 of 20 tests |
| v4 | harbor | `bb354b2b` | `late_effort`: lower reasoning effort near the deadline. 22 of 22 tests |
| v4 | TUA-Bench | `ad0bbec` | `pilot/check_tasks.py`, nop config, two smoke configs, `subset/tools/ablation_report.py` |
| v5 | harbor | `dfa93a21` | `clock: wall`: budget in real time. 24 of 24 tests |
| v5 | TUA-Bench | `e73285c` | `subset/tools/event_log.py`; oracle config for dev tasks 11 to 20 |
| v6 | harbor | `c61156e9` | `packages/time-budget`: core + LangChain middleware. 11 of 11 tests |
| v6 | harbor | `2749ca37` | `packages/time-budget/examples/live_smoke.py`; live check and server-side cancel check in the READMEs |
| v7 | harbor | `c41a5847` | `interrupt_at_stop`: Ctrl-C the terminal's running command at a budget stop and check it exited; one container call each for the check and the saved diff; `stopped_at_sec`. 30 of 30 tests |
| v7 | TUA-Bench | `c03e843` | `pilot/selftest/` scripted-model self-test; `interrupt_at_stop` on in the seven pilot configs; analysis-plan change recorded |
| v8 | harbor | `6382238d` | `report_request`: the contract's report asked for in every arm. 32 of 32 tests |
| v8 | TUA-Bench | `f107f6e` | `report_request` on in the seven pilot configs; report check and condition (d) in the analysis plan; report in the event log; live check |
| v9 | harbor | `0576eec9` | Plugin parity (the user's goal: one plugin for every agent harness): the core gains the report request and stop timing; the LangChain adapter gains `report_request`, an end-of-run hook with stop and cleanup times and an `on_stop` callback for the application's own cleanup; README table of features per framework. 15 of 15 package tests. The Harbor agent is not changed until the running experiments finish |
| v10 | harbor | `5bf7ae17` | `TimeBudget`: the budget for any agent loop without a framework (instructions, meter before each call, timed and deadline-cancelled model and tool calls, cleanup hook, resumable plain-dict state). 22 of 22 package tests |
| v11 | harbor | `920c6fd2` | The LangChain adapter becomes a thin layer over `TimeBudget`: one implementation of the timing, texts and stop for every framework. 22 of 22 tests; live check on qwen3.8 (normal finish, cut at 8.0 s) |
| v12 | harbor | `efe819e2` | `time_budget.proxy`: the budget for an unchanged agent through its model base URL (meter per request, reply cut at the deadline, stop reply in the agent's own format, tool-call pieces held until a reply completes); `TimeBudget.run` re-reads the budget clock every 0.5 s instead of one asyncio timeout on the monotonic clock. 32 of 32 tests; live checks with LangChain and stock terminus-2 |
| v13 | harbor | `3cb6ddda` | The proxy also edits the Anthropic messages format: Claude Code (Harbor's installed agent, unchanged) ran through it in the task container on qwen3.8, cut at 300.0 s, reward 1. 35 of 35 tests |
| v14 | harbor | `5bae9619` | Proxy `--track-conversations`: requests without a run id are sorted into runs by the history they resend, so concurrent trials that share one base URL keep separate clocks. 37 of 37 tests; live check passed (2 concurrent Claude Code trials on one URL, separate clocks) |
| v15 | harbor | `8e401e5f` | The proxy also edits the OpenAI responses format (Codex, OpenAI Agents SDK), including runs that chain on the server by `previous_response_id`. 40 of 40 tests; live check with the openai SDK (tool call whole, cut at 6.0 s, closing event parsed) |
| v16 | harbor | `9a84f839` | Launcher `python -m time_budget.run ... -- <agent command>`: proxy + agent in one command; stops the agent's process group if it runs past the deadline plus a grace period (the one thing the proxy cannot do). 43 of 43 tests; live check: a 60 s command stopped at 45.9 s on a 40 s budget with 5 s grace |
| v17 | harbor | `8f2ba7a1` | The proxy records each run's first user message (`first_user`) on its first request, so a run can be matched to its task. TUA-Bench `subset/tools/proxy_report.py` joins a proxy event log with the Harbor trials (matches, close calls, trials stopped by time, lateness after the deadline, replies); on the two Claude Code smoke jobs it matched 3 of 3 trials, lateness 0.5 s and 0.2 s. 43 of 43 tests |
| v18 | harbor | `63217a11` | The Harbor agent's hard deadline waits for a reply or a command on the budget clock, re-read every 0.5 s, instead of one asyncio timeout on the event loop's clock (late under WSL with `clock: wall`). Live: work lateness 0.2 to 0.5 s, against 2.0 to 4.1 s before (3 trials each at 90 s). 35 of 35 budget tests, 64 of 64 terminus-2 tests. Not yet in the WSL copy (the ablation imports it) |
| v19 | harbor | `8cee7b44` | Proxy and launcher `--cap-tool-timeout TOOL:FIELD:UNIT[:DEFAULT]` and `--cap-margin`: a tool call reaches the agent with its timeout no longer than the time left minus the margin (all three formats, streamed or not); later requests carry the model's own value back; `tool_capped` events. 50 of 50 package tests. Self-tests with Claude Code 2.1.322: the command is ended at the deadline only with `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` |
| v20 | harbor | `bb0307c9` | A failed model call is not a turn (plan p11 retry timing): counted in `failed_calls`, its time in the turn of the retry; tests for retries (loop and proxy) and a failing LangChain tool. 54 of 54 package tests |
| v21 | harbor | `e6528875` | The proxy records every user message of a run's first request (`user_text`), not only the first: Codex sends its environment context as a user message before the task, so its run could not be matched to its trial. `proxy_report.py` reads `user_text` (and `first_user` in older logs). 55 of 55 package tests |
| v22 | harbor | `519886a6` | A command wait cut by the hard deadline ends the attempt at once with no screen read; cleanup timed apart (`interrupt_sec`, `diff_sec`). In the Windows copy; WSL gets it after batch 4 |
| v23 | harbor | `c6193f7b` | At a budget stop: Ctrl-C, then SIGKILL after 1 s for what still runs, in one call into the container (was up to two Ctrl-Cs 1 s apart, each its own call); `sigkill` count recorded. Windows copy; WSL after batch 4 |
| v24, v25 | harbor | `fb148dfe` | The stop is one `docker exec` (listing, Ctrl-C, 1 s, listing; SIGKILL only for what is left); a timer started inside the container when a turn's waits reach the deadline sends Ctrl-C at the deadline itself; stop parts timed (`stop_sec`, `kill_sec`, `timer_late_sec`, `diff_sec`) |
| 0.2.0 | harbor | `572e6af1`, `83e9be0d` | `time-budget` package release number and versions table (handover item 1) |
| v6 | TUA-Bench | `f5f9c4f`, `011bc36` | `pilot/excluded.md` and rule 6; new split; first pilot batch configs (`swe-dev-{hidden,full,wrap120}-time900-rounds3`: 900 s, real-time clock, hard deadline, saved diff) |
| v3 | TUA-Bench | `367a9e6` | `pilot/`: task contract, budget and logging spec, 20 + 40 Django task split, oracle config; H2 counts by time; `pilot/**` added to the redact filter in `.gitattributes` |

## Runs

| Session | Arms | State |
|---|---|---|
| `abl38` (first launch) | `-attempt3` configs | Started 09:40, stopped 09:53 on 2026-11-11 because the server was busy; the four partial job folders under `jobs/qwen38-flash-next/*-attempt3/` are left as they are and are not used |
| `abl38` | I0 `harness0-time2400-rounds3`, I1 `harness7-time2400-once-rounds3`, I2 `harness7-time2400-clock-rounds3`, I3 `harness7-time2400-rounds3`; 3 rounds of 40 trials per arm | Waiting since 2026-11-11 09:58 for 10 quiet minutes (3 requests from others running) |
| `smoke` + `tbproxy` | Stock terminus-2 through the budget proxy: `swe-smoke-proxy-stock-time300/2026-11-11__22-00-45`, `swe-smoke-proxy-stock-time90/2026-11-11__22-07-49` (1 trial each; proxy event logs in `~/work/proxy-smoke/`) | Done: reward 1 in both |
| `smoke` + `tbproxy` | Harbor's claude-code agent through the proxy: `smoke-proxy-claude-code/2026-11-11__23-01-37` (1 trial); `2026-11-11__22-49-37` was stopped (wrong proxy address) and is not used | Done: reward 1 |
| `smoke` + `tbproxy` | 2 Claude Code trials at once through one proxy URL: `smoke-proxy-claude-code/2026-11-12__00-18-33` | Done: separate clocks, reward 1 in both |
| `smoke` | Pilot settings at 90 s, 3 trials each: `swe-smoke-wall-time90/2026-11-12__05-26-14` (v18 code via `PYTHONPATH` to the Windows copy), `2026-11-12__05-36-10` (the WSL copy's code, before v18) | Done: reward 1 in 6 of 6; lateness in the clock section |
| `probe` | Claude Code tool-timeout self-tests with a scripted model: `jobs/pilot/selftest-cc-timeout/2026-11-12__06-09-02`, `jobs/pilot/selftest-cc-timeout-nobg/2026-11-12__06-12-19` and `2026-11-12__06-17-13` (proxy events `~/work/proxy-smoke/probe-cc*.jsonl`) | Done: results in the section "Commands still running at the deadline under the proxy" |
| `codex` | Harbor's Codex agent 0.118.0 through the proxy (responses format, 300 s, reserve 60 s): `smoke-proxy-codex/2026-11-12__08-48-16` (1 trial; events `~/work/proxy-smoke/events-codex.jsonl`) | Done: 12 replies, wrap-up notice at 231 s, answer at 263 s, reward 1; `proxy_report.py` could not match it to the trial (0 of 1) because the recorded text was Codex's environment context, fixed in v21 |

## Log

- 2026-11-11: read the plan; made the branch; v1 and v2 written, tested and committed; delivery metrics, timeliness
  and H1 computed for qwen3.8; ablation set up as quiet-start rounds. qwen3.6 metrics, H2, speed check; pilot
  folder with the week-1 items; oracle check started (no model calls). Smoke trials confirmed the hard deadline
  and diff saving live; nop check added after a task passed with no change; late-effort setting added (v4). The
  qwen3.8 server had 2 to 4 requests from other users running all morning, so ablation round 1 has not started.
  Later: nop check done, two broken tasks excluded and replaced; clock drift measured and `clock: wall` added (v5);
  event log converter; pilot batch configs ready. Run order on the server: ablation first (plan week 3), then the
  pilot batch (week 4), each in quiet-start rounds, never both at once.
- 2026-11-11 afternoon: still no quiet 10 minutes (the last was 2026-11-10 19:03; 13 of the last 14 days had at
  least one). Checks on finished runs while waiting: no filler actions near the deadline; no dose-response of the
  clock gap to natural speed (range too narrow to replace the latency arm). LangChain adapter checked live; vLLM
  drops cancelled replies. Turn forecast checked: the mean of the last 3 turns plus a fixed reserve is as good
  as the adaptive rules tried; 120 s covers 16856 of 17655 next turns.
  Latency batch (plan p5) prepared: 4 configs, batch 3 added to the analysis plan before any of its
  trials, `--did` checked on finished runs (reproduces the second-curve result, +0 of 200, -20 to +20).
  Deadline cleanup (plan p4, p11): `interrupt_at_stop` (v7), checked live with a scripted model in a Django
  container (3 runs, 2 fixes); on in the pilot configs.
  Plugin-off check: H7 hidden sends the model exactly what stock terminus-2 sends (3 of 3 prompts); three
  concurrent scripted trials kept separate clocks.
  Code-repair report (v8): asked for in every pilot arm; live check on one task: report written, its test claim
  matches the trajectory, reward 1.
  History miner (`pilot/mine_fixes.py`): 8 marshmallow tasks generated; their check waits for permission to
  run external project code in Docker.
  Plugin parity (v9): the LangChain adapter now has the report request, stop timing and a cleanup hook;
  the Harbor agent moves onto the shared core after the ablation, so the evaluated runs stay byte-identical.
  `TimeBudget` (v10): a few calls in any agent loop give the same budget without a framework adapter.
  v11: LangChain adapter rebuilt on `TimeBudget`, so the package has one implementation.
- 2026-11-11 evening: still no quiet 10 minutes (2 to 4 requests from others at 21:40 to 22:11). v12: the budget
  proxy, checked live with an unmodified LangChain agent and with Harbor's stock terminus-2 (2 smoke trials, reward 1
  each, the 90 s one cut at 90.0 s and graded). The live checks found the deadline running on the monotonic clock
  (1.6 s late in 3 of 5 cuts); fixed in the package; the same fix is due in the Harbor agent after the ablation.
  v13: the proxy handles the Anthropic messages format; Harbor's Claude Code agent ran unchanged through it inside
  the task container (cut at 300.0 s, reward 1). The model sent 7 more replies after the wrap-up notice
  while the turn count rose from 1 to 9; logged as idea 4, then checked on the H7 runs: such a rise happened in 13 of
  219 trials, with no more timeouts; no change.
  v14: concurrent trials in one Harbor job all get the same base URL (Harbor's agent `env` is per job), so the
  proxy now sorts requests into runs by conversation. Its live check (2 Claude Code trials at once) was held back:
  at 23:42 the server read 0 requests for the first time since the afternoon, and the ablation gate gets that
  window first.
- 2026-11-12 00:18: the server was busy again (3 to 4 requests from others), so the held check ran: 2 Claude Code
  trials at once on one proxy URL kept separate clocks (`smoke-proxy-claude-code/2026-11-12__00-18-33`).
  Batch 4 added to the analysis plan before any of its trials: the same clock through the proxy in a second harness
  (Claude Code), hidden vs full on the 20 dev tasks, decision on the full - hidden gap; configs load in Harbor.
- 2026-11-12 01:00: v15, the responses format in the proxy; checked live with the openai SDK while the server was
  busy (3 requests from others).
- 2026-11-12 01:40: the gate has waited 15.5 h. Measured what each start rule costs (section "Quiet-start gate"):
  at most 2 other requests would have opened 197 times in 7 days (median wait 0.6 h) against 23 for the current
  rule (12.6 h); put to the user as a recommendation.
- 2026-11-12 02:10: no answer yet; the gate keeps the current rule. v16: the launcher, checked live.
- 2026-11-12 02:45: batch 4's secondary metrics are ready to compute: `proxy_report.py` (proxy runs joined to trials;
  failed matches and lateness as the analysis plan defines them), checked on the smoke jobs.
- 2026-11-12 03:20: batch 2's secondary metrics are ready too: `pilot/pilot_report.py` (outcome states, wrong
  declarations, trials stopped by time, delivery and work lateness against each trial's own budget, stops that left a
  process running, $ per qualified) and, for the report check, one blinded packet per trial that declared completion
  (the reports, then the commands and outputs, with meter lines and wrap-up notices removed so the arm does not
  show; ids random, the key kept apart). Checked on the three smoke runs: the 75 s run's delivery lateness reads
  2.0 s, as measured live.
- 2026-11-12 03:50: `ablation_report.py` reads Claude Code trials (3 of 3 smoke trials, paired gap computed), so batch
  4's primary comparison needs no new tool. Two of its columns do not apply there: "$ per solved" comes from Claude
  Code's own cost field, which prices the unknown model at Anthropic rates ($0.65 per solved on qwen3.8, meaningless),
  and "ended by time" reads the Harbor agent's stop flag; batch 4 takes trials stopped by time from
  `proxy_report.py`.
- 2026-11-12 05:50: the gate still waits (1 to 4 requests from others through the night). v18: the Harbor agent's
  deadline fix, made in the Windows copy only, so the ablation's code stays as it is. Checked live with the pilot
  settings at 90 s against the old code on the same task (3 trials each): work lateness 0.2 to 0.5 s against 2.0 to
  4.1 s. The "77.0 s on 75 s" cited earlier as evidence of the drift was corrected: it was a monotonic-clock run whose
  lateness included the saved diff. Change entry added to the analysis plan before any trial of batches 2 and 3.
- 2026-11-12 06:25: v19, the proxy lowers a tool's own timeout to the time left, so an agent ends a command still
  running at the deadline. Checked on Claude Code 2.1.322 with a scripted model (no load on the shared server):
  Harbor turns Claude Code's background tasks on, and then a timed-out command keeps running and Claude Code waits
  for it (exit at 100.8 s on a 40 s budget); with them off and a 3.5 s margin it ended at 39.0 s. Batch 4 changed
  before any of its trials: cap and margin on both proxies, background tasks off, model aliases in the configs (the
  config route for the proxy address was used live for the first time here, and Harbor sets the aliases only on
  the shell route).
- 2026-11-12 07:15: the gate still waits (2 to 4 requests from others). `proxy_report.py` counts lowered timeouts.
  Went through the plan's minimum engineering checks and handover list (p11, section above): retry timing failed
  (a failed model call counted as a turn), fixed in v20 with tests; tool failure now tested. Open handover items:
  a package release number, one page on the stop semantics, the two example trajectories (from batch 2), a real
  cost report (needs p9 or GPU-hour accounting), one list of failure modes.
- 2026-11-12 08:00: the gate still waits (3 to 4 requests from others). Handover items 3 and 8 written into the
  package README (the per-framework table brought up to v20; nine failure modes seen in the runs, where the clock
  helps, how to turn it off). Item 7, self-hosted: `server_hours.py` charges each run its share of the shared
  server's time from the vllmtop history; a solved task cost 0.16 to 0.27 server-hours, and the shown arm 0.75 to
  0.89 times the hidden arm's, the same direction as the API-price ratios.
- 2026-11-12 08:55: the gate still waits (2 to 4 requests from others). A third agent harness through the proxy:
  Harbor's Codex agent (OpenAI responses format, unchanged) on one task, wrap-up notice at 231 s of 300 s, answer at
  263 s, reward 1. The run report could not match it to its trial, because Codex sends its environment context as a
  user message before the task; v21 records every user message of a run's first request.
- 2026-11-12 13:27: the gate still waits (0 to 4 requests from others in the last hour; the longest quiet stretch
  was 8 of the 10 minutes, 12:52 to 12:59). The user: no money for hosted APIs, so p9 is not run. The user asked
  whether other users' load affects the clock: per-request speed against load measured over the whole history
  (section "Quiet-start gate"); the arms share the load, so the gate protects only the start.
- 2026-11-13 11:09: the gate opened after 49 hours of waiting (server at 0 from 10:58; 19 of the 60 minutes before
  11:23 had no requests from others). Batch 1 round 1 started: the four arms launched 11:10 to 11:13, one trial each
  side by side; at 11:25 all four were still building the first task's image (load average 24).
- 2026-11-13 11:47: round 1 check. All four arms reached the agent (8 to 10 turns each on task 009, no errors in the
  trial logs). Each arm shows what it should: I0 no budget text, I1 the budget sentence once, I2 the clock line only
  (`[Time 87 of 2400 s, 2313 s left]`), I3 the full meter (`... | last reply 31 s at 12 tok/s | about 67 turns fit`).
  Replies ran at 8 to 15 tok/s per request with four arms plus other users on the server.
- 2026-11-13 19:00: the user asked whether sharing the server with other users' runs skews the results. Since the
  start (11:10 to 19:00), 4 to 7 requests were usually running on the server (my 4 plus 0 to 4 from others), the KV
  cache reached full, and some request was queued in 2410 of 28847 seconds. TTFT stayed short (median 1.75 s, p95
  under 5 s at every load level). Per arm, from agent start to end of each finished trial:

  | Arm | Trials | Mean requests running | Seconds with any request queued, per trial | Per-request tok/s |
  |---|---|---|---|---|
  | I0 hidden | 15 | 5.5 | 124 (max 507) | 13.9 |
  | I1 once | 15 | 5.4 | 145 (max 1077) | 14.0 |
  | I2 clock | 14 | 5.3 | 148 (max 1065) | 14.0 |
  | I3 meter | 14 | 5.3 | 160 (max 1094) | 14.0 |

  The arms run at the same time, so they share the load almost equally: the comparison between arms holds, the
  absolute scores are lower than on a quiet server. The queued seconds are an upper bound on time lost (any request
  queued, not necessarily ours). Plan: report these load columns per arm and per trial with the ablation result.
- 2026-11-13 19:20: the user pointed out that the report's runs had the server to themselves (at most 4 requests, all
  from TUA-Bench), so the clock they were scored on ran under a lighter load. The meter lines the model saw confirm a
  difference: report run `harness7-time2400-attempt5/2026-10-08__15-37-09` replies at median 17 tok/s, 32 s per reply
  (90th percentile 97 s, 2176 replies); ablation arm I3 so far median 13 tok/s, 41.5 s (90th percentile 167 s, 194
  replies). A reply takes about 1.3 times as long at the median and 1.7 times at the 90th percentile, so a 2400 s
  budget holds fewer turns. The ablation's scores are therefore not comparable with the report's, and the gap between
  arms may also differ under this load. Asked the user whether to continue it as a shared-load condition or stop it.
- 2026-11-13 21:00: the user chose to finish batch 1 as a separate "shared server" condition (option A): all three
  rounds, reported with the load per arm and per trial, never compared with the report's numbers. Rule from now on
  (the user): no benchmark runs while other users share the model server. Batches 2 to 4 start only on a server
  serving TUA-Bench alone (at most 4 requests, all ours), in a window arranged with the user.
- 2026-11-14 10:53: batch 1 round 1 finished (shared server). Fully solved, of 40: I0 hidden 14, I1 once 16, I2 clock
  15, I3 meter 15; hit the 2400 s limit: 13, 17, 11, 10. No other errors. Round 2 waits for the gate.
- 2026-11-15 10:53: batch 1 round 2 finished 2026-11-15 09:35 (shared server). Fully solved, of 40: I0 hidden 15,
  I1 once 17, I2 clock 19, I3 meter 17; hit the 2400 s limit: 14, 14, 10, 8. No other errors. Over two rounds the
  meter arm hits the limit least (18 of 80, against 27 of 80 hidden). Round 3 waits for the gate.
- 2026-11-16 08:20: batch 1 round 3 finished 2026-11-16 02:18; all 3 rounds done. Round 3 fully solved, of 40: I0 17,
  I1 19, I2 17, I3 17; hit the 2400 s limit: 10, 10, 7, 8; no other errors. Loop paused at the user's request
  (machine shutdown); no new runs until the user says so.
- 2026-11-18 15:30: the user freed the server for our runs ("the server is free for you to use") and asked for the
  loop to resume. WSL harbor got v18 (`budget_meter.py`, real-time clock deadline); WSL `lite_llm.py` keeps its
  ChatGPT patch (the Windows copy lacks it; not used by qwen runs). 90 s smoke check with the WSL code started.
- 2026-11-18 15:35: batch 1 report (`ablation_report.py ... --vs I3`, shared-server condition, 3 rounds, 480 of 480
  trials, no errors). Solved of 120: I0 hidden 46, I1 once 52, I2 clock 51, I3 meter 49; gaps vs I0: +6 (-3 to +16),
  +5 (-4 to +14), +3 (-4 to +10); all inside the noise. Ended by time: 37, 41, 28, 26 of 120. $ per solved: $0.0789,
  $0.0654, $0.0721, $0.0580. On quiet trials (other users' load below 0.5; 135 of 480, an easier task mix) the arms
  are equal within 4 of about 34. Reading: under shared load no feedback level beats hidden on solved tasks; the
  clock and the meter cut time-limit endings by about a quarter to a third, and the meter has the lowest $ per
  solved. The plan's choice between levels is not decided by this batch; batch 2 keeps `full` as frozen.
- 2026-11-18 15:23: smoke check with the WSL v18 code (`swe-smoke-wall-time90/2026-11-18__15-10-09`, 3 trials, 2 of 3
  solved): work lateness 0.2 to 1.0 s, delivery lateness 1.2 to 2.1 s. Batch 2 launched (tmux `b2`, gate log
  `~/work/b2-gate.log`): hidden, full and wrap120 arms, 1 trial each, 3 rounds, on the server serving TUA-Bench alone.
- 2026-11-18 15:45: batch 2 round 1 started 15:33 (arms 15:34, 15:35, 15:36). First trial of each arm checked: hidden
  shows no budget text; full and wrap120 show the meter (`[Time 236 of 900 s, 664 s left | last reply 8.4 s at 20
  tok/s | about 13 turns fit]`); 19 to 20 tok/s, the server running only our 3 trials. Harbor fork `572e6af1`,
  `83e9be0d`: package release 0.2.0 (handover item 1) with a versions table in its README; mirrored to WSL.
- 2026-11-18 16:00: batches 3 and 4 chained after batch 2 (tmux `chain`, log `~/work/chain.log`): batch 3 starts when
  `b2-gate.log` says all 3 rounds are done, batch 4 (`run_cc_batch.sh 3`) when `b3-gate.log` does; every round still
  waits for 10 quiet minutes. One trial per arm takes about 15 to 20 minutes, so a round of 20 tasks takes about
  5 to 6 hours.
- 2026-11-18 17:00: batch 2 round 1 at 19 of 60 trials (hidden 6 of 7 qualified, full 5 of 6, wrap120 5 of 6; no
  errors; 1 stop by time per arm, delivery lateness 1.4 to 1.8 s). `pilot_report.py` runs on the new trials and its
  blinded packets carry no meter line or wrap-up notice. Plan for the report check (handover item 8): once batch 2
  ends, a fresh reviewer agent that sees only the packets (not `key.json`) marks each false verification claim; the
  key is joined afterwards.
- 2026-11-18 20:00: batch 2 round 1 finished 19:53 (60 of 60 trials, no errors, other users' load 0.04 on average:
  the server served TUA-Bench alone). Qualified, of 20: hidden 14, full 15, wrap120 16; ended by time: 8, 3, 5;
  $ per qualified $0.0291, $0.0236, $0.0223; wrong declarations 2 of 14, 4 of 17, 1 of 17; P95 delivery lateness
  1.8, 1.8, 1.5 s (target 5 s); no stop left a process running. Fix: the report scripts took the task name as the
  text before the first `__`, so every SWE-bench trial (`django__django-11099__<id>`) counted as one task "django"
  and the paired gaps used 1 task; they now cut at the last `__` (`ablation_report.py`, `plan_metrics.py` and the
  other TUA tools; `plot_budget_curve.py` has the same line and is left for the user's pending edits). With 20 tasks:
  full - hidden +1 (+0 to +3), wrap120 - hidden +2 (+0 to +5). Round 2 waits for the gate.
- 2026-11-18 21:00: handover item 5, example trajectories picked from batch 2 round 1, full arm
  (`jobs/qwen38-flash-next/swe-dev-full-time900-rounds3/2026-11-18__15-35-03/`): full success
  `django__django-11099__3TvnhFa` (reward 1, done at 603.7 s, 18 steps, the meter on every update); timeout
  `django__django-11265__sDyygtZ` (stopped by time at 900 s, 25 steps, reward 0, diff saved). Also worth showing:
  `django__django-11149__WMjJysw` and `django__django-11276__fSF3HQ4` were stopped by time and still scored 1,
  because the diff saved at the stop held a working fix. Round 2 running (4 of 20 per arm by 20:54).
- 2026-11-19 00:10: batch 2 round 2 finished 00:05 (120 of 180 trials, no errors, other users' load 0.04). After 2
  rounds, qualified of 40: hidden 28, full 32, wrap120 31; gaps vs hidden +4 (+0 to +9) and +3 (-2 to +10), 20 tasks;
  ended by time 13, 6, 10; $ per qualified $0.0272, $0.0217, $0.0215; wrong declarations 4 of 29, 6 of 34, 4 of 34.
  Lateness: P95 delivery 1.8 s (hidden), 2.1 s (full), 10.1 s (wrap120). The wrap120 value is one trial
  (`2026-11-18__20-06-49/django__django-11149__ih2xJqR`): the deadline came while a parallel Django test run was
  printing (25 worker processes); work stopped at 903.7 s (3.7 s late, the command wait was cut twice) and the
  cleanup took 6.3 s (Ctrl-C to the 25 workers, all ended, then the saved diff). It is 1 of 29 time stops in the
  batch so far; the other 28 were at most 2.1 s late. Likely cause of the 3.7 s: after the cut, the agent still reads
  the screen (`get_incremental_output`) while the tests flood it, and that output is never used because no reply
  follows. Fix to test after batch 4 (the code stays frozen until then, since batch 3's 0 s reference is batch 2):
  on a cut command wait, set the stop at once and skip the screen read; time the Ctrl-C and the diff separately.
- 2026-11-19 04:40: **batch 2 finished** 04:24 (180 of 180 trials; the server served TUA-Bench alone, other users'
  load 0.03 on average). Qualified, of 60: hidden 41, full 45, wrap120 45; gaps vs hidden +4 (-1 to +10) and +4 (-3
  to +14); wrap120 vs full +0 (-5 to +6) (20 tasks, paired bootstrap). By the frozen decision, neither gap's lower
  bound is above 0: the pilot shows no clear gain in qualified deliveries. Secondary: ended by time 19, 9, 12 of 60;
  $ per qualified $0.0254, $0.0237, $0.0208; wrong declarations 6 of 42, 11 of 51, 6 of 50 (the full arm declares
  completion more often and is wrong more often); outcome states partial 13, 13, 10 and failed 6, 2, 5; P95 delivery
  lateness 1.8, 2.1, 3.3 s (max 2.5, 2.1, 10.1 s; target 5 s at P95 met in every arm); no stop left a process
  running. Infrastructure errors (counted as failures, not dropped): 3 `AgentSetupTimeoutError` (agent setup past
  360 s) in round 3, hidden `django__django-10880`, wrap120 `django__django-10880` and `django__django-10999`. Fix:
  `ablation_report.py` skipped trials with no agent run; it now keeps them as failures, as the analysis plan's rules
  require (before the fix it showed 41 of 59 and 45 of 58). Report check: 143 blinded packets (trials that declared
  completion) split over 5 reviewer agents that see only the packets; the key is joined after their verdicts.
  Batch 3 started 04:24 (tmux `b3`, 4 arms).
- 2026-11-19 05:00: batch 2 report check (handover item 8). 143 trials declared completion; 5 reviewer agents (one
  model, no access to the key) each read about 29 blinded packets and marked false verification claims; the key was
  joined afterwards. False claims: hidden 5 of 42, full 3 of 51, wrap120 5 of 50 (13 of 143 overall). Kinds seen: a
  "confirmed pre-existing by reverting" or "failed before the change" check that the trajectory never ran (4), a
  result read from output the agent never saw because it was cut off (4), a test or count that the output does not
  show or contradicts (5). The reviewer groups differed in strictness (1 to 6 flags per about 29 packets); arms
  are mixed across groups by the random ids, so the arm comparison is fair, but single counts carry that reviewer
  noise. Reading: the clock does not raise false claims (full has the fewest); the full arm's extra wrong
  declarations (11 of 51) are not explained by false claims (3 in that arm), so most of them are reports whose
  stated checks are real while the hidden grading tests failed.
  Verdicts with arm and trial: `pilot/report-check-batch2.json`.
- 2026-11-19 05:30: batch 3 round 1 started 04:35 (4 arms, 1 trial each, server serving TUA-Bench alone). Each arm
  checked: `extra_reply_delay_sec` 5 or 20 and feedback hidden or full as configured; the meter counts the delay in
  the reply time (`last reply 30 s at 5 tok/s` at +20 s), as the design intends. 18 of 80 round-1 trials done, no
  errors.
- 2026-11-19 06:40: v22 (harbor fork, Windows copy only; WSL keeps the frozen code until batch 4 ends): when the hard
  deadline cuts a command wait, the agent stops at once and no longer reads the screen (no reply follows, so the read
  only adds lateness); the metadata now splits the cleanup into `interrupt_sec` (Ctrl-C) and `diff_sec` (saved diff).
  64 of 64 agent tests pass. Batch 3 round 1: 35 of 80 trials, no errors.
- 2026-11-19 09:20: batch 3 round 1 finished 09:18 (80 of 80 trials, no errors). Qualified, of 20: hidden +5 s 15,
  full +5 s 14, hidden +20 s 16, full +20 s 15 (batch 2's 0 s arms, 3 rounds: hidden 41 of 60, full 45 of 60).
  Ended by time 9, 8, 9, 11 of 20. The estimated other-user load over batches 2 and 3 is 0.22 on average and 48 of
  the 200 trials sit above 0.5; the estimate counts each of our trials at 0.8, so with 4 arms at once part of this is
  our own load; checked again at the end of the batch. Round 2 waits for the gate.
- 2026-11-19 10:20: load check for batch 3 round 1 (04:35 to 09:18, 16036 seconds sampled): requests running on the
  server were 0 to 4 in every second (4 in 1861 s), never more than our own 4 trials. So no other user shared the
  server; the 0.22 "other-user load" above is an error of the estimator, which assumes each of our trials keeps a
  request open 0.8 of its time (the true share varies by trial). For "quiet" use the server's own count (at most our
  trials running) rather than the estimate. Round 2 started 09:29.
- 2026-11-20 10:20: **batch 3 finished** 2026-11-19 18:47 (240 of 240 trials, no errors; the server never ran more
  requests than our own trials). Qualified, of 60 (with batch 2's 0 s arms): hidden 41 / 37 / 40 and full 45 / 41 /
  38 at 0 / +5 / +20 s. Full - hidden gap: +4 (-1 to +10) at 0 s, +4 at +5 s, -2 at +20 s; difference of gaps
  (+20 s minus 0 s) -6 per arm (-12 to +0), 20 tasks. Frozen decision: the 95% lower bound is not above 0, so "no
  evidence that the clock helps more when replies are slower"; if anything the point estimate goes the other way,
  as the natural-speed check of 2026-11-11 suggested. The delay cuts what fits: ended by time 19 / 22 / 25 (hidden)
  and 9 / 20 / 26 (full) of 60, so at +20 s the full arm loses its timeout advantage. $ per qualified falls with
  the delay (fewer turns): $0.0254 / $0.0234 / $0.0188 hidden, $0.0237 / $0.0178 / $0.0164 full. Wrong declarations
  3 of 27, 3 of 36, 3 of 30, 6 of 34 (h5, f5, h20, f20). Lateness: P95 delivery 2.9 s (h5), 9.9 s (f5), 19.5 s
  (h20), 3.3 s (f20), so the 5 s target is missed in 2 of 4 arms. All 5 trials more than 5 s late stopped during a
  parallel Django test run (26 foreground processes): work stopped 0.5 to 6.9 s late (the screen read after the cut,
  removed in v22) and the cleanup (Ctrl-C, check, saved diff) took 5.4 to 19.2 s. Next fix to test with v22's split
  timings: end the foreground process group at once (SIGKILL after one Ctrl-C) and measure Ctrl-C and diff apart.
  The "quiet trials" table of `ablation_report.py` is not usable for the delay arms (its load estimate marks all of
  them quiet and drops batch 2 trials); the server count shows every trial ran on a server serving TUA-Bench alone.
- 2026-11-20 10:10: batch 4 had waited at its gate since 2026-11-19 18:48 (15 h lost): `run_gate.sh` takes the
  metrics URL from the config's `api_base`, which the Claude Code configs do not have (they talk to the proxy), so
  it polled "/metrics" and never saw a quiet server. Fixed: `METRICS_URL` override, passed by `run_parallel.sh` and
  set by `run_cc_batch.sh` from `UPSTREAM`; the gate now exits with a message when it has no URL. The batch 4 gate
  window was restarted with the URL at 10:09 (the arm windows and proxies kept running).
- 2026-11-20 10:30: batch 4 round 1 started 10:19 (Claude Code 2.1.322 through the proxy, 2 trials per arm, 4 at
  once; the server shows 4 running requests, all ours). Arms checked in the proxy event logs: full sends the meter
  (`[Time 116 of 900 s, 784 s left | last reply 22 s at 14 tok/s | about 65 turns fit]`); hidden sends none (0 of 33
  model inputs).
- 2026-11-20 16:20: batch 4 rounds 1 and 2 finished (13:03 and 15:48; 80 of 80 trials, no errors); round 3 started
  15:59. Reward 1, of 40: hidden 23, full 29; full - hidden **+6 (+1 to +12)**, 20 tasks: the first batch whose
  lower bound is above 0 (frozen rule: "carries over to the second harness" if this holds after round 3). Proxy
  matching: 40 of 40 trials per arm matched to one run, 0 close calls. Stopped by time (proxy): hidden 27 of 40,
  full 18 of 40. (`ablation_report.py`'s "ended by time" and $ columns do not apply to Claude Code: it reads the
  Harbor agent's stop flag, and harbor prices Claude Code's calls at Anthropic list prices.)
  Two findings:
  1. **Web access leaks fixes.** The task containers have internet. Claude Code used WebFetch, WebSearch or fetched
     Django's GitHub sources in 18 of 40 (hidden) and 10 of 40 (full) trials, e.g. `raw.githubusercontent.com/
     django/django/main/django/db/migrations/loader.py` (the current file holds the upstream fix). The Harbor agent
     did it far less (batch 2: 1, 1, 3 of about 60 per arm; batch 3: 1 to 7). Sensitivity (all trials kept, a
     trial that used the web counted as unsolved): batch 4 full - hidden +10 (+2 to +18) instead of +6; batch 2
     +3 (-2 to +9) instead of +4. The batch 4 gap does not come from the leak (the hidden arm used the web more).
  2. **A WebFetch gets its own clock.** Claude Code's WebFetch sends a separate model request (summarise the page);
     the proxy's conversation tracking sees a new conversation and starts a fresh 900 s budget, and Claude Code
     waits for it. 8 of 80 trials ended 62 to 812 s after their deadline this way (e.g. hidden
     `django__django-11141__zP5DqiW`: WebFetch at 811 s, `durationMs` 900627, agent end at 1712 s). These are the
     "proxy runs without a trial" (26 and 24). Fix for the next version (not mid-batch): turn off WebFetch and
     WebSearch in Claude Code (`--disallowedTools`), which also closes the leak; and for every harness, run task
     containers without internet (the Harbor agent runs outside the container, Claude Code needs only the proxy).
- 2026-11-20 17:30: v23 (harbor, Windows copy): the stop's cleanup is one call, Ctrl-C then SIGKILL after 1 s for
  whatever still runs; 64 of 64 agent tests pass, and the shell code ended a process that ignores Ctrl-C in 1.2 s
  in a real bash. With v22 this targets both parts of the batch 3 lateness (work 0.5 to 6.9 s late, cleanup 5 to
  19 s). To check after batch 4: a smoke run whose deadline falls in a parallel Django test run.
- 2026-11-20 19:00: **batch 4 finished** 18:52 (120 of 120 trials, no errors; the server ran only our 4 trials).
  Reward 1, of 60: hidden 34, full 43; full - hidden **+9 (+2 to +17)**, 20 tasks, 4000 resamples, seed 0. Frozen
  decision: the lower bound is above 0, so the clock **carries over to the second harness** (Claude Code, unchanged,
  through the proxy). Sensitivity with every trial that used the web counted as unsolved (full 15 of 60, hidden 26
  of 60 used it): +11 (+2 to +20). Proxy: 60 of 60 trials per arm matched to one run, 0 close calls; stopped by time
  hidden 40 of 60, full 28 of 60; replies per trial, median, 18 and 14; last in-time reply, median, 791 s and 771 s;
  tool calls with a lowered timeout 131 (33 trials) and 107 (31 trials). Lateness median 0.2 s in both arms, but
  P95 457 s (hidden) and 416 s (full) from the WebFetch sub-requests that get their own clock (finding of 16:20).
  All four batches are done; the server is free of our runs.
- 2026-11-20 19:10: after batch 4, WSL harbor got v22 and v23 (`budget_meter.py`; the freeze for batches 2 to 4 is
  over). Lateness check started: `swe-latecheck-full-time900` (the batch 2 full config, 3 attempts on the 4 tasks
  whose stops ran late: django 11149, 11095, 11276, 11141; 3 trials at once; server serving TUA-Bench alone).
  Question: with v22 and v23, are stops during a parallel test run within 5 s?
- 2026-11-20 20:10: lateness check finished (`swe-latecheck-full-time900/2026-11-20__19-*`, 12 of 12 trials, no
  errors, 7 of 12 qualified): 5 stops by time, delivery 1.2 to 1.5 s late, work 0.0 to 0.2 s late; none of them fell
  in a test run (0 foreground jobs at the stop), so the bad case did not recur by chance. A scripted self-test now
  forces it: `pilot/selftest/selftest-testflood.yaml` (script `testflood`: a 26-worker Django test run with verbose
  output, waited 120 s, budget 40 s, 3 trials, no model server). Also ready: `cc-dev-{hidden,full}-noweb-
  time900-rounds3` (batch 4 configs with `disallowed_tools: "WebFetch WebSearch"`; `TAG=-noweb
  bash subset/tools/run_cc_batch.sh`), for a repeat of batch 4 without the web leak and the WebFetch clock.
- 2026-11-20 20:45: lateness during a test flood, fixed. The self-test `selftest-testflood.yaml` (26-worker Django
  test run with verbose output, 40 s budget, 3 trials per version) reproduces batch 3's late stops; delivery
  lateness by version: v23 10.0 to 13.2 s (work stopped on time, cleanup 10 to 13 s); split timing showed each
  `docker exec` takes 4 to 9 s under that load (listing 5.7 to 6.1 s, stop call 3.8 to 6.5 s); v24 (one call) 7.7
  to 10.1 s; v25 (Ctrl-C from a timer inside the container) **3.7 to 4.5 s**, within the 5 s target; work stopped
  at 40.0 to 40.1 s in every trial. The timer still fires 2.2 to 2.6 s after the deadline under that load, and
  0 or 1 process needed SIGKILL. A bug found on the way: Docker's exec merges stderr into stdout, so the kill
  markers are now read from both. 66 of 66 agent tests pass; WSL harbor has v25.
- 2026-11-20 21:30: batch 4 repeat without web tools started 20:56 (`TAG=-noweb`, tmux `cc4-noweb`, same 20 tasks, 3
  rounds, 2 trials per arm). Checked: Claude Code runs with `--disallowedTools WebFetch WebSearch`; in the first
  trials no tool call fetched a URL (no WebFetch, WebSearch, or curl/wget of http); GitHub links appear only as text
  the model wrote. This run is an added check, not part of the frozen analysis plan; it is reported next to batch 4.
- 2026-11-20 23:30: no-web repeat round 1 finished 23:23 (40 of 40 trials, no errors). Reward 1, of 20: hidden 11,
  full 14 (batch 4 round 1: 11 and 15). With WebFetch and WebSearch off the proxy problems are gone: 20 of 20
  trials per arm matched, 0 proxy runs without a trial (batch 4: 38 and 28), lateness P95 0.4 s (hidden) and 0.6 s
  (full), max 0.6 s (batch 4: 457 and 416 s). Stopped by time 12 and 9 of 20. Rounds 2 and 3 follow.
- 2026-11-21 04:50: **no-web repeat of batch 4 finished** 04:4x (120 of 120 trials, no errors; server serving only our
  trials). Claude Code with WebFetch and WebSearch off: reward 1, of 60, hidden 36, full 45; full - hidden **+9 (+4
  to +15)**, 20 tasks, 4000 resamples, seed 0 (batch 4: +9, +2 to +17). Proxy: 60 of 60 trials per arm matched, 0
  runs without a trial, 0 close calls; lateness median 0.1 and 0.2 s, P95 0.4 and 0.5 s, max 0.6 s (target 5 s
  met); stopped by time 34 vs 23 of 60; last in-time reply median 812 and 803 s; tool calls with a lowered timeout
  175 (43 trials) and 143 (40 trials). Reading: the second-harness result replicates without the web leak and with
  every stop on time; the clock gives Claude Code 9 more solved of 60 on these 20 tasks, twice in a row.
- 2026-11-21 05:00: held-out set prepared, not used. The 40 held-out pilot tasks had never been checked; the oracle
  (2 attempts) and nop checks run now (`pilot/configs/{oracle,nop}-heldout.yaml`; no model sees the tasks, so the
  set stays unspent). Batch 5 (held-out confirmation of Claude Code no-web, full vs hidden, 3 rounds, about 16 h) is
  written into the analysis plan with its decision rule and configs (`cc-heldout-{hidden,full}-noweb-
  time900-rounds3`; `SET=heldout TAG=-noweb bash subset/tools/run_cc_batch.sh`), and waits for the user's
  go-ahead: running it spends the held-out set, which is the user's call.
