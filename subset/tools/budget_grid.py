#!/usr/bin/env python3
"""Budget sweep grid: every budget, for every model, in two arms.

  shown  = H6 / H7 / H8: the cap, plus the budget in the task text and a meter on every update
  hidden = H0 + the same cap: same stop code, nothing told to the model (H8/H7 with show_budget: false;
           stock terminus-2 with max_turns for turns). At 2400 s harbor's own limit ends both arms first, so the
           hidden 2400 s run is an H0 re-run on today's server (the old H0 ran on a slower server day).

    python3 subset/tools/budget_grid.py configs   # write missing configs (make_variant.py), never overwrites
    python3 subset/tools/budget_grid.py queues    # write subset/queue/<model>.txt in run order

run_tracker.py imports GRID and the name functions from here.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
Q38, Q36 = "qwen38-flash-next", "qwen36-35b-a3b"

# five budgets per type and model: 0.5x, 0.75x, 1x (base), 1.5x, 2x the base budget.
# Base: 40 turns (H6), 2400 s (harbor's agent limit, H7), the model's H0 mean cost_usd per trial (H8).
GRID = {
    Q38: {"turns": [20, 30, 40, 60, 80], "time": [1200, 1800, 2400, 3600, 4800],
          "cost": ["0.015", "0.0225", "0.030", "0.045", "0.060"]},
    Q36: {"turns": [20, 30, 40, 60, 80], "time": [1200, 1800, 2400, 3600, 4800],
          "cost": ["0.08", "0.12", "0.16", "0.24", "0.32"]},
}
CURRENT = {Q38: {"turns": 40, "time": 2400, "cost": "0.030"}, Q36: {"turns": 40, "time": 2400, "cost": "0.16"}}

# run order (same for both models): first the 0.75x and 1.5x budgets, by type time > cost > turns (the hidden
# control of the done shown base run first), then 0.5x and 2x in the same type order. Shown + hidden pairs of a
# budget run back to back so they see the same server conditions.
def _order(m):
    t, c, n = GRID[m]["time"], GRID[m]["cost"], GRID[m]["turns"]  # each: [0.5x, 0.75x, 1x, 1.5x, 2x]
    return [("time", [t[2], t[1], t[3]]), ("cost", [c[2], c[1], c[3]]), ("turns", [n[2], n[1], n[3]]),
            ("time", [t[0], t[4]]), ("cost", [c[0], c[4]]), ("turns", [n[0], n[4]])]


ORDER = {m: _order(m) for m in (Q38, Q36)}

SHOWN_CLS = {"turns": "terminus_2_harness6:Terminus2Harness6", "time": "terminus_2_harness7:Terminus2Harness7",
             "cost": "terminus_2_harness8:Terminus2Harness8"}
KWARG = {"turns": "max_turns", "time": "time_budget_sec", "cost": "cost_budget_usd"}
PREFIX = {"turns": "turns", "time": "time", "cost": "cost"}

MODEL_ARGS = {
    Q38: [],
    Q36: ["agents.0.model_name=openai/nvidia/Qwen3.6-35B-A3B-NVFP4",
          "agents.0.kwargs.api_base=http://<qwen36-vllm-host>:8000/v1",
          "agents.0.kwargs.model_info.max_input_tokens=262144",
          "agents.0.kwargs.model_info.input_cost_per_token=5.0e-08",
          "agents.0.kwargs.model_info.output_cost_per_token=7.0e-07",
          "+agents.0.kwargs.llm_call_kwargs={max_tokens: 32768}"],
}


def shown_name(kind, b):
    return f"harness{ {'turns': 6, 'time': 7, 'cost': 8}[kind] }-{PREFIX[kind]}{b}-attempt5"


def hidden_name(kind, b):
    return f"harness0-{PREFIX[kind]}{b}-attempt5"


def args(model, kind, b, shown):
    a = ["n_attempts=5", "n_concurrent_trials=4"]
    if kind == "turns" and not shown:
        a += [f"agents.0.kwargs.max_turns={b}", "+agents.0.kwargs.suppress_max_turns_warning=true"]
    else:
        a += ["agents.0.name=null", f"+agents.0.import_path=harbor.agents.terminus_2.{SHOWN_CLS[kind]}"]
        a += [f"{'' if kind == 'turns' else '+'}agents.0.kwargs.{KWARG[kind]}={b}"]
        if not shown:
            a += ["+agents.0.kwargs.show_budget=false"]
    if kind == "time" and b > 2400:
        a += [f"+agents.0.override_timeout_sec={b + 600}"]  # room for the harness stop + the last turn
    return a + MODEL_ARGS[model]


def configs():
    for model, kinds in GRID.items():
        for kind, budgets in kinds.items():
            for b in budgets:
                for shown, name in ((True, shown_name(kind, b)), (False, hidden_name(kind, b))):
                    if (REPO / f"subset/variants/{model}/{name}.yaml").exists():
                        continue
                    subprocess.run([sys.executable, str(REPO / "subset/make_variant.py"), f"{model}/{name}",
                                    *args(model, kind, b, shown)], check=True)


def queue(model):
    out = []
    for kind, budgets in ORDER[model]:
        for b in budgets:
            names = [hidden_name(kind, b)] if b == CURRENT[model][kind] else [shown_name(kind, b), hidden_name(kind, b)]
            out += names
    return out


def queues():
    d = REPO / "subset/queue"
    d.mkdir(exist_ok=True)
    for model in GRID:
        lines = [f"# {model}: run order for run_queue.sh (edit freely; done configs are skipped, read before each run)"]
        lines += queue(model)
        (d / f"{model}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote subset/queue/{model}.txt: {len(lines) - 1} runs")


if __name__ == "__main__":
    {"configs": configs, "queues": queues}[sys.argv[1]]()
