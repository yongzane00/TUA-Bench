# Run tracker: budget sweep (hidden vs shown) and other runs

Question: as a budget (time, turns, dollars) gets tighter or looser, how does the score change, and does it
matter whether the model is **told** the budget? Every budget runs in two arms, on both models:

| Arm | Config | Budget enforced | Model told |
|---|---|---|---|
| Hidden | `harness0-<budget>-attempt5`: H0 + the same stop (`show_budget: false` on H7/H8; stock `max_turns` for turns) | yes | no |
| Shown | `harness6-turns…` / `harness7-time…` / `harness8-cost…` | yes | budget sentence + meter on every update |

Same stop code, same grading; only the prompt injection differs. "Shown − hidden" is what telling the model is
worth at that budget. Plain H0 (no budget) is the right-hand end of every curve, and the hidden arm at 2400 s.

Five budgets per type and model: 0.5×, 0.75×, **1× (base)**, 1.5×, 2×, each in both arms.

| Budget type | qwen38-flash-next | qwen36-35b-a3b |
|---|---|---|
| Turns (H6 vs H0) | 20 · 30 · **40** · 60 · 80 | 20 · 30 · **40** · 60 · 80 |
| Time (H7 vs H0) | 1200 · 1800 · **2400** · 3600 · 4800 s | 1200 · 1800 · **2400** · 3600 · 4800 s |
| Cost per trial (H8 vs H0, harbor `cost_usd`) | $0.015 · $0.0225 · **$0.030** · $0.045 · $0.060 | $0.08 · $0.12 · **$0.16** · $0.24 · $0.32 |

Base: 40 turns (H6's budget), 2400 s (harbor's agent limit), each model's H0 mean `cost_usd` per trial. The shown
base runs are done already; their hidden base runs (`harness0-turns40`, `harness0-time2400`, `harness0-cost0.030` /
`0.16`) go first. At 2400 s harbor's limit ends both arms, so `harness0-time2400` is an H0 re-run on today's server
(the old H0 ran on a slower server day, which confounds the H7 comparison). Time above 2400 s sets
`override_timeout_sec` = budget + 600 in both arms. Grid and run order: `subset/tools/budget_grid.py`.

## Running it: two queues, one per model server

54 runs (27 per model), one at a time per server, both servers in parallel (started 2026-10-10 10:56).
Order (since 2026-10-10 11:15): **phase 1** = base, 0.75× and 1.5×, by type time → cost → turns (15 runs per model:
qwen38 ~12 days, to ~Oct 22; qwen36 ~9 days, to ~Oct 19); **phase 2** = 0.5× and 2×, same type order (12 runs per
model, ~8–9 more days for qwen38, ~7 for qwen36). Shown and hidden runs of one budget run back to back.
Each queue runs `subset/queue/<model>.txt` top to bottom, skipping configs that already have a finished run,
re-reading the file before each run (edit the order any time). Shown and hidden runs of one budget run back to
back so they see the same server conditions.

```
cd ~/work/TUA-Bench
tmux new -d -s q38 'bash subset/tools/run_queue.sh qwen38-flash-next 2>&1 | tee -a ~/work/qwen38-queue.log'
tmux new -d -s q36 'bash subset/tools/run_queue.sh qwen36-35b-a3b    2>&1 | tee -a ~/work/qwen36-queue.log'
```

- Status: refresh this file (command below), `/run-status`, or `tail ~/work/qwen38-queue.log`.
- Watch live: `tmux attach -t q38` (detach with Ctrl+B then D).
- Stop after the current run: `touch ~/work/STOP-qwen38-flash-next`. Stop now: Ctrl+C inside `tmux attach -t q38`.
- A crashed or interrupted run is retried once, then skipped (shows ⚠ stopped below).

Refresh the status tables:

```
wsl -e bash -lc 'python3 /mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/subset/tools/run_tracker.py'
```

Run a single config by hand (gpt55 also needs `export CHATGPT_DEFAULT_INSTRUCTIONS="You are a helpful assistant."`):

```
cd ~/work/TUA-Bench && uv run harbor run -c subset/variants/<model>/<config>.yaml   -o /mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/jobs/<model>/<config> --yes
```

Column "H0 cut (simulated)": H0's old trials re-scored as if stopped at the budget (reward kept only if the trial
had finished by then). It ignores partial credit at the cut and comes from a different server day, so it is a rough
check; the hidden arm replaces it. Token budgets are not run separately: cost is tokens × price.

## Planned, not in the queues (run by hand after the sweep, or add to a queue file)

| What | Configs | Why / note |
|---|---|---|
| H9 "All budget" | qwen38 `harness9-time2400-cost0.048-attempt5`, qwen36 `harness9-time2400-cost0.26-attempt5` | does the cost line add anything on top of the clock |
| H0 with a long limit | qwen38 `harness0-timeout12000-attempt5` | how far H0 gets with 5× the time |
| Replicate qwen38 H7 2400 s | `harness7-time2400-attempt5` (second run) | +0.094 is one run; repeat before writing it up |
| gpt-5.5 H0 and H6 40 turns | `gpt55-chatgpt/harness0-attempt5`, `harness6-turns40-attempt5` | ChatGPT plan limit (~$10 of usage per 5 h): needs per-window slices + merge; H0 attempt stopped at 16/200 |
| Extra tight points (configs exist) | `harness7-time600`, `harness6-turns10` / `15`, `harness8-cost0.048` (qwen38); `harness7-time600`, `harness8-cost0.05` / `0.10` / `0.26` (qwen36) | outside the 0.5×–2× grid; add with a matching hidden config if wanted |

## Status

<!-- status:start -->
Status as of 2026-10-21 10:52 (`python3 subset/tools/run_tracker.py` refreshes it). Cells: ✅ score · mean `cost_usd` / 🔄 trials done / ⚠ stopped / ⬜ not started.

### Queues (one run at a time per model server)

| Model | Queue process | Done | Now running | Next | Time left (rough) |
|---|---|---|---|---|---|
| qwen38-flash-next | ⬜ not running? | 7/27 | — | `harness0-time2400-attempt5-rerun` | ~382 h (15.9 days) |
| qwen36-35b-a3b | ⬜ not running? | 7/27 | — | `harness7-time1800-attempt5-rerun` | ~401 h (16.7 days) |

### Run order: qwen38-flash-next (27 runs)

| # | Config | Budget type | Arm | Budget | Status | Run |
|---|---|---|---|---|---|---|
| 1 | `harness7-time3600-attempt5` | time | shown (H7) | 3600 s | ✅ **0.571** · $0.0454 | 2026-10-14__13-51-45 |
| 2 | `harness0-time3600-attempt5` | time | hidden (H0 + cap) | 3600 s | ✅ **0.434** · $0.0542 | 2026-10-15__15-17-05 |
| 3 | `harness7-time1200-attempt5` | time | shown (H7) | 1200 s | ✅ **0.443** · $0.0183 | 2026-10-16__17-04-47 |
| 4 | `harness0-time1200-attempt5` | time | hidden (H0 + cap) | 1200 s | ✅ **0.366** · $0.0190 | 2026-10-17__12-23-16 |
| 5 | `harness7-time4800-attempt5` | time | shown (H7) | 4800 s | ⬜ |  |
| 6 | `harness0-time4800-attempt5` | time | hidden (H0 + cap) | 4800 s | ⬜ |  |
| 7 | `harness0-time2400-attempt5` | time | hidden (H0 + cap) | 2400 s | ✅ **0.459** · $0.0329 | 2026-10-10__10-56-12 |
| 8 | `harness7-time1800-attempt5` | time | shown (H7) | 1800 s | ✅ **0.467** · $0.0263 | 2026-10-11__06-00-37 |
| 9 | `harness0-time1800-attempt5` | time | hidden (H0 + cap) | 1800 s | ✅ **0.463** · $0.0265 | 2026-10-11__22-58-31 |
| 10 | `harness0-cost0.030-attempt5` | cost | hidden (H0 + cap) | $0.030 | ⬜ |  |
| 11 | `harness8-cost0.0225-attempt5` | cost | shown (H8) | $0.0225 | ⬜ |  |
| 12 | `harness0-cost0.0225-attempt5` | cost | hidden (H0 + cap) | $0.0225 | ⬜ |  |
| 13 | `harness8-cost0.045-attempt5` | cost | shown (H8) | $0.045 | ⬜ |  |
| 14 | `harness0-cost0.045-attempt5` | cost | hidden (H0 + cap) | $0.045 | ⬜ |  |
| 15 | `harness0-turns40-attempt5` | turns | hidden (H0 + cap) | 40 turns | ⬜ |  |
| 16 | `harness6-turns30-attempt5` | turns | shown (H6) | 30 turns | ⬜ |  |
| 17 | `harness0-turns30-attempt5` | turns | hidden (H0 + cap) | 30 turns | ⬜ |  |
| 18 | `harness6-turns60-attempt5` | turns | shown (H6) | 60 turns | ⬜ |  |
| 19 | `harness0-turns60-attempt5` | turns | hidden (H0 + cap) | 60 turns | ⬜ |  |
| 20 | `harness8-cost0.015-attempt5` | cost | shown (H8) | $0.015 | ⬜ |  |
| 21 | `harness0-cost0.015-attempt5` | cost | hidden (H0 + cap) | $0.015 | ⬜ |  |
| 22 | `harness8-cost0.060-attempt5` | cost | shown (H8) | $0.060 | ⬜ |  |
| 23 | `harness0-cost0.060-attempt5` | cost | hidden (H0 + cap) | $0.060 | ⬜ |  |
| 24 | `harness6-turns20-attempt5` | turns | shown (H6) | 20 turns | ⬜ |  |
| 25 | `harness0-turns20-attempt5` | turns | hidden (H0 + cap) | 20 turns | ⬜ |  |
| 26 | `harness6-turns80-attempt5` | turns | shown (H6) | 80 turns | ⬜ |  |
| 27 | `harness0-turns80-attempt5` | turns | hidden (H0 + cap) | 80 turns | ⬜ |  |

### Run order: qwen36-35b-a3b (27 runs)

| # | Config | Budget type | Arm | Budget | Status | Run |
|---|---|---|---|---|---|---|
| 1 | `harness0-time2400-attempt5` | time | hidden (H0 + cap) | 2400 s | ✅ **0.200** · $0.1439 | 2026-10-11__02-22-16 |
| 2 | `harness7-time1800-attempt5` | time | shown (H7) | 1800 s | ✅ **0.218** · $0.1112 | 2026-10-11__19-39-23 |
| 3 | `harness0-time1800-attempt5` | time | hidden (H0 + cap) | 1800 s | ✅ **0.185** · $0.1194 | 2026-10-14__15-10-17 |
| 4 | `harness7-time3600-attempt5` | time | shown (H7) | 3600 s | ✅ **0.208** · $0.2081 | 2026-10-15__09-18-16 |
| 5 | `harness0-time3600-attempt5` | time | hidden (H0 + cap) | 3600 s | ✅ **0.187** · $0.2156 | 2026-10-16__09-25-20 |
| 6 | `harness0-cost0.16-attempt5` | cost | hidden (H0 + cap) | $0.16 | ✅ **0.229** · $0.0852 | 2026-10-10__10-56-12 |
| 7 | `harness8-cost0.12-attempt5` | cost | shown (H8) | $0.12 | ⬜ |  |
| 8 | `harness0-cost0.12-attempt5` | cost | hidden (H0 + cap) | $0.12 | ⬜ |  |
| 9 | `harness8-cost0.24-attempt5` | cost | shown (H8) | $0.24 | ⬜ |  |
| 10 | `harness0-cost0.24-attempt5` | cost | hidden (H0 + cap) | $0.24 | ⬜ |  |
| 11 | `harness0-turns40-attempt5` | turns | hidden (H0 + cap) | 40 turns | ⬜ |  |
| 12 | `harness6-turns30-attempt5` | turns | shown (H6) | 30 turns | ⬜ |  |
| 13 | `harness0-turns30-attempt5` | turns | hidden (H0 + cap) | 30 turns | ⬜ |  |
| 14 | `harness6-turns60-attempt5` | turns | shown (H6) | 60 turns | ⬜ |  |
| 15 | `harness0-turns60-attempt5` | turns | hidden (H0 + cap) | 60 turns | ⬜ |  |
| 16 | `harness7-time1200-attempt5` | time | shown (H7) | 1200 s | ⬜ |  |
| 17 | `harness0-time1200-attempt5` | time | hidden (H0 + cap) | 1200 s | ⬜ |  |
| 18 | `harness7-time4800-attempt5` | time | shown (H7) | 4800 s | ✅ **0.218** · $0.2310 | 2026-10-17__12-25-49 |
| 19 | `harness0-time4800-attempt5` | time | hidden (H0 + cap) | 4800 s | ⬜ |  |
| 20 | `harness8-cost0.08-attempt5` | cost | shown (H8) | $0.08 | ⬜ |  |
| 21 | `harness0-cost0.08-attempt5` | cost | hidden (H0 + cap) | $0.08 | ⬜ |  |
| 22 | `harness8-cost0.32-attempt5` | cost | shown (H8) | $0.32 | ⬜ |  |
| 23 | `harness0-cost0.32-attempt5` | cost | hidden (H0 + cap) | $0.32 | ⬜ |  |
| 24 | `harness6-turns20-attempt5` | turns | shown (H6) | 20 turns | ⬜ |  |
| 25 | `harness0-turns20-attempt5` | turns | hidden (H0 + cap) | 20 turns | ⬜ |  |
| 26 | `harness6-turns80-attempt5` | turns | shown (H6) | 80 turns | ⬜ |  |
| 27 | `harness0-turns80-attempt5` | turns | hidden (H0 + cap) | 80 turns | ⬜ |  |

### No budget (H0, uncapped): the right-hand end of every curve

| Model | Score | Mean `cost_usd` | Run |
|---|---|---|---|
| qwen38-flash-next | 0.445 | $0.0302 | 2026-09-23__14-45-40 |
| qwen36-35b-a3b | 0.197 | $0.1585 | 2026-10-02__21-45-56 |

### Time budget (shown = H7)

| Model | Budget | Hidden: H0 + cap (model not told) | Shown: model told | Shown − hidden | H0 cut (simulated) |
|---|---|---|---|---|---|
| qwen38-flash-next | 1200 s | ✅ **0.366** · $0.0190 | ✅ **0.443** · $0.0183 | +0.077 | 0.360 |
| qwen38-flash-next | 1800 s | ✅ **0.463** · $0.0265 | ✅ **0.467** · $0.0263 | +0.004 | 0.420 |
| qwen38-flash-next | 2400 s (current) | ✅ **0.459** · $0.0329 | ✅ **0.539** · $0.0316 | +0.080 | 0.430 |
| qwen38-flash-next | 3600 s | ✅ **0.434** · $0.0542 | ✅ **0.571** · $0.0454 | +0.137 |  |
| qwen38-flash-next | 4800 s | ⬜ | ⬜ |  |  |
| qwen36-35b-a3b | 1200 s | ⬜ | ⬜ |  | 0.145 |
| qwen36-35b-a3b | 1800 s | ✅ **0.185** · $0.1194 | ✅ **0.218** · $0.1112 | +0.033 | 0.171 |
| qwen36-35b-a3b | 2400 s (current) | ✅ **0.200** · $0.1439 | ✅ **0.227** · $0.1599 | +0.028 | 0.189 |
| qwen36-35b-a3b | 3600 s | ✅ **0.187** · $0.2156 | ✅ **0.208** · $0.2081 | +0.021 |  |
| qwen36-35b-a3b | 4800 s | ⬜ | ✅ **0.218** · $0.2310 |  |  |

### Turn budget (shown = H6)

| Model | Budget | Hidden: H0 + cap (model not told) | Shown: model told | Shown − hidden | H0 cut (simulated) |
|---|---|---|---|---|---|
| qwen38-flash-next | 20 turns | ⬜ | ⬜ |  | 0.395 |
| qwen38-flash-next | 30 turns | ⬜ | ⬜ |  |  |
| qwen38-flash-next | 40 turns (current) | ⬜ | ✅ **0.476** · $0.0342 |  | 0.445 |
| qwen38-flash-next | 60 turns | ⬜ | ⬜ |  |  |
| qwen38-flash-next | 80 turns | ⬜ | ⬜ |  |  |
| qwen36-35b-a3b | 20 turns | ⬜ | ⬜ |  | 0.088 |
| qwen36-35b-a3b | 30 turns | ⬜ | ⬜ |  | 0.113 |
| qwen36-35b-a3b | 40 turns (current) | ⬜ | ✅ **0.174** · $0.0389 |  | 0.125 |
| qwen36-35b-a3b | 60 turns | ⬜ | ⬜ |  | 0.158 |
| qwen36-35b-a3b | 80 turns | ⬜ | ⬜ |  |  |

### Cost budget (shown = H8, harbor `cost_usd`)

| Model | Budget | Hidden: H0 + cap (model not told) | Shown: model told | Shown − hidden | H0 cut (simulated) |
|---|---|---|---|---|---|
| qwen38-flash-next | $0.015 | ⬜ | ⬜ |  | 0.265 |
| qwen38-flash-next | $0.0225 | ⬜ | ⬜ |  |  |
| qwen38-flash-next | $0.030 (current) | ⬜ | ✅ **0.401** · $0.0178 |  | 0.359 |
| qwen38-flash-next | $0.045 | ⬜ | ⬜ |  |  |
| qwen38-flash-next | $0.060 | ⬜ | ⬜ |  |  |
| qwen36-35b-a3b | $0.08 | ⬜ | ⬜ |  |  |
| qwen36-35b-a3b | $0.12 | ⬜ | ⬜ |  |  |
| qwen36-35b-a3b | $0.16 (current) | ✅ **0.229** · $0.0852 | ✅ **0.229** · $0.0776 | -0.000 | 0.164 |
| qwen36-35b-a3b | $0.24 | ⬜ | ⬜ |  |  |
| qwen36-35b-a3b | $0.32 | ⬜ | ⬜ |  |  |

Budgets are 0.5×, 0.75×, 1× (current), 1.5×, 2× the base. At 2400 s harbor's own limit ends both arms, so the hidden 2400 s run is an H0 re-run on today's server.

### Other (not in the queues)

| Model | Config | What | Status | Run |
|---|---|---|---|---|
| qwen38-flash-next | `harness9-time2400-cost0.048-attempt5` | H9, 2400 s + $0.048 | ⬜ |  |
| qwen36-35b-a3b | `harness9-time2400-cost0.26-attempt5` | H9, 2400 s + $0.26 | ⬜ |  |
| qwen38-flash-next | `harness0-timeout12000-attempt5` | H0, 12000 s limit | ⬜ |  |
| gpt55-chatgpt | `test` | gpt-5.5, 3 tasks × 1 | ⬜ |  |
| gpt55-chatgpt | `harness0-attempt5` | gpt-5.5 H0 | ⚠ stopped 16/200 | 2026-10-09__14-14-20 |
| gpt55-chatgpt | `harness6-turns40-attempt5` | gpt-5.5 H6, 40 turns | ⬜ |  |
<!-- status:end -->
