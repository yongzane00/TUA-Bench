# Code-repair pilot: technical check on public tasks

The plan's first pilot (p2) is an in-house code-repair assistant that must deliver a reviewable patch within 15
minutes. There is no partner team yet, so this folder runs the technical check the plan allows first: fixed-version
public tasks, reported separately from any business tasks. A result here shows the mechanism works on real code
fixes; it does not show business value.

## The five items for the group meeting (plan p12)

| Item | Where | State (2026-11-11) |
|---|---|---|
| One-page task contract | [Task contract](#task-contract) below | Written |
| 10 reproducible tasks | [`reproducibility.md`](reproducibility.md) | All 20 dev tasks reproduce (reference fix scores 1, no change scores 0); 2 candidates failed and are excluded ([`excluded.md`](excluded.md)) |
| Data split | [`tasks.md`](tasks.md) | 20 dev + 40 held-out Django tasks by a fixed rule ([`select_tasks.py`](select_tasks.py)); held-out tasks are later tickets and are not used until the configuration is locked |
| Budget and logging spec | [Budget and timing](#budget-and-timing), [Logging spec](#logging-spec) below | Written; every gap in the first version is closed except exit codes |
| First experiment configs | `subset/variants/qwen38-flash-next/swe-dev-*-rounds3.yaml`; decision rules in `subset/results/analysis-plan.md` (frozen before any trial) | Ready; run after the TUA feedback ablation |

## Files

| File | What it is |
|---|---|
| `README.md` | This page: task contract, budget and timing rules, logging spec |
| [`tasks.md`](tasks.md), [`select_tasks.py`](select_tasks.py) | The data split and the rule that produced it |
| [`reproducibility.md`](reproducibility.md), [`excluded.md`](excluded.md), [`check_tasks.py`](check_tasks.py) | Reproducibility check of every dev task and the tasks it excluded |
| [`configs/`](configs/) | Checks without a model: `oracle-week1.yaml`, `oracle-dev-rest.yaml`, `check-dev-added.yaml` (reference fix), `nop-dev.yaml` (no change) |
| [`selftest/`](selftest/) | Harness checks with a scripted model, no model server: the stop and its cleanup (`selftest-interrupt.yaml`), plugin off = stock agent and separate clocks for concurrent trials (`selftest-baseline.yaml`, `compare_prompts.py`) |

## Task contract

| Item | Agreement |
|---|---|
| User and pain point | On-call or maintenance engineer. Small fixes with a clear report, where agents tend to time out while exploring. Here: public Django tickets from SWE-bench Verified |
| Input | The repo at a fixed commit (the task's Docker image), the issue text, the test environment, a 900 s deadline. As in SWE-bench, the agent is not told which tests grade it; the plan's "reproduce command" is therefore not given |
| Scope | One repo (django/django); SWE-bench difficulty "<15 min fix" or "15 min - 1 hour"; the reference fix changes one source file. Each attempt runs in its own container |
| Must deliver | The code change in the working tree at the deadline. Asked for in the task text: the tests run and their real results, a short note on the fix, and what is still unverified |
| Acceptance | The task's FAIL_TO_PASS and PASS_TO_PASS tests pass on the state saved at the deadline. The grader first resets every test file the reference test patch touches, so editing the grading tests cannot pass a task. Blind review for off-ticket changes is planned but needs reviewers |
| Out of scope | Merging or deploying; repo-wide refactors; issues that cannot be reproduced |
| Outcome states | Qualified = all acceptance tests pass (reward 1). Partial = a non-empty saved diff but some tests fail. Failed = no change, or the run errored. Only "qualified" counts in the main metric |
| Caveat | SWE-bench tickets are public and old (2016-2023); the model may have seen the fixes in training. This affects both arms equally but limits what the absolute numbers mean |

## Budget and timing

| Rule | Value | Why |
|---|---|---|
| Time budget | 900 s, counted from the agent's start | The plan's business default (p4). Environment setup and grading are timed separately (Harbor records both) |
| Clock | `clock: wall`: real time (the larger of the monotonic and the system-clock elapsed time) | The WSL monotonic clock runs slow: in finished TUA runs a "2400 s" budget lasted up to about 2580 real seconds. A deadline promised to a person must be real time |
| Stop | `hard_deadline: true` | A model reply still running at the deadline is cancelled and command waits are cut. Without it the stop came up to one reply late: on qwen3.8 at a 1200 s TUA budget, 758 s late at P95. The vLLM server drops a cancelled request within about 0.5 s |
| Local processes at the stop | `interrupt_at_stop: true` | Ctrl-C to the command still running in the terminal (at most twice), then a check that it exited, so it cannot change files while the grader runs (plan p4). Background jobs are recorded, not killed. Self-test: the deliverable was final 4.5 s past a 20 s budget |
| Saved deliverable | `save_diff_of: /testbed` | `git diff` and `git status` saved at the stop (`agent/final.diff`, `final.status`); separates a partial delivery from none |
| Wrap-up reserve (arm P) | 120 s | The plan's starting value (p4). Checked two ways: grading the reference fixes took 84 s at P90 (68 trials); and on 17655 TUA turns, "mean of the last 3 turns + 120 s" covered 16856 next turns, as well as any adaptive rule tried |
| Arms, first batch | hidden (I0, same stop), full meter (I3), full meter + wrap-up (P) | The plan's p6 batch "20 dev x 3 arms x 3 attempts = 180"; I1 and I2 follow the TUA ablation's result |
| Lateness | Reported two ways: work stopped (`stopped_at_sec`) and deliverable final (`elapsed_sec`), each minus 900 s | The plan's target is 5 s at P95 |

## Logging spec

The plan (p11) asks for these fields on every event. `subset/tools/event_log.py` turns a finished trial into one JSON
line per event (agent start, each model reply, each command batch, agent end, grading) with these fields:

| Field | Where it comes from | Gap |
|---|---|---|
| run_id, task_id | Job id and trial name; task name (`result.json`) | none |
| Config version | Agent version string (`2.0.0+harness7-time...` with its suffixes) and the job's `config.json` | none |
| Model, provider | `config.agent.model_name`, `api_base` | Server software version and quantization are not recorded |
| Event type, start and end | Trajectory step timestamps split by the recorded request times into reply and commands | Commands within one batch are not timed one by one |
| Remaining budget, phase | Budget clock per event, also in the hidden arm; phase "work", "wrap-up" after the notice, "late" past the budget | none |
| Tool, exit code | Keystrokes in each command batch; terminal output | No exit codes (tmux keystrokes, not a tool API) |
| Tokens, cost | Per reply from the trajectory; totals in `result.json` | Cancelled replies (hard deadline) have no token count |
| Exit reason | `metadata.budget.stop`, `exception_info.exception_type`, replies cut, waits cut, the local-process check (`stop_interrupt`) | Remote cancel is checked for the vLLM server as a whole, not per request; hosted APIs not checked |
| Artifact path | `agent/final.diff` and `final.status`, with counts of files and lines changed | none |
| Acceptance result | `verifier_result.rewards.reward` and the verifier's test output | none |
