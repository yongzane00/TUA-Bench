"""Stratified success rate for the frozen 40-task subset.

The subset over-samples hard (5 of 8) and under-samples medium (27 of 90),
so a plain mean over 40 tasks is a biased estimate of benchmark success.
Re-weight each stratum by its share of the full 120-task benchmark:

    S = (22/120) * S_easy + (90/120) * S_medium + (8/120) * S_hard

    python subset/score.py jobs/harness0-attempt3/2026-.../result.json
"""

import collections
import glob
import json
import pathlib
import re
import sys

WEIGHTS = {"easy": 22 / 120, "medium": 90 / 120, "hard": 8 / 120}
TASKS_DIR = pathlib.Path(__file__).resolve().parent.parent / "tasks"


def difficulty_of() -> dict[str, str]:
    out = {}
    for toml in glob.glob(str(TASKS_DIR / "*" / "task.toml")):
        p = pathlib.Path(toml)
        text = p.read_text(encoding="utf8")
        out[p.parent.name] = re.search(r'difficulty\s*=\s*"([^"]+)"', text).group(1)
    return out


def stratified(job_dir: pathlib.Path) -> tuple[float, dict]:
    """Mean reward per stratum, then re-weighted to benchmark proportions."""
    diff = difficulty_of()
    rewards = collections.defaultdict(list)

    for result in job_dir.glob("*/result.json"):
        data = json.loads(result.read_text(encoding="utf8"))
        # trial dir is "<task-name>__<hash>"; strip the hash
        task = result.parent.name.rsplit("__", 1)[0]
        verifier = data.get("verifier_result") or {}
        reward = (verifier.get("rewards") or {}).get("reward", verifier.get("reward"))
        if reward is None or task not in diff:
            continue
        rewards[diff[task]].append(float(reward))

    per_stratum = {k: sum(v) / len(v) for k, v in rewards.items() if v}
    score = sum(WEIGHTS[k] * v for k, v in per_stratum.items())
    detail = {
        k: {"S": round(per_stratum.get(k, 0.0), 4),
            "w": round(WEIGHTS[k], 4),
            "n_trials": len(rewards.get(k, []))}
        for k in ("easy", "medium", "hard")
    }
    return score, detail


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    target = pathlib.Path(sys.argv[1])
    job_dir = target.parent if target.name == "result.json" else target
    score, detail = stratified(job_dir)
    for level, d in detail.items():
        print(f"  {level:7} S={d['S']:.4f}  w={d['w']:.4f}  n={d['n_trials']}")
    missing = [k for k, d in detail.items() if d["n_trials"] == 0]
    if missing:
        print(f"  WARNING: no trials for {', '.join(missing)} — S is under-counted")
    print(f"  S = {score:.4f}")
