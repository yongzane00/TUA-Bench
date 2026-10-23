#!/usr/bin/env python3
"""Model-server speed seen by the agent: output tokens per second of LLM wait time.

For each trial: n_output_tokens (result.json) / sum of llm_api_duration_ms over
agent/episode-*/debug.json. That includes prefill and queueing, so it drops when
the server is busier -- which is the point: compare it between runs to check they
got the same server conditions (a slower server means more 2400 s timeouts).

    python3 subset/tools/llm_speed.py <run_dir> [<run_dir> ...]
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def trial_speed(trial_dir: Path) -> tuple[float, float, str] | None:
    result = json.loads((trial_dir / "result.json").read_text())
    out = (result.get("agent_result") or {}).get("n_output_tokens")
    started = (result.get("agent_execution") or {}).get("started_at")
    llm_ms = 0.0
    for debug in trial_dir.glob("agent/episode-*/debug.json"):
        llm_ms += json.loads(debug.read_text()).get("llm_api_duration_ms") or 0.0
    if not out or llm_ms <= 0 or not started:
        return None
    return out / (llm_ms / 1000), llm_ms / 1000, started


def report(run_dir: Path) -> None:
    rows = [r for t in sorted(run_dir.glob("*__*")) if (t / "result.json").exists() and (r := trial_speed(t))]
    if not rows:
        print(f"{run_dir}: no trials with LLM timing yet")
        return
    speeds = sorted(r[0] for r in rows)
    q1, med, q3 = statistics.quantiles(speeds, n=4) if len(speeds) > 1 else (speeds[0],) * 3
    print(f"{run_dir}")
    print(f"  trials {len(rows)}   output tok/s of LLM time: median {med:.1f}  IQR {q1:.1f}-{q3:.1f}")
    by_hour: dict[str, list[float]] = {}
    for speed, _, started in rows:
        by_hour.setdefault(started[:13], []).append(speed)
    print("  by start hour (UTC): " + "  ".join(f"{h[-5:]}h {statistics.median(v):.0f}" for h, v in sorted(by_hour.items())))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        report(Path(arg))
