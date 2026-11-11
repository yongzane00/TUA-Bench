# Professor's plan: progress log

Source: `Time-Aware_Harness_落地导向下一步工作计划.pdf` (2026-11-01, 12 pages). Work branch `time-aware-plugin` in both
repos (TUA-Bench and the Harbor fork); one commit per version. Nothing is pushed.

## Plan items and status

| Plan item (page) | What is done here | Status |
|---|---|---|
| I0-I3 feedback ablation, 40 tasks x 4 arms x 3 attempts = 480 trials (p6); frozen analysis plan with rounds 4-5 | `feedback` levels in the agent (v1); 4 configs; arms run side by side, 1 trial each; 3 rounds, each started only when the server is quiet | Waiting for a quiet server (tmux `abl38`, gate log `~/work/abl38-gate.log`) |
| Finalize control "P" with a reserve (p4) | `finalize_reserve_sec` (v2): one wrap-up notice when time left <= recent turn length + reserve | Code and tests done; run after the ablation |
| Timeliness: overrun past the deadline, P95 target 5 s (p4, p7) | Measured in finished runs (below); `hard_deadline` (v2) cancels a running reply and cuts command waits | Live check passed: 75 s budget, stopped at 77.0 s with 1 reply cut (smoke run `swe-smoke-wrap30-time75`) |
| Latency intervention, +5 s and +20 s per reply (p5) | `extra_reply_delay_sec` (v2) | Code and tests done; run after P |
| H1: the clock helps tasks that can be done but run out of time (p5) | Classes from other base runs; gap by class (below) | First result: supported at 2400 s |
| H2: feedback brings the deliverable earlier (p5) | First `mark_task_complete` time from trajectories | Not supported: the clock delays the first "done" and adds more just before the deadline (below) |
| Paired task-level bootstrap, decision routes A and B (p7) | `subset/tools/plan_metrics.py` | Done for both models |
| Cost per qualified delivery, empty-handed timeouts (p7) | same | Done for both models |
| Week-1 items for the next group meeting (p11): task contract, 10 reproducible tasks, data split, budget and logging spec, first configs | `pilot/README.md` (contract, budget, logging), `pilot/tasks.md` (split), `pilot/configs/oracle-week1.yaml` | Contract, split, spec and configs written; oracle check of the 10 tasks running (tmux `pilot`) |
| Event log with run_id, task_id, phase, remaining budget, ... (p11) | `subset/tools/event_log.py`: one JSON line per model call, command batch, stop and grading | Done; tested on a pilot smoke trial and a TUA trial |
| Framework middleware + LangChain adapter (p3) | harbor `packages/time-budget`: framework-free core (state, forecast, texts equal to the Harbor agent's) and `TimeBudgetMiddleware` for LangChain 1.4 (state per run in the agent state, meter per call outside the history, tool timing, stop, async hard deadline) | Done; 11 of 11 tests in a real `create_agent` loop; not yet used on a live model |
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

## Ideas to test (new, beyond the plan)

1. **Effort that follows the clock.** About four fifths of the time goes to waiting for the model. Near the
   deadline the harness lowers `reasoning_effort` instead of only telling the model (v4, `late_effort`). This
   changes the inference, not the prompt, so it also works in the hidden arm. Checked first that the server
   honours it: the same coding question used 88 and 90 reasoning tokens at `low` vs 241 and 236 at `xhigh` (14 to
   16 s vs 25 s per reply). To run as its own arm after the wrap-up comparison.
2. **Natural latency experiment.** Server load changes the model's speed from trial to trial. Tagging each trial
   with its measured tokens per second (from the agent's own request times) and the vllmtop load gives a free
   dose-response check of H1 before paying for injected delays.
3. **Turn-length forecast by command type** (plan p4): keep durations per command class (install, build, test,
   GUI action) instead of the mean of the last 3 turns.

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
| v6 | TUA-Bench | `f5f9c4f`, `011bc36` | `pilot/excluded.md` and rule 6; new split; first pilot batch configs (`swe-dev-{hidden,full,wrap120}-time900-rounds3`: 900 s, real-time clock, hard deadline, saved diff) |
| v3 | TUA-Bench | `367a9e6` | `pilot/`: task contract, budget and logging spec, 20 + 40 Django task split, oracle config; H2 counts by time; `pilot/**` added to the redact filter in `.gitattributes` |

## Runs

| Session | Arms | State |
|---|---|---|
| `abl38` (first launch) | `-attempt3` configs | Started 09:40, stopped 09:53 on 2026-11-11 because the server was busy; the four partial job folders under `jobs/qwen38-flash-next/*-attempt3/` are left as they are and are not used |
| `abl38` | I0 `harness0-time2400-rounds3`, I1 `harness7-time2400-once-rounds3`, I2 `harness7-time2400-clock-rounds3`, I3 `harness7-time2400-rounds3`; 3 rounds of 40 trials per arm | Waiting since 2026-11-11 09:58 for 10 quiet minutes (3 requests from others running) |

## Log

- 2026-11-11: read the plan; made the branch; v1 and v2 written, tested and committed; delivery metrics, timeliness
  and H1 computed for qwen3.8; ablation set up as quiet-start rounds. qwen3.6 metrics, H2, speed check; pilot
  folder with the week-1 items; oracle check started (no model calls). Smoke trials confirmed the hard deadline
  and diff saving live; nop check added after a task passed with no change; late-effort setting added (v4). The
  qwen3.8 server had 2 to 4 requests from other users running all morning, so ablation round 1 has not started.
  Later: nop check done, two broken tasks excluded and replaced; clock drift measured and `clock: wall` added (v5);
  event log converter; pilot batch configs ready. Run order on the server: ablation first (plan week 3), then the
  pilot batch (week 4), each in quiet-start rounds, never both at once.
