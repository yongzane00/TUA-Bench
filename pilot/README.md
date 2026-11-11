# Code-repair pilot: technical check on public tasks

The plan's first pilot (p2) is an in-house code-repair assistant that must deliver a reviewable patch within 15
minutes. There is no partner team yet, so this folder runs the technical check the plan allows first: fixed-version
public tasks, reported separately from any business tasks. A result here shows the mechanism works on real code
fixes; it does not show business value.

| File | What it is |
|---|---|
| `README.md` | Task contract, budget and timing rules, logging spec (this page) |
| [`tasks.md`](tasks.md) | Data split: 20 dev + 40 held-out Django tasks, with the week-1 set of 10 |
| [`select_tasks.py`](select_tasks.py) | The fixed selection rule that produced `tasks.md` |
| [`configs/`](configs/) | Run configs: `oracle-week1.yaml` (reproducibility check, no model) |

## Task contract

| Item | Agreement |
|---|---|
| User and pain point | On-call or maintenance engineer. Small fixes with a clear report, where agents tend to time out while exploring. Here: public Django tickets from SWE-bench Verified |
| Input | The repo at a fixed commit (the task's Docker image), the issue text, the test environment, a 900 s deadline. As in SWE-bench, the agent is not told which tests grade it; the plan's "reproduce command" is therefore not given |
| Scope | One repo (django/django); SWE-bench difficulty "<15 min fix" or "15 min - 1 hour"; the reference fix changes one source file. Each attempt runs in its own container |
| Must deliver | The code change in the working tree at the deadline. Asked for in the task text: the tests run and their real results, a short note on the fix, and what is still unverified |
| Acceptance | The task's FAIL_TO_PASS and PASS_TO_PASS tests pass on the state saved before the deadline. The grader first resets every test file the reference test patch touches, so editing the grading tests cannot pass a task. Blind review for off-ticket changes is planned but needs reviewers |
| Out of scope | Merging or deploying; repo-wide refactors; issues that cannot be reproduced |
| Outcome states | Qualified = all acceptance tests pass (reward 1). Partial = a non-empty change but some tests fail. Failed = no change, or the run errored. Only "qualified" counts in the main metric |
| Caveat | SWE-bench tickets are public and old (2016-2023); the model may have seen the fixes in training. This affects both arms equally but limits what the absolute numbers mean |

## Budget and timing

| Rule | Value | Why |
|---|---|---|
| Time budget | 900 s, counted from the agent's start | The plan's business default (p4). Environment setup is timed separately (Harbor records it) |
| Stop | `hard_deadline: true` | Without it the stop comes up to one model reply late; on qwen3.8 at a 1200 s TUA budget that was 758 s late at P95 (`subset/results/deployment-plan-progress.md`). The plan's target is 5 s at P95 |
| Wrap-up reserve | 120 s to start; then the P90 of the verify time measured on the dev tasks | The plan's starting value (p4); the oracle run measures how long the acceptance tests take |
| Arms, first batch | hidden (I0, same stop), full meter (I3), full meter + wrap-up (P) | The plan's p6 batch "20 dev x 3 arms x 3 attempts = 180"; I1 and I2 follow the TUA ablation's result |
| Clock | The harness's monotonic clock; Harbor's wall-clock timestamps are kept as well | The WSL clock can run up to 8 s per 100 s slow against the wall clock |

## Logging spec

The plan (p11) asks for these fields on every event. What Harbor and the agent already record, and what is missing:

| Field | Where it comes from now | Gap |
|---|---|---|
| run_id, task_id | Job id and trial name; task name (`result.json`) | none |
| Config version | Agent version string (`2.0.0+harness7-time...` with its suffixes) and the job's `config.json` | none |
| Model, provider | `config.agent.model_name`, `api_base` | Server software version and quantization are not recorded |
| Event type, start and end | Trajectory steps (agent, user, system) with timestamps; `agent_execution` start and end | Command start and end inside a turn are not separate events |
| Remaining budget, phase | Meter line in each update (shown arms); `wrapup_at_sec`, `stop` in `metadata.budget` | Hidden arm: recomputed from timestamps |
| Tool, exit code | Keystrokes in each tool call; terminal output | No exit codes (tmux keystrokes, not a tool API) |
| Tokens, cost | Per step in the trajectory; totals in `result.json` | Cancelled replies (hard deadline) have no token count |
| Exit reason | `metadata.budget.stop`, `exception_info.exception_type`, `cut_replies`, `cut_waits` | Remote cancel of a cut reply is not confirmed |
| Artifact path | The trial folder | The final diff is graded inside the container but not saved; to add: write `git diff` to the agent log folder at the stop |
| Acceptance result | `verifier_result.rewards.reward` and the verifier's test output | none |
