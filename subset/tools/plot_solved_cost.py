#!/usr/bin/env python3
"""Solved trials (x of 200) vs total cost_usd per run, hidden (H0 + stop) vs shown (H7 clock), one model -> one SVG.

    python3 plot_solved_cost.py <out.svg> [qwen38|qwen36]     (default qwen38)

Uses every finished run of jobs/<model>/harness{0,7}-time<B>-attempt5/ (same discovery as plot_budget_curve.py).
Solved = trials with reward 1, counted over the run's trials. Total cost = harbor's `cost_usd` summed over the run's
trials (no cache discount). One point per run, each arm joined in budget order; hover a point for its numbers.
"""
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_attempts import COLOR, MODEL_NAME  # noqa: E402
from plot_budget_curve import ARM_NAME, runs  # noqa: E402


def stats(run):
    n = solved = 0
    cost = rsum = 0.0
    for p in glob.glob(f"{run}/*__*/result.json"):
        r = json.load(open(p))
        rw = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward", 0) or 0
        n += 1; solved += rw >= 1; rsum += rw
        cost += (r.get("agent_result") or {}).get("cost_usd") or 0
    return dict(n=n, solved=solved, cost=cost, score=rsum / n)


def svg(mk, pts):
    W, Ht, ml, mr, mt, mb = 900, 560, 70, 40, 112, 70
    costs = [v["cost"] for v in pts.values()]; sol = [v["solved"] for v in pts.values()]
    x0, x1 = math.log10(min(costs) / 1.25), math.log10(max(costs) * 1.25)
    ylo, yhi = math.floor((min(sol) - 8) / 10) * 10, math.ceil((max(sol) + 8) / 10) * 10
    X = lambda c: ml + (math.log10(c) - x0) / (x1 - x0) * (W - ml - mr)
    Y = lambda s: Ht - mb - (s - ylo) / (yhi - ylo) * (Ht - mt - mb)
    n = max(v["n"] for v in pts.values())
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
         f'<text x="32" y="34" class="t1" font-size="17" font-weight="600">Solved trials vs total cost — {MODEL_NAME[mk]}</text>',
         f'<text x="32" y="54" class="t2" font-size="12.5">one point per run of {n} trials (40 tasks × 5) · label = time budget · '
         'cost = harbor <tspan font-family="monospace">cost_usd</tspan> summed over the run (no cache discount)</text>']
    for i, arm in enumerate(("shown", "hidden")):
        lx = 32 + i * 290
        o.append(f'<line x1="{lx}" x2="{lx + 22}" y1="82" y2="82" class="line {arm}"/><circle cx="{lx + 11}" cy="82" r="5" class="mark {arm}"/>'
                 f'<text x="{lx + 30}" y="86" class="t2" font-size="12">{ARM_NAME[arm]}</text>')
    for s in range(ylo, yhi + 1, 10):
        o.append(f'<line x1="{ml}" x2="{W - mr}" y1="{Y(s):.1f}" y2="{Y(s):.1f}" style="stroke:var(--grid)"/>'
                 f'<text x="{ml - 8}" y="{Y(s) + 4:.1f}" class="tm" font-size="11" text-anchor="end">{s}</text>')
    for c in (2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100):
        if x0 <= math.log10(c) <= x1:
            o.append(f'<line x1="{X(c):.1f}" x2="{X(c):.1f}" y1="{mt}" y2="{Ht - mb}" style="stroke:var(--grid)"/>'
                     f'<text x="{X(c):.1f}" y="{Ht - mb + 18}" class="tm" font-size="11" text-anchor="middle">${c}</text>')
    o.append(f'<line x1="{ml}" x2="{W - mr}" y1="{Ht - mb}" y2="{Ht - mb}" style="stroke:var(--axis)"/>'
             f'<text x="{(ml + W - mr) / 2}" y="{Ht - mb + 40}" class="tm" font-size="12" text-anchor="middle">Total cost_usd for the run (log scale)</text>')
    cy = (mt + Ht - mb) / 2
    o.append(f'<text x="20" y="{cy}" class="tm" font-size="12" text-anchor="middle" transform="rotate(-90 20 {cy})">Solved trials (of {n})</text>')
    marks = [(X(v["cost"]), Y(v["solved"])) for v in pts.values()]
    boxes = []  # placed labels: (x0, y0, x1, y1)

    def place(x, y, text, prefer_above):
        w, h = 6.1 * len(text), 13
        cands = [(0, -12), (0, 20), (-10 - w / 2, 4), (10 + w / 2, 4), (0, -26), (0, 34)]
        if not prefer_above:
            cands[0], cands[1] = cands[1], cands[0]
        for dx, dy in cands:  # first spot clear of other labels and of every point
            bx = (x + dx - w / 2, y + dy - h + 3, x + dx + w / 2, y + dy + 3)
            if all(bx[2] < b[0] or bx[0] > b[2] or bx[3] < b[1] or bx[1] > b[3] for b in boxes) and \
               all(not (bx[0] - 6 < mx < bx[2] + 6 and bx[1] - 6 < my < bx[3] + 6) for mx, my in marks):
                break
        boxes.append(bx)
        return x + dx, y + dy

    for arm in ("hidden", "shown"):
        seq = sorted((b, v) for (a, b), v in pts.items() if a == arm)
        if len(seq) > 1:
            o.append('<path class="line ' + arm + '" d="' + " ".join(f'{"M" if i == 0 else "L"}{X(v["cost"]):.1f},{Y(v["solved"]):.1f}'
                                                              for i, (b, v) in enumerate(seq)) + '"/>')
    for arm in ("shown", "hidden"):  # marks on top of both lines; shown labels placed first (above), hidden below
        for b, v in sorted((b, v) for (a, b), v in pts.items() if a == arm):
            x, y = X(v["cost"]), Y(v["solved"])
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" class="mark {arm}"><title>{arm} {b} s: {v["solved"]} of {v["n"]} solved · '
                     f'total cost_usd ${v["cost"]:.2f} (${v["cost"] / v["n"]:.4f} per trial) · score {v["score"]:.3f}</title></circle>')
            text = f'{b} s · {v["solved"]} · ${v["cost"]:.2f}'
            lx, ly = place(x, y, text, arm == "shown")
            o.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="t2" font-size="11" text-anchor="middle">{text}</text>')
    o.append(f'<text x="32" y="{Ht - 12}" class="tm" font-size="10.5">Solved = reward 1. Up and to the left is better. '
             'Hover a point for its numbers. Write-up: subset/results/qwen38-h0-vs-h7.md.</text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    out, mk = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "qwen38")
    pts = {}
    for (m, arm, b), run in sorted(runs().items()):
        if m == mk:
            pts[(arm, b)] = v = stats(run)
            print(f"{arm:6} {b:5}: {v['solved']} of {v['n']} solved, total cost_usd ${v['cost']:.2f}")
    open(out, "w", encoding="utf-8").write(svg(mk, pts))
    print("wrote", out)


if __name__ == "__main__":
    main()
