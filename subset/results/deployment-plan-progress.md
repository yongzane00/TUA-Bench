# Professor's plan: progress log

Source: `Time-Aware_Harness_落地导向下一步工作计划.pdf` (2026-11-01, 12 pages). Work branch `time-aware-plugin` in both
repos (TUA-Bench and the Harbor fork); one commit per version. Nothing is pushed.

## Plan items and status

| Plan item (page) | What is done here | Status |
|---|---|---|
| I0-I3 feedback ablation, 40 tasks x 4 arms x 3 attempts = 480 trials (p6); frozen analysis plan with rounds 4-5 | `feedback` levels in the agent (v1); 4 configs; arms run side by side, 1 trial each; 3 rounds, each started only when the server is quiet | Waiting for a quiet server (tmux `abl38`, gate log `~/work/abl38-gate.log`) |
| Finalize control "P" with a reserve (p4) | `finalize_reserve_sec` (v2): one wrap-up notice when time left <= recent turn length + reserve | Code and tests done; run after the ablation |
| Timeliness: overrun past the deadline, P95 target 5 s (p4, p7) | Measured in finished runs (below); `hard_deadline` (v2) cancels a running reply and cuts command waits | Live check passed: 75 s budget, stopped at 77.0 s with 1 reply cut (smoke run `swe-smoke-wrap30-time75`) |
| Latency intervention, +5 s and +20 s per reply (p5) | `extra_reply_delay_sec` (v2); 4 configs `swe-dev-{hidden,full}-delay{5,20}-time900-rounds3` (the pilot configs plus the delay); batch 3 in the frozen analysis plan with its decision rule; `ablation_report.py --did` for the change in the gap | Ready; runs after the pilot batch (batch 2), whose hidden and full arms are the 0 s reference |
| H1: the clock helps tasks that can be done but run out of time (p5) | Classes from other base runs; gap by class (below) | First result: supported at 2400 s |
| H2: feedback brings the deliverable earlier (p5) | First `mark_task_complete` time from trajectories | Not supported: the clock delays the first "done" and adds more just before the deadline (below) |
| Paired task-level bootstrap, decision routes A and B (p7) | `subset/tools/plan_metrics.py` | Done for both models |
| Cost per qualified delivery, empty-handed timeouts (p7) | same | Done for both models |
| Week-1 items for the next group meeting (p11): task contract, 10 reproducible tasks, data split, budget and logging spec, first configs | `pilot/README.md` (contract, budget, logging), `pilot/tasks.md` (split), `pilot/configs/oracle-week1.yaml` | Contract, split, spec and configs written; oracle check of the 10 tasks running (tmux `pilot`) |
| Event log with run_id, task_id, phase, remaining budget, ... (p11) | `subset/tools/event_log.py`: one JSON line per model call, command batch, stop and grading | Done; tested on a pilot smoke trial and a TUA trial |
| Framework middleware + LangChain adapter (p3) | harbor `packages/time-budget`: framework-free core (state, forecast, texts equal to the Harbor agent's) and `TimeBudgetMiddleware` for LangChain 1.4 (state per run in the agent state, meter per call outside the history, tool timing, stop, async hard deadline) | Done; 11 of 11 tests in a real `create_agent` loop; live check on qwen3.8 passed (wrap-up notice, cut at 20.0 s; the server drops a cancelled reply within 0.5 s). Since v12 also a proxy for agents that cannot be changed: stock terminus-2 in Harbor ran through it with no code change (reward 1 at 300 s and at 90 s, cut at 90.0 s) |
| Second harness (p3; the user's goal of one plugin for every harness) | Batch 4 in the frozen analysis plan: Harbor's claude-code agent (unchanged, version pinned) through the proxy, hidden vs full, 20 dev tasks x 3 rounds; configs `cc-dev-{hidden,full}-time900-rounds3`, launcher `subset/tools/run_cc_batch.sh`; checked live on 1 task (1 trial, and 2 at once on one URL) | Ready; runs after batch 3 |
| Hosted API replication (p9) | | Needs money: ask the user |
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

Since v13 the proxy also edits the Anthropic messages format (`/v1/messages`), so Claude Code and other Anthropic
clients take it through `ANTHROPIC_BASE_URL`; vLLM serves that format too. Claude Code runs inside the task
container: with Docker Desktop the container reaches a proxy on WSL's 127.0.0.1 as `host.docker.internal`, but not
at the WSL eth0 address. The first attempt used that address, and Claude Code retried with no answer until it was
stopped (`smoke-proxy-claude-code/2026-11-11__22-49-37`, not used).

**After the wrap-up notice the model kept working.** In the Claude Code run the notice went out at 193 s; the
model then sent 7 more replies (the last one cut at the deadline). The turn forecast swung with them: "about 1 turn fit" at 205 s and 212 s, then
"about 9 turns fit" at 219 s, after three short turns (7 to 11 s) pulled the 3-turn mean down. A model reading
"9 turns fit" right after a wrap-up notice gets mixed signals. Idea 4 below.

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

**The Harbor agent has the same clock problem (to fix before pilot batch 2).** `budget_meter.py:457` cuts a reply
with `asyncio.wait_for(..., timeout=left)`, so with `clock: wall` the cut is late by the drift: up to about 8 of
every 100 s still left when the reply started. The earlier live checks fit this (77.0 s on a 75 s budget; 21.7 s on
20 s). The ablation arms do not use the hard deadline, but they import this file, so it stays unchanged until the
ablation ends. Then the same slicing goes in (as part of moving the agent onto the shared core), with a change entry
in the analysis plan, before the pilot batch, whose lateness target (P95 within 5 s) depends on it.

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
