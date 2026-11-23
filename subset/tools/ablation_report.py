#!/usr/bin/env python3
"""Report for a side-by-side ablation (run_parallel.sh): every arm vs the first arm, plus server load per trial.

    python3 ablation_report.py <model> <label>=<config> [<label>=<config> ...] [--vs <label>] [--did A,B,C,D]
                               [--own-calls <proxy events.jsonl>,...]  (WSL)
    e.g. ablation_report.py qwen38-flash-next I0=harness0-time2400-rounds3 I1=harness7-time2400-once-rounds3 \
         I2=harness7-time2400-clock-rounds3 I3=harness7-time2400-rounds3

Merges every finished job folder of each config (one per round). Per arm: solved (reward 1) x of n, mean
reward, $ per solved, trials ended by time. Per arm vs the first arm (and vs the --vs arm, if given): solved gap with a 95% CI from a paired
bootstrap over tasks (attempts stay with their task). --did A,B,C,D adds the difference of gaps (A - B) - (C - D),
e.g. (full - hidden at +20 s) - (full - hidden at 0 s) for the latency batch, bootstrapped with all of a task's trials
in the four arms kept together (all trials and quiet trials). Server load: for each trial, the mean number of requests
running on the model server during its agent phase, from vllmtop's history (~/.local/share/vllmtop/usage.db),
minus our own trials active at the same time (each counted at 0.8, the share of time our agents wait on the
model). Trials with an estimated other-user load below 0.5 count as "quiet"; the arms are compared on all
trials and on quiet trials only. With --own-calls (the budget proxy's event logs of every arm, for agents such as
Claude Code that send several requests at once), our own load is counted exactly instead: at each vllmtop sample,
the proxy's model calls in flight (`model_call` events: end time `ts`, duration `seconds`) are subtracted.
"""
import glob
import json
import os
import random
import sqlite3
import statistics as stx
import sys
from collections import defaultdict
from datetime import datetime, timezone

JOBS = os.environ.get("TUA_JOBS", "/mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/jobs")
DB = os.path.expanduser("~/.local/share/vllmtop/usage.db")
ENDPOINT = os.environ.get("VLLMTOP_ENDPOINT", "rpt-isp-dgx")
OWN_SHARE = 0.8
REPS = 4000


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp()


def load_arm(model, cfg):
    out = []
    for job in sorted(glob.glob(f"{JOBS}/{model}/{cfg}/20*/")):
        try:
            jr = json.load(open(job + "result.json"))
            if not jr.get("finished_at"):
                continue
            if (jr.get("stats") or {}).get("n_errored_trials", 0) >= (jr.get("n_total_trials") or 1):
                continue  # every trial errored (infrastructure): not a round; the round is run again as a whole
        except Exception:
            continue
        for p in glob.glob(job + "*__*/result.json"):
            r = json.load(open(p))
            ae = r.get("agent_execution") or {}
            if not ae.get("started_at") or not ae.get("finished_at"):  # e.g. agent setup failed: a failure, kept
                ae = r if r.get("started_at") and r.get("finished_at") else None  # (analysis plan: no trial dropped)
                if ae is None:
                    continue
            rw = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward", 0) or 0
            bud = ((r.get("agent_result") or {}).get("metadata") or {}).get("budget") or {}
            exc = (r.get("exception_info") or {}).get("exception_type")
            out.append(dict(task=os.path.basename(os.path.dirname(p)).rsplit("__", 1)[0], reward=rw, solved=rw >= 1,
                            cost=(r.get("agent_result") or {}).get("cost_usd") or 0.0,
                            by_time=bud.get("stop") == "time" or exc == "AgentTimeoutError",
                            t0=ts(ae["started_at"]), t1=ts(ae["finished_at"]), job=os.path.basename(job.rstrip("/"))))
    return out


def server_load(trials):
    """Mean 'running' during each trial, from the vllmtop db (None if no samples)."""
    if not os.path.exists(DB):
        return
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    for t in trials:
        row = c.execute("select avg(value), count(*) from samples where endpoint=? and metric='running' "
                        "and ts_ms between ? and ?", (ENDPOINT, int(t["t0"] * 1000), int(t["t1"] * 1000))).fetchone()
        t["running"] = row[0] if row and row[1] else None


def own_calls_load(trials, paths):
    """Other users' load per trial: mean over vllmtop samples of (running - our proxy calls in flight), floored at 0."""
    calls = []
    for p in paths:
        for line in open(p):
            d = json.loads(line)
            if d.get("event") == "model_call" and d.get("seconds") is not None:
                calls.append((d["ts"] - d["seconds"], d["ts"]))
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    for t in trials:
        rows = c.execute("select ts_ms, value from samples where endpoint=? and metric='running' "
                         "and ts_ms between ? and ?", (ENDPOINT, int(t["t0"] * 1000), int(t["t1"] * 1000))).fetchall()
        mine = [cl for cl in calls if cl[1] > t["t0"] and cl[0] < t["t1"]]
        if not rows:
            t["others"] = None
            continue
        t["others"] = stx.mean(max(0.0, v - sum(a <= ms / 1000 <= b for a, b in mine)) for ms, v in rows)


def own_overlap(t, everyone):
    """Our other trials' average concurrency during t (time-weighted)."""
    span = t["t1"] - t["t0"]
    if span <= 0:
        return 0.0
    tot = 0.0
    for u in everyone:
        if u is t:
            continue
        lo, hi = max(t["t0"], u["t0"]), min(t["t1"], u["t1"])
        if hi > lo:
            tot += hi - lo
    return tot / span


def gap_ci(a, b):
    ta, tb = defaultdict(list), defaultdict(list)
    for t in a:
        ta[t["task"]].append(t["solved"])
    for t in b:
        tb[t["task"]].append(t["solved"])
    tasks = sorted(set(ta) & set(tb))
    if not tasks:
        return None
    n_per = len(a) / max(1, len(set(ta)))

    def g(ts_):
        return sum(stx.mean(ta[x]) - stx.mean(tb[x]) for x in ts_) * n_per

    rnd = random.Random(0)
    gs = sorted(g([rnd.choice(tasks) for _ in tasks]) for _ in range(REPS))
    return g(tasks), gs[int(.025 * REPS)], gs[int(.975 * REPS)], len(tasks)


def did_ci(groups):
    """(A - B) - (C - D) in solved trials per arm size, bootstrap over the tasks all four arms share."""
    by = [defaultdict(list) for _ in groups]
    for g, ts_ in zip(by, groups):
        for t in ts_:
            g[t["task"]].append(t["solved"])
    tasks = sorted(set.intersection(*(set(g) for g in by)))
    if not tasks:
        return None
    n_per = len(groups[0]) / max(1, len(by[0]))

    def f(ts_):
        m = [[stx.mean(g[x]) for x in ts_] for g in by]
        return sum(a - b - c + d for a, b, c, d in zip(*m)) * n_per

    rnd = random.Random(0)
    fs = sorted(f([rnd.choice(tasks) for _ in tasks]) for _ in range(REPS))
    return f(tasks), fs[int(.025 * REPS)], fs[int(.975 * REPS)], len(tasks)


def did_line(arms, keep, labels, title):
    pick = {label: [t for t in ts_ if keep(t)] for label, _, ts_ in arms}
    if not all(pick.get(x) for x in labels):
        print(f"\n{title}: n/a (an arm has no trials)")
        return
    r = did_ci([pick[x] for x in labels])
    a, b, c, d = labels
    print(f"\n{title}: ({a} - {b}) - ({c} - {d}) = {r[0]:+.0f} solved per arm ({r[1]:+.0f} to {r[2]:+.0f}), {r[3]} tasks")


def table(arms, keep, title, ref=None):
    print(f"\n{title}\n")
    extra = f" Solved gap vs {ref} (95% CI) |" if ref else ""
    print("| Arm | Config | Rounds | Solved | Mean reward | $ per solved | Ended by time | Solved gap vs first arm (95% CI) |"
          + extra)
    print("|---|---|---|---|---|---|---|---|" + ("---|" if ref else ""))
    fmt = lambda r: "n/a" if r is None else f"{r[0]:+.0f} ({r[1]:+.0f} to {r[2]:+.0f}), {r[3]} tasks"
    ref_ts = next(([t for t in ts_ if keep(t)] for label, _, ts_ in arms if label == ref), None)
    base = None
    for label, cfg, ts_ in arms:
        ts_ = [t for t in ts_ if keep(t)]
        if not ts_:
            print(f"| {label} | `{cfg}` | 0 | no trials | | | | |" + (" |" if ref else ""))
            continue
        s = sum(t["solved"] for t in ts_)
        cost = sum(t["cost"] for t in ts_)
        gap = "" if base is None else fmt(gap_ci(ts_, base))
        vs = "" if not ref else (" |" if label == ref or not ref_ts else f" {fmt(gap_ci(ts_, ref_ts))} |")
        print(f"| {label} | `{cfg}` | {len({t['job'] for t in ts_})} | {s} of {len(ts_)} | "
              f"{sum(t['reward'] for t in ts_) / len(ts_):.3f} | {'$%.4f' % (cost / s) if s else 'n/a'} | "
              f"{sum(t['by_time'] for t in ts_)} of {len(ts_)} | {gap} |" + vs)
        if base is None:
            base = ts_


def main():
    argv = sys.argv[2:]
    ref = None
    if "--vs" in argv:
        i = argv.index("--vs"); ref = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    did = None
    if "--did" in argv:
        i = argv.index("--did"); did = argv[i + 1].split(","); argv = argv[:i] + argv[i + 2:]
    own_calls = None
    if "--own-calls" in argv:
        i = argv.index("--own-calls"); own_calls = argv[i + 1].split(","); argv = argv[:i] + argv[i + 2:]
    model, pairs = sys.argv[1], [a.split("=", 1) for a in argv]
    arms = [(label, cfg, load_arm(model, cfg)) for label, cfg in pairs]
    everyone = [t for _, _, ts_ in arms for t in ts_]
    server_load(everyone)
    for t in everyone:
        r = t.get("running")
        t["others"] = None if r is None else max(0.0, r - OWN_SHARE * (1 + own_overlap(t, everyone)))
    if own_calls and os.path.exists(DB):
        own_calls_load(everyone, own_calls)
    table(arms, lambda t: True, "All trials:", ref)
    if did:
        did_line(arms, lambda t: True, did, "Difference of gaps, all trials")
    known = [t for t in everyone if t["others"] is not None]
    if known:
        quiet = sum(t["others"] < 0.5 for t in known)
        print(f"\nServer load known for {len(known)} of {len(everyone)} trials; quiet (other users' load "
              f"below 0.5): {quiet} of {len(known)}. Mean other-user load: {stx.mean(t['others'] for t in known):.2f}.")
        table(arms, lambda t: t["others"] is not None and t["others"] < 0.5, "Quiet trials only:", ref)
        if did:
            did_line(arms, lambda t: t["others"] is not None and t["others"] < 0.5, did, "Difference of gaps, quiet trials")


if __name__ == "__main__":
    main()
