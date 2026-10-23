#!/usr/bin/env python3
"""Accuracy-vs-cost SVG with one dot per harness run, computed straight from the job dirs.

y, chosen with --metric:
  success     (default) share of attempts solved (reward = 1), every task weighted equally --
              plain accuracy over the 40 tasks; 95% bootstrap over tasks, then attempts
  stratified  subset/score.py's S, re-weighted to the 120-task difficulty mix; bootstrap
              resamples tasks within difficulty
x = proxy cost per attempt from the token counts in each trial's result.json. The panel also
shows the leak-adjusted value (trials whose commands ran `chrome_state.py solved`, the task's
own solution script, scored 0). --note adds a footnote line (repeatable).

Usage:
  python3 plot_harness_compare.py out.svg [--metric=success|stratified] [--note="..."] \
      "H0|stock terminus-2|jobs/harness0-attempt5/<ts>" "H1|instruction re-check|jobs/harness1-attempt5/<ts>" ...
"""

from __future__ import annotations

import json
import random
import re
import statistics
import sys
from collections import defaultdict
from html import escape
from pathlib import Path

TASKS = Path(__file__).resolve().parents[2] / "tasks"
W8 = {"easy": 22 / 120, "medium": 90 / 120, "hard": 8 / 120}
PRICE_IN, PRICE_OUT = 0.15e-6, 0.47e-6

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
COLORS = ["#52514e", "#eb6834", "#2a78d6", "#1baf7a"]  # baseline in ink, variants in the validated palette
SHAPES = ["circle", "square", "diamond", "triangle"]
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"
WIDTH, HEIGHT = 900, 560
AX0, AX1, AY0, AY1 = 90, 620, 110, 430  # plot box: x left/right, y top/bottom
XMAX, YMAX = 0.07, 0.8

_diff: dict[str, str] = {}


def difficulty(task: str) -> str:
    if task not in _diff:
        _diff[task] = re.search(r'difficulty\s*=\s*"(\w+)"', (TASKS / task / "task.toml").read_text()).group(1)
    return _diff[task]


def ran_solved(trial: Path) -> bool:
    for e in trial.glob("agent/episode-*/response.txt"):
        m = re.search(r"\{.*\}", e.read_text(errors="ignore"), re.S)
        try:
            cmds = "\n".join(c.get("keystrokes", "") for c in json.loads(m.group(0)).get("commands", []))
        except Exception:
            continue
        if re.search(r"chrome_state(\.py)?\s+solved", cmds):
            return True
    return False


def score(by: dict[str, list[float]], metric: str) -> float:
    if metric == "success":
        return statistics.mean(statistics.mean(v) for v in by.values())  # each task weighted equally
    keys = {k: [t for t in by if difficulty(t) == k] for k in W8}
    return sum(W8[k] * statistics.mean(x for t in ts for x in by[t]) for k, ts in keys.items())


def bootstrap(by: dict[str, list[float]], metric: str, reps: int = 10000) -> tuple[float, float]:
    rng = random.Random(0)
    groups = ({"all": list(by)} if metric == "success"
              else {k: [t for t in by if difficulty(t) == k] for k in W8})
    weight = {"all": 1.0, **W8}
    vals = []
    for _ in range(reps):
        tot = 0.0
        for k, ts in groups.items():
            pool = []
            for _ in ts:
                t = rng.choice(ts)
                pool.append(statistics.mean(rng.choice(by[t]) for _ in by[t]))
            tot += weight[k] * statistics.mean(pool)
        vals.append(tot)
    vals.sort()
    return vals[int(reps * .025)], vals[int(reps * .975) - 1]


def summarize(run: Path, metric: str) -> dict:
    raw, adj = defaultdict(list), defaultdict(list)
    tin = tout = n = 0
    rewards = []
    for r in sorted(run.glob("*__*/result.json")):
        d = json.loads(r.read_text())
        task = r.parent.name.rsplit("__", 1)[0]
        rw = next(iter(((d.get("verifier_result") or {}).get("rewards") or {}).values()), None) or 0.0
        # success counts only a full solve; stratified S uses the reward itself, as subset/score.py does
        val = float(rw == 1) if metric == "success" else rw
        raw[task].append(val)
        adj[task].append(0.0 if ran_solved(r.parent) else val)
        rewards.append(rw)
        ar = d.get("agent_result") or {}
        tin += ar.get("n_input_tokens") or 0
        tout += ar.get("n_output_tokens") or 0
        n += 1
    lo, hi = bootstrap(raw, metric)
    return dict(S=score(raw, metric), lo=lo, hi=hi, S_adj=score(adj, metric), cost=(tin * PRICE_IN + tout * PRICE_OUT) / n,
                mean_reward=statistics.mean(rewards), n=n)


def marker(shape: str, x: float, y: float, color: str, tip: str) -> str:
    common = f'fill="{color}" stroke="{SURFACE}" stroke-width="2"'
    if shape == "circle":
        el = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" {common}>'
        end = "</circle>"
    elif shape == "square":
        el = f'<rect x="{x - 7.5:.1f}" y="{y - 7.5:.1f}" width="15" height="15" rx="2" {common}>'
        end = "</rect>"
    elif shape == "diamond":
        el = f'<path d="M{x:.1f},{y - 10:.1f} L{x + 10:.1f},{y:.1f} L{x:.1f},{y + 10:.1f} L{x - 10:.1f},{y:.1f} Z" {common}>'
        end = "</path>"
    else:
        el = f'<path d="M{x:.1f},{y - 10:.1f} L{x + 9:.1f},{y + 7:.1f} L{x - 9:.1f},{y + 7:.1f} Z" {common}>'
        end = "</path>"
    return f"{el}<title>{escape(tip)}</title>{end}"


def main(out: str, specs: list[str], metric: str, notes: list[str]) -> None:
    runs = []
    for i, spec in enumerate(specs):
        key, name, path = spec.split("|", 2)
        runs.append(dict(key=key, name=name, path=path, color=COLORS[i % 4], shape=SHAPES[i % 4], **summarize(Path(path), metric)))
        r = runs[-1]
        print(f"{key}: {metric} {r['S']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]  leak-adj {r['S_adj']:.3f}  "
              f"${r['cost']:.4f}/attempt  mean reward {r['mean_reward']:.3f}  n={r['n']}")
    plain = metric == "success"
    y_title = ("accuracy — share of attempts solved (40 tasks, equal weight)" if plain
               else "accuracy — stratified S (estimate for all 120 tasks)")
    subtitle = ("40-task subset × 5 attempts per harness · one dot per harness run · accuracy = reward 1 on an attempt · "
                "whiskers = 95% bootstrap interval" if plain else
                "40-task subset × 5 attempts per harness · one dot per harness run · whiskers = 95% bootstrap interval")

    def px(c):
        return AX0 + c / XMAX * (AX1 - AX0)

    def py(v):
        return AY1 - v / YMAX * (AY1 - AY0)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" font-family="{FONT}">',
         f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{SURFACE}"/>',
         f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" fill="none" stroke="rgba(11,11,11,0.10)"/>',
         f'<text x="40" y="36" fill="{INK}" font-size="17" font-weight="600">terminus-2 harness variants × qwen3.8-flash-next — accuracy vs cost</text>',
         f'<text x="40" y="58" fill="{INK2}" font-size="12.5">{escape(subtitle)}</text>']

    for v in (0, .2, .4, .6, .8):
        y = py(v)
        s.append(f'<line x1="{AX0}" y1="{y:.1f}" x2="{AX1}" y2="{y:.1f}" stroke="{GRID}"/>')
        s.append(f'<text x="{AX0 - 10}" y="{y + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{int(v * 100)}%</text>')
    for c in (0, .01, .02, .03, .04, .05, .06, .07):
        x = px(c)
        s.append(f'<line x1="{x:.1f}" y1="{AY1}" x2="{x:.1f}" y2="{AY1 + 5}" stroke="{AXIS}"/>')
        s.append(f'<text x="{x:.1f}" y="{AY1 + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">${c:.2f}</text>')
    s.append(f'<line x1="{AX0}" y1="{AY1}" x2="{AX1}" y2="{AY1}" stroke="{AXIS}"/>')
    s.append(f'<text x="{(AX0 + AX1) / 2}" y="{AY1 + 42}" fill="{INK2}" font-size="12" text-anchor="middle">'
             f'cost per attempt (USD, proxy pricing $0.15/M input · $0.47/M output)</text>')
    s.append(f'<text x="-{(AY0 + AY1) / 2}" y="34" fill="{INK2}" font-size="12" text-anchor="middle" transform="rotate(-90)">'
             f'{escape(y_title)}</text>')

    for r in runs:
        x, y = px(r["cost"]), py(r["S"])
        s.append(f'<line x1="{x:.1f}" y1="{py(r["lo"]):.1f}" x2="{x:.1f}" y2="{py(r["hi"]):.1f}" stroke="{r["color"]}" stroke-width="2" stroke-opacity="0.55"/>')
        for v in (r["lo"], r["hi"]):
            s.append(f'<line x1="{x - 5:.1f}" y1="{py(v):.1f}" x2="{x + 5:.1f}" y2="{py(v):.1f}" stroke="{r["color"]}" stroke-width="2" stroke-opacity="0.55"/>')
    for r in runs:
        x, y = px(r["cost"]), py(r["S"])
        tip = (f'{r["key"]} {r["name"]}: {r["S"]:.1%} (95% {r["lo"]:.1%}–{r["hi"]:.1%}), leak-adjusted {r["S_adj"]:.1%}, '
               f'mean reward {r["mean_reward"]:.3f}, ${r["cost"]:.4f} per attempt')
        s.append(marker(r["shape"], x, y, r["color"], tip))

    # direct labels; per-run offsets chosen so labels clear each other's whiskers
    offsets = {0: (-16, -14, "end"), 1: (16, 20, "start"), 2: (16, -8, "start"), 3: (16, 0, "start")}
    for i, r in enumerate(runs):
        x, y = px(r["cost"]), py(r["S"])
        dx, dy, anchor = offsets[i % 4]
        s.append(f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" fill="{INK}" font-size="12.5" font-weight="600" text-anchor="{anchor}">'
                 f'{escape(r["key"])} · {escape(r["name"])}</text>')
        s.append(f'<text x="{x + dx:.1f}" y="{y + dy + 15:.1f}" fill="{INK2}" font-size="11.5" text-anchor="{anchor}">'
                 f'{r["S"] * 100:.1f}% · ${r["cost"]:.3f}/attempt</text>')

    # right panel: the numbers
    bx = 660
    s.append(f'<text x="{bx}" y="{AY0 + 4}" fill="{INK}" font-size="13.5" font-weight="600">Numbers</text>')
    y0 = AY0 + 30
    for r in runs:
        s.append(marker(r["shape"], bx + 8, y0 - 4, r["color"], r["key"]))
        s.append(f'<text x="{bx + 24}" y="{y0}" fill="{INK}" font-size="12.5" font-weight="600">{escape(r["key"])} · {escape(r["name"])}</text>')
        name = "accuracy" if plain else "S"
        s.append(f'<text x="{bx + 24}" y="{y0 + 17}" fill="{INK2}" font-size="11.5">{name} {r["S"] * 100:.1f}%  '
                 f'(95% {r["lo"] * 100:.0f}–{r["hi"] * 100:.0f}%)</text>')
        s.append(f'<text x="{bx + 24}" y="{y0 + 33}" fill="{INK2}" font-size="11.5">leak-adjusted {r["S_adj"] * 100:.1f}% · '
                 f'mean reward {r["mean_reward"]:.3f}</text>')
        s.append(f'<text x="{bx + 24}" y="{y0 + 49}" fill="{INK2}" font-size="11.5">${r["cost"] * r["n"]:.2f} total · ${r["cost"]:.4f}/attempt</text>')
        y0 += 78

    foot = ["Leak-adjusted: trials that ran the task's own solution script (chrome_state.py solved) scored 0."] + notes
    s.append(f'<line x1="40" y1="{HEIGHT - 58}" x2="{WIDTH - 40}" y2="{HEIGHT - 58}" stroke="{GRID}"/>')
    for k, line in enumerate(foot):
        s.append(f'<text x="40" y="{HEIGHT - 38 + k * 17}" fill="{INK2}" font-size="11.5">{escape(line)}</text>')
    s.append("</svg>")
    Path(out).write_text("\n".join(s))
    print(f"wrote {out}")


if __name__ == "__main__":
    args = sys.argv[1:]
    opts = [a for a in args if a.startswith("--")]
    pos = [a for a in args if not a.startswith("--")]
    if len(pos) < 2:
        sys.exit(__doc__)
    metric = next((o.split("=", 1)[1] for o in opts if o.startswith("--metric=")), "success")
    if metric not in ("success", "stratified"):
        sys.exit(f"--metric must be success or stratified, got {metric!r}")
    main(pos[0], pos[1:], metric, [o.split("=", 1)[1] for o in opts if o.startswith("--note=")])
