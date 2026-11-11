# Professor's plan: progress log

Source: `Time-Aware_Harness_落地导向下一步工作计划.pdf` (2026-11-01, 12 pages). Work branch `time-aware-plugin` in both
repos (TUA-Bench and the Harbor fork); one commit per version. Nothing is pushed.

## Plan items and status

| Plan item (page) | What is done here | Status |
|---|---|---|
| I0-I3 feedback ablation, 40 tasks x 4 arms x 3 attempts = 480 trials (p6) | `feedback` levels in the agent (v1); 4 configs; arms run side by side, 1 trial each, so they share server conditions | Launched 2026-11-11 09:38 in tmux `abl38`; waiting for the qwen3.8 server |
| Finalize control "P" with a reserve (p4) | | Next |
| Timeliness: overrun past the deadline, P95 target 5 s (p4, p7) | | Next: measure in finished runs, then bound it in code |
| Latency intervention, +5 s and +20 s per reply (p5) | | After P |
| H1: the clock helps tasks that can be done but run out of time (p5) | | Analysis on finished runs |
| H2: feedback brings the deliverable earlier (p5) | | Analysis on finished runs |
| Paired task-level bootstrap, decision routes A and B (p7) | | Analysis on finished runs |
| Cost per qualified delivery, empty-handed timeouts (p7) | | Analysis on finished runs |
| Event log with run_id, task_id, phase, remaining budget, ... (p11) | | Later |
| Framework middleware (BudgetState, ClockFeedback, ToolObserver, FinalizeController) + LangChain adapter (p3) | | Later |
| Hosted API replication (p9) | | Needs money: ask the user |
| Business tasks and pilot (p2, p8, p11) | | Needs a partner team; public-repo technical validation is possible |
| Held-out 80 TUA tasks, full 120 (p6) | | After the configuration is locked |

## Versions

| Version | Repo | Commit | What changed |
|---|---|---|---|
| v1 | harbor | `ac7c6ba3` | `feedback` kwarg: `hidden` (I0), `once` (I1), `clock` (I2), `full` (I3, same text as the finished H7 runs, checked against a trajectory). 9 of 9 unit tests pass |
| v1 | TUA-Bench | | Ablation configs `harness0-time2400-attempt3`, `harness7-time2400-{once,clock}-attempt3`, `harness7-time2400-attempt3` (n_concurrent_trials 1 each); `tools/run_parallel.sh` + `tools/run_one.sh` |

## Runs

| Session | Arms | Started | State |
|---|---|---|---|
| `abl38` | I0 `harness0-time2400-attempt3`, I1 `harness7-time2400-once-attempt3`, I2 `harness7-time2400-clock-attempt3`, I3 `harness7-time2400-attempt3` | 2026-11-11 09:38 | Both model servers unreachable from this machine at 09:30 (`<qwen38-vllm-host>` times out, `<qwen36-vllm-host>` refuses); arms start when the qwen3.8 server answers |

## Log

- 2026-11-11: read the plan; made the branch; v1 (feedback levels) written, tested and committed; ablation launched.
