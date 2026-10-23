#!/usr/bin/env python3
"""Per-trial verifier duration + artefact count, to spot verifiers that never ran."""
import glob
import json
import os
import sys
from datetime import datetime

R = sys.argv[1]


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


rows = []
for p in sorted(glob.glob(os.path.join(R, "*", "result.json"))):
    d = json.load(open(p))
    v = d.get("verifier") or {}
    if not v.get("finished_at"):
        continue
    dur = (ts(v["finished_at"]) - ts(v["started_at"])).total_seconds()
    ex = (d.get("exception_info") or {}).get("exception_type") or "-"
    rw = next(iter((d.get("verifier_result") or {}).get("rewards", {}).values()), None)
    vdir = os.path.join(os.path.dirname(p), "verifier")
    files = len(os.listdir(vdir)) if os.path.isdir(vdir) else -1
    task = os.path.basename(os.path.dirname(p)).split("__")[0]
    rows.append((dur, task, rw, ex, files))

rows.sort()
hdr = "%8s  %-32s %6s  %5s  %s" % ("verif_s", "task", "reward", "files", "exception")
print(hdr)
print("-" * len(hdr))
for dur, t, rw, ex, f in rows:
    print("%8.2f  %-32s %6s  %5d  %s" % (dur, t, str(rw), f, ex))
