#!/usr/bin/env python3
"""Does the clock help more when the model is slow? A free dose-response check of plan H1 (p5), from finished runs.

    python -X utf8 speed_dose.py [qwen38|qwen36] [--cache <file.json>]      (Windows Python reads jobs/ fastest)

Server load changes the model's speed from trial to trial. A slow trial has less model time inside the same budget,
the same thing the plan's injected delay (+5 s / +20 s per reply) does on purpose. So if the clock matters more when
time is scarce, the shown - hidden gap should be larger on slow trials.

Speed of a trial: output tokens / seconds spent waiting for the model (llm_speed.py; includes queueing and prefill).
Relative speed z: log(speed) minus the mean log(speed) of the same task over every run of that model, so a task's
own pace (long contexts, long outputs) is taken out and what is left is mostly server load.

Reported per budget and pooled:
  - balance: mean z per arm (the arms should have met the same server)
  - slow half vs fast half (split at the median z of the pair): solved, shown and hidden
  - linear probability model with task fixed effects (task x budget when pooled):
        solved = FE + b*shown + c*z + d*shown*z
    d < 0 means the clock's advantage grows as the trial gets slower. Shown as the gap at z = -0.2 vs +0.2
    (about 18% slower / 22% faster than the task's usual speed), per 200 trials, with a 95% CI from a bootstrap
    over tasks (all of a task's trials stay together).
Caveat: z is measured, not assigned. The arms could change speed themselves (e.g. shorter replies near the
deadline are slower per token, because prefill weighs more), so the balance row is part of the result.
"""
import json
import math
import os
import random
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_speed import trial_speed  # noqa: E402
from plot_budget_curve import runs  # noqa: E402
from pathlib import Path  # noqa: E402

REPS = 2000
Z = 0.2


def load(model, cache):
    if cache and os.path.exists(cache):
        return json.load(open(cache))
    out = []
    for (m, arm, b), run in sorted(runs().items()):
        if m != model:
            continue
        for t in sorted(Path(run).glob("*__*")):
            if not (t / "result.json").exists():
                continue
            r = json.loads((t / "result.json").read_text(encoding="utf-8"))
            rw = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward", 0) or 0
            sp = trial_speed(t)
            out.append(dict(task=t.name.split("__")[0], arm=arm, budget=b, solved=int(rw >= 1),
                            speed=sp[0] if sp else None, llm_sec=sp[1] if sp else None))
    if cache:
        json.dump(out, open(cache, "w"))
    return out


def add_z(rows):
    logs = defaultdict(list)
    for r in rows:
        if r["speed"]:
            logs[r["task"]].append(math.log(r["speed"]))
    for r in rows:
        r["z"] = math.log(r["speed"]) - sum(logs[r["task"]]) / len(logs[r["task"]]) if r["speed"] else None


def fit(rows):
    """LPM with fixed effects per group key; returns gap(-Z) - gap(+Z) pieces: (b, d)."""
    groups = sorted({r["g"] for r in rows})
    gi = {g: i for i, g in enumerate(groups)}
    X = np.zeros((len(rows), len(groups) + 3))
    y = np.zeros(len(rows))
    for k, r in enumerate(rows):
        X[k, gi[r["g"]]] = 1
        s = 1.0 if r["arm"] == "shown" else 0.0
        X[k, -3], X[k, -2], X[k, -1] = s, r["z"], s * r["z"]
        y[k] = r["solved"]
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return beta[-3], beta[-1]


def gaps(rows):
    b, d = fit(rows)
    return 200 * (b - d * Z), 200 * (b + d * Z)  # gap per 200 trials on slow (z=-Z) and fast (z=+Z) trials


def boot(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["task"]].append(r)
    tasks = sorted(by)
    rnd = random.Random(0)
    slow, fast, diff = [], [], []
    for _ in range(REPS):
        pick = []
        for i, t in enumerate(rnd.choice(tasks) for _ in tasks):
            pick += [dict(r, g=(i, r["g"][1])) for r in by[t]]  # each draw gets its own fixed effect
        s, f = gaps(pick)
        slow.append(s); fast.append(f); diff.append(s - f)
    q = lambda xs: (sorted(xs)[int(.025 * REPS)], sorted(xs)[int(.975 * REPS)])
    return q(slow), q(fast), q(diff)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    model = args[0] if args else "qwen38"
    cache = sys.argv[sys.argv.index("--cache") + 1] if "--cache" in sys.argv else None
    rows = load(model, cache)
    add_z(rows)
    rows = [r for r in rows if r["z"] is not None]
    budgets = sorted({r["budget"] for r in rows if r["arm"] == "shown"})
    print(f"\n## {model}: clock gap on slow vs fast trials\n")
    print("| Budget (s) | Mean z, hidden / shown | Median speed, hidden / shown (tok/s) | Slow half: solved, hidden / shown | "
          "Fast half: solved, hidden / shown |")
    print("|---|---|---|---|---|")
    pooled = []
    for b in budgets:
        rb = [dict(r, g=(r["task"], b)) for r in rows if r["budget"] == b]
        med = sorted(r["z"] for r in rb)[len(rb) // 2]
        cell = lambda arm, slow: (lambda xs: f"{sum(r['solved'] for r in xs)} of {len(xs)}")(
            [r for r in rb if r["arm"] == arm and (r["z"] < med) == slow])
        mz = lambda arm: sum(r["z"] for r in rb if r["arm"] == arm) / max(1, sum(r["arm"] == arm for r in rb))
        ms = lambda arm: sorted(r["speed"] for r in rb if r["arm"] == arm)[sum(r["arm"] == arm for r in rb) // 2]
        print(f"| {b} | {mz('hidden'):+.3f} / {mz('shown'):+.3f} | {ms('hidden'):.1f} / {ms('shown'):.1f} | "
              f"{cell('hidden', True)} / {cell('shown', True)} | {cell('hidden', False)} / {cell('shown', False)} |")
        pooled += rb
    print(f"\nFixed-effects fit, solved = FE + b*shown + c*z + d*shown*z; gap per 200 trials at z = -{Z} (slow) and "
          f"+{Z} (fast), 95% CI from {REPS} bootstrap draws over tasks:\n")
    print("| Budget (s) | Trials | Gap on slow trials | Gap on fast trials | Slow - fast |")
    print("|---|---|---|---|---|")
    for b, rb in [(b, [r for r in pooled if r["budget"] == b]) for b in budgets] + [("pooled", pooled)]:
        s, f = gaps(rb)
        (sl, sh), (fl, fh), (dl, dh) = boot(rb)
        print(f"| {b} | {len(rb)} | {s:+.0f} ({sl:+.0f} to {sh:+.0f}) | {f:+.0f} ({fl:+.0f} to {fh:+.0f}) | "
              f"{s - f:+.0f} ({dl:+.0f} to {dh:+.0f}) |")


if __name__ == "__main__":
    main()
