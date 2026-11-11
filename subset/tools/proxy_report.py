#!/usr/bin/env python3
"""Join the time-budget proxy's event log with the Harbor trials it served (batch 4 secondary metrics).

    python3 proxy_report.py <proxy events.jsonl> <job dir> [<job dir> ...] [--budget 900] [--datasets <dir>] [--pairs]

Each proxy run (one per conversation) is matched to one trial: its first request must fall inside the trial's agent
execution, and, when the proxy recorded the run's first user message (`first_user`, proxy v17 on), that text must
contain the start of the task's instruction. Among the candidates the pair whose start and end times lie closest
wins, one to one. Reported per job set:
  matched           trials with exactly one run, and runs left without a trial (a "failed proxy match" in the
                    analysis plan: a trial's requests split over two runs, or two trials in one run)
  close calls       trials whose best and second-best run differ by less than 5 s in timing (possible swaps; only
                    possible when two trials of the same task run at once)
  stopped by time   runs whose reply was cut at the deadline or that were refused after it
  lateness          the trial's agent end minus the run's deadline (run start + budget), for runs stopped by time:
                    how long the agent took to finish after the deadline (its running command, its own wrap-up)
  replies           model replies per trial; last answer: when the last reply that finished in time ended
"""
import glob
import json
import re
import statistics as stx
import sys
from datetime import datetime
from pathlib import Path


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def norm(text):
    return " ".join(re.sub(r"\s+", " ", text or "").split()).lower()


def load_runs(path):
    runs = {}
    for line in open(path, encoding="utf-8"):
        e = json.loads(line)
        r = runs.setdefault(e["run_id"], dict(start=None, first_user=None, calls=[], cut=False, refused=False,
                                              last=e["ts"], wrapup=None))
        r["last"] = max(r["last"], e["ts"])
        if e["event"] == "agent_start":
            r["start"] = e["ts"]
        elif e["event"] == "model_input" and e.get("first_user") is not None:
            r["first_user"] = norm(e["first_user"])
        elif e["event"] == "model_call":
            r["calls"].append(e)
            r["cut"] |= bool(e.get("cut_by_deadline"))
        elif e["event"] == "wrapup_notice":
            r["wrapup"] = e["elapsed_s"]
        elif e["event"] == "agent_end" and e.get("exit_reason") == "budget stop":
            r["refused"] = True
    return {k: v for k, v in runs.items() if v["start"] is not None}


def load_trials(job_dirs, datasets):
    trials = []
    for d in job_dirs:
        for p in sorted(glob.glob(f"{d}/*__*/result.json")):
            r = json.load(open(p))
            ex = r.get("agent_execution") or {}
            if not ex.get("started_at"):
                continue
            task = r["trial_name"].rsplit("__", 1)[0]
            inst = Path(datasets) / task / "instruction.md"
            trials.append(dict(name=r["trial_name"], task=task, start=ts(ex["started_at"]),
                               end=ts(ex["finished_at"]) if ex.get("finished_at") else None,
                               reward=((r.get("verifier_result") or {}).get("rewards") or {}).get("reward", 0) or 0,
                               head=norm(inst.read_text(encoding="utf-8"))[:80] if inst.exists() else None))
    return trials


def match(trials, runs):
    pairs = []
    for t in trials:
        for rid, r in runs.items():
            end = t["end"] or r["last"]
            if not (t["start"] - 5 <= r["start"] <= end + 5):
                continue
            if t["head"] and r["first_user"] and t["head"] not in r["first_user"]:
                continue
            pairs.append((abs(r["start"] - t["start"]) + abs(r["last"] - end), t["name"], rid))
    pairs.sort()
    by_trial = {}
    for score, tn, rid in pairs:
        by_trial.setdefault(tn, []).append(score)
    close = sum(1 for s in by_trial.values() if len(s) > 1 and s[1] - s[0] < 5)
    got_t, got_r, out = set(), set(), {}
    for score, tn, rid in pairs:
        if tn not in got_t and rid not in got_r:
            got_t.add(tn)
            got_r.add(rid)
            out[tn] = rid
    return out, close


def main():
    args = sys.argv[1:]
    budget = float(args[args.index("--budget") + 1]) if "--budget" in args else 900.0
    datasets = args[args.index("--datasets") + 1] if "--datasets" in args else "/home/<win-user>/work/datasets/swe-bench-verified"
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or not args[i - 1].startswith("--"))]
    runs, trials = load_runs(pos[0]), load_trials(pos[1:], datasets)
    m, close = match(trials, runs)
    late, replies, last_answer, stopped = [], [], [], 0
    for t in trials:
        r = runs.get(m.get(t["name"]))
        if not r:
            continue
        ok = [c for c in r["calls"] if c.get("status") == "success"]
        replies.append(len(r["calls"]))
        if ok:
            last_answer.append(ok[-1]["elapsed_s"])
        if r["cut"] or r["refused"]:
            stopped += 1
            if t["end"]:
                late.append(t["end"] - (r["start"] + budget))
    n = len(trials)
    print(f"{len(pos) - 1} job folder(s), {n} trials, {len(runs)} proxy runs, budget {budget:.0f} s\n")
    print("| Measure | Value |")
    print("|---|---|")
    print(f"| Trials matched to exactly one run | {len(m)} of {n} |")
    print(f"| Proxy runs without a trial | {len(runs) - len(m)} of {len(runs)} |")
    print(f"| Close calls (possible swaps) | {close} of {n} |")
    print(f"| Stopped by time | {stopped} of {len(m)} |")
    if late:
        q = sorted(late)
        p95 = q[min(len(q) - 1, int(round(0.95 * (len(q) - 1))))]
        print(f"| Lateness after the deadline, median / P95 / max (s) | {stx.median(q):.1f} / {p95:.1f} / {q[-1]:.1f} |")
    if replies:
        print(f"| Replies per trial, median | {stx.median(replies):.0f} |")
    if last_answer:
        print(f"| Last reply finished in time, median (s from the run's start) | {stx.median(last_answer):.0f} |")
    print(f"| Reward 1 | {sum(t['reward'] == 1 for t in trials)} of {n} |")
    if "--pairs" in args:
        print("\n| Trial | Proxy run | Replies | Stopped by time | Reward |")
        print("|---|---|---|---|---|")
        for t in trials:
            rid = m.get(t["name"])
            r = runs.get(rid) or {}
            print(f"| {t['name']} | {rid or '-'} | {len(r.get('calls', []))} | "
                  f"{'yes' if r.get('cut') or r.get('refused') else 'no'} | {t['reward']:g} |")


if __name__ == "__main__":
    main()
