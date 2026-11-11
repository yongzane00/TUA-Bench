#!/usr/bin/env python3
"""Does the meter's "turns that fit" count climb back up near the deadline? (idea 4 in the plan progress log)

    python -X utf8 forecast_rebound.py [qwen38]

Reads the meter lines the model actually saw in the finished shown-arm (H7) runs: each agent step's observation
starts the next turn with "[Time X of B s, L s left | ... | about N turns fit]". The moment the count first reads
1 or 0 is the meter's own "last turn" signal (the same moment a wrap-up notice is meant for). After it:
  rebound    the count later reads 3 or more again (short turns pulled the 3-turn mean down)
  turns      how many more turns the model took
  outcome    timed out (harbor's AgentTimeoutError) or finished
Two other displays are simulated on the same turns, from the X values (turn length = gap between two meter lines):
  max3       time left // the longest of the last 3 turns
  frozen     after the moment, never more than the count at the moment
"""
import json
import re
import statistics as stx
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_budget_curve import runs  # noqa: E402

METER = re.compile(r"\[Time (\d+) of (\d+) s, (\d+) s left[^\]]*?(?:about (\d+) turns? fit)?\]")


def meters(traj: dict) -> list[tuple[float, float, int | None]]:
    out = []
    for s in traj["steps"]:
        if s.get("source") != "agent":
            continue
        m = METER.search(json.dumps(s.get("observation") or {}))
        if m:
            out.append((float(m[1]), float(m[3]), int(m[4]) if m[4] else None))
    return out


def max3_counts(seq):
    xs = [x for x, _, _ in seq]
    out = []
    for j, (x, left, _) in enumerate(seq):
        d = [b - a for a, b in zip([0.0] + xs[:j], xs[:j + 1])][-3:]
        d = [v for v in d if v > 0]
        out.append(int(left // max(d)) if d else None)
    return out


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen38"
    rows = []
    for (m, arm, b), run in sorted(runs().items()):
        if m != model or arm != "shown":
            continue
        for p in sorted(Path(run).glob("*__*/agent/trajectory.json")):
            try:
                seq = meters(json.loads(p.read_text(encoding="utf-8")))
                res = json.loads((p.parent.parent / "result.json").read_text(encoding="utf-8"))
            except (OSError, ValueError, KeyError):
                continue
            k = next((i for i, (_, _, n) in enumerate(seq) if n is not None and n <= 1), None)
            if k is None:
                continue
            later = [n for _, _, n in seq[k + 1:] if n is not None]
            alt = max3_counts(seq)
            rows.append(dict(budget=b, left=seq[k][1], n0=seq[k][2], turns=len(seq) - 1 - k,
                             rebound=any(n >= 3 for n in later), peak=max(later, default=seq[k][2]),
                             max3_rebound=any(n is not None and n >= 3 for n in alt[k + 1:]),
                             timeout=((res.get("exception_info") or {}).get("exception_type") == "AgentTimeoutError"),
                             reward=((res.get("verifier_result") or {}).get("rewards") or {}).get("reward", 0) or 0))
    print(f"{model}, shown arm: {len(rows)} trials where the count first read 1 or 0\n")
    print("| Budget | Trials | Count later read >= 3 | Same, if the count used the longest of the last 3 turns | "
          "Turns after the moment (median) | Time left at the moment (median s) |")
    print("|---|---|---|---|---|---|")
    for b in sorted({r["budget"] for r in rows}) + [None]:
        rs = [r for r in rows if b is None or r["budget"] == b]
        print(f"| {b or 'all'} | {len(rs)} | {sum(r['rebound'] for r in rs)} of {len(rs)} | "
              f"{sum(r['max3_rebound'] for r in rs)} of {len(rs)} | {stx.median([r['turns'] for r in rs]):.0f} | "
              f"{stx.median([r['left'] for r in rs]):.0f} |")
    print("\n| After the moment | Trials | Timed out | Reward == 1 | Turns after (median) |")
    print("|---|---|---|---|---|")
    for name, rs in (("count rose to >= 3 again", [r for r in rows if r["rebound"]]),
                     ("count stayed below 3", [r for r in rows if not r["rebound"]])):
        if rs:
            print(f"| {name} | {len(rs)} | {sum(r['timeout'] for r in rs)} of {len(rs)} | "
                  f"{sum(r['reward'] == 1 for r in rs)} of {len(rs)} | {stx.median([r['turns'] for r in rs]):.0f} |")
    peaks = Counter(min(r["peak"], 10) for r in rows if r["rebound"])
    print("\nHighest later count in the rebound trials (10 = 10 or more):",
          ", ".join(f"{k}: {v}" for k, v in sorted(peaks.items())))


if __name__ == "__main__":
    main()
