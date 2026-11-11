#!/usr/bin/env python3
"""How long would each quiet-start rule have kept the ablation waiting, and what does other users' load cost in speed?

    python3 gate_options.py [days] [endpoint]      (in WSL; reads vllmtop's database read-only)

From vllmtop's per-second samples of the shared qwen3.8 server (endpoint `rpt-isp-dgx`, the .146 server since
2026-10-23) over the last `days` days (default 7):

1. For each rule "start when at most k requests from others are running or waiting, for 10 minutes in a row"
   (k = 0 is the current gate), how many such openings there were, and the wait from a random moment to the next
   opening (median and the share of moments that waited more than 12 hours). A scrape hole of 10 s or more breaks a
   stretch (the server state is unknown then).
2. Decode speed per request at each load: generation tokens per second divided by the running requests, median
   over the seconds with that many running. The ablation adds 4 requests (one trial per arm), so the cost of a
   rule is the speed at 4 + k running against 4.
"""
import sqlite3
import statistics as stx
import sys
import time
from collections import defaultdict

DAYS = float(sys.argv[1]) if len(sys.argv) > 1 else 7
EP = sys.argv[2] if len(sys.argv) > 2 else "rpt-isp-dgx"
DB = "file:/home/<win-user>/.local/share/vllmtop/usage.db?mode=ro"
QUIET_S, HOLE_S = 600, 10


def series(db, metric, since):
    out = defaultdict(float)
    for ts, v in db.execute("select ts_ms, value from samples where endpoint=? and metric=? and ts_ms>=?",
                            (EP, metric, since)):
        out[ts // 1000] += v  # summed over engines
    return out


def main():
    db = sqlite3.connect(DB, uri=True)
    now = time.time()
    since = int((now - DAYS * 86400) * 1000)
    run, wait, tps = series(db, "running", since), series(db, "waiting", since), series(db, "generation_tps", since)
    secs = sorted(run)
    load = [(s, run[s] + wait.get(s, 0)) for s in secs]
    print(f"{EP}: {len(secs)} seconds sampled over {DAYS:g} days ({len(secs) / (DAYS * 864):.0f} of 100 seconds)\n")

    print("| Rule: start when others' requests <= k for 10 min | Openings | Wait from a random moment, median | "
          "Moments that waited > 12 h |")
    print("|---|---|---|---|")
    for k in (0, 1, 2):
        opens, start, prev = [], None, None
        for s, v in load:
            if v <= k and prev is not None and s - prev < HOLE_S:
                if start is None:
                    start = prev
            elif v <= k:
                start = s
            else:
                start = None
            if start is not None and s - start >= QUIET_S and (not opens or opens[-1] < start):
                opens.append(s)  # first second at which this stretch reached 10 minutes
                start = s + 10 ** 9  # count one opening per stretch
            prev = s
        opens_set = sorted(opens)
        waits, j = [], 0
        for s in secs[::60]:  # one sample per minute
            while j < len(opens_set) and opens_set[j] < s:
                j += 1
            waits.append((opens_set[j] - s) if j < len(opens_set) else (now - s) + 1e9)
        known = [w for w in waits if w < 1e9]
        long = sum(w > 12 * 3600 for w in waits)
        med = stx.median(waits)
        med_txt = f"{med / 3600:.1f} h" if med < 1e9 else "no opening yet"
        print(f"| k = {k} | {len(opens_set)} | {med_txt} | {long} of {len(waits)} |")

    print("\n| Running requests | Seconds | Decode speed per request (tok/s, median) | vs 4 running |")
    print("|---|---|---|---|")
    by = defaultdict(list)
    for s in secs:
        n = int(run[s])
        if n >= 1 and tps.get(s, 0) > 0:
            by[n].append(tps[s] / n)
    base = stx.median(by[4]) if by.get(4) else None
    for n in range(1, 10):
        if len(by.get(n, [])) >= 60:
            m = stx.median(by[n])
            rel = f"{m / base:.2f} x" if base else "-"
            print(f"| {n} | {len(by[n])} | {m:.0f} | {rel} |")


if __name__ == "__main__":
    main()
