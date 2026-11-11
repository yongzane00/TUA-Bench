#!/usr/bin/env python3
"""How well does the meter's turn forecast predict the next turn? (plan p4: forecast accuracy, wrap-up reserve)

    python -X utf8 turn_forecast.py [qwen38] [--budgets 2400,3600]

A turn is the time from one agent step to the next (one model reply plus the commands it ran), from the
trajectory timestamps of the finished hidden / shown runs. For every turn after the third, each forecaster predicts
its length from the earlier turns of the same trial only:
  mean3       mean of the last 3 turns (what the meter and the wrap-up notice use now)
  last        the last turn
  median5     median of the last 5
  max3        longest of the last 3
  p80         80th percentile of all earlier turns of the trial
  same-class  mean of earlier turns whose commands were of the same class as the last turn's (install, build,
              test, other); falls back to mean3
Reported: median absolute error, and how often the turn ran past its forecast by more than 30 s (late), which is
what makes a wrap-up notice come too late.
Second table, rules for the time set aside for one more turn (the wrap-up trigger "time left <= forecast +
reserve"): how many next turns finish inside it (coverage) and the mean time it sets aside. A rule that covers
more turns for less time set aside is better.
"""
import json
import re
import statistics as stx
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_budget_curve import runs  # noqa: E402

CLASSES = [("install", re.compile(r"\b(pip|pip3|apt|apt-get|npm|yarn|conda|uv)\b.*\b(install|add)\b")),
           ("build", re.compile(r"\b(make|cmake|cargo build|gcc|g\+\+|javac|mvn|gradle|go build|tsc|webpack)\b")),
           ("test", re.compile(r"\b(pytest|unittest|npm test|cargo test|go test|ctest|tox|python3? -m pytest)\b"))]
LATE = 30.0


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def klass(step):
    text = " ".join(((c.get("arguments") or {}).get("keystrokes") or "") for c in (step.get("tool_calls") or []))
    for name, rx in CLASSES:
        if rx.search(text):
            return name
    return "other"


def forecasts(d, cls, i):
    past = d[:i]
    m3 = stx.mean(past[-3:])
    same = [x for x, c in zip(past, cls[:i]) if c == cls[i - 1]]
    return {"mean3": m3, "last": past[-1], "median5": stx.median(past[-5:]), "max3": max(past[-3:]),
            "p80": sorted(past)[int(0.8 * (len(past) - 1))], "same-class": stx.mean(same) if same else m3}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    model = args[0] if args else "qwen38"
    want = None
    if "--budgets" in sys.argv:
        want = {int(x) for x in sys.argv[sys.argv.index("--budgets") + 1].split(",")}
    err, late, n = defaultdict(list), defaultdict(int), 0
    cover, aside = defaultdict(int), defaultdict(list)
    lengths = []
    for (m, arm, b), run in sorted(runs().items()):
        if m != model or b == 12000 or (want and b not in want):
            continue
        for p in Path(run).glob("*__*/agent/trajectory.json"):
            try:
                steps = [s for s in json.loads(p.read_text(encoding="utf-8"))["steps"]
                         if s.get("source") == "agent" and s.get("timestamp")]
            except (OSError, ValueError, KeyError):
                continue
            t = [ts(s["timestamp"]) for s in steps]
            d = [b_ - a_ for a_, b_ in zip(t, t[1:])]
            cls = [klass(s) for s in steps[:-1]]
            lengths += d
            for i in range(3, len(d)):
                n += 1
                fc = forecasts(d, cls, i)
                for k, f in fc.items():
                    err[k].append(abs(d[i] - f))
                    late[k] += d[i] > f + LATE
                sd5 = stx.pstdev(d[max(0, i - 5):i])
                for k, f in {"mean3 + 60 s": fc["mean3"] + 60, "mean3 + 120 s": fc["mean3"] + 120,
                             "max3 + 60 s": fc["max3"] + 60, "max3 + 120 s": fc["max3"] + 120,
                             "mean3 + 2 x sd5 + 30 s": fc["mean3"] + 2 * sd5 + 30,
                             "mean3 x 2 + 30 s": 2 * fc["mean3"] + 30, "mean3 x 3": 3 * fc["mean3"]}.items():
                    cover[k] += d[i] <= f
                    aside[k].append(f)
    print(f"{model}: {n} turns forecast (turns 4 onward); turn length median {stx.median(lengths):.0f} s, "
          f"P90 {sorted(lengths)[int(.9 * len(lengths))]:.0f} s\n")
    print(f"| Forecaster | Median abs. error (s) | Turn ran > {LATE:.0f} s past the forecast |")
    print("|---|---|---|")
    for k in err:
        print(f"| {k} | {stx.median(err[k]):.0f} | {late[k]} of {n} |")
    print("\n| Rule for one more turn | Next turn finished inside it | Mean time set aside (s) |")
    print("|---|---|---|")
    for k in cover:
        print(f"| {k} | {cover[k]} of {n} | {stx.mean(aside[k]):.0f} |")


if __name__ == "__main__":
    main()
