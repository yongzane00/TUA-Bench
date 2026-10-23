#!/usr/bin/env python3
"""Re-run trials whose environment setup failed (docker compose failed before the agent ran), then merge them.

    python3 subset/tools/rerun_failed.py make  <model>/<variant> [--since 2026-10-12T01:30]  # write <variant>-rerun.yaml, queue it first
    python3 subset/tools/rerun_failed.py merge <model>/<variant> [--apply]  # after the re-run finished

make: finds the setup-failed trials in the newest finished run of <variant> and writes
  subset/variants/<model>/<variant>-rerun.yaml (same config, those tasks only, n_attempts = most failures of one task),
  then puts `<variant>-rerun` at the top of subset/queue/<model>.txt (the queue runs it at the next run boundary,
  so the server never gets more than one run's 4 trials).
merge (dry run unless --apply):
  - each setup-failed trial of the original run  -> jobs/<model>/aborted/<variant>__<run>__replaced/
  - one usable re-run trial per failed trial      -> the original run folder
  - the re-run job folder keeps its job-level files and a note (so the queue sees it as done)
  - MERGED.md in the original run
Agent-side errors (e.g. tmux "failed to send keys" mid-run) are not setup failures and stay as they are.
--since <UTC time>: also re-run every trial that finished at or after that time (result.json finished_at, UTC),
  e.g. after an infrastructure problem began. make records it in the -rerun.yaml header; merge reads it from there.
"""

import collections
import glob
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path("/mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench")
if not REPO.exists():
    REPO = Path(__file__).resolve().parents[2]
WSL_REPO = Path.home() / "work/TUA-Bench"
JOBS = REPO / "jobs"


def runs(model, variant):
    return sorted(d for d in glob.glob(str(JOBS / model / variant / "20*")) if os.path.exists(f"{d}/config.json"))


def finished(run) -> bool:
    try:
        return bool(json.load(open(f"{run}/result.json", encoding="utf-8")).get("finished_at"))
    except (OSError, ValueError):
        return False


def setup_failed(trial) -> bool:
    try:
        r = json.load(open(f"{trial}/result.json", encoding="utf-8"))
    except (OSError, ValueError):
        return False
    e = r.get("exception_info") or {}
    if not e.get("exception_type") or e["exception_type"] == "AgentTimeoutError":
        return False
    return "Docker compose command failed" in (e.get("exception_message") or "") or not r.get("agent_execution")


def since_of(model, variant):  # the --since recorded by make in the -rerun.yaml header
    p = REPO / f"subset/variants/{model}/{variant}-rerun.yaml"
    for line in p.read_text(encoding="utf-8").splitlines() if p.exists() else []:
        if line.startswith("# since: "):
            return line.split(": ", 1)[1].strip()
    return None


def selected(trial, since) -> bool:
    if setup_failed(trial):
        return True
    if not since:
        return False
    try:
        return (json.load(open(f"{trial}/result.json", encoding="utf-8")).get("finished_at") or "")[:19] >= since
    except (OSError, ValueError):
        return False


def make(model, variant, since=None):
    import yaml
    done = [r for r in runs(model, variant) if finished(r)]
    if not done:
        sys.exit(f"{model}/{variant}: no finished run")
    run = done[-1]
    failed = sorted(t for t in glob.glob(f"{run}/*__*") if selected(t, since))
    if not failed:
        print(f"{model}/{variant} {os.path.basename(run)}: nothing to re-run")
        return
    count = collections.Counter(os.path.basename(t).split("__")[0] for t in failed)
    for root in {REPO, WSL_REPO}:
        if not root.exists():
            continue
        src = root / f"subset/variants/{model}/{variant}.yaml"
        cfg = yaml.safe_load(src.read_text(encoding="utf-8"))
        cfg["n_attempts"] = max(count.values())
        cfg["datasets"][0]["task_names"] = sorted(count)
        why = ("setup-failed trials (docker compose failed before\n# the agent ran)" if not since else
               f"trials that failed at setup or finished at/after {since} UTC\n# (infrastructure problem from then on)")
        head = (f"# {model}/{variant}-rerun: re-run of the {len(failed)} {why} of {variant}/{os.path.basename(run)}: "
                f"{', '.join(sorted(count))}.\n" + (f"# since: {since}\n" if since else "") +
                f"# Same config as {variant}.yaml except n_attempts and the task list. Merge afterwards with\n"
                f"#   python3 subset/tools/rerun_failed.py merge {model}/{variant} --apply\n")
        (root / f"subset/variants/{model}/{variant}-rerun.yaml").write_text(
            head + yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        q = root / f"subset/queue/{model}.txt"
        if q.exists():
            lines = q.read_text(encoding="utf-8").splitlines()
            if f"{variant}-rerun" not in lines:
                i = next((k for k, l in enumerate(lines) if l and not l.startswith("#")), len(lines))
                lines.insert(i, f"{variant}-rerun")
                tmp = q.with_suffix(".tmp")
                tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
                os.replace(tmp, q)
    print(f"{model}/{variant}: {len(failed)} trial(s) to re-run {[os.path.basename(t) for t in failed]}"
          f" -> {variant}-rerun.yaml, queued first")


def merge(model, variant, apply):
    orig = [r for r in runs(model, variant) if finished(r)][-1]
    rr = [r for r in runs(model, f"{variant}-rerun") if finished(r)]
    if not rr:
        sys.exit(f"{model}/{variant}-rerun: no finished re-run yet; nothing done")
    rerun = Path(rr[-1])
    if (rerun / "MERGED_INTO.md").exists():
        sys.exit(f"{rerun} was already merged")
    orig = Path(orig)
    since = since_of(model, variant)
    failed = sorted(t for t in orig.glob("*__*") if selected(t, since))
    pool = collections.defaultdict(list)
    for t in sorted(rerun.glob("*__*")):
        if not setup_failed(t):
            pool[t.name.split("__")[0]].append(t)
    swaps = []
    for old in failed:
        task = old.name.split("__")[0]
        if pool[task]:
            swaps.append((old, pool[task].pop(0)))
    print(f"original {orig}\nre-run   {rerun}")
    for old, new in swaps:
        r = json.load(open(new / "result.json", encoding="utf-8"))
        print(f"  replace {old.name} -> {new.name}  reward {((r.get('verifier_result') or {}).get('rewards') or {}).get('reward')}")
    for old in failed:
        if old not in [o for o, _ in swaps]:
            print(f"  KEEP    {old.name} (its re-run failed again or is missing)")
    if not apply:
        print("(dry run: add --apply)")
        return
    replaced = JOBS / model / "aborted" / f"{variant}__{orig.name}__replaced"
    replaced.mkdir(parents=True, exist_ok=True)
    for old, new in swaps:
        shutil.move(str(old), str(replaced / old.name))
        shutil.move(str(new), str(orig / new.name))
    why = ("never started: `docker compose` failed while setting up the task container" if not since else
           f"failed at setup or finished at/after {since} UTC, when the model server's network link became unstable")
    prev = (orig / "MERGED.md").read_text(encoding="utf-8") + "\n" if (orig / "MERGED.md").exists() else ""
    (orig / "MERGED.md").write_text(
        prev + "# Merged re-run\n\n"
        f"{len(swaps)} trial(s) of this run {why}. "
        f"They were re-run with an identical config (`subset/variants/{model}/{variant}-rerun.yaml`, job "
        f"`{variant}-rerun/{rerun.name}`) and the new trials moved here. The failed originals are in "
        f"`jobs/{model}/aborted/{replaced.name}/`.\n\nThis run's own job-level `result.json` stats predate the merge; "
        "analyse per-trial results.\n\n" + "\n".join(f"- {o.name} -> {n.name}" for o, n in swaps) + "\n",
        encoding="utf-8")
    (rerun / "MERGED_INTO.md").write_text(f"Trials moved into `{variant}/{orig.name}` (see MERGED.md there).\n",
                                          encoding="utf-8")
    print(f"applied: {len(swaps)} swapped; originals in {replaced}")


if __name__ == "__main__":
    cmd, mv = sys.argv[1], sys.argv[2]
    model, variant = mv.split("/", 1)
    since = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else None
    make(model, variant, since) if cmd == "make" else merge(model, variant, "--apply" in sys.argv)
