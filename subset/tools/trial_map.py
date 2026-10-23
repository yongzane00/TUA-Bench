import json
import sys
from datetime import datetime
from pathlib import Path


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


run = Path(sys.argv[1])
rows = []
for t in sorted(d for d in run.iterdir() if d.is_dir()):
    r = json.loads((t / "result.json").read_text())
    ex = (r.get("exception_info") or {}).get("exception_type")
    v = r.get("verifier_result") or {}
    rew = next(iter(v.get("rewards", {}).values()), None)
    e = r.get("agent_execution") or {}
    wall = (ts(e["finished_at"]) - ts(e["started_at"])).total_seconds() if e.get("finished_at") else None
    ag = r.get("agent_result") or {}
    rows.append((t.name.split("__")[0], t.name.split("__")[1], rew, ex, wall,
                 ag.get("n_input_tokens"), ag.get("n_output_tokens")))

rows.sort()
print(f"{'task':<26} {'id':<9} {'reward':>7} {'wall':>7} {'exception':<20} {'in':>9} {'out':>7}")
for task, tid, rew, ex, wall, ti, to in rows:
    mark = "PASS" if rew == 1 else "fail"
    print(f"{task:<26} {tid:<9} {mark:>7} {wall or 0:>7.0f} {ex or '-':<20} {ti or 0:>9,} {to or 0:>7,}")
