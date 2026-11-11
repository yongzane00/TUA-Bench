#!/usr/bin/env python3
"""Compare what the model was sent in the plugin-off check (pilot/selftest/selftest-baseline.yaml).

    python3 compare_prompts.py <job folder>

Reads every trial's agent/episode-*/prompt.txt in order, replaces the container's hostname, collapses the pane's empty
padding lines, and compares each H7 arm with stock terminus-2: identical prompt sequences pass; otherwise the differing
lines are printed. Also checks that the trials overlapped in time and that each H7 trial's budget clock matches its own
run time (no shared clock).
"""
import difflib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HOST = re.compile(r"root@[0-9a-f]{12}")
PAD = re.compile(r"\n{3,}")  # the pane pads the screen with empty lines; how many depends on earlier output


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def load(trial: Path):
    r = json.loads((trial / "result.json").read_text(encoding="utf-8"))
    eps = sorted((trial / "agent").glob("episode-*/prompt.txt"), key=lambda p: int(p.parent.name.split("-")[1]))
    prompts = [PAD.sub("\n\n", HOST.sub("root@HOST", p.read_text(encoding="utf-8"))) for p in eps]
    ae = r.get("agent_execution") or {}
    bud = ((r.get("agent_result") or {}).get("metadata") or {}).get("budget") or {}
    return dict(version=(r.get("agent_info") or {}).get("version"), prompts=prompts, t0=ts(ae["started_at"]),
                t1=ts(ae["finished_at"]), elapsed=bud.get("elapsed_sec"),
                reward=((r.get("verifier_result") or {}).get("rewards") or {}).get("reward"))


def main():
    job = Path(sys.argv[1])
    trials = [load(t) for t in sorted(job.glob("*__*")) if (t / "result.json").exists()]
    stock = next(t for t in trials if "harness7" not in (t["version"] or ""))
    print(f"stock: {stock['version']}, {len(stock['prompts'])} prompts, reward {stock['reward']}")
    for t in trials:
        if t is stock:
            continue
        same = t["prompts"] == stock["prompts"]
        print(f"\n{t['version']}: {len(t['prompts'])} prompts, reward {t['reward']}, identical to stock: {same}")
        if not same:
            for i, (a, b) in enumerate(zip(stock["prompts"], t["prompts"])):
                diff = [d for d in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0)
                        if d[:1] in "+-" and not d.startswith(("+++", "---"))]
                if diff:
                    print(f"  prompt {i}:")
                    for d in diff[:6]:
                        print(f"    {d[:160]}")
        if t["elapsed"] is not None:
            print(f"  budget clock {t['elapsed']:.1f} s vs agent run time {t['t1'] - t['t0']:.1f} s")
    lo, hi = max(t["t0"] for t in trials), min(t["t1"] for t in trials)
    print(f"\nall {len(trials)} trials ran at the same time for {max(0.0, hi - lo):.1f} s")


if __name__ == "__main__":
    main()
