#!/usr/bin/env python3
"""Run tracker: the budget sweep (hidden vs shown, every budget, both models), the queues, other runs.

Reads the jobs folders (newest timestamp folder of each config), prints the tables and rewrites the
status section of subset/results/run-tracker.md. The grid and run order live in budget_grid.py.

    wsl -e bash -lc 'python3 /mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/subset/tools/run_tracker.py'

Run it from WSL so it can see live harbor and queue processes (pgrep); from Windows, "running" is guessed
from trial files written in the last 20 minutes.
"""

import datetime
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from budget_grid import CURRENT, GRID, Q36, Q38, hidden_name, queue, shown_name  # noqa: E402

WIN = Path("/mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench")
REPO = WIN if WIN.exists() else Path(__file__).resolve().parents[2]
JOBS = Path(os.environ.get("TUA_JOBS", REPO / "jobs"))
MD = REPO / "subset/results/run-tracker.md"
GPT = "gpt55-chatgpt"

# H0 cut at budget (simulated from the H0 trajectories: a trial keeps its reward only if it finished within
# the budget). Rough check only; the hidden arm is the real control.
CUT = {
    (Q38, "turns", 10): "0.230", (Q38, "turns", 15): "0.346", (Q38, "turns", 20): "0.395", (Q38, "turns", 40): "0.445",
    (Q36, "turns", 20): "0.088", (Q36, "turns", 30): "0.113", (Q36, "turns", 40): "0.125", (Q36, "turns", 60): "0.158",
    (Q38, "time", 600): "0.248", (Q38, "time", 1200): "0.360", (Q38, "time", 1800): "0.420", (Q38, "time", 2400): "0.430",
    (Q36, "time", 600): "0.129", (Q36, "time", 1200): "0.145", (Q36, "time", 1800): "0.171", (Q36, "time", 2400): "0.189",
    (Q38, "cost", "0.015"): "0.265", (Q38, "cost", "0.030"): "0.359", (Q38, "cost", "0.048"): "0.400",
    (Q36, "cost", "0.05"): "0.119", (Q36, "cost", "0.10"): "0.147", (Q36, "cost", "0.16"): "0.164",
    (Q36, "cost", "0.26"): "0.179",
}
UNIT = {"turns": lambda b: f"{b} turns", "time": lambda b: f"{b} s", "cost": lambda b: f"${b}"}
TITLE = {"turns": "Turn budget (shown = H6)", "time": "Time budget (shown = H7)", "cost": "Cost budget (shown = H8, harbor `cost_usd`)"}
OTHER = [
    (Q38, "harness9-time2400-cost0.048-attempt5", "H9, 2400 s + $0.048"),
    (Q36, "harness9-time2400-cost0.26-attempt5", "H9, 2400 s + $0.26"),
    (Q38, "harness0-timeout12000-attempt5", "H0, 12000 s limit"),
    (GPT, "test", "gpt-5.5, 3 tasks × 1"),
    (GPT, "harness0-attempt5", "gpt-5.5 H0"),
    (GPT, "harness6-turns40-attempt5", "gpt-5.5 H6, 40 turns"),
]


def pgrep(pattern: str) -> str:
    try:
        return subprocess.run(["pgrep", "-af", pattern], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return ""


def ts(s):
    return datetime.datetime.fromisoformat(s) if s else None


def status(model: str, variant: str, procs: str) -> dict:
    cfg = REPO / f"subset/variants/{model}/{variant}.yaml"
    runs = sorted(d for d in glob.glob(str(JOBS / model / variant / "*")) if os.path.exists(f"{d}/config.json"))
    if not runs:
        return dict(state="⬜", run="", done=0, n=0, score=None, cost=None, hours=None, cfg=cfg.exists())
    run = runs[-1]
    jc = json.load(open(f"{run}/config.json", encoding="utf-8"))
    n = jc.get("n_attempts", 1) * sum(len(d.get("task_names") or []) for d in jc.get("datasets", []))
    rewards, costs, newest = [], [], 0.0
    for t in glob.glob(f"{run}/*__*"):
        newest = max(newest, os.path.getmtime(t))
        try:
            r = json.load(open(f"{t}/result.json", encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rewards.append(((r.get("verifier_result") or {}).get("rewards") or {}).get("reward", 0) or 0)
        costs.append((r.get("agent_result") or {}).get("cost_usd") or 0)
    try:
        jr = json.load(open(f"{run}/result.json", encoding="utf-8"))
    except (OSError, ValueError):
        jr = {}
    finished, started = ts(jr.get("finished_at")), ts(jr.get("started_at"))
    alive = f"{model}/{variant}." in procs if procs else (time.time() - newest < 1200)
    state = "✅" if finished else ("🔄" if alive else "⚠ stopped")
    hours = (finished - started).total_seconds() / 3600 if finished and started else None
    return dict(state=state, run=os.path.basename(run), done=len(rewards), n=n, hours=hours, cfg=True,
                score=sum(rewards) / n if n and finished else None, cost=sum(costs) / len(costs) if costs else None)


def cell(s: dict) -> str:
    if s["state"] == "✅":
        return f"✅ **{s['score']:.3f}** · ${s['cost']:.4f}"
    if s["state"] == "⬜":
        return "⬜" if s["cfg"] else "⬜ no config"
    return f"{s['state']} {s['done']}/{s['n']}"


def main() -> None:
    procs = pgrep("harbor run")
    qprocs = pgrep("run_queue.sh")
    st = {}

    def get(model, variant):
        if (model, variant) not in st:
            st[(model, variant)] = status(model, variant, procs)
        return st[(model, variant)]

    lines = []
    # ---- queues
    lines += ["", "### Queues (one run at a time per model server)", "",
              "| Model | Queue process | Done | Now running | Next | Time left (rough) |", "|---|---|---|---|---|---|"]
    for model in GRID:
        allq = [c for c in open(REPO / f"subset/queue/{model}.txt", encoding="utf-8").read().split()
                if c.startswith("harness")] if (REPO / f"subset/queue/{model}.txt").exists() else queue(model)
        q = [c for c in allq if not c.endswith("-rerun")]  # re-runs of setup failures (rerun_failed.py) aren't counted
        ss = [(c, get(model, c)) for c in allq]
        done = [s for c, s in ss if s["state"] == "✅" and c in q]
        running = [f"`{c}` {s['done']}/{s['n']}" for c, s in ss if s["state"] == "🔄"]
        todo = [c for c, s in ss if s["state"] != "✅" and s["state"] != "🔄"]
        hrs = [s["hours"] for s in done if s["hours"]] or [12.0]
        left = (len([c for c in todo if c in q]) + 0.5 * len(running)) * sum(hrs) / len(hrs)
        alive = "🔄 running" if f"run_queue.sh {model}" in qprocs else ("⬜ not running" if qprocs or procs else "⬜ not running?")
        lines.append(f"| {model} | {alive} | {len(done)}/{len(q)} | {', '.join(running) or '—'} | "
                     f"{'`' + todo[0] + '`' if todo else '—'} | ~{left:.0f} h ({left / 24:.1f} days) |")

    # ---- every queued run, in run order
    for model in GRID:
        qf = REPO / f"subset/queue/{model}.txt"
        q = [c for c in open(qf, encoding="utf-8").read().split() if c.startswith("harness")] if qf.exists() else queue(model)
        q = [c for c in q if not c.endswith("-rerun")]
        lines += ["", f"### Run order: {model} ({len(q)} runs)", "",
                  "| # | Config | Budget type | Arm | Budget | Status | Run |", "|---|---|---|---|---|---|---|"]
        for i, c in enumerate(q, 1):
            body = c.removesuffix("-attempt5").split("-", 1)[1]  # e.g. time1200, cost0.16, turns40
            kind = next(k for k in ("turns", "time", "cost") if body.startswith(k))
            b = body[len(kind):]
            arm = "hidden (H0 + cap)" if c.startswith("harness0-") else f"shown (H{c[7]})"
            s = get(model, c)
            lines.append(f"| {i} | `{c}` | {kind} | {arm} | {UNIT[kind](b)} | {cell(s)} | {s['run']} |")

    # ---- reference
    lines += ["", "### No budget (H0, uncapped): the right-hand end of every curve", "",
              "| Model | Score | Mean `cost_usd` | Run |", "|---|---|---|---|"]
    for model in GRID:
        s = get(model, "harness0-attempt5")
        lines.append(f"| {model} | {s['score']:.3f} | ${s['cost']:.4f} | {s['run']} |" if s["score"] is not None
                     else f"| {model} | {cell(s)} | | |")

    # ---- grid
    for kind in ("time", "turns", "cost"):
        lines += ["", f"### {TITLE[kind]}", "",
                  "| Model | Budget | Hidden: H0 + cap (model not told) | Shown: model told | Shown − hidden | "
                  "H0 cut (simulated) |", "|---|---|---|---|---|---|"]
        for model in GRID:
            for b in GRID[model][kind]:
                h, s = get(model, hidden_name(kind, b)), get(model, shown_name(kind, b))
                diff = f"{s['score'] - h['score']:+.3f}" if h["score"] is not None and s["score"] is not None else ""
                tag = " (current)" if b == CURRENT[model][kind] else ""
                lines.append(f"| {model} | {UNIT[kind](b)}{tag} | {cell(h)} | {cell(s)} | {diff} | "
                             f"{CUT.get((model, kind, b), '')} |")
    lines += ["", "Budgets are 0.5×, 0.75×, 1× (current), 1.5×, 2× the base. At 2400 s harbor's own limit ends both arms, "
              "so the hidden 2400 s run is an H0 re-run on today's server."]

    # ---- other
    lines += ["", "### Other (not in the queues)", "", "| Model | Config | What | Status | Run |", "|---|---|---|---|---|"]
    for model, variant, what in OTHER:
        s = get(model, variant)
        lines.append(f"| {model} | `{variant}` | {what} | {cell(s)} | {s['run']} |")

    stamp = time.strftime("%Y-%m-%d %H:%M")
    table = "\n".join([f"Status as of {stamp} (`python3 subset/tools/run_tracker.py` refreshes it). "
                       "Cells: ✅ score · mean `cost_usd` / 🔄 trials done / ⚠ stopped / ⬜ not started.", *lines])
    print(table)
    if MD.exists():
        text = MD.read_text(encoding="utf-8")
        a, b = "<!-- status:start -->", "<!-- status:end -->"
        if a in text and b in text:
            text = text[: text.index(a) + len(a)] + "\n" + table + "\n" + text[text.index(b):]
            MD.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
