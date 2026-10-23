#!/usr/bin/env python3
"""Live status for a running harbor job. Usage: status.py <run_dir>"""
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

run = Path(sys.argv[1])
r = json.loads((run / "result.json").read_text())
s = r["stats"]
e = list(s["evals"].values())[0]

started = datetime.fromisoformat(r["started_at"])
updated = datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00")).replace(tzinfo=None)
elapsed = (datetime.now() - started).total_seconds()

total = r["n_total_trials"]
done = s["n_completed_trials"]
err = s["n_errored_trials"]
run_ = s["n_running_trials"]
pend = s["n_pending_trials"]

print(f"elapsed   : {elapsed/3600:.2f} h   (started {started:%H:%M})")
print(f"trials    : {done} finished / {run_} running / {pend} pending   of {total}")
print(f"  of finished: {done - err} scored, {err} errored")
print(f"mean      : {e['metrics'][0]['mean']:.4f}")
print(f"tokens    : {s['n_input_tokens']:,} in / {s['n_output_tokens']:,} out")
cost = s.get("cost_usd")
print(f"cost_usd  : {cost if cost is not None else '(not reported)'}")

rate = done / (elapsed / 3600) if elapsed else 0
print(f"rate      : {rate:.1f} trials/h  ->  ETA {(total-done)/rate:.1f} h "
      f"for remaining {total-done}" if rate else "rate      : n/a")

print("\nexceptions:")
for k, v in sorted(e.get("exception_stats", {}).items(), key=lambda x: -len(x[1])):
    print(f"  {k:<28} {len(v)}")

# per-task rollup from the trial dirs
per = {}
for p in sorted(run.glob("*/result.json")):
    d = json.loads(p.read_text())
    task = (d.get("task_name") or p.parent.name).split("/")[-1]
    v = d.get("verifier_result") or {}
    rew = next(iter(v.get("rewards", {}).values()), None)
    ex = (d.get("exception_info") or {}).get("exception_type")
    a = per.setdefault(task, {"pass": 0, "n": 0, "ex": Counter()})
    a["n"] += 1
    if rew == 1:
        a["pass"] += 1
    if ex:
        a["ex"][ex] += 1

print(f"\nper-task ({len(per)} tasks touched):")
for t in sorted(per):
    a = per[t]
    exs = " ".join(f"{k.replace('Error','')}x{c}" for k, c in a["ex"].items())
    print(f"  {t:<34} {a['pass']}/{a['n']}  {exs}")
