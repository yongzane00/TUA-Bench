"""Mechanical repetition statistics over a job's trials.

Answers: are timed-out trials stuck repeating themselves, or doing new work?
Reads each trial's agent/trajectory.json (ATIF), which already has commands
parsed into tool_calls, so no fragile re-parsing of raw model output.

    python subset/tools/loop_stats.py <job_dir>
"""

import collections
import glob
import json
import os
import re
import statistics
import sys


def norm(s: str) -> str:
    """Collapse whitespace so cosmetically-different repeats still match."""
    return re.sub(r"\s+", " ", (s or "")).strip()


def commands_per_episode(trial: str) -> list[list[str]]:
    """Command strings issued at each agent step, in order."""
    path = os.path.join(trial, "agent", "trajectory.json")
    if not os.path.exists(path):
        return []
    try:
        traj = json.loads(open(path, encoding="utf8").read())
    except Exception:
        return []
    steps = traj.get("steps") or traj.get("trajectory") or []
    out = []
    for step in steps:
        if step.get("source") != "agent":
            continue
        keys = [
            norm((tc.get("arguments") or {}).get("keystrokes", ""))
            for tc in (step.get("tool_calls") or [])
            if tc.get("function_name") == "bash_command"
        ]
        out.append([k for k in keys if k])
    return out


def observations(trial: str) -> list[str]:
    """Terminal output returned at each agent step."""
    path = os.path.join(trial, "agent", "trajectory.json")
    if not os.path.exists(path):
        return []
    try:
        traj = json.loads(open(path, encoding="utf8").read())
    except Exception:
        return []
    out = []
    for step in traj.get("steps") or []:
        if step.get("source") != "agent":
            continue
        results = ((step.get("observation") or {}).get("results")) or []
        out.append(norm(" ".join(r.get("content") or "" for r in results)))
    return out


def longest_static_run(seq: list[str]) -> int:
    """Longest run of consecutive identical entries."""
    best = run = 1 if seq else 0
    for a, b in zip(seq, seq[1:]):
        run = run + 1 if a == b and a else 1
        best = max(best, run)
    return best


def analyse(trial: str) -> dict | None:
    per_ep = commands_per_episode(trial)
    if not per_ep:
        return None
    flat = [c for ep in per_ep for c in ep]
    if not flat:
        return None
    counts = collections.Counter(flat)
    obs = observations(trial)
    return {
        "trial": os.path.basename(trial),
        "eps": len(per_ep),
        "cmds": len(flat),
        "distinct": len(counts),
        "dup_pct": 100 * (1 - len(counts) / len(flat)),
        "maxrep": max(counts.values()),
        "n_rep3": sum(1 for v in counts.values() if v >= 3),
        "waits": sum(1 for ep in per_ep if not ep),
        "static_obs": longest_static_run(obs),
        "top": counts.most_common(1)[0],
    }


def summarise(label: str, group: list[dict]) -> None:
    if not group:
        return
    med = lambda k: statistics.median(r[k] for r in group)
    rep3 = sum(1 for r in group if r["maxrep"] >= 3)
    print(f"\n=== {label}  (n={len(group)}) ===")
    print(f"  episodes                     median {med('eps'):.0f}")
    print(f"  commands issued              median {med('cmds'):.0f}")
    print(f"  distinct commands            median {med('distinct'):.0f}")
    print(f"  duplicate rate               median {med('dup_pct'):.1f}%"
          f"   mean {statistics.mean(r['dup_pct'] for r in group):.1f}%")
    print(f"  most-repeated command        median {med('maxrep'):.0f}"
          f"   max {max(r['maxrep'] for r in group)}")
    print(f"  trials w/ a command >=3x     {rep3}/{len(group)} = {100*rep3/len(group):.0f}%")
    print(f"  empty 'wait' episodes        median {med('waits'):.0f}"
          f"   total {sum(r['waits'] for r in group)}")
    print(f"  longest identical-obs run    median {med('static_obs'):.0f}"
          f"   max {max(r['static_obs'] for r in group)}")


def main(job_dir: str) -> int:
    rows = []
    for rp in glob.glob(os.path.join(job_dir, "*", "result.json")):
        trial = os.path.dirname(rp)
        try:
            res = json.loads(open(rp, encoding="utf8").read())
        except Exception:
            continue
        row = analyse(trial)
        if row is None:
            continue
        exc = (res.get("exception_info") or {}).get("exception_type", "")
        verifier = res.get("verifier_result") or {}
        row["timeout"] = exc == "AgentTimeoutError"
        row["reward"] = (verifier.get("rewards") or {}).get(
            "reward", verifier.get("reward")
        )
        rows.append(row)

    if not rows:
        print("no trials parsed", file=sys.stderr)
        return 1

    summarise("TIMED OUT", [r for r in rows if r["timeout"]])
    summarise("COMPLETED", [r for r in rows if not r["timeout"]])

    print("\n=== most-repeated single command, top 12 trials ===")
    for r in sorted(rows, key=lambda r: -r["maxrep"])[:12]:
        cmd, n = r["top"]
        flag = "TO" if r["timeout"] else "  "
        print(f"  {r['trial']:44} {flag} eps={r['eps']:>3} dup={r['dup_pct']:>4.0f}% "
              f"x{n:<3} {cmd[:58]!r}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    raise SystemExit(main(sys.argv[1]))
