#!/usr/bin/env python3
"""Pick the code-repair tasks for the technical check of the plan (p2): 20 dev + 40 held-out, one repo.

    python3 pilot/select_tasks.py <swe-bench-verified dir> > pilot/tasks.md

The rule is fixed here, before any agent runs, so the split cannot follow the results:
  1. Repo django/django (the largest repo in SWE-bench Verified; one environment family).
  2. Difficulty "<15 min fix" or "15 min - 1 hour" (SWE-bench's own labels): small fixes, as the plan asks.
  3. One source file changed by the reference patch (small scope) and at least one FAIL_TO_PASS test.
  4. Fault family = the Django package of that file, two levels deep (for example contrib/auth, db/models);
     shown for reference.
  5. Sort by issue date. Dev = the 20 oldest. Held-out = the 40 newest that change none of the files a dev task
     changes, so the two sets differ in time and in the code they touch, and no ticket can be in both.
     (Excluding whole families left only 18 held-out tasks: Django's fixes cluster in a few packages.)
The first 10 dev tasks are the "10 reproducible tasks" for week 1 (checked with Harbor's oracle agent).
"""
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
rows = []
for d in sorted(root.iterdir()):
    cfg = d / "tests" / "config.json"
    if not cfg.exists():
        continue
    c = json.loads(cfg.read_text())
    if c["repo"] != "django/django" or c["difficulty"] not in ("<15 min fix", "15 min - 1 hour"):
        continue
    files = sorted(set(re.findall(r"^diff --git a/(\S+) ", c["patch"], flags=re.M)))
    f2p = json.loads(c["FAIL_TO_PASS"]) if isinstance(c["FAIL_TO_PASS"], str) else c["FAIL_TO_PASS"]
    if len(files) != 1 or not files[0].startswith("django/") or not f2p:
        continue
    parts = files[0].split("/")[1:-1]
    family = "/".join(parts[:2]) if parts else "(top)"
    rows.append(dict(task=d.name, date=c["created_at"][:10], diff=c["difficulty"], file=files[0], family=family,
                     f2p=len(f2p)))

rows.sort(key=lambda r: (r["date"], r["task"]))
dev = rows[:20]
dev_fams = {r["family"] for r in dev}
dev_files = {r["file"] for r in dev}
held = [r for r in rows[20:] if r["file"] not in dev_files][-40:]


def table(rs, first_n_marked=0):
    out = ["| # | Task | Issue date | Difficulty | File changed by the reference patch | Family | Tests that must turn to pass |",
           "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rs, 1):
        mark = " (week 1)" if i <= first_n_marked else ""
        out.append(f"| {i} | `{r['task']}`{mark} | {r['date']} | {r['diff']} | `{r['file']}` | {r['family']} | {r['f2p']} |")
    return "\n".join(out)


print(f"Candidates after rules 1-3: {len(rows)} Django tasks. Dev families: {len(dev_fams)}; "
      f"held-out families: {len({r['family'] for r in held})}; families shared: "
      f"{len(dev_fams & {r['family'] for r in held})}.\n")
print(f"Dev, 20 tasks ({dev[0]['date']} to {dev[-1]['date']}); the first 10 are the week-1 reproducible set:\n")
print(table(dev, 10))
print(f"\nHeld-out, {len(held)} tasks ({held[0]['date']} to {held[-1]['date']}); not used for any tuning:\n")
print(table(held))
print("\n```text")
print("# dev")
print("\n".join(r["task"] for r in dev))
print("# held-out")
print("\n".join(r["task"] for r in held))
print("```")
