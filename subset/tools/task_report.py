#!/usr/bin/env python3
"""Per-task outcome + cost table for a harbor run, separating model failures
from harness faults.

A trial with no reward is not a model failure. This classifies every trial:

    pass      reward == 1
    partial   0 < reward < 1
    fail      reward == 0             (includes debian timeouts that still graded)
    uid       RewardFileNotFoundError  verifier could not write (ubuntu UID bug)
    infra     RuntimeError before the agent started (e.g. image build) -- not a model outcome
    error     RuntimeError after the agent ran
    timeout   AgentTimeoutError with no reward (timed out AND ungraded)

Usage:  python3 task_report.py <run_dir> [--json out.json]
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

TASKS = Path(__file__).resolve().parents[2] / "tasks"
WEIGHTS = {"easy": 22 / 120, "medium": 90 / 120, "hard": 8 / 120}


def task_meta(name: str) -> tuple[str, str]:
    toml = (TASKS / name / "task.toml").read_text(encoding="utf8")
    diff = re.search(r'difficulty\s*=\s*"([^"]+)"', toml).group(1)
    df = TASKS / name / "environment" / "Dockerfile"
    m = re.search(r"(?im)^FROM\s+(\S+)", df.read_text(errors="ignore")) if df.exists() else None
    return diff, (m.group(1) if m else "?")


def classify(r: dict) -> tuple[str, float | None]:
    v = (r.get("verifier_result") or {}).get("rewards") or {}
    reward = next(iter(v.values()), None)
    if reward is not None:
        reward = float(reward)
        return ("pass" if reward == 1 else "fail" if reward == 0 else "partial"), reward
    ex = (r.get("exception_info") or {}).get("exception_type")
    if ex == "RuntimeError":
        started = (r.get("agent_execution") or {}).get("started_at")
        return ("error" if started else "infra"), None
    return {"RewardFileNotFoundError": "uid", "AgentTimeoutError": "timeout"}.get(ex, "other"), None


def main(run: Path, json_out: Path | None) -> None:
    tasks: dict[str, dict] = defaultdict(lambda: {"outcomes": Counter(), "rewards": [], "costs": []})
    for p in sorted(run.glob("*/result.json")):
        r = json.loads(p.read_text())
        name = p.parent.name.rsplit("__", 1)[0]
        kind, reward = classify(r)
        t = tasks[name]
        t["outcomes"][kind] += 1
        if reward is not None:
            t["rewards"].append(reward)
        t["costs"].append((r.get("agent_result") or {}).get("cost_usd") or 0.0)

    rows = []
    for name, t in tasks.items():
        diff, img = task_meta(name)
        n = sum(t["outcomes"].values())
        graded = len(t["rewards"])
        rows.append({
            "task": name, "difficulty": diff, "image": img, "attempts": n,
            "graded": graded,
            "passes": t["outcomes"]["pass"],
            "mean_reward_graded": (sum(t["rewards"]) / graded) if graded else None,
            "pass_rate_all": t["outcomes"]["pass"] / n,
            "cost_per_attempt": sum(t["costs"]) / n,
            "cost_total": sum(t["costs"]),
            "outcomes": dict(t["outcomes"]),
        })
    rows.sort(key=lambda x: (["easy", "medium", "hard"].index(x["difficulty"]), x["task"]))

    # ---- table
    print(f"{'task':<32}{'diff':<7}{'image':<17}{'grd':>4}{'pass':>5}  {'$/att':>7}  outcomes")
    for x in rows:
        o = " ".join(f"{k}:{v}" for k, v in sorted(x["outcomes"].items()))
        print(f"{x['task']:<32}{x['difficulty']:<7}{x['image'][:16]:<17}"
              f"{x['graded']:>3}/{x['attempts']}{x['passes']:>5}  {x['cost_per_attempt']:>7.4f}  {o}")

    # ---- run-level
    allk = Counter()
    for x in rows:
        allk.update(x["outcomes"])
    n_trials = sum(allk.values())
    total_cost = sum(x["cost_total"] for x in rows)
    graded_tasks = [x for x in rows if x["graded"] == x["attempts"]]
    ungradeable = [x for x in rows if x["graded"] == 0]

    print(f"\ntrials {n_trials}  cost ${total_cost:.4f}  (${total_cost / n_trials:.4f}/trial)")
    print("outcomes: " + "  ".join(f"{k}={v}" for k, v in allk.most_common()))
    print(f"tasks fully graded (5/5): {len(graded_tasks)}   never graded (0/5): {len(ungradeable)}"
          f"   partially graded: {len(rows) - len(graded_tasks) - len(ungradeable)}")

    # stratified score restricted to fully-graded tasks, with coverage per stratum
    print("\nstratified, fully-graded tasks only:")
    s = 0.0
    for d in ("easy", "medium", "hard"):
        g = [x for x in graded_tasks if x["difficulty"] == d]
        tot = sum(1 for x in rows if x["difficulty"] == d)
        mean = sum(x["mean_reward_graded"] for x in g) / len(g) if g else None
        if mean is not None:
            s += WEIGHTS[d] * mean
        print(f"  {d:<7} {len(g):>2}/{tot:<2} tasks measurable   S={'n/a' if mean is None else f'{mean:.4f}'}")

    if json_out:
        json_out.write_text(json.dumps({"rows": rows, "outcomes": dict(allk),
                                        "total_cost": total_cost, "n_trials": n_trials}, indent=1))
        print(f"\nwrote {json_out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = Path(sys.argv[sys.argv.index("--json") + 1]) if "--json" in sys.argv else None
    main(Path(sys.argv[1]), out)
