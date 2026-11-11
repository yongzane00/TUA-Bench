#!/usr/bin/env python3
"""The professor's delivery metrics (plan p4, p5, p7) for every finished hidden / shown budget pair.

    python3 plan_metrics.py [qwen38|qwen36] [--h2]          (default: both models; prints markdown)

Per run (40 tasks x 5 attempts):
  solved        trials with reward 1 (the plan's "qualified delivery before the deadline"), x of 200
  $/solved      total cost_usd of the run / solved trials (failed trials' spend included)
  ended by time trials stopped by the budget or by Harbor's agent time limit; "empty" = of those, reward 0
  overrun       for trials whose clock reached the budget: seconds past it when the agent stopped
                (harness clock, budget.elapsed_sec); P50 / P95 / max
Per pair (shown - hidden, same budget):
  solved gap with a 95% CI from a paired bootstrap over the 40 tasks (attempts stay with their task)
  route A: gap >= +10 of 200 (the plan's 5 points), CI lower bound > 0, $/solved at most 5% worse
  route B: $/solved at least 15% lower, CI lower bound of the gap > -6 of 200 (the plan's -3 points)
H1 (--h1 is always on): the solved gap split by task class, classes taken from OTHER runs of the base arm:
  capable      base solved the task at least once in 5 tries at 12000 s
  time-limited base was ended by time in at least 3 of 5 tries at 3600 s
H2 (--h2, reads trajectories, slow): when the agent first declares the task complete (mark_task_complete),
  and how many ended-by-time trials never declared it.
"""
import glob
import json
import os
import random
import statistics as stx
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_budget_curve import runs  # noqa: E402

REPS = 4000


def trials(run, budget):
    out = []
    for p in sorted(glob.glob(f"{run}/*__*/result.json")):
        r = json.load(open(p, encoding="utf-8"))
        rw = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward", 0) or 0
        ar = r.get("agent_result") or {}
        bud = (ar.get("metadata") or {}).get("budget") or {}
        exc = (r.get("exception_info") or {}).get("exception_type")
        ae = r.get("agent_execution") or {}
        wall = None
        if ae.get("started_at") and ae.get("finished_at"):
            wall = (datetime.fromisoformat(ae["finished_at"].rstrip("Z")) -
                    datetime.fromisoformat(ae["started_at"].rstrip("Z"))).total_seconds()
        elapsed = bud.get("elapsed_sec", wall)
        by_time = bud.get("stop") == "time" or exc == "AgentTimeoutError"
        out.append(dict(task=os.path.basename(os.path.dirname(p)).split("__")[0], reward=rw, solved=rw >= 1,
                        cost=ar.get("cost_usd") or 0.0, by_time=by_time, elapsed=elapsed, wall=wall,
                        overrun=(elapsed - budget) if (elapsed is not None and elapsed >= budget - 1) else None,
                        dir=os.path.dirname(p)))
    return out


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def summary(ts):
    n, s = len(ts), sum(t["solved"] for t in ts)
    cost = sum(t["cost"] for t in ts)
    bt = [t for t in ts if t["by_time"]]
    ov = [t["overrun"] for t in ts if t["overrun"] is not None]
    return dict(n=n, solved=s, score=sum(t["reward"] for t in ts) / n, cost=cost,
                per_solved=cost / s if s else None, by_time=len(bt), empty=sum(not t["solved"] and t["reward"] == 0 for t in bt),
                ov50=pct(ov, .5), ov95=pct(ov, .95), ovmax=max(ov) if ov else None, n_ov=len(ov))


def by_task(ts, key):
    d = defaultdict(list)
    for t in ts:
        d[t["task"]].append(t[key])
    return d


def paired_gap(sh, hi, tasks):
    """Solved gap shown - hidden in trials (scaled to the run size), with a paired bootstrap 95% CI over tasks."""
    a, b = by_task(sh, "solved"), by_task(hi, "solved")
    ca, cb = by_task(sh, "cost"), by_task(hi, "cost")
    scale = len(sh) / len(tasks)  # trials per task

    def gap(ts):
        return sum(stx.mean(a[t]) - stx.mean(b[t]) for t in ts) * scale

    def ratio(ts):  # $/solved shown / $/solved hidden
        sa = sum(stx.mean(a[t]) for t in ts); sb = sum(stx.mean(b[t]) for t in ts)
        if not sa or not sb:
            return None
        return (sum(stx.mean(ca[t]) for t in ts) / sa) / (sum(stx.mean(cb[t]) for t in ts) / sb)

    rnd = random.Random(0)
    gs, rs = [], []
    for _ in range(REPS):
        smp = [rnd.choice(tasks) for _ in tasks]
        gs.append(gap(smp))
        r = ratio(smp)
        if r is not None:
            rs.append(r)
    gs.sort(); rs.sort()
    return gap(tasks), gs[int(.025 * REPS)], gs[int(.975 * REPS)], ratio(tasks), pct(rs, .025), pct(rs, .975)


def first_complete(trial_dir):
    """Seconds from the first agent step to the first mark_task_complete call, or None."""
    p = os.path.join(trial_dir, "agent", "trajectory.json")
    if not os.path.exists(p):
        return None
    try:
        steps = json.load(open(p, encoding="utf-8")).get("steps") or []
    except Exception:
        return None
    t0 = None
    for s in steps:
        ts = s.get("timestamp")
        if ts and t0 is None:
            t0 = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        for c in s.get("tool_calls") or []:
            if c.get("function_name") == "mark_task_complete" and ts and t0:
                return (datetime.fromisoformat(ts.replace("Z", "+00:00")) - t0).total_seconds()
    return None


def fmt(x, f="{:.0f}"):
    return "n/a" if x is None else f.format(x)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want = set(args) or {"qwen38", "qwen36"}
    h2 = "--h2" in sys.argv
    allruns = runs()
    for mk in ("qwen38", "qwen36"):
        if mk not in want:
            continue
        budgets = sorted({b for (m, a, b) in allruns if m == mk})
        data = {(a, b): trials(allruns[(mk, a, b)], b) for (m, a, b) in allruns if m == mk}
        print(f"\n## {mk}\n")
        print("| Budget (s) | Arm | Solved | Mean reward | Total $ | $ per solved | Ended by time | Of those, reward 0 | "
              "Overrun P50 / P95 / max (s), n |")
        print("|---|---|---|---|---|---|---|---|---|")
        for b in budgets:
            for arm in ("hidden", "shown"):
                if (arm, b) not in data:
                    continue
                s = summary(data[(arm, b)])
                print(f"| {b} | {arm} | {s['solved']} of {s['n']} | {s['score']:.3f} | ${s['cost']:.2f} | "
                      f"${fmt(s['per_solved'], '{:.4f}')} | {s['by_time']} of {s['n']} | {s['empty']} of {s['by_time']} | "
                      f"{fmt(s['ov50'])} / {fmt(s['ov95'])} / {fmt(s['ovmax'])}, {s['n_ov']} |")
        print("\nPaired shown - hidden (bootstrap over 40 tasks):\n")
        print("| Budget (s) | Solved gap (of 200) | 95% CI | $ per solved, shown / hidden | 95% CI | Route A | Route B |")
        print("|---|---|---|---|---|---|---|")
        for b in budgets:
            if ("hidden", b) not in data or ("shown", b) not in data:
                continue
            sh, hi = data[("shown", b)], data[("hidden", b)]
            tasks = sorted(set(by_task(sh, "solved")) & set(by_task(hi, "solved")))
            g, glo, ghi, r, rlo, rhi = paired_gap(sh, hi, tasks)
            route_a = g >= 10 and glo > 0 and r is not None and r <= 1.05
            route_b = r is not None and r <= 0.85 and glo > -6
            print(f"| {b} | {g:+.0f} | {glo:+.0f} to {ghi:+.0f} | {fmt(r, '{:.2f}')} | {fmt(rlo, '{:.2f}')} to {fmt(rhi, '{:.2f}')} | "
                  f"{'pass' if route_a else 'no'} | {'pass' if route_b else 'no'} |")

        # H1: task classes from other base-arm runs
        cap_run, lim_run = data.get(("hidden", 12000)), data.get(("hidden", 3600))
        if cap_run and lim_run:
            cap = {t for t, v in by_task(cap_run, "solved").items() if sum(v) >= 1}
            lim = {t for t, v in by_task(lim_run, "by_time").items() if sum(v) >= 3}
            cls = lambda t: ("capable, time-limited" if t in cap and t in lim else
                             "capable, not time-limited" if t in cap else "not solved at 12000 s")
            print("\nH1: solved gap by task class (classes from the base arm at 12000 s and 3600 s, not from the pair):\n")
            names = ["capable, time-limited", "capable, not time-limited", "not solved at 12000 s"]
            print("| Budget (s) | " + " | ".join(f"{c}" for c in names) + " |")
            print("|---|" + "---|" * len(names))
            sizes = defaultdict(int)
            for t in by_task(cap_run, "solved"):
                sizes[cls(t)] += 1
            for b in budgets:
                if ("hidden", b) not in data or ("shown", b) not in data or b in (3600, 12000):
                    continue
                a, h = by_task(data[("shown", b)], "solved"), by_task(data[("hidden", b)], "solved")
                cells = []
                for c in names:
                    ts = [t for t in a if t in h and cls(t) == c]
                    sa, sh_ = sum(sum(a[t]) for t in ts), sum(sum(h[t]) for t in ts)
                    cells.append(f"{sa - sh_:+d}: {sh_} to {sa} of {sum(len(a[t]) for t in ts)}")
                print(f"| {b} | " + " | ".join(cells) + " |")
            print("\nClass sizes (tasks): " + ", ".join(f"{c} {sizes[c]}" for c in names))
            print("(3600 s and 12000 s rows are left out: their base runs define the classes.)")

        if h2:
            print("\nH2: first declaration of completion (mark_task_complete), seconds from the first step:\n")
            print("| Budget (s) | Arm | Trials that declared | Median first declaration (s) | Ended by time and never declared |")
            print("|---|---|---|---|---|")
            for b in budgets:
                for arm in ("hidden", "shown"):
                    if (arm, b) not in data:
                        continue
                    ts = data[(arm, b)]
                    fc = [first_complete(t["dir"]) for t in ts]
                    dec = [x for x in fc if x is not None]
                    never = sum(1 for t, x in zip(ts, fc) if t["by_time"] and x is None)
                    print(f"| {b} | {arm} | {len(dec)} of {len(ts)} | {fmt(stx.median(dec) if dec else None)} | "
                          f"{never} of {sum(t['by_time'] for t in ts)} |")


if __name__ == "__main__":
    main()
