#!/usr/bin/env python3
"""Reproducibility of the pilot tasks: oracle (reference fix) must score 1, nop (no change) must score 0.

    python3 pilot/check_tasks.py <jobs/pilot dir>          (prints a markdown table)

Reads every job folder under <jobs/pilot>/oracle-*/ and <jobs/pilot>/nop-*/. A task is reproducible when every oracle
trial scored 1 and every nop trial scored 0. Also prints the grading time (verifier phase) per task and its P90,
which sets the wrap-up reserve (plan p4).
"""
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

root = sys.argv[1]


def dur(phase):
    if not phase or not phase.get("started_at") or not phase.get("finished_at"):
        return None
    f = lambda s: datetime.fromisoformat(s.rstrip("Z"))
    return (f(phase["finished_at"]) - f(phase["started_at"])).total_seconds()


res = defaultdict(lambda: {"oracle": [], "nop": [], "verify": []})
for kind in ("oracle", "nop"):
    for p in glob.glob(f"{root}/{kind}-*/20*/*__*/result.json"):
        r = json.load(open(p, encoding="utf-8"))
        task = os.path.basename(os.path.dirname(p)).split("__")[0] + "__" + os.path.basename(os.path.dirname(p)).split("__")[1]
        rw = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        res[task][kind].append(rw)
        v = dur(r.get("verifier"))
        if v is not None:
            res[task]["verify"].append(v)

print("| Task | Oracle (reference fix) | Nop (no change) | Grading time (s) | Reproducible |")
print("|---|---|---|---|---|")
ok = 0
allv = []
for task in sorted(res, key=lambda t: int(t.split("-")[-1])):
    d = res[task]
    o, n = d["oracle"], d["nop"]
    good = bool(o) and bool(n) and all(x == 1 for x in o) and all(x == 0 for x in n)
    ok += good
    allv += d["verify"]
    fmt = lambda xs: (", ".join("-" if x is None else f"{x:g}" for x in xs) or "not run")
    vt = f"{max(d['verify']):.0f}" if d["verify"] else ""
    print(f"| `{task}` | {fmt(o)} | {fmt(n)} | {vt} | {'yes' if good else ('pending' if not (o and n) else 'no')} |")
allv.sort()
p90 = allv[min(len(allv) - 1, int(0.9 * len(allv)))] if allv else None
print(f"\nReproducible: {ok} of {len(res)} tasks checked. Grading time over {len(allv)} trials: "
      f"median {allv[len(allv) // 2]:.0f} s, P90 {p90:.0f} s." if allv else "")
