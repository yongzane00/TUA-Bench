#!/usr/bin/env python3
"""Per-task accuracy-vs-cost SVG for a harbor run, from task_report.py's JSON.

Graded tasks are plotted at (cost per attempt, mean reward over graded attempts).
Tasks with no grade on any attempt can't be placed on the y axis, so -- if there are
any -- they sit in a strip below the plot at their true cost.

The right-hand panel adapts:
  * run with ungraded tasks -> outcome breakdown + "two scores, neither valid"
  * clean run               -> leaderboard headline (needs the extra JSON keys below)

Optional JSON keys (add them before plotting):
  harbor_mean, score_py                      both modes
  ci_lo, ci_hi, pass1, pass5, all5, timeouts clean-run headline
  labels: {task: [text, dx, dy, anchor, leader_dy]}   points to annotate

Usage:
  python3 task_report.py <run_dir> --json r.json
  python3 plot_accuracy_cost.py r.json out.svg "subtitle text" ["title model name"]
"""

from __future__ import annotations

import json
import sys
from html import escape

# Validated palette (dataviz reference, first three slots pass all-pairs in light mode).
DIFF_COLOR = {"easy": "#2a78d6", "medium": "#eb6834", "hard": "#1baf7a"}
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"

W, H = 960, 572
AX0, AX1, AY_TOP = 86, 610, 122
XMAX = 0.09
ROW = 11


def marker(diff: str, x: float, y: float, filled: bool, tip: str) -> str:
    col = DIFF_COLOR[diff]
    fill, stroke = (col, SURFACE) if filled else (SURFACE, col)
    if diff == "easy":
        shape = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6"'
    elif diff == "medium":
        shape = f'<rect x="{x - 5.5:.1f}" y="{y - 5.5:.1f}" width="11" height="11" rx="2"'
    else:
        shape = (f'<path d="M{x:.1f},{y - 7.5:.1f} L{x + 7.5:.1f},{y:.1f} '
                 f'L{x:.1f},{y + 7.5:.1f} L{x - 7.5:.1f},{y:.1f} Z"')
    tag = shape.split()[0][1:]
    return f'{shape} fill="{fill}" stroke="{stroke}" stroke-width="2"><title>{escape(tip)}</title></{tag}>'


def main(src: str, dst: str, subtitle: str, model: str) -> None:
    d = json.load(open(src))
    rows = d["rows"]
    graded = [r for r in rows if r["graded"] > 0]
    ungraded = [r for r in rows if r["graded"] == 0]
    clean = not ungraded
    oc, n = d["outcomes"], d["n_trials"]
    n_graded = oc.get("pass", 0) + oc.get("partial", 0) + oc.get("fail", 0)
    labels = d.get("labels", {})

    ay_bot = 450 if clean else 388
    strip_y0 = ay_bot + 30

    def px(c):
        return AX0 + min(c, XMAX) / XMAX * (AX1 - AX0)

    def py(r):
        return ay_bot - r * (ay_bot - AY_TOP)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" fill="none" stroke="rgba(11,11,11,0.10)"/>',
         f'<text x="40" y="34" fill="{INK}" font-size="17" font-weight="600">terminus-2 × {escape(model)} — accuracy vs cost, per task</text>',
         f'<text x="40" y="55" fill="{INK2}" font-size="12.5">{escape(subtitle)}</text>']

    # legend
    lx, ly = 42, 80
    for diff in ("easy", "medium", "hard"):
        s.append(marker(diff, lx + 6, ly, True, diff))
        s.append(f'<text x="{lx + 18}" y="{ly + 4}" fill="{INK2}" font-size="12.5">{diff}</text>')
        lx += 86
    if not clean:
        s.append(f'<circle cx="{lx + 10}" cy="{ly}" r="6" fill="{SURFACE}" stroke="{MUTED}" stroke-width="2"/>')
        s.append(f'<text x="{lx + 22}" y="{ly + 4}" fill="{INK2}" font-size="12.5">hollow = never graded (harness fault)</text>')
    else:
        s.append(f'<text x="{lx + 4}" y="{ly + 4}" fill="{MUTED}" font-size="12">one point per task · 5 attempts each</text>')

    # ---------- panel A ----------
    s.append(f'<text x="40" y="110" fill="{INK}" font-size="13.5" font-weight="600">{"All 40 tasks" if clean else "Graded tasks"}</text>')
    s.append(f'<text x="{140 if clean else 136}" y="110" fill="{MUTED}" font-size="11">mean reward over graded attempts</text>')
    for r in (0, .25, .5, .75, 1):
        y = py(r)
        s.append(f'<line x1="{AX0}" y1="{y}" x2="{AX1}" y2="{y}" stroke="{GRID}"/>')
        s.append(f'<text x="{AX0 - 8}" y="{y + 4}" fill="{MUTED}" font-size="11" text-anchor="end">{int(r * 100)}%</text>')
    s.append(f'<line x1="{AX0}" y1="{ay_bot}" x2="{AX1}" y2="{ay_bot}" stroke="{AXIS}"/>')
    s.append(f'<text x="-{(AY_TOP + ay_bot) / 2}" y="30" fill="{INK2}" font-size="12" text-anchor="middle" transform="rotate(-90)">mean reward</text>')

    for r in sorted(graded, key=lambda r: r["difficulty"] == "hard"):
        x, y = px(r["cost_per_attempt"]), py(r["mean_reward_graded"])
        tip = (f'{r["task"]} ({r["difficulty"]}, {r["image"]}) — reward {r["mean_reward_graded"]:.2f}, '
               f'{r["passes"]}/{r["attempts"]} passed, ${r["cost_per_attempt"]:.4f}/attempt')
        s.append(marker(r["difficulty"], x, y, True, tip))
        if r["task"] in labels:
            text, dx, dy, anchor, *rest = labels[r["task"]]
            leader = rest[0] if rest else None
            if leader:
                s.append(f'<line x1="{x:.1f}" y1="{y - 8:.1f}" x2="{x + dx:.1f}" y2="{y + dy + 3:.1f}" stroke="{MUTED}"/>')
            s.append(f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" fill="{INK}" font-size="11" text-anchor="{anchor}">{escape(text)}</text>')

    xa = ay_bot
    if ungraded:
        s.append(f'<line x1="{AX0}" y1="{strip_y0 - 16}" x2="{AX1}" y2="{strip_y0 - 16}" stroke="{GRID}" stroke-dasharray="3 3"/>')
        s.append(f'<text x="{AX0 - 8}" y="{strip_y0 + 4}" fill="{INK2}" font-size="11" text-anchor="end">never</text>')
        s.append(f'<text x="{AX0 - 8}" y="{strip_y0 + 17}" fill="{INK2}" font-size="11" text-anchor="end">graded</text>')
        rows_taken: list[list[float]] = []
        ys = []
        for r in sorted(ungraded, key=lambda r: r["cost_per_attempt"]):
            x = px(r["cost_per_attempt"])
            for k, taken in enumerate(rows_taken):
                if all(abs(x - t) >= ROW + 2 for t in taken):
                    taken.append(x)
                    break
            else:
                rows_taken.append([x])
                k = len(rows_taken) - 1
            y = strip_y0 + k * ROW
            ys.append(y)
            oc_t = ", ".join(f"{a} {b}" for a, b in sorted(r["outcomes"].items()))
            s.append(marker(r["difficulty"], x, y, False,
                            f'{r["task"]} ({r["difficulty"]}, {r["image"]}) — no grade: {oc_t}'))
        xa = max(ys) + 20
        s.append(f'<line x1="{AX0}" y1="{xa}" x2="{AX1}" y2="{xa}" stroke="{AXIS}"/>')
    for t in (0, .02, .04, .06, .08):
        s.append(f'<text x="{px(t):.1f}" y="{xa + 16}" fill="{MUTED}" font-size="11" text-anchor="middle">${t:.2f}</text>')
    s.append(f'<text x="{(AX0 + AX1) / 2}" y="{xa + 36}" fill="{INK2}" font-size="12" text-anchor="middle">cost per attempt (USD)</text>')

    # ---------- panel B ----------
    bx, bw = 668, 250
    s.append(f'<text x="{bx}" y="110" fill="{INK}" font-size="13.5" font-weight="600">{n} trials</text>')

    def bar(y, count, label, detail, filled, sub=None):
        w = count / n * bw
        s.append(f'<text x="{bx}" y="{y}" fill="{INK}" font-size="12" font-weight="600">{label} — {count}</text>')
        if filled:
            s.append(f'<rect x="{bx}" y="{y + 7}" width="{w:.1f}" height="13" rx="4" fill="{INK2}"/>')
        else:
            s.append(f'<rect x="{bx + 1}" y="{y + 8}" width="{max(w - 2, 0):.1f}" height="11" rx="3" fill="none" stroke="{MUTED}" stroke-width="2" stroke-dasharray="4 3"/>')
        s.append(f'<text x="{bx}" y="{y + 36}" fill="{INK2}" font-size="11.5">{escape(detail)}</text>')
        if sub:
            s.append(f'<text x="{bx}" y="{y + 52}" fill="{MUTED}" font-size="11">{escape(sub)}</text>')

    def stat(y, big, name, note):
        s.append(f'<text x="{bx}" y="{y}" fill="{INK}" font-size="20" font-weight="600">{big}</text>')
        s.append(f'<text x="{bx + 72}" y="{y - 5}" fill="{INK}" font-size="12">{escape(name)}</text>')
        s.append(f'<text x="{bx + 72}" y="{y + 9}" fill="{MUTED}" font-size="11">{escape(note)}</text>')

    if clean:
        bar(136, n_graded, "graded", f'{oc.get("pass", 0)} pass · {oc.get("partial", 0)} partial · {oc.get("fail", 0)} fail',
            True, f'{d["timeouts"]} of the fails were timeouts ({100 * d["timeouts"] / n:.0f}%)')
        s.append(f'<line x1="{bx}" y1="{206}" x2="{bx + bw}" y2="{206}" stroke="{GRID}"/>')
        s.append(f'<text x="{bx}" y="228" fill="{INK}" font-size="12.5" font-weight="600">Headline</text>')
        stat(260, f'{d["score_py"]:.3f}', "stratified S", f'95% CI {d["ci_lo"]:.2f}–{d["ci_hi"]:.2f} · subset → 120 tasks')
        stat(300, f'{d["harbor_mean"]:.3f}', "mean reward", "unweighted over 40 tasks")
        stat(340, f'{100 * d["pass1"]:.1f}%', "Pass@1", "reward = 1 on a single attempt")
        stat(380, f'{100 * d["pass5"]:.1f}%', "Pass@5", "solved in at least 1 of 5")
        stat(420, f'{100 * d["all5"]:.1f}%', "All-5", "solved in all 5")
        yb = 450
    else:
        wasted = sum(r["cost_total"] for r in ungraded)
        bar(136, n_graded, "graded", f'{oc.get("pass", 0)} pass · {oc.get("partial", 0)} partial · {oc.get("fail", 0)} fail', True)
        bar(196, n - n_graded, "never graded",
            f'{oc.get("uid", 0)} UID · {oc.get("timeout", 0)} timeout · {oc.get("infra", 0)} infra · {oc.get("error", 0)} error', False)
        imgs = ", ".join(sorted({r["image"] for r in ungraded}))
        s.append(f'<text x="{bx}" y="250" fill="{MUTED}" font-size="11">{len(ungraded)} tasks, all {escape(imgs)} — ${wasted:.2f} spent</text>')
        s.append(f'<line x1="{bx}" y1="264" x2="{bx + bw}" y2="264" stroke="{GRID}"/>')
        s.append(f'<text x="{bx}" y="286" fill="{INK}" font-size="12.5" font-weight="600">Two scores, neither valid</text>')
        stat(314, f'{d["harbor_mean"]:.3f}', "harbor mean", "ungraded counted as 0 — too low")
        stat(358, f'{d["score_py"]:.3f}', "score.py, stratified", "ungraded dropped — too high")
        g = sum(1 for r in rows if r["graded"])
        by = {k: (sum(1 for r in graded if r["difficulty"] == k), sum(1 for r in rows if r["difficulty"] == k)) for k in DIFF_COLOR}
        stat(402, f'{g}/{len(rows)}', "tasks with any grade",
             f'easy {by["easy"][0]}/{by["easy"][1]} · medium {by["medium"][0]}/{by["medium"][1]} · hard {by["hard"][0]}/{by["hard"][1]}')
        yb = 432
    s.append(f'<line x1="{bx}" y1="{yb}" x2="{bx + bw}" y2="{yb}" stroke="{GRID}"/>')
    s.append(f'<text x="{bx}" y="{yb + 22}" fill="{INK2}" font-size="11.5">${d["total_cost"]:.2f} total · ${d["total_cost"] / n:.4f} per trial</text>')
    s.append(f'<text x="{bx}" y="{yb + 38}" fill="{MUTED}" font-size="11">proxy pricing: $0.15/M in, $0.47/M out</text>')

    s.append(f'<line x1="40" y1="{H - 38}" x2="{W - 40}" y2="{H - 38}" stroke="{GRID}"/>')
    foot = ("Hover a point for task, reward and cost. Every trial produced a grade."
            if clean else
            "Hover a point for task, reward and cost. The never-graded strip is the harbor UID bug, not model performance — see subset/RUNNING.md.")
    s.append(f'<text x="40" y="{H - 17}" fill="{INK2}" font-size="11.5">{escape(foot)}</text>')
    s.append("</svg>")
    open(dst, "w").write("\n".join(s))
    print(f"wrote {dst}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "",
         sys.argv[4] if len(sys.argv) > 4 else "qwen3.8-flash-next")
