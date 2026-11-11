#!/usr/bin/env python3
"""Filler actions near the deadline: does an arm pad its last minutes with waiting or repeated commands?

    python -X utf8 filler_check.py <budget_sec> <label>=<run_dir>[,<run_dir>...] [...] [--window 300]
    python -X utf8 filler_check.py --plan-runs qwen38          (every finished hidden / shown pair of plot_budget_curve)

For every agent step (trajectory.json) in the last <window> seconds of the budget, counted from the first step:
  wait-only  every command in the step is empty, `sleep N`, `wait`, `true`, `:` or a one-word `echo`
  repeated   the same commands as an earlier step of the same trial
  declared   the step calls mark_task_complete
Steps before the window are counted too, as the reference rate.
"""
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

WAIT = re.compile(r"^\s*(sleep\s+[\d.]+|wait|true|:|echo\s*['\"]?\w*['\"]?)?\s*;?\s*$")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def count(run_dirs, budget, window):
    c = Counter()
    for run in run_dirs:
        for p in Path(run).glob("*__*/agent/trajectory.json"):
            try:
                steps = json.loads(p.read_text(encoding="utf-8"))["steps"]
            except (OSError, ValueError, KeyError):
                continue
            agent = [s for s in steps if s.get("source") == "agent" and s.get("timestamp")]
            if not agent:
                continue
            t0, seen = ts(steps[0]["timestamp"]), set()
            c["trials"] += 1
            for s in agent:
                k = "late" if ts(s["timestamp"]) - t0 >= budget - window else "early"
                calls = s.get("tool_calls") or []
                keys = tuple((cl.get("arguments") or {}).get("keystrokes") or "" for cl in calls
                             if cl.get("function_name") == "bash_command")
                c[k] += 1
                c[k + "_wait"] += bool(keys) and all(WAIT.match(x.replace("\n", " ").strip()) for x in keys)
                c[k + "_repeat"] += bool(keys) and keys in seen
                c[k + "_done"] += any(cl.get("function_name") == "mark_task_complete" for cl in calls)
                seen.add(keys)
    return c


def row(label, budget, c):
    late = lambda key: f"{c['late_' + key]} of {c['late']}"
    return (f"| {budget} | {label} | {c['trials']} | {c['late']} | {late('wait')} | {late('repeat')} | {late('done')} | "
            f"{c['early_wait']} of {c['early']} | {c['early_repeat']} of {c['early']} |")


def main():
    args = sys.argv[1:]
    window = 300
    if "--window" in args:
        i = args.index("--window"); window = float(args[i + 1]); args = args[:i] + args[i + 2:]
    print(f"| Budget (s) | Arm | Trials | Steps in the last {window:.0f} s | Wait-only | Repeated | Declared complete | "
          "Wait-only before | Repeated before |")
    print("|---|---|---|---|---|---|---|---|---|")
    if args and args[0] == "--plan-runs":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from plot_budget_curve import runs
        allruns = runs()
        model = args[1] if len(args) > 1 else "qwen38"
        for b in sorted({b for (m, a, b) in allruns if m == model}):
            if (model, "shown", b) not in allruns:
                continue
            for arm in ("hidden", "shown"):
                print(row(arm, b, count([allruns[(model, arm, b)]], b, window)))
        return
    budget = float(args[0])
    for spec in args[1:]:
        label, dirs = spec.split("=", 1)
        print(row(label, f"{budget:.0f}", count(dirs.split(","), budget, window)))


if __name__ == "__main__":
    main()
