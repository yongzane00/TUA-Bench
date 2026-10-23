#!/usr/bin/env python3
"""Per-stream decode throughput vs how many requests were actually in flight.

Concurrency is sampled at each call's MIDPOINT (instantaneous), not by counting
every call that overlaps the window anywhere -- the latter inflates the number
for long calls, since a 2000s call "overlaps" every short call that happens
during it.
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

run = Path(sys.argv[1])
calls = []
for trial in sorted(d for d in run.iterdir() if d.is_dir()):
    for dbg in trial.glob("agent/episode-*/debug.json"):
        txt = dbg.read_text(errors="ignore")
        t = re.search(r'"api_call_start_time": "([^"]+)"', txt)
        d = re.search(r'"llm_api_duration_ms":\s*([0-9.]+)', txt)
        c = re.search(r'\\"completion_tokens\\":\s*(\d+)', txt)
        if not (t and d and c):
            continue
        start = datetime.fromisoformat(t.group(1))
        dur = float(d.group(1)) / 1000
        calls.append((start, start + timedelta(seconds=dur), dur, int(c.group(1))))

buckets = {}
for start, end, dur, tok in calls:
    mid = start + (end - start) / 2
    inflight = sum(1 for s2, e2, _, _ in calls if s2 <= mid <= e2)
    buckets.setdefault(inflight, []).append(tok / dur if dur else 0)

print(f"{'in flight':>10} {'calls':>6} {'mean tok/s':>11} {'median':>8} {'aggregate tok/s':>16}")
for k in sorted(buckets):
    v = sorted(buckets[k])
    mean = sum(v) / len(v)
    print(f"{k:>10} {len(v):>6} {mean:>11.1f} {v[len(v) // 2]:>8.1f} {mean * k:>16.1f}")
