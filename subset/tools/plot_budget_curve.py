#!/usr/bin/env python3
"""Time-budget sweep: score vs budget, hidden (H0 + stop) vs shown (H7 clock), one panel per model -> one SVG.

    python3 plot_budget_curve.py <out.svg> [qwen38|qwen36]     (optional: one model only)

Finds every finished run of jobs/<model>/harness{0,7}-time<B>-attempt5/ (newest folder with >= 200 trial results),
scores it as harbor's Mean (reward over all 200 trials), and labels the paired shown - hidden gap at every budget
that has both arms (bootstrap over the 40 tasks; bold when P(gap <= 0) < 0.05). Points carry hover tooltips with the
95% CI and the per-trial cost (prefix caching, as in plot_attempts.py). Follows the viewer's light/dark setting.
"""
import glob
import json
import math
import os
import random
import re
import statistics as stx
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_attempts import COLOR, MODEL_NAME, load  # noqa: E402

JOBS = os.environ.get("TUA_JOBS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../jobs"))
MODELS = {"qwen38": "qwen38-flash-next", "qwen36": "qwen36-35b-a3b"}
ARMS = {"shown": ("7", "H7"), "hidden": ("0", "H0")}
ARM_NAME = {"shown": "shown (H7: budget + clock told)", "hidden": "hidden (H0 + same stop, not told)"}


def runs():
    out = {}
    for mk, folder in MODELS.items():
        for arm, (n, _) in ARMS.items():
            for vdir in glob.glob(f"{JOBS}/{folder}/harness{n}-time*-attempt5"):
                m = re.search(r"-time(\d+)-attempt5$", vdir)
                done = [d for d in sorted(glob.glob(f"{vdir}/20*")) if len(glob.glob(f"{d}/*__*/result.json")) >= 200]
                if m and done:
                    out[(mk, arm, int(m.group(1)))] = done[-1]
    return out


def task_rewards(run):
    b = defaultdict(float)
    for p in glob.glob(f"{run}/*__*/result.json"):
        r = json.load(open(p))
        b[os.path.basename(os.path.dirname(p)).split("__")[0]] += (((r.get("verifier_result") or {}).get("rewards") or {}).get("reward", 0) or 0) / 5
    return b  # mean reward per task over its 5 attempts (a missing trial counts as 0)


def boot(fn, tasks, reps=10000):
    rnd = random.Random(0)
    xs = sorted(fn([rnd.choice(tasks) for _ in tasks]) for _ in range(reps))
    return fn(tasks), xs[int(.025 * reps)], xs[int(.975 * reps)], sum(x <= 0 for x in xs) / reps


def svg(data):
    PW, PH, ml, mt, gap_x = 430, 330, 64, 124, 70
    panels = [mk for mk in MODELS if any(m == mk for (m, _, _) in data)]
    W, Ht = max(ml + len(panels) * PW + (len(panels) - 1) * gap_x + 40, 760), mt + PH + 96
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Ht}" width="{W}" height="{Ht}" '
         'font-family="system-ui, -apple-system, \'Segoe UI\', sans-serif">', "<style>",
         ":root{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--ring:rgba(11,11,11,.10)"
         f";--h0:{COLOR['H0'][0]};--h7:{COLOR['H7'][0]}}}",
         "@media (prefers-color-scheme: dark){:root{--bg:#1a1a19;--ink:#ffffff;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;"
         f"--ring:rgba(255,255,255,.10);--h0:{COLOR['H0'][1]};--h7:{COLOR['H7'][1]}}}}}",
         ".t1{fill:var(--ink)}.t2{fill:var(--ink2)}.tm{fill:var(--muted)}.hidden{stroke:var(--h0);fill:var(--h0)}"
         ".shown{stroke:var(--h7);fill:var(--h7)}.line{fill:none;stroke-width:2}.mark{stroke:var(--bg);stroke-width:2}", "</style>",
         f'<rect width="{W}" height="{Ht}" style="fill:var(--bg)"/>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{Ht - 1}" style="fill:none;stroke:var(--ring)"/>',
         '<text x="32" y="34" class="t1" font-size="17" font-weight="600">Time-budget sweep — score vs budget, told vs not told</text>',
         '<text x="32" y="54" class="t2" font-size="12.5">40-task subset × 5 attempts per point · harbor Mean · '
         'labels: shown − hidden at that budget (paired over tasks; bold = P(≤0) &lt; 0.05)</text>']
    for i, arm in enumerate(("shown", "hidden")):
        lx = 32 + i * 290
        o.append(f'<line x1="{lx}" x2="{lx + 22}" y1="80" y2="80" class="line {arm}"/><circle cx="{lx + 11}" cy="80" r="4.5" class="mark {arm}"/>'
                 f'<text x="{lx + 30}" y="84" class="t2" font-size="12">{ARM_NAME[arm]}</text>')
    for pi, mk in enumerate(panels):
        px = ml + pi * (PW + gap_x)
        pts = {(a, b): v for (m, a, b), v in data.items() if m == mk}
        if not pts:
            continue
        ticks = sorted({b for (_, b) in pts})  # each panel spans its own budgets
        x0, x1 = math.log10(min(ticks) / 1.25), math.log10(max(ticks) * 1.35)
        accs = [v["acc"] for v in pts.values()]
        ylo, yhi = math.floor((min(accs) - .03) * 20) / 20, math.ceil((max(accs) + .03) * 20) / 20
        X = lambda b: px + (math.log10(b) - x0) / (x1 - x0) * PW
        Y = lambda a: mt + PH - (a - ylo) / (yhi - ylo) * PH
        o.append(f'<text x="{px}" y="{mt - 12}" class="t1" font-size="13.5" font-weight="600">{MODEL_NAME[mk]}</text>')
        a = ylo
        while a <= yhi + 1e-9:
            o.append(f'<line x1="{px}" x2="{px + PW}" y1="{Y(a):.1f}" y2="{Y(a):.1f}" style="stroke:var(--grid)"/>'
                     f'<text x="{px - 8}" y="{Y(a) + 4:.1f}" class="tm" font-size="11" text-anchor="end">{a:.2f}</text>')
            a += .05
        for b in ticks:
            o.append(f'<line x1="{X(b):.1f}" x2="{X(b):.1f}" y1="{mt}" y2="{mt + PH}" style="stroke:var(--grid)"/>'
                     f'<text x="{X(b):.1f}" y="{mt + PH + 17}" class="tm" font-size="11" text-anchor="middle">{b}</text>')
        o.append(f'<line x1="{X(2400):.1f}" x2="{X(2400):.1f}" y1="{mt}" y2="{mt + PH}" style="stroke:var(--axis);stroke-dasharray:4 4"/>'
                 f'<text x="{X(2400) + 4:.1f}" y="{mt + 12}" class="tm" font-size="10.5">TUA-Bench limit</text>')
        o.append(f'<line x1="{px}" x2="{px + PW}" y1="{mt + PH}" y2="{mt + PH}" style="stroke:var(--axis)"/>'
                 f'<text x="{px + PW / 2}" y="{mt + PH + 38}" class="tm" font-size="12" text-anchor="middle">Time budget (s, log scale)</text>')
        if pi == 0:
            cy = mt + PH / 2
            o.append(f'<text x="18" y="{cy}" class="tm" font-size="12" text-anchor="middle" transform="rotate(-90 18 {cy})">Score (harbor Mean)</text>')
        for b in sorted({b for (_, b) in pts}):  # gap labels where both arms exist
            if ("shown", b) in pts and ("hidden", b) in pts:
                s, h = pts[("shown", b)], pts[("hidden", b)]
                g = s["gap"]
                ys, yh = Y(s["acc"]), Y(h["acc"])
                # label between the two points, or under the lower point's value when they sit too close together
                gy = (ys + yh) / 2 + 4 if abs(yh - ys) >= 34 else max(ys, yh) + 32
                o.append(f'<line x1="{X(b):.1f}" x2="{X(b):.1f}" y1="{ys:.1f}" y2="{yh:.1f}" style="stroke:var(--muted);stroke-dasharray:2 3"/>'
                         f'<text x="{X(b) + (7 if abs(yh - ys) >= 34 else 0):.1f}" y="{gy:.1f}" class="t1" font-size="11.5" '
                         f'text-anchor="{"start" if abs(yh - ys) >= 34 else "middle"}" '
                         f'font-weight="{700 if g[3] < .05 else 400}">{g[0]:+.3f}<title>shown − hidden at {b} s: {g[0]:+.3f} '
                         f'(95% CI {g[1]:+.3f} to {g[2]:+.3f}), P(≤0) {g[3]:.3f}</title></text>')
        for arm in ("hidden", "shown"):
            seq = sorted((b, v) for (a2, b), v in pts.items() if a2 == arm)
            if len(seq) > 1:
                o.append('<path class="line ' + arm + '" d="' + " ".join(f'{"M" if i == 0 else "L"}{X(b):.1f},{Y(v["acc"]):.1f}' for i, (b, v) in enumerate(seq)) + '"/>')
            for b, v in seq:
                x, y = X(b), Y(v["acc"])
                tip = (f'<title>{MODEL_NAME[mk]} · {arm} {b} s: {v["acc"]:.3f} (95% CI {v["lo"]:.3f}–{v["hi"]:.3f}) · '
                       f'${v["cost"]:.4f}/trial · {os.path.basename(v["run"])}</title>')
                if mk == "qwen36":
                    o.append(f'<path d="M{x:.1f},{y - 6.5:.1f} L{x + 6.5:.1f},{y:.1f} L{x:.1f},{y + 6.5:.1f} L{x - 6.5:.1f},{y:.1f} Z" class="mark {arm}">{tip}</path>')
                else:
                    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="mark {arm}">{tip}</circle>')
                o.append(f'<text x="{x:.1f}" y="{y + (17 if arm == "hidden" else -10):.1f}" class="t2" font-size="10.5" text-anchor="middle">{v["acc"]:.3f}</text>')
    o.append(f'<text x="32" y="{Ht - 28}" class="tm" font-size="10.5">2400 s ends with harbor\'s hard kill (the official limit); the other budgets with the harness '
             'soft stop, which lets the turn under way finish.</text>')
    o.append(f'<text x="32" y="{Ht - 12}" class="tm" font-size="10.5">Hard-stop-equivalent scores: subset/results/qwen38-h0-vs-h7.md. '
             'Hover a point for its 95% CI and cost; hover a gap label for its CI.</text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    out = sys.argv[1]
    R = {k: v for k, v in runs().items() if len(sys.argv) < 3 or k[0] == sys.argv[2]}
    data, tr = {}, {}
    for (mk, arm, b), run in sorted(R.items()):
        tr[(mk, arm, b)] = t = task_rewards(run)
        acc, lo, hi, _ = boot(lambda ts: stx.mean(t[x] for x in ts), sorted(t), 4000)
        data[(mk, arm, b)] = dict(acc=sum(t.values()) / 40, lo=lo, hi=hi, cost=load(mk, run)["all"]["cost"], run=run)
        print(f"{mk} {arm:6} {b:5}: {data[(mk, arm, b)]['acc']:.3f}  {os.path.relpath(run, JOBS)}")
    for (mk, arm, b) in list(data):
        if arm == "shown" and (mk, "hidden", b) in data:
            s, h = tr[(mk, "shown", b)], tr[(mk, "hidden", b)]
            data[(mk, "shown", b)]["gap"] = g = boot(lambda ts: stx.mean(s[x] - h[x] for x in ts), sorted(s))
            print(f"   {mk} shown - hidden {b}: {g[0]:+.3f} ({g[1]:+.3f} to {g[2]:+.3f}) P {g[3]:.3f}")
    open(out, "w", encoding="utf-8").write(svg(data))
    print("wrote", out)


if __name__ == "__main__":
    main()
