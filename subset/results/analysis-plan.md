# Analysis plan, frozen before the runs

The plan (p1, p7) asks that budgets, sample sizes and thresholds be fixed before the experiments and not adjusted to
the results. This file fixes them for batches 1 and 2 below. It was committed before any trial of either batch ran;
the git commit time is the record. Changes after that, including batches 3 and 4 (each added before any of its
trials), are listed at the end with their reason and date.

## Batch 1: feedback ablation (TUA-Bench, plan p6)

| Item | Fixed value |
|---|---|
| Model, server | qwen3.8-flash-next on the qwen3.8 vLLM server |
| Tasks | The 40-task TUA subset (`subset/baseline.yaml`) |
| Arms | I0 `harness0-time2400-rounds3` (hidden, same stop), I1 `harness7-time2400-once-rounds3`, I2 `harness7-time2400-clock-rounds3`, I3 `harness7-time2400-rounds3` (full meter) |
| Budget | 2400 s, monotonic clock (as every earlier TUA run) |
| Size | 3 rounds; each round runs all 40 tasks once per arm, the four arms side by side at one trial each; a round starts only after 10 minutes with no requests from other users |
| Primary metric | Solved trials (reward 1), x of 120 per arm |
| Secondary | Mean reward (Harbor Mean), $ per solved trial, trials ended by time and how many scored 0, first declaration of completion |
| Comparison | Each arm against I0, and I1, I2 against I3: paired bootstrap over the 40 tasks (attempts stay with their task), 4000 resamples, seed 0, 95% interval (`subset/tools/ablation_report.py`) |
| Sensitivity | The same comparison on trials with other users' server load below 0.5 (vllmtop history) |

**Decision (the plan's week-3 gate: pick the simplest feedback that works).** An arm "works" when its gap against I0
has a 95% lower bound above 0. Take the simplest working arm (once, then clock, then full) whose gap against I3 has a
lower bound above -4 of 120 (the plan's -3 points). If no arm works, keep I3 for the next steps, because it is the
level validated in the earlier 5-attempt runs (+12 of 200 at 2400 s, interval +0 to +24), and report the ablation as
"uncertain", as the plan prescribes (p7).

**Expected precision.** Resampling 3 of the 5 attempts per task from the finished 2400 s runs gives an interval of
about ±9 of 120 for I3 against I0, whose effect there is about +7 of 120; the interval excluded 0 in 40 of 200
resamples. So "uncertain" is the most likely outcome for I1 and I2 unless their effects are large. Five rounds would
give about ±12 of 200 (the finished runs' interval). Extending to 5 rounds is decided here, in advance: rounds 4 and
5 run if the server allows within two weeks of round 3, whatever rounds 1 to 3 show, and the decision then uses all
rounds.

## Batch 2: code-repair pilot, first batch (plan p6 "wrap-up policy", week 4)

| Item | Fixed value |
|---|---|
| Tasks | The 20 dev tasks in `pilot/tasks.md` (all checked: reference fix scores 1, no change scores 0) |
| Arms | `swe-dev-hidden-time900-rounds3`, `swe-dev-full-time900-rounds3`, `swe-dev-wrap120-time900-rounds3` |
| Budget | 900 s on the real-time clock, hard deadline, `git diff` saved at the stop, Ctrl-C to a command still running at the stop (`interrupt_at_stop`) |
| Size | 3 rounds of 20 tasks per arm (60 trials per arm), arms side by side, quiet-start rounds; run after batch 1 |
| Primary metric | Qualified deliveries: reward 1, x of 60 |
| Outcome states | Qualified (reward 1); partial (reward below 1, non-empty saved diff); failed (empty diff or an error) |
| Secondary | $ per qualified delivery; wrong declarations (declared complete, not qualified); lateness past the deadline on the real-time clock, P95, in two forms: delivery lateness `elapsed_sec` - 900 (work stopped, terminal cleaned, diff saved) and work lateness `stopped_at_sec` - 900; trials whose stop left a foreground process running (`stop_interrupt.stopped` false); false verification claims (below) |
| Report check | Every trial that declared completion ends with a report (`report_request`: checks run and their results, what changed, what is unverified). A reviewer who does not see the arm compares the report with the commands and outputs in the trajectory; a **false verification claim** is a report that states a check the trajectory does not show (a test never run, or a failure reported as a pass). Passing its own tests while the hidden grading tests fail is not a false claim. Counted per arm, x of the trials that declared completion |
| Comparison | Same paired bootstrap over the 20 tasks |

**Decision (the plan's week-4 gate).** The wrap-up arm is kept only if (a) its qualified gap against the full arm
has a lower bound above -3 of 60, (b) it does not have more wrong declarations than the full arm, and (c) its point
estimate is not below the full arm's, and (d) it does not have more false verification claims than the full arm (the
plan's week-4 condition: P must not add false success reports or missing checks). Otherwise the full arm stays the
default and the wrap-up notice stays off.
Timeliness target: P95 lateness at most 5 s in every arm.

## Batch 3: latency intervention (plan p5, p6 "延迟机制"), added 2026-11-11 before any of its trials

| Item | Fixed value |
|---|---|
| Tasks | The same 20 dev tasks as batch 2 |
| Arms | `swe-dev-hidden-delay5-time900-rounds3`, `swe-dev-full-delay5-time900-rounds3`, `swe-dev-hidden-delay20-time900-rounds3`, `swe-dev-full-delay20-time900-rounds3`: batch 2's hidden and full configs plus `extra_reply_delay_sec` 5 or 20 (a wait after every model reply, counted in the budget and cut by the hard deadline). The 0 s reference is batch 2's hidden and full arms, which differ only in the delay (the plan allows reusing results with an identical configuration) |
| Budget | 900 s on the real-time clock, hard deadline, `git diff` saved at the stop |
| Size | 3 rounds of 20 tasks per arm (60 trials per arm, 240 in all), the four arms side by side, quiet-start rounds; run after batch 2 |
| Primary metric | Qualified deliveries (reward 1), x of 60 |
| Comparison | Shown - hidden gap at 0, 5 and 20 s, paired bootstrap over the 20 tasks; the change in the gap from 0 s to 20 s (and to 5 s), bootstrapped with all of a task's trials in the six arms kept together; 4000 resamples, seed 0 |
| Secondary | Turns per trial, wrong declarations, P95 lateness, trials ended by time with an empty diff |

**Decision (plan H1, dose form).** The clock's value grows with reply latency if the 20 s gap minus the 0 s gap has a
95% lower bound above 0. If the interval includes 0, the result is "no evidence that the clock helps more when
replies are slower", and the claim is narrowed as the plan prescribes; if it spans both a clear gain and a clear loss
(beyond +-6 of 60), it is reported as "uncertain". The natural-speed check on the finished TUA runs (progress log,
2026-11-11) found no dose-response within +-10% speed, so a null here is the expected outcome unless the effect
appears only at larger delays. The shown arm stays `full` even if batch 1 picks a simpler level, so that the 0 s
reference from batch 2 stays valid.

## Batch 4: second harness through the budget proxy (plan p3), added 2026-11-12 before any of its trials

The method was tested in one harness (terminus-2). Batch 4 asks whether the same clock, given to an unchanged
agent through the proxy (`time_budget.proxy`, harbor fork `5bae9619`), shows the same direction in a second one.

| Item | Fixed value |
|---|---|
| Tasks | The same 20 dev tasks as batch 2 |
| Agent | Harbor's `claude-code` agent, version 2.1.322 pinned, no code change; model qwen3.8-flash-next behind the proxy (Anthropic messages format) |
| Arms | `cc-dev-hidden-time900-rounds3` (proxy `--feedback hidden`: nothing shown, same stop) and `cc-dev-full-time900-rounds3` (`--feedback full`: budget sentence and meter line); both with `--report-request` (the same report request in both arms) and no wrap-up notice |
| Budget | 900 s per trial on the wall clock, from the trial's first model request (Claude Code's install is outside it); a reply still running at 900 s is cut and replaced by the stop reply; later requests get HTTP 400. Every Bash call reaches Claude Code with its timeout no longer than the time left minus 3.5 s (`--cap-tool-timeout Bash:timeout:ms:120000 --cap-margin 3.5`; the model's own value is restored in later requests), and `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` makes Claude Code end a command at its timeout instead of moving it to the background, so a command running at the deadline is ended by Claude Code itself (both arms; added 2026-11-12, see the changes below) |
| Size | 3 rounds of 20 tasks per arm (60 trials per arm, 120 in all), the two arms side by side with 2 trials each (4 at once; the proxy keeps one clock per conversation), quiet-start rounds (`subset/tools/run_cc_batch.sh`); run after batch 3 |
| Primary metric | Qualified deliveries (reward 1), x of 60 per arm |
| Comparison | Full - hidden gap, paired bootstrap over the 20 tasks, 4000 resamples, seed 0. Shown next to batch 2's full - hidden gap on the same tasks; the two gaps are not tested against each other (too few tasks) |
| Secondary | Lateness: Claude Code's end minus the deadline, P95 per arm; trials stopped by the deadline; Bash calls whose timeout was lowered (`tool_capped` events); replies per trial; time of the final answer; failed proxy matches (a trial's requests split over two runs or two trials in one run, from the proxy event log against the trial logs) |

**Decision.** The clock "carries over to the second harness" if the full - hidden gap has a 95% lower bound above
0; "does no harm there" if the lower bound is above -3 of 60; otherwise "uncertain" (an interval beyond +-6 of 60 on
both sides) or "hurts" (upper bound below 0). A run with any failed proxy match is reported with its count, and the
affected trials are listed; they are not dropped.

## Batch 5 (proposed 2026-11-21, not started; waits for the user's go-ahead): held-out confirmation

The dev results (batch 4 and its no-web repeat) chose one configuration: Claude Code through the proxy with
`--feedback full`, WebFetch and WebSearch off. Batch 5 runs it once on the held-out tasks, which no run has used.

| Item | Fixed value |
|---|---|
| Tasks | The 40 held-out tasks in `pilot/tasks.md` (2022-01-27 to 2023-07-17), minus any that fail the oracle / nop check (`pilot/configs/{oracle,nop}-heldout.yaml`, done before this batch); excluded tasks are listed, not replaced |
| Arms | `cc-heldout-hidden-noweb-time900-rounds3`, `cc-heldout-full-noweb-time900-rounds3` (the no-web dev configs with the held-out task list) |
| Budget | 900 s, as batch 4 |
| Size | 3 rounds per arm, 2 trials per arm at once (4 at once), quiet-start rounds; about 16 h on a server serving TUA-Bench alone |
| Primary metric | Reward 1, x of (tasks x 3) per arm |
| Comparison | Full - hidden gap, paired bootstrap over tasks, 4000 resamples, seed 0 |
| Secondary | As batch 4 (lateness, stopped by time, replies, lowered tool timeouts, proxy matching) |

**Decision.** The dev result "holds on held-out tasks" if the gap's 95% lower bound is above 0; "no harm" if it is
above -3 per 60 trials (scaled to the task count); otherwise "uncertain" or "hurts" as in batch 4. Whatever the
result, the held-out set is then spent: no further tuning is reported on it.

## Rules for all batches

- No trial is dropped after the fact. A trial with an infrastructure error counts as a failure (missing reward = 0,
  as Harbor's Mean does) and is listed by its error type.
- A round that does not finish is run again as a whole round; single failed trials are not re-run.
- Results are reported as counts (x of n) with the interval; an interval that spans both a clear gain and a clear
  loss is reported as "uncertain".
- The held-out pilot tasks (40) and the other 80 TUA tasks are not used until the configuration is locked.
- Batches share the server one at a time, in the order 1, 2, 3, 4; two batches never run at once.

## Changes after the freeze

- 2026-11-11, before any trial of it: batch 3 (latency intervention) added. Batches 1 and 2 are unchanged.
- 2026-11-11, before any trial of batches 2 and 3: `interrupt_at_stop: true` added to all seven pilot configs, the same
  in every arm (plan p4: at the deadline, cancel local processes and check they exited; p11: long tool cancellation).
  Without it a command cut by the hard deadline kept running while the verifier graded. Lateness is defined in two
  forms (batch 2, Secondary). Batch 1 is unchanged.
- 2026-11-11, before any trial of batches 2 and 3: `report_request: true` added to all seven pilot configs, the same in
  every arm. The task text now asks for the contract's report (plan p2: tests run and their real results, a short fix
  note, what is unverified), which the SWE-bench task text does not contain. Added the report check and condition
  (d) to batch 2, from the plan's week-4 condition (p8). Batch 1 is unchanged.
- 2026-11-12, before any trial of it: batch 4 (second harness through the budget proxy) added. Batches 1 to 3 are
  unchanged.
- 2026-11-12, before any trial of batches 2 and 3: the hard deadline now waits for a model reply or a command on the
  budget's own real-time clock, re-read every 0.5 s (Harbor fork `63217a11`). Before, one asyncio timeout counted
  the event loop's clock, which runs slow under WSL, so cuts came late: on a 90 s smoke task, work lateness 2.0 to
  4.1 s before and 0.2 to 0.5 s after (3 trials each). The configs do not change, and every arm of batches 2 and 3
  runs the new code. Batch 1 does not use the hard deadline and runs on the earlier code: the copy of the agent it
  imports is updated only after it ends.
- 2026-11-12, before any trial of batch 4, the same in both arms: (1) the proxies lower each Bash call's timeout to
  the time left minus 3.5 s, and (2) `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` is set, because Harbor turns Claude Code's
  background tasks on and a timed-out command is then moved to the background and keeps running. Scripted-model
  self-tests (`pilot/selftest/selftest-cc-timeout*.yaml`, 40 s budget, one 90 s command): without (2) the command
  ran all 90 s, Claude Code waited for it and then exited with an error at 100.8 s; with (2) the command was ended at
  its timeout and Claude Code exited cleanly at 46.5 s, and with the 3.5 s margin at 39.0 s. The earlier text
  expected batch 4's lateness to exceed batch 2's because the proxy could not stop a running command; that no longer
  holds. (3) The model aliases (`ANTHROPIC_DEFAULT_{SONNET,OPUS,HAIKU}_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL`) are set to
  qwen3.8 in the configs' env: Harbor sets them only when the proxy address comes from the shell environment, which
  the smoke runs used, and not when it comes from the config, which the batch uses. Batches 1 to 3 are unchanged.
- 2026-11-12, before any trial of batch 4: a model request that fails (an HTTP error from the server) no longer
  counts as a turn in the proxy's meter; its time goes into the turn of the agent's retry (harbor fork `bb0307c9`).
  Before, a retry made the turns that fit read too high in the full arm. Batches 1 to 3 do not use the proxy.
