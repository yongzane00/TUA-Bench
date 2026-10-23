#!/usr/bin/env python3
"""Split agent wall-clock into LLM time vs environment time.

Every terminus-2 episode writes agent/episode-N/debug.json containing
llm_api_duration_ms for that API call. Summing those and subtracting from the
agent_execution window in result.json gives the time spent NOT waiting on the
model -- i.e. tmux keystroke waits, command execution, container I/O.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def trial_report(trial_dir: Path) -> None:
    result = json.loads((trial_dir / "result.json").read_text())
    exec_win = result.get("agent_execution") or {}
    if not exec_win.get("started_at") or not exec_win.get("finished_at"):
        return
    wall = (parse_ts(exec_win["finished_at"]) - parse_ts(exec_win["started_at"])).total_seconds()

    llm_ms = 0.0
    calls = 0
    for dbg in sorted((trial_dir / "agent").glob("episode-*/debug.json")):
        text = dbg.read_text(errors="ignore")
        # one post_api_call record per episode; take every duration it reports
        for m in re.finditer(r'"llm_api_duration_ms":\s*([0-9.]+)', text):
            llm_ms += float(m.group(1))
            calls += 1

    llm_s = llm_ms / 1000
    env_s = wall - llm_s
    out_tok = (result.get("agent_result") or {}).get("n_output_tokens") or 0

    name = trial_dir.name.split("__")[0]
    print(f"  {name:<28} wall={wall:7.0f}s  llm={llm_s:6.0f}s ({llm_s / wall * 100:4.1f}%)  "
          f"env={env_s:7.0f}s ({env_s / wall * 100:4.1f}%)  calls={calls:3d}  "
          f"out_tok/s={out_tok / llm_s if llm_s else 0:5.1f}")


if __name__ == "__main__":
    for run in sys.argv[1:]:
        run_dir = Path(run)
        print(f"\n=== {run_dir.name} ===")
        for trial in sorted(d for d in run_dir.iterdir() if d.is_dir()):
            trial_report(trial)
