#!/usr/bin/env python3
"""Write a results markdown page (headline + per-task table) from task_report.py's JSON.

Usage:  python3 results_md.py r.json out.md <run_dir> "<header line>" <chart.svg>

The JSON must carry harbor_mean and score_py. For a clean run (every trial graded) it
should also carry ci_lo, ci_hi, pass1, pass2, pass4, pass5, all5, timeouts.
"""

import json
import sys

src, dst, run_dir, header, chart = sys.argv[1:6]
d = json.load(open(src))
rows, oc = d["rows"], d["outcomes"]
n = d["n_trials"]
ungraded_trials = n - oc.get("pass", 0) - oc.get("partial", 0) - oc.get("fail", 0)
never = [r for r in rows if r["graded"] == 0]
clean = not never and ungraded_trials == 0
by = {k: (sum(1 for r in rows if r["difficulty"] == k and r["graded"]), sum(1 for r in rows if r["difficulty"] == k))
      for k in ("easy", "medium", "hard")}
name = run_dir.rstrip("/").split("/")[-2]

out = [f"# {name} — results\n", f"Run `{run_dir}` · {header}\n"]

if clean:
    out += [
        # Deliberately no "every zero is a verdict" claim: a grader that needs a missing API key
        # fails inside pytest and looks like an ordinary FAILED. Pass known caveats via "notes".
        f"> **Clean run: all {n} trials graded.** No UID failures and no infrastructure failures.\n",
        *[f"> **Caveat:** {note}\n" for note in d.get("notes", [])],
        f"![accuracy vs cost]({chart})\n",
        "## Headline\n",
        "| metric | value | note |",
        "|---|---|---|",
        f"| **stratified S** (`subset/score.py`) | **{d['score_py']:.3f}** | estimate for the full 120-task "
        f"benchmark · 95% bootstrap CI **{d['ci_lo']:.3f}–{d['ci_hi']:.3f}** |",
        f"| mean reward | {d['harbor_mean']:.3f} | unweighted over the 40 subset tasks (harbor `mean`) |",
        f"| Pass@1 | {100 * d['pass1']:.1f}% | reward exactly 1 on a single attempt |",
        f"| Pass@2 / Pass@4 | {100 * d['pass2']:.1f}% / {100 * d['pass4']:.1f}% | |",
        f"| Pass@5 | {100 * d['pass5']:.1f}% | solved in at least 1 of 5 |",
        f"| All-5 | {100 * d['all5']:.1f}% | solved in all 5 |",
        f"| timeouts | {d['timeouts']} / {n} ({100 * d['timeouts'] / n:.0f}%) | the paper reports 4 / 600 at the same 2400 s |",
        f"| cost | ${d['total_cost']:.2f} | ${d['total_cost'] / n:.4f}/trial · proxy pricing $0.15/M in, "
        "$0.47/M out (no OpenRouter listing for flash-next) |",
        "",
        "harbor's own `pass_at_k` is empty: it refuses when any reward isn't exactly 0 or 1. Pass@k above "
        "comes from `subset/tools/leaderboard_metrics.py` and counts only reward = 1 as a pass.\n",
        "**Trial outcomes:** " + " · ".join(f"{k} {v}" for k, v in sorted(oc.items(), key=lambda x: -x[1])),
        "",
    ]
else:
    out += [
        f"> **Not a valid measurement of the model.** {ungraded_trials} of {n} trials were never graded, "
        f"{len(never)} of {len(rows)} tasks produced no grade on any attempt, and those {len(never)} are exactly the "
        f"`{', '.join(sorted({r['image'] for r in never}))}` tasks — the harbor UID bug documented in "
        "[`../RUNNING.md`](../RUNNING.md). Re-run with job output on `/mnt/c`, or after patching harbor, "
        "before quoting any number here.\n",
        f"![accuracy vs cost]({chart})\n",
        "## Headline\n",
        "| metric | value | caveat |",
        "|---|---|---|",
        f"| harbor `mean` | **{d['harbor_mean']:.3f}** | counts the {ungraded_trials} ungraded trials as 0 — biased low |",
        f"| `subset/score.py` (stratified) | **{d['score_py']:.3f}** | drops ungraded trials, so it measures only the "
        "gradeable, mostly-browser half — biased high |",
        "| harbor `pass_at_k` | *empty* | harbor refuses when any reward is not exactly 0 or 1 |",
        f"| tasks with any grade | **{sum(v[0] for v in by.values())} / {len(rows)}** | "
        f"easy {by['easy'][0]}/{by['easy'][1]} · medium {by['medium'][0]}/{by['medium'][1]} · "
        f"**hard {by['hard'][0]}/{by['hard'][1]}** |",
        f"| cost | **${d['total_cost']:.2f}** | ${d['total_cost'] / n:.4f}/trial · proxy pricing |",
        "",
        "**Trial outcomes:** " + " · ".join(f"{k} {v}" for k, v in sorted(oc.items(), key=lambda x: -x[1])),
        "",
        "- `uid` — the verifier could not write its output (ubuntu UID collision); never graded",
        "- `timeout` — agent hit 2400 s **and** the task is ubuntu, so it was also never graded",
        "- `infra` — `RuntimeError` **before** the agent started (e.g. an image build failing); not a model "
        "outcome. Report separately; re-run only these if needed, disclosed (see `RUNNING.md`, *Retries are not "
        "in the baseline*)",
        "- `error` — `RuntimeError` **after** the agent ran; counts as that attempt's result",
        "",
    ]

out += [
    "## Per task\n",
    "`graded` = attempts that produced a reward. `reward` = mean over graded attempts.\n",
    "| task | diff | image | graded | pass | reward | $/attempt | outcomes |",
    "|---|---|---|---|---|---|---|---|",
]
for r in rows:
    rew = "—" if r["mean_reward_graded"] is None else f"{r['mean_reward_graded']:.2f}"
    o = " ".join(f"{k} {v}" for k, v in sorted(r["outcomes"].items()))
    out.append(f"| `{r['task']}` | {r['difficulty']} | `{r['image'].replace('docker.io/', '')}` | "
               f"{r['graded']}/{r['attempts']} | {r['passes']} | {rew} | {r['cost_per_attempt']:.4f} | {o} |")
out += [
    "",
    "## Reproduce\n",
    "```bash",
    f"R={run_dir}",
    "python3 subset/tools/task_report.py $R --json /tmp/r.json",
    "python3 subset/score.py $R",
    "python3 subset/tools/leaderboard_metrics.py $R",
    "# add harbor_mean, score_py (and for a clean run ci_lo, ci_hi, pass1/2/4/5, all5, timeouts) to /tmp/r.json",
    'python3 subset/tools/plot_accuracy_cost.py /tmp/r.json subset/results/<name>-accuracy-cost.svg "subtitle"',
    'python3 subset/tools/results_md.py /tmp/r.json subset/results/<name>.md $R "header" <name>-accuracy-cost.svg',
    "```",
]
open(dst, "w").write("\n".join(out) + "\n")
print(f"wrote {dst}")
