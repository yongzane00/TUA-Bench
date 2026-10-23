#!/usr/bin/env python3
"""Per-task token + cost rollup for any harbor job run directory.

Priced at OpenRouter list rates for qwen/qwen3.8-27b:
  $0.15 / M input, $1.875 / M output.  Cache reads ($0.0375/M) don't apply --
  neither vLLM nor SGLang reports cached_tokens back to harbor.

Usage:  python3 cost_summary.py <job_run_dir> [<job_run_dir> ...]
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

IN_RATE, OUT_RATE = 0.15 / 1e6, 1.875 / 1e6


def report(run_dir: Path) -> None:
    agg: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])  # in, out, passes, trials
    for result_path in sorted(run_dir.glob("*/result.json")):
        r = json.loads(result_path.read_text())
        task = (r.get("task_name") or result_path.parent.name).split("/")[-1]
        ag = r.get("agent_result") or {}
        v = r.get("verifier_result") or {}
        rew = next(iter(v.get("rewards", {}).values()), 0)
        a = agg[task]
        a[0] += ag.get("n_input_tokens") or 0
        a[1] += ag.get("n_output_tokens") or 0
        a[2] += 1 if rew == 1 else 0
        a[3] += 1

    print(f"\n=== {run_dir.name} ===")
    print(f"  {'task':<28} {'pass':>6} {'input':>11} {'output':>9} {'cost':>9}")
    ti = to = 0
    for task in sorted(agg):
        i, o, p, n = agg[task]
        ti += i
        to += o
        print(f"  {task:<28} {f'{p}/{n}':>6} {i:>11,} {o:>9,} {f'${i * IN_RATE + o * OUT_RATE:.4f}':>9}")
    cost = ti * IN_RATE + to * OUT_RATE
    print(f"  {'TOTAL':<28} {'':>6} {ti:>11,} {to:>9,} {f'${cost:.4f}':>9}")
    print(f"  input ${ti * IN_RATE:.4f} / output ${to * OUT_RATE:.4f}  "
          f"(output = {to * OUT_RATE / cost * 100:.0f}% of cost, {to / (ti + to) * 100:.1f}% of tokens)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    for arg in sys.argv[1:]:
        report(Path(arg))
