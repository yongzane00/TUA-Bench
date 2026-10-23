#!/usr/bin/env python3
"""Compute leaderboard-style metrics for a harbor job directory.

harbor reports mean reward and pass@k for k in {2,4,5} at n_attempts=5, but it
does NOT report pass@1 or All-5 (see harbor/utils/pass_at_k.py:_eligible_k_values,
which starts its powers-of-2 sequence at k=2). This fills both gaps.

Usage:
    python3 leaderboard_metrics.py <job_run_dir> [<job_run_dir> ...]
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Codex/HumanEval). n attempts, c successes."""
    if n - c < k:
        return 1.0
    product = 1.0
    for i in range(k):
        product *= (n - c - i) / (n - i)
    return 1.0 - product


def collect(run_dir: Path) -> dict[str, list[int]]:
    """task_name -> list of 0/1 outcomes, one per attempt."""
    successes: defaultdict[str, list[int]] = defaultdict(list)
    for result_path in sorted(run_dir.glob("*/result.json")):
        result = json.loads(result_path.read_text())
        task = result.get("task_name") or result_path.parent.name
        verifier = result.get("verifier_result")
        if not verifier or not verifier.get("rewards"):
            # errored / timed-out trial with no reward file counts as a failure
            successes[task].append(0)
            continue
        reward = next(iter(verifier["rewards"].values()))
        successes[task].append(1 if reward == 1 else 0)
    return dict(successes)


def report(run_dir: Path) -> None:
    successes = collect(run_dir)
    if not successes:
        print(f"{run_dir.name}: no trials found")
        return

    n_per_task = {t: len(v) for t, v in successes.items()}
    n = min(n_per_task.values())
    attempts = sum(n_per_task.values())
    total_pass = sum(sum(v) for v in successes.values())
    n_tasks = len(successes)

    success_rate = total_pass / attempts
    p1 = sum(pass_at_k(len(v), sum(v), 1) for v in successes.values()) / n_tasks
    all_n = sum(1 for v in successes.values() if sum(v) == len(v)) / n_tasks

    print(f"\n=== {run_dir.name} ===")
    print(f"  tasks={n_tasks}  attempts/task={sorted(set(n_per_task.values()))}  trials={attempts}")
    print(f"  Success Rate : {success_rate:.3f}")
    print(f"  Pass@1       : {p1 * 100:.1f}%")
    for k in (2, 4, 5):
        if k <= n:
            pk = sum(pass_at_k(len(v), sum(v), k) for v in successes.values()) / n_tasks
            print(f"  Pass@{k}       : {pk * 100:.1f}%")
    label = f"All-{n}" if n > 1 else "All-1"
    print(f"  {label:<13}: {all_n * 100:.1f}%")
    if n < 5:
        print(f"  NOTE: only {n} attempt(s) per task — Pass@5 and All-5 are undefined.")

    print("  per task:")
    for task in sorted(successes):
        v = successes[task]
        print(f"    {task:<40} {sum(v)}/{len(v)}  {''.join('o' if x else '.' for x in v)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    for arg in sys.argv[1:]:
        report(Path(arg))
