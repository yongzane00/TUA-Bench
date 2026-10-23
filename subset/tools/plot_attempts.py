#!/usr/bin/env python3
"""Accuracy vs cost per attempt, for harness x model runs -> one SVG (and its data as JSON).

    python3 plot_attempts.py <out.svg> "<model>|<harness>|<run_dir>" [...]
    python3 plot_attempts.py <out.svg> --from-json     (re-draw from the saved <out>.json)
    python3 plot_attempts.py <out.svg> --add "<model>|<harness>|<run_dir>" ...   (add/replace runs, keep the rest)
    python3 plot_attempts.py <out.svg> --means <data.json>   (one mark per run, from another plot's saved data)

<model> is a key of PRICE / MODEL_NAME below (qwen38, qwen36); <harness> is H0, H1, ... .
For each run: five small marks, one per attempt (attempt k = the k-th trial of every task by
start time, scored over the 40 tasks), one translucent circle, the smallest that holds the run's five
attempt marks, and a + at all five attempts pooled. Color = harness, shape = model (circle qwen38,
diamond qwen36); the run circle is always a circle. Score = harbor's Mean: the reward averaged over every trial, partial credit included,
a missing reward counted as 0. pass@5 / solved-in-all-5 use reward == 1. Cost = mean per-trial cost with prefix
caching: each turn's previous prompt is billed at the cache-read price. Cost axis is log scale.
--means draws only the all-five mean of each run, as a solid mark in the model's shape.
The SVG carries native hover tooltips (<title>) and follows the viewer's light/dark setting.
"""
import glob
import itertools
import json
import math
import os
import re
import statistics as stx
import sys
from collections import defaultdict

# $ per token: input, output, cache read
PRICE = {"qwen38": (0.15e-6, 0.47e-6, 0.016e-6), "qwen36": (0.05e-6, 0.70e-6, 0.025e-6)}
MODEL_NAME = {"qwen38": "qwen3.8-flash-next", "qwen36": "Qwen3.6-35B-A3B"}
HARNESS_NAME = {"H0": "stock terminus-2", "H1": "instruction re-check", "H2": "reasoning kept",
                "H3": "Listen", "H4": "observation window (none)", "H5": "snapshot verifier",
                "H6": "turn budget", "H7": "time budget", "H8": "cost budget", "H9": "all budget"}
# validated categorical slots (light, dark); H0 is the baseline in secondary ink
COLOR = {"H0": ("#52514e", "#c3c2b7"), "H1": ("#2a78d6", "#3987e5"), "H2": ("#eb6834", "#d95926"),
         "H3": ("#1baf7a", "#199e70"), "H4": ("#4a3aa7", "#4a3aa7"), "H5": ("#e87ba4", "#d55181"),
         "H6": ("#008300", "#008300"), "H7": ("#eda100", "#c98500"), "H8": ("#e34948", "#e66767")}
# H9 has no slot yet: the 8 categorical slots are used up. Pick one when H9 is first plotted.
# A label may carry the budget after the harness number, e.g. "H8-cost0.048" (as in the config name):
# color and legend name come from the "H8" part, the full label is shown, so budgets of one harness share a color.
base = lambda h: re.match(r"H\d+", h).group(0)
hname = lambda h: f"{h} {HARNESS_NAME.get(base(h), '')}"


def load(model, run):
    pin, pout, pc = PRICE[model]
    by_task = defaultdict(list)
    for t in glob.glob(f"{run}/*__*"):
        d = json.load(open(f"{t}/result.json"))
        rw = next(iter(((d.get("verifier_result") or {}).get("rewards") or {}).values()), 0) or 0
        tj = f"{t}/agent/trajectory.json"
        st = [s for s in json.load(open(tj))["steps"] if s.get("source") == "agent"] if os.path.exists(tj) else []
        P = [(s.get("metrics") or {}).get("prompt_tokens") or 0 for s in st]
        C = [(s.get("metrics") or {}).get("completion_tokens") or 0 for s in st]
        cached = sum(min(a, b) for a, b in zip([0] + P, P))
        cost = (sum(P) - cached) * pin + cached * pc + sum(C) * pout
        # calls outside the main turns (H4 summarizer, terminus-2 summarization) are in harbor's totals
        # but not in the trajectory steps; bill the difference at the uncached price
        ar = d.get("agent_result") or {}
        cost += max(0, (ar.get("n_input_tokens") or 0) - sum(P)) * pin + max(0, (ar.get("n_output_tokens") or 0) - sum(C)) * pout
        by_task[os.path.basename(t).split("__")[0]].append((d["started_at"], float(rw), cost))
    for v in by_task.values():
        v.sort()
    n_att = min(len(v) for v in by_task.values())
    att = [dict(k=k + 1, acc=stx.mean(v[k][1] for v in by_task.values()), cost=stx.mean(v[k][2] for v in by_task.values()))
           for k in range(n_att)]
    pooled = [x for v in by_task.values() for x in v]
    return dict(attempts=att, n_tasks=len(by_task), n_trials=len(pooled),
                all=dict(acc=stx.mean(x[1] for x in pooled), cost=stx.mean(x[2] for x in pooled)),
                pass_at_5=stx.mean(any(x[1] == 1 for x in v) for v in by_task.values()),
                solved_all_5=stx.mean(all(x[1] == 1 for x in v) for v in by_task.values()))


def enclose(p):
    """Smallest circle (cx, cy, r) holding the points: brute force over pairs and triples, fine for five points."""
    def circ(a, b, c=None):
        if c is None:
            return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, math.dist(a, b) / 2)
        d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
        if abs(d) < 1e-9:  # collinear: some pair's circle covers it
            return None
        s = [q[0] ** 2 + q[1] ** 2 for q in (a, b, c)]
        ux = (s[0] * (b[1] - c[1]) + s[1] * (c[1] - a[1]) + s[2] * (a[1] - b[1])) / d
        uy = (s[0] * (c[0] - b[0]) + s[1] * (a[0] - c[0]) + s[2] * (b[0] - a[0])) / d
        return (ux, uy, math.dist((ux, uy), a))
    if len(p) == 1:
        return (p[0][0], p[0][1], 0.0)
    cands = [circ(a, b) for a, b in itertools.combinations(p, 2)] + [c for t in itertools.combinations(p, 3) if (c := circ(*t))]
    return min((c for c in cands if all(math.dist(c[:2], q) <= c[2] + 1e-6 for q in p)), key=lambda c: c[2])


def svg(rows, means=False):
    W, Ht, ml, mr, mt, mb = 940, 620, 64, 190, 122, 72
    if means:  # no legend rows on top; a legend table with the exact values on the right instead of callouts
        W, mr, mt = 1040, 360, 80
    tw = lambda s: 6.4 * len(s)  # approx text width at 12px
    # harness legend: wrap onto more rows when it does not fit, and grow the chart to make room
    legend, lx, lrow = [], 32, 0
    for h in dict.fromkeys(r["harness"] for r in rows) if not means else []:
        s = hname(h)
        if lx > 32 and lx + 15 + tw(s) > W - 16:
            lx, lrow = 32, lrow + 1
        legend.append((h, s, lx, 76 + 21 * lrow))
        lx += 15 + tw(s) + 22
    extra = 21 * lrow
    mt, Ht = mt + extra, Ht + extra
    if means:  # grow the figure so the legend table (one block per model) and the footnote fit
        n_by_model = [sum(r["model"] == m for r in rows) for m in dict.fromkeys(r["model"] for r in rows)]
        Ht = max(Ht, mt + 6 + sum(60 + 21 * n for n in n_by_model) + 24)
    else:  # grow the figure so the tallest label column (34 px per run) fits between the legend and the x axis
        n_max = max(sum(r["model"] == m for r in rows) for m in dict.fromkeys(r["model"] for r in rows))
        Ht = max(Ht, mt + mb + 34 * n_max + 10)
    pts = lambda r: [r["all"]] if means else r["attempts"]  # the marks drawn for a run
    costs = [a["cost"] for r in rows for a in pts(r)] + [r["all"]["cost"] for r in rows]
    x0, x1 = math.log10(min(costs) * 0.8), math.log10(max(costs) * 1.6)
    ytop = max(0.6, math.ceil(max(a["acc"] for r in rows for a in pts(r)) * 10 + 0.5) / 10)
    X = lambda c: ml + (math.log10(c) - x0) / (x1 - x0) * (W - ml - mr)
    Y = lambda a: Ht - mb - a / ytop * (Ht - mt - mb)
    of = lambda r, k: f"{round(r[k] * r['n_tasks'])} of {r['n_tasks']} tasks"  # counts, not percentages
    sc = lambda v: f"{v:.3f}"
    usd = lambda v: f"${v:.4f}"
    harnesses = list(dict.fromkeys(r["harness"] for r in rows))
    models = list(dict.fromkeys(r["model"] for r in rows))
    bases = list(dict.fromkeys(base(h) for h in harnesses))
    css_l = "".join(f".h-{h}{{fill:{COLOR[h][0]};stroke:{COLOR[h][0]}}}" for h in bases)
    css_d = "".join(f".h-{h}{{fill:{COLOR[h][1]};stroke:{COLOR[h][1]}}}" for h in bases)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Ht}" width="{W}" height="{Ht}" '
         'font-family="system-ui, -apple-system, \'Segoe UI\', sans-serif">',
         "<style>",
         ":root{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--ring:rgba(11,11,11,.10)}",
         css_l,
         "@media (prefers-color-scheme: dark){:root{--bg:#1a1a19;--ink:#ffffff;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--ring:rgba(255,255,255,.10)}" + css_d + "}",
         ".mark{stroke:var(--bg);stroke-width:2}.pool{fill-opacity:.16;stroke-opacity:.55;stroke-width:1.5}",
         ".t1{fill:var(--ink)}.t2{fill:var(--ink2)}.tm{fill:var(--muted)}.key{fill:none;stroke:var(--ink2);stroke-width:1.5}",
         "</style>",
         f'<rect width="{W}" height="{Ht}" style="fill:var(--bg)"/>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{Ht - 1}" style="fill:none;stroke:var(--ring)"/>',
         '<text x="32" y="34" class="t1" font-size="17" font-weight="600">terminus-2 harnesses × models — mean reward vs cost'
         + ('' if means else ', per attempt and all five') + '</text>',
         '<text x="32" y="54" class="t2" font-size="12.5">40-task subset × 5 attempts · '
         + ('each mark: one run, mean over all 200 trials' if means else "small marks: each attempt as its own run · circle: holds a run's 5 attempts, + = all 5 pooled")
         + ' · color = harness · shape = model</text>']
    # legend: harness colors on one row, model shapes and the pooled mark on the next
    for h, s, lx, ly in legend:
        o.append(f'<circle cx="{lx + 5}" cy="{ly}" r="5" class="h-{base(h)}"/><text x="{lx + 15}" y="{ly + 4}" class="t2" font-size="12">{s}</text>')
    lx = 32
    for mdl in models if not means else []:
        if mdl == "qwen36":
            o.append(f'<path d="M{lx + 5},{92 + extra} L{lx + 10},{97 + extra} L{lx + 5},{102 + extra} L{lx},{97 + extra} Z" class="key"/>')
        else:
            o.append(f'<circle cx="{lx + 5}" cy="{97 + extra}" r="4.5" class="key"/>')
        o.append(f'<text x="{lx + 15}" y="{101 + extra}" class="t2" font-size="12">{MODEL_NAME[mdl]}</text>')
        lx += 15 + tw(MODEL_NAME[mdl]) + 22
    if not means:
        o.append(f'<circle cx="{lx + 8}" cy="{97 + extra}" r="8" style="fill:var(--ink2);fill-opacity:.16;stroke:var(--ink2);stroke-opacity:.55"/>'
                 f'<path d="M{lx + 5},{97 + extra} H{lx + 11} M{lx + 8},{94 + extra} V{100 + extra}" style="fill:none;stroke:var(--ink2);stroke-width:1.6"/>'
                 f'<text x="{lx + 21}" y="{101 + extra}" class="t2" font-size="12">a run\'s 5 attempts, + = all 5 pooled</text>')
    # grid and axes
    a = 0.0
    while a <= ytop + 1e-9:
        o.append(f'<line x1="{ml}" x2="{W - mr}" y1="{Y(a):.1f}" y2="{Y(a):.1f}" style="stroke:var(--grid)"/>'
                 f'<text x="{ml - 10}" y="{Y(a) + 4:.1f}" class="tm" font-size="11.5" text-anchor="end">{a:.1f}</text>')
        a += 0.1
    for c in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5):
        if x0 <= math.log10(c) <= x1:
            o.append(f'<line x1="{X(c):.1f}" x2="{X(c):.1f}" y1="{mt}" y2="{Ht - mb}" style="stroke:var(--grid)"/>'
                     f'<text x="{X(c):.1f}" y="{Ht - mb + 20}" class="tm" font-size="11.5" text-anchor="middle">${c:g}</text>')
    o.append(f'<line x1="{ml}" x2="{W - mr}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" style="stroke:var(--axis)"/>')
    o.append(f'<text x="{(ml + W - mr) / 2}" y="{Ht - mb + 40}" class="tm" font-size="12" text-anchor="middle">Cost per trial (USD, log scale, with prefix caching)</text>')
    cy = (mt + Ht - mb) / 2
    o.append(f'<text x="18" y="{cy}" class="tm" font-size="12" text-anchor="middle" transform="rotate(-90 18 {cy})">Mean reward (harbor Mean)</text>')
    # pooled circles, then attempt marks on top (--means: one solid mark per run in the model's shape)
    # run circle: the smallest circle holding the run's five attempt marks (plus each mark's half-size and surface
    # ring); the all-five pooled value is the + inside it. Largest first so smaller circles stay hoverable.
    edge = lambda mdl: 6.8 if mdl == "qwen36" else 5.5
    pool = {}
    for r in rows if not means else []:
        cx, cy, rr = enclose([(X(a["cost"]), Y(a["acc"])) for a in r["attempts"]])
        pool[id(r)] = (cx, cy, max(10.0, rr + edge(r["model"]) + 1.5))
    for r in sorted(rows, key=lambda r: -pool[id(r)][2]) if not means else []:
        cx, cy, rr = pool[id(r)]
        o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" class="pool h-{base(r["harness"])}"><title>{hname(r["harness"])} · '
                 f'{MODEL_NAME[r["model"]]} · all 5 attempts ({r["n_trials"]} trials): mean reward {sc(r["all"]["acc"])}, cost {usd(r["all"]["cost"])}/trial, '
                 f'pass@5 {of(r, "pass_at_5")}, solved in all 5 {of(r, "solved_all_5")}</title></circle>')
    for r in rows if not means else []:
        x, y = X(r["all"]["cost"]), Y(r["all"]["acc"])
        o.append(f'<path d="M{x - 4:.1f},{y:.1f} H{x + 4:.1f} M{x:.1f},{y - 4:.1f} V{y + 4:.1f}" class="h-{base(r["harness"])}" style="fill:none;stroke-width:1.6"/>')
    for r in rows:
        for at in pts(r):
            x, y = X(at["cost"]), Y(at["acc"])
            tip = (f'<title>{hname(r["harness"])} · {MODEL_NAME[r["model"]]} · {r["n_trials"]} trials: mean reward {sc(at["acc"])}, '
                   f'cost {usd(at["cost"])}/trial, pass@5 {of(r, "pass_at_5")}, solved in all 5 {of(r, "solved_all_5")}</title>' if means else
                   f'<title>{r["harness"]} · {MODEL_NAME[r["model"]]} · attempt {at["k"]}: mean reward {sc(at["acc"])}, cost {usd(at["cost"])}/trial</title>')
            if r["model"] == "qwen36":
                d = 11 if means else 5.8
                o.append(f'<path d="M{x:.1f},{y - d:.1f} L{x + d:.1f},{y:.1f} L{x:.1f},{y + d:.1f} L{x - d:.1f},{y:.1f} Z" class="mark h-{base(r["harness"])}">{tip}</path>')
            else:
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{8 if means else 4.5}" class="mark h-{base(r["harness"])}">{tip}</circle>')
    # --means: legend table right of the plot, one block per model, runs by score, exact values
    def shape(mdl, h, x, y, k=1.0):
        if mdl == "qwen36":
            d = 6.5 * k
            return f'<path d="M{x:.1f},{y - d:.1f} L{x + d:.1f},{y:.1f} L{x:.1f},{y + d:.1f} L{x - d:.1f},{y:.1f} Z" class="{h}"/>'
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5 * k:.1f}" class="{h}"/>'
    tx, ty = W - mr + 10, mt + 6
    c_score, c_cost = tx + 262, tx + 330  # right edges of the number columns
    for mdl in models if means else []:
        o.append(shape(mdl, "key", tx + 6, ty - 4) + f'<text x="{tx + 18}" y="{ty}" class="t1" font-size="12.5" font-weight="600">{MODEL_NAME[mdl]}</text>')
        ty += 20
        o.append(f'<text x="{tx + 18}" y="{ty}" class="tm" font-size="11">harness</text>'
                 f'<text x="{c_score}" y="{ty}" class="tm" font-size="11" text-anchor="end">mean reward</text>'
                 f'<text x="{c_cost}" y="{ty}" class="tm" font-size="11" text-anchor="end">$ / trial</text>')
        o.append(f'<line x1="{tx}" x2="{c_cost}" y1="{ty + 6}" y2="{ty + 6}" style="stroke:var(--grid)"/>')
        ty += 22
        for r in sorted((r for r in rows if r["model"] == mdl), key=lambda r: -r["all"]["acc"]):
            o.append(shape(mdl, f'mark h-{base(r["harness"])}', tx + 6, ty - 4, 1.15)
                     + f'<text x="{tx + 18}" y="{ty}" class="t1" font-size="12">{hname(r["harness"])}</text>'
                     f'<text x="{c_score}" y="{ty}" class="t1" font-size="12" text-anchor="end" style="font-variant-numeric:tabular-nums">{sc(r["all"]["acc"])}</text>'
                     f'<text x="{c_cost}" y="{ty}" class="t2" font-size="12" text-anchor="end" style="font-variant-numeric:tabular-nums">{usd(r["all"]["cost"])}</text>')
            ty += 21
        ty += 18
    # direct labels: one column per model, right of its cluster, leader lines from the pooled circle
    for mdl in models if not means else []:
        grp = [r for r in rows if r["model"] == mdl]
        colx = max(max(X(a["cost"]) for r in grp for a in pts(r)) + 40,
                   max(pool[id(r)][0] + pool[id(r)][2] for r in grp) + 14)  # clear of the widest run circle
        items = sorted(((r, X(r["all"]["cost"]), Y(r["all"]["acc"])) for r in grp), key=lambda i: i[2])
        ys, prev = [], -1e9
        for _, _, y in items:
            prev = max(y, prev + 34)
            ys.append(prev)
        shift = stx.mean(ys) - stx.mean(i[2] for i in items)
        shift = min(shift, ys[0] - (mt + 10))  # keep the column below the legend
        shift = max(shift, ys[-1] + 15 - (Ht - mb))  # and above the x axis
        for (r, x, y), ly in zip(items, (v - shift for v in ys)):
            cx, cy, rr = pool[id(r)]
            ang = math.atan2(ly - cy, colx - 6 - cx)
            o.append(f'<line x1="{cx + rr * math.cos(ang):.1f}" y1="{cy + rr * math.sin(ang):.1f}" x2="{colx - 6:.1f}" y2="{ly:.1f}" style="stroke:var(--muted)"/>'
                     f'<text x="{colx:.1f}" y="{ly + 1:.1f}" class="t1" font-size="12" font-weight="500">{r["harness"]} {sc(r["all"]["acc"])}</text>'
                     f'<text x="{colx:.1f}" y="{ly + 15:.1f}" class="t2" font-size="11">{MODEL_NAME[mdl]} · {usd(r["all"]["cost"])}</text>')
    prices = " · ".join(f"{MODEL_NAME[m]} ${PRICE[m][0] * 1e6:g} / ${PRICE[m][1] * 1e6:g} / ${PRICE[m][2] * 1e6:g}" for m in models)
    o.append(f'<text x="32" y="{Ht - 10}" class="tm" font-size="10.5">Prices per 1M input / output / cache-read tokens: {prices}. Hover any mark for its values.</text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    out, specs = sys.argv[1], sys.argv[2:]
    if specs[:1] == ["--means"]:  # one mark per run, from the data saved with another plot
        open(out, "w", encoding="utf-8").write(svg(json.load(open(specs[1])), means=True))
        print("wrote", out)
        return
    if specs == ["--from-json"]:  # re-draw from the data saved by an earlier run
        open(out, "w", encoding="utf-8").write(svg(json.load(open(os.path.splitext(out)[0] + ".json"))))
        print("redrew", out)
        return
    rows = []
    if specs and specs[0] == "--add":  # keep the saved runs, add or replace the given ones
        specs = specs[1:]
        new_keys = {tuple(s.split("|")[:2]) for s in specs}
        rows = [r for r in json.load(open(os.path.splitext(out)[0] + ".json")) if (r["model"], r["harness"]) not in new_keys]
    for s in specs:
        model, harness, run = s.split("|")
        r = load(model, run)
        r.update(model=model, harness=harness, run=run)
        rows.append(r)
        print(f"{model} {harness}: attempts {[round(a['acc'], 3) for a in r['attempts']]}  mean {r['all']['acc']:.3f}  "
              f"cost ${r['all']['cost']:.4f}  pass@5 {round(r['pass_at_5'] * r['n_tasks'])} of {r['n_tasks']}  solved-all-5 {round(r['solved_all_5'] * r['n_tasks'])} of {r['n_tasks']}")
    open(out, "w", encoding="utf-8").write(svg(rows))
    json.dump(rows, open(os.path.splitext(out)[0] + ".json", "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
