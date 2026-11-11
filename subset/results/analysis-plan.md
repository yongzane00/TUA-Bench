# Analysis plan, frozen before the runs

The plan (p1, p7) asks that budgets, sample sizes and thresholds be fixed before the experiments and not adjusted to
the results. This file fixes them for the two batches below. It was committed before any trial of either batch ran;
the git commit time is the record. Changes after that are listed at the end with their reason and date.

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
| Budget | 900 s on the real-time clock, hard deadline, `git diff` saved at the stop |
| Size | 3 rounds of 20 tasks per arm (60 trials per arm), arms side by side, quiet-start rounds; run after batch 1 |
| Primary metric | Qualified deliveries: reward 1, x of 60 |
| Outcome states | Qualified (reward 1); partial (reward below 1, non-empty saved diff); failed (empty diff or an error) |
| Secondary | $ per qualified delivery; wrong declarations (declared complete, not qualified); lateness past the deadline on the real-time clock, P95 |
| Comparison | Same paired bootstrap over the 20 tasks |

**Decision (the plan's week-4 gate).** The wrap-up arm is kept only if (a) its qualified gap against the full arm
has a lower bound above -3 of 60, (b) it does not have more wrong declarations than the full arm, and (c) its point
estimate is not below the full arm's. Otherwise the full arm stays the default and the wrap-up notice stays off.
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

## Rules for all batches

- No trial is dropped after the fact. A trial with an infrastructure error counts as a failure (missing reward = 0,
  as Harbor's Mean does) and is listed by its error type.
- A round that does not finish is run again as a whole round; single failed trials are not re-run.
- Results are reported as counts (x of n) with the interval; an interval that spans both a clear gain and a clear
  loss is reported as "uncertain".
- The held-out pilot tasks (40) and the other 80 TUA tasks are not used until the configuration is locked.
- Batches share the server one at a time, in the order 1, 2, 3; two batches never run at once.

## Changes after the freeze

- 2026-11-11, before any trial of it: batch 3 (latency intervention) added. Batches 1 and 2 are unchanged.
