#!/usr/bin/env python3
"""Bar chart: agent time per trial by difficulty, solved vs not solved.

Time is harbor's agent clock -- the clock its `wait_for(agent.run(), timeout=...)` enforces:
  * attempts that finished on their own: the agent_execution span (wait_for returned
    as soon as agent.run() did, so the span is exactly the agent's time)
  * attempts that hit the limit: exactly the limit, e.g. 2400 s. Their recorded span
    is longer, because harbor cancels the agent at the deadline and then waits for it
    to stop before closing the timer; that shutdown lag is excluded here.

Bar = median, whisker = middle 50% (25th-75th percentile).
Medians, not means: times are skewed by trials that run to the agent limit.

Usage:  python3 plot_time_by_difficulty.py <run_dir> <out.svg> ["subtitle"]
"""

from __future__ import annotations

import json
import re
import statistics as st
import sys
from datetime import datetime
from html import escape
from pathlib import Path

TASKS = Path(__file__).resolve().parents[2] / "tasks"
LEVELS = ("easy", "medium", "hard")
SOLVED, UNSOLVED = "#2a78d6", "#898781"          # accent + muted: the question is time-to-solve
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def pct(v, p):
    v = sorted(v)
    k = (len(v) - 1) * p
    f = int(k)
    return v[f] + (v[min(f + 1, len(v) - 1)] - v[f]) * (k - f)


LIMIT_MSG = re.compile(r"timed out after ([0-9.]+) seconds")


def collect(run: Path):
    """Rows with `min` = harbor's agent clock in minutes.

    The limit for a timed-out attempt is read from its own exception message
    ("Agent execution timed out after 2400.0 seconds") -- the value harbor actually
    enforced, including any --agent-timeout-multiplier.
    """
    rows, limits = [], set()
    for p in run.glob("*/result.json"):
        r = json.loads(p.read_text())
        t = p.parent.name.rsplit("__", 1)[0]
        diff = re.search(r'difficulty\s*=\s*"([^"]+)"', (TASKS / t / "task.toml").read_text()).group(1)
        ae = r.get("agent_execution") or {}
        if not (ae.get("started_at") and ae.get("finished_at")):
            continue
        rw = next(iter(((r.get("verifier_result") or {}).get("rewards") or {}).values()), None)
        span = (ts(ae["finished_at"]) - ts(ae["started_at"])).total_seconds() / 60
        ex = r.get("exception_info") or {}
        timed_out = ex.get("exception_type") == "AgentTimeoutError"
        clock = span
        if timed_out:
            m = LIMIT_MSG.search(ex.get("exception_message") or "")
            if m:
                clock = float(m.group(1)) / 60
                limits.add(float(m.group(1)))
        rows.append({"task": t, "diff": diff, "span": span, "min": clock, "solved": rw == 1, "timeout": timed_out})
    # one enforced limit -> draw it; several (mixed runs) -> skip the reference line
    timeout_sec = limits.pop() if len(limits) == 1 else None
    return rows, timeout_sec


def stats(v):
    return {"n": len(v), "median": st.median(v), "mean": st.mean(v), "p25": pct(v, .25), "p75": pct(v, .75)} if v else None


def main(run: Path, dst: str, subtitle: str) -> None:
    rows, timeout_sec = collect(run)
    S = {d: {"solved": stats([x["min"] for x in rows if x["diff"] == d and x["solved"]]),
             "unsolved": stats([x["min"] for x in rows if x["diff"] == d and not x["solved"]]),
             "n": sum(1 for x in rows if x["diff"] == d),
             "tasks_solved": sorted({x["task"] for x in rows if x["diff"] == d and x["solved"]}),
             "solved_timeouts": sum(1 for x in rows if x["diff"] == d and x["solved"] and x["timeout"])}
         for d in LEVELS}

    W, H = 920, 540
    X0, X1, YT, YB, YMAX = 90, 590, 132, 392, 45.0
    py = lambda m: YB - m / YMAX * (YB - YT)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" fill="none" stroke="rgba(11,11,11,0.10)"/>',
         f'<text x="40" y="34" fill="{INK}" font-size="17" font-weight="600">Time per attempt by difficulty — solved vs not solved</text>',
         f'<text x="40" y="55" fill="{INK2}" font-size="12.5">{escape(subtitle)}</text>']

    # legend
    s.append(f'<rect x="42" y="72" width="11" height="11" rx="2" fill="{SOLVED}"/>')
    s.append(f'<text x="60" y="82" fill="{INK2}" font-size="12.5">solved (reward = 1)</text>')
    s.append(f'<rect x="196" y="72" width="11" height="11" rx="2" fill="{UNSOLVED}"/>')
    s.append(f'<text x="214" y="82" fill="{INK2}" font-size="12.5">not solved</text>')
    if timeout_sec:
        s.append(f'<line x1="300" y1="77.5" x2="324" y2="77.5" stroke="{INK2}" stroke-dasharray="5 4"/>')
        s.append(f'<text x="332" y="82" fill="{INK2}" font-size="12.5">{timeout_sec:.0f} s agent limit</text>')
    s.append(f'<text x="470" y="82" fill="{MUTED}" font-size="12">bar = median · whisker = middle 50% of attempts</text>')

    # grid + axis
    for m in range(0, 46, 10):
        y = py(m)
        s.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{GRID}"/>')
        s.append(f'<text x="{X0 - 8}" y="{y + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{m}</text>')
    s.append(f'<line x1="{X0}" y1="{YB}" x2="{X1}" y2="{YB}" stroke="{AXIS}"/>')
    s.append(f'<text x="-{(YT + YB) / 2}" y="40" fill="{INK2}" font-size="12" text-anchor="middle" transform="rotate(-90)">agent time per attempt (minutes, agent clock)</text>')

    if timeout_sec:
        ty = py(timeout_sec / 60)
        s.append(f'<line x1="{X0}" y1="{ty:.1f}" x2="{X1}" y2="{ty:.1f}" stroke="{INK2}" stroke-dasharray="5 4"/>')

    gw = (X1 - X0) / len(LEVELS)
    BW = 50
    for i, d in enumerate(LEVELS):
        c = X0 + gw * (i + .5)
        for key, col, x in (("solved", SOLVED, c - BW - 1), ("unsolved", UNSOLVED, c + 1)):
            v = S[d][key]
            if not v:
                continue
            top = py(v["median"])
            tip = (f"{d}, {key}: median {v['median']:.1f} min, mean {v['mean']:.1f} min, "
                   f"middle 50% {v['p25']:.1f}-{v['p75']:.1f} min, n={v['n']}")
            # bar with rounded top corners, square base on the axis
            r = 4
            s.append(f'<path d="M{x:.1f},{YB} L{x:.1f},{top + r:.1f} Q{x:.1f},{top:.1f} {x + r:.1f},{top:.1f} '
                     f'L{x + BW - r:.1f},{top:.1f} Q{x + BW:.1f},{top:.1f} {x + BW:.1f},{top + r:.1f} L{x + BW:.1f},{YB} Z" '
                     f'fill="{col}"><title>{escape(tip)}</title></path>')
            cx = x + BW / 2
            y1, y2 = py(v["p25"]), py(v["p75"])
            s.append(f'<line x1="{cx:.1f}" y1="{y1:.1f}" x2="{cx:.1f}" y2="{y2:.1f}" stroke="{INK}" stroke-width="1.5"/>')
            for yy in (y1, y2):
                s.append(f'<line x1="{cx - 5:.1f}" y1="{yy:.1f}" x2="{cx + 5:.1f}" y2="{yy:.1f}" stroke="{INK}" stroke-width="1.5"/>')
            # median sits under its own bar, clear of the whisker
            s.append(f'<text x="{cx:.1f}" y="{YB + 17}" fill="{INK}" font-size="12.5" font-weight="600" text-anchor="middle">{v["median"]:.1f}</text>')
            s.append(f'<text x="{cx:.1f}" y="{YB + 31}" fill="{MUTED}" font-size="10.5" text-anchor="middle">n={v["n"]}</text>')
        s.append(f'<text x="{c:.1f}" y="{YB + 52}" fill="{INK}" font-size="13" font-weight="600" text-anchor="middle">{d}</text>')
        sv = S[d]["solved"]["n"] if S[d]["solved"] else 0
        s.append(f'<text x="{c:.1f}" y="{YB + 69}" fill="{INK2}" font-size="11.5" text-anchor="middle">'
                 f'solved {sv}/{S[d]["n"]} ({100 * sv / S[d]["n"]:.0f}%)</text>')

    # small-sample flag on any solved bar resting on one or two tasks
    for i, d in enumerate(LEVELS):
        ts_ = S[d]["tasks_solved"]
        if S[d]["solved"] and len(ts_) <= 2:
            c = X0 + gw * (i + .5)
            which = ", ".join(t.split("-")[0] for t in ts_)
            s.append(f'<text x="{c:.1f}" y="{YB + 85}" fill="{MUTED}" font-size="10.5" text-anchor="middle">'
                     f'every solve was task {which}</text>')

    # takeaway panel
    bx = 628
    s.append(f'<text x="{bx}" y="140" fill="{INK}" font-size="13.5" font-weight="600">What it shows</text>')
    med = [S[d]["solved"]["median"] for d in LEVELS if S[d]["solved"]]
    lines = [
        (INK, 12.5, f"Solves take {min(med):.0f}–{max(med):.0f} min at every"),
        (INK, 12.5, "difficulty."),
        (INK2, 11.5, "Difficulty changes how often the"),
        (INK2, 11.5, "agent solves, not how long it takes."),
        (None, 0, ""),
        (INK, 12.5, "Unsolved attempts are the slow ones."),
        (INK2, 11.5, "Most run until the agent limit"),
        (INK2, 11.5, "kills them."),
    ]
    y = 168
    for col, fs, txt in lines:
        if col:
            s.append(f'<text x="{bx}" y="{y}" fill="{col}" font-size="{fs}">{escape(txt)}</text>')
        y += 19 if col else 10
    y += 10
    s.append(f'<line x1="{bx}" y1="{y}" x2="{W - 36}" y2="{y}" stroke="{GRID}"/>')
    y += 22
    for d in LEVELS:
        u = S[d]["unsolved"]
        if u:
            s.append(f'<text x="{bx}" y="{y}" fill="{INK2}" font-size="11.5">{d}: {u["n"]} unsolved, median {u["median"]:.1f} min</text>')
            y += 18
    # timed-out attempts are counted at the limit; say how much shutdown lag that excludes
    to_spans = [x["span"] for x in rows if x["timeout"]]
    if timeout_sec and to_spans:
        lag = st.median(to_spans) - timeout_sec / 60
        y += 8
        s.append(f'<text x="{bx}" y="{y}" fill="{MUTED}" font-size="11">{len(to_spans)} timed-out attempts are counted at</text>')
        s.append(f'<text x="{bx}" y="{y + 15}" fill="{MUTED}" font-size="11">exactly {timeout_sec:.0f} s. The ~{lag * 60:.0f} s the agent takes</text>')
        s.append(f'<text x="{bx}" y="{y + 30}" fill="{MUTED}" font-size="11">to stop after the limit is excluded.</text>')
        y += 30
    st_ = sum(S[d]["solved_timeouts"] for d in LEVELS)
    if st_:
        y += 22
        s.append(f'<text x="{bx}" y="{y}" fill="{MUTED}" font-size="11">{st_} attempts hit the limit and were still</text>')
        s.append(f'<text x="{bx}" y="{y + 15}" fill="{MUTED}" font-size="11">graded as solved.</text>')

    s.append(f'<line x1="40" y1="{H - 36}" x2="{W - 40}" y2="{H - 36}" stroke="{GRID}"/>')
    s.append(f'<text x="40" y="{H - 16}" fill="{INK2}" font-size="11.5">Agent clock = the time harbor\'s agent timeout measures. '
             f'Numbers under each bar are medians in minutes. Hover a bar for mean, middle 50% and n.</text>')
    s.append("</svg>")
    Path(dst).write_text("\n".join(s))
    print(f"wrote {dst}")
    for d in LEVELS:
        a, b = S[d]["solved"], S[d]["unsolved"]
        print(f"  {d:<7} solved n={a['n'] if a else 0:<3} median={a['median'] if a else float('nan'):5.1f}   "
              f"unsolved n={b['n'] if b else 0:<3} median={b['median'] if b else float('nan'):5.1f}   "
              f"solved-but-timed-out={S[d]['solved_timeouts']}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(Path(sys.argv[1]), sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
