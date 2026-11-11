#!/usr/bin/env python3
"""Secondary metrics of the code-repair pilot (batch 2 of subset/results/analysis-plan.md) and blinded report packets.

    python3 pilot/pilot_report.py <model> <label>=<config> [<label>=<config> ...] [--packets <dir>]
    e.g. pilot/pilot_report.py qwen38-flash-next hidden=swe-dev-hidden-time900-rounds3 \
         full=swe-dev-full-time900-rounds3 wrap=swe-dev-wrap120-time900-rounds3 --packets ~/work/report-check

Merges every job folder of each config (one per round). The qualified counts and the paired gaps come from
subset/tools/ablation_report.py; this adds the frozen secondary metrics, per arm:
  outcome states     qualified (reward 1); partial (reward below 1, saved diff not empty); failed (the rest)
  wrong declarations declared complete (mark_task_complete in the trajectory) but not qualified, x of declared
  stopped by time    the budget stop fired (`budget.stop` = "time")
  lateness           over trials stopped by time: delivery lateness `elapsed_sec` - budget (work stopped, terminal
                     cleaned, diff saved) and work lateness `stopped_at_sec` - budget, each trial against its own
                     `time_budget_sec`; median, P95, max
  process left       stops where the Ctrl-C did not end the foreground command (`stop_interrupt.stopped` false)
  $ per qualified    the arm's model cost over its qualified trials

--packets <dir> writes one Markdown file per trial that declared completion, for the report check: the report (the
analysis of each reply that marked the task complete) and the commands and outputs from the trajectory, with every
harness line that would show the arm (meter lines, the wrap-up notice) removed. Files are named by a random id;
`<dir>/key.json` maps the ids back to arm and trial and is opened only after the review.
"""
import glob
import json
import os
import random
import re
import statistics as stx
import sys

JOBS = os.environ.get("TUA_JOBS", "/mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/jobs")
HARNESS_LINES = re.compile(r"^\[(Time \d+ of \d+ s|Wrap-up:)[^\n]*\]\n?", re.M)
OUT_CHARS = 1500


def trials_of(model, cfg):
    out = []
    for p in sorted(glob.glob(f"{JOBS}/{model}/{cfg}/*/*__*/result.json")):
        r = json.load(open(p))
        ar = r.get("agent_result") or {}
        md = (ar.get("metadata") or {}).get("budget") or {}
        traj = os.path.join(os.path.dirname(p), "agent", "trajectory.json")
        steps = json.load(open(traj, encoding="utf-8"))["steps"] if os.path.exists(traj) else []
        declaring = [s for s in steps if any(c.get("function_name") == "mark_task_complete"
                                             for c in s.get("tool_calls") or [])]
        out.append(dict(name=r["trial_name"], reward=((r.get("verifier_result") or {}).get("rewards") or {})
                        .get("reward", 0) or 0, cost=ar.get("cost_usd") or 0.0, budget=md,
                        diff_files=(md.get("final_diff") or {}).get("files_changed") or 0,
                        declared=bool(declaring), declaring=declaring, steps=steps,
                        error=(r.get("exception_info") or {}).get("exception_type")))
    return out


def q(xs, f):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(f * (len(xs) - 1))))]


def lateness(ts, key):
    xs = [t["budget"][key] - t["budget"]["time_budget_sec"] for t in ts
          if t["budget"].get("stop") == "time" and t["budget"].get(key) is not None]
    return f"{stx.median(xs):.1f} / {q(xs, .95):.1f} / {max(xs):.1f} (n {len(xs)})" if xs else "-"


def packet(t):
    lines = [f"# Trial for review\n", "## Report(s) the agent gave when it marked the task complete\n"]
    for s in t["declaring"]:
        lines.append(HARNESS_LINES.sub("", str(s.get("message") or "")).strip() + "\n")
    lines.append("## What the agent ran and saw (in order)\n")
    for i, s in enumerate(t["steps"]):
        if s.get("source") != "agent":
            continue
        cmds = [(c.get("arguments") or {}).get("keystrokes", "") for c in s.get("tool_calls") or []
                if c.get("function_name") == "bash_command"]
        res = (s.get("observation") or {}).get("results") or []
        out = HARNESS_LINES.sub("", "\n".join(str(r.get("content") or "") for r in res)).strip()
        if not cmds and not out:
            continue
        lines.append(f"### Step {i}\n")
        for c in cmds:
            lines.append("```\n$ " + c.rstrip() + "\n```")
        if out:
            cut = out if len(out) <= OUT_CHARS else out[:OUT_CHARS // 2] + "\n[...]\n" + out[-OUT_CHARS // 2:]
            lines.append("Output:\n```\n" + cut + "\n```\n")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    pdir = args[args.index("--packets") + 1] if "--packets" in args else None
    model = args[0]
    arms = [a.split("=", 1) for a in args[1:] if "=" in a and not a.startswith("--")]
    data = {label: trials_of(model, cfg) for label, cfg in arms}
    print("| Arm | Trials | Qualified | Partial | Failed | Wrong declarations | Stopped by time | "
          "Delivery lateness, median / P95 / max (s) | Work lateness, median / P95 / max (s) | Process left running | "
          "$ per qualified |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for label, ts in data.items():
        n = len(ts)
        qual = [t for t in ts if t["reward"] == 1]
        part = [t for t in ts if t["reward"] < 1 and t["diff_files"] > 0]
        decl = [t for t in ts if t["declared"]]
        wrong = [t for t in decl if t["reward"] < 1]
        stopped = [t for t in ts if t["budget"].get("stop") == "time"]
        left = [t for t in ts if (t["budget"].get("stop_interrupt") or {}).get("stopped") is False]
        cost = sum(t["cost"] for t in ts)
        print(f"| {label} | {n} | {len(qual)} of {n} | {len(part)} of {n} | {n - len(qual) - len(part)} of {n} | "
              f"{len(wrong)} of {len(decl)} | {len(stopped)} of {n} | {lateness(ts, 'elapsed_sec')} | "
              f"{lateness(ts, 'stopped_at_sec')} | {len(left)} of {len(stopped)} | "
              f"{'$%.4f' % (cost / len(qual)) if qual else '-'} |")
    if pdir:
        os.makedirs(pdir, exist_ok=True)
        rnd, key = random.Random(0), {}
        for label, ts in data.items():
            for t in ts:
                if not t["declared"]:
                    continue
                pid = "%06x" % rnd.getrandbits(24)
                while pid in key:
                    pid = "%06x" % rnd.getrandbits(24)
                key[pid] = {"arm": label, "trial": t["name"]}
                with open(os.path.join(pdir, f"{pid}.md"), "w", encoding="utf-8") as f:
                    f.write(packet(t))
        with open(os.path.join(pdir, "key.json"), "w") as f:
            json.dump(key, f, indent=1, sort_keys=True)
        print(f"\n{len(key)} packets in {pdir} (key.json maps ids to arms; open it after the review)")


if __name__ == "__main__":
    main()
