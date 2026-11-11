#!/usr/bin/env python3
"""Turn a Python repo's past bug fixes into Harbor tasks (plan p2: "收集 60 个可运行的历史修复任务").

    python3 mine_fixes.py <git clone> <owner/name> <out dir> [--since 2024-01-01] [--max 30] [--python 3.12]
                          [--install '-e .[tests]'] [--skip-labels ...] [--dry-run]

A team with few new tickets still has its history: every past fix that came with a test is a task. This applies the
SWE-bench recipe to any Python repo on GitHub (for a company repo, swap the issue lookup for the ticket system).

Candidate: a non-merge commit that changes at least one source .py file and adds or modifies at least one test file
(no deleted or renamed test files), and whose message points to a GitHub issue: "Fixes #12" directly, or "(#34)" for
a squash-merged pull request whose description says which issue it fixes. The task text is that issue's title and
body, i.e. what a user reported, never the fix; issues whose text already contains a diff, or labelled as a feature,
enhancement, RFC, refactor or breaking change (--skip-labels) or titled "Feature request", "RFC" or "Proposal",
are skipped.

Task layout (Harbor):
  environment/Dockerfile  python:<version>-slim; the repo at the fix's parent commit, re-initialised as a fresh git
                          repo with one commit, so `git log` cannot show the future fix; `pip install <install> pytest`
  instruction.md          the issue title and body
  tests/test.sh           resets the test files the fix touched, applies the fix's test changes (tests/test.patch),
                          runs those test files with pytest; reward 1 when all pass
  solution/solve.sh       applies the fix's source changes (the oracle)
Each task must then pass the reproducibility check (pilot/check_tasks.py): the oracle scores 1 and no change scores 0.
<out dir>/tasks.json lists every task with its commit, parent, issue and files.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

FIX_REF = re.compile(r"\b(?:fix(?:e[sd])?|close[sd]?|resolve[sd]?)\b\s*:?\s*#(\d+)", re.I)
PR_REF = re.compile(r"\(#(\d+)\)")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def is_test(path):
    parts = path.split("/")
    name = parts[-1]
    return (any(p in ("test", "tests", "testing") for p in parts[:-1]) or name.startswith("test_")
            or name.endswith("_test.py") or name == "conftest.py")


def is_source(path):
    return path.endswith(".py") and not is_test(path) and not path.startswith(("docs/", "doc/", "examples/"))


class GitHub:
    """Issue lookups through the public REST API (GITHUB_TOKEN raises the limit from 60 to 5000 requests an hour)."""

    def __init__(self, repo, cache_file=None):
        self.repo, self.cache_file = repo, cache_file
        self.cache = {}
        if cache_file and os.path.exists(cache_file):
            self.cache = {int(k): v for k, v in json.load(open(cache_file)).items()}
        self.token = os.environ.get("GITHUB_TOKEN")

    def save(self):
        if self.cache_file:
            Path(self.cache_file).parent.mkdir(parents=True, exist_ok=True)
            json.dump(self.cache, open(self.cache_file, "w"))

    def item(self, n):
        if n not in self.cache:
            req = urllib.request.Request(f"https://api.github.com/repos/{self.repo}/issues/{n}",
                                         headers={"Accept": "application/vnd.github+json",
                                                  "User-Agent": "harbor-task-miner"})
            if self.token:
                req.add_header("Authorization", f"Bearer {self.token}")
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    self.cache[n] = json.load(r)
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):
                    self.save()
                    reset = e.headers.get("X-RateLimit-Reset")
                    sys.exit("GitHub API rate limit reached (lookups so far are cached); set GITHUB_TOKEN or rerun "
                             f"after {reset and time.strftime('%H:%M', time.localtime(int(reset)))}")
                self.cache[n] = None
        return self.cache[n]

    def issue_for(self, message):
        """The issue a commit fixes: a direct "Fixes #N", or the issue named by the squash-merged PR "(#N)"."""
        direct = [int(n) for n in FIX_REF.findall(message)]
        prs = [int(n) for n in PR_REF.findall(message)]
        for n in direct + prs:
            it = self.item(n)
            if not it:
                continue
            if "pull_request" not in it:
                return it
            for m in FIX_REF.findall(it.get("body") or ""):
                linked = self.item(int(m))
                if linked and "pull_request" not in linked:
                    return linked
        return None


def candidates(repo, since):
    out = git(repo, "log", "--no-merges", f"--since={since}", "--format=%H%x00%P%x00%cs%x00%B%x1e")
    for rec in out.split("\x1e"):
        if not rec.strip():
            continue
        sha, parents, date, msg = rec.strip("\n").split("\x00", 3)
        if len(parents.split()) != 1:
            continue
        files = [ln.split("\t") for ln in git(repo, "diff-tree", "--no-commit-id", "--name-status", "-r", sha).splitlines()]
        tests = [(st, f[0]) for st, *f in files if f and is_test(f[0])]
        src = [f[0] for st, *f in files if f and is_source(f[0])]
        if not src or not tests or any(st[0] not in "AM" for st, _ in tests):
            continue
        yield dict(commit=sha, parent=parents.strip(), date=date, message=msg.strip(), src=src,
                   tests_modified=[p for st, p in tests if st == "M"], tests_added=[p for st, p in tests if st == "A"])


DOCKERFILE = """FROM python:{python}-slim
RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*
RUN git config --global user.email task@local && git config --global user.name task
# The repo at the fix's parent commit, as a fresh repo with one commit: the future fix is not in its history.
RUN git clone -q --filter=blob:none https://github.com/{repo}.git /src && git -C /src checkout -q {parent} \\
 && rm -rf /src/.git && mv /src /testbed && cd /testbed && git init -q && git add -A && git commit -qm base
WORKDIR /testbed
RUN pip install --no-cache-dir {install} pytest
RUN mkdir -p /logs
"""

TEST_SH = """#!/bin/bash
# Grade the state the agent left: reset the test files the reference fix touched, apply its test changes, run them.
cd /testbed
mkdir -p /logs/verifier
{reset}
if ! git apply --whitespace=nowarn /tests/test.patch; then
  echo "test patch does not apply" | tee /logs/verifier/pytest.log
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi
python -m pytest -p no:cacheprovider -q {files} 2>&1 | tee /logs/verifier/pytest.log
if [ "${{PIPESTATUS[0]}}" -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
"""

SOLVE_SH = """#!/bin/bash
set -euo pipefail
cat > /tmp/fix.patch <<'__FIX_PATCH__'
{patch}__FIX_PATCH__
cd /testbed
git apply --whitespace=nowarn /tmp/fix.patch
"""

TASK_TOML = """schema_version = "1.1"
artifacts = []

[task]
name = "mined/{tid}"
description = "{repo} issue #{issue}, fixed by {commit}"
authors = []
keywords = []

[metadata]
category = "debugging"
tags = ["debugging", "mined-history"]

[verifier]
timeout_sec = 1200.0

[agent]
timeout_sec = 3000.0

[environment]
build_timeout_sec = 1800.0
os = "linux"
cpus = 1
memory_mb = 4096
storage_mb = 10240
gpus = 0
allow_internet = true
"""


def write_task(out, repo, c, issue, a):
    owner_name = repo.replace("/", "__")
    tid = f"{owner_name}-{issue['number']}"
    d = Path(out) / tid
    for sub in ("environment", "tests", "solution"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    q = lambda paths: " ".join(f"'{p}'" for p in paths)
    tests = c["tests_modified"] + c["tests_added"]
    src_patch = git(a.repo_dir, "diff", c["parent"], c["commit"], "--", *c["src"])
    test_patch = git(a.repo_dir, "diff", c["parent"], c["commit"], "--", *tests)
    (d / "instruction.md").write_text(f"{issue['title'].strip()}\n\n{(issue.get('body') or '').strip()}\n")
    (d / "environment" / "Dockerfile").write_text(
        DOCKERFILE.format(python=a.python, repo=repo, parent=c["parent"], install=a.install))
    (d / "tests" / "test.patch").write_text(test_patch)
    (d / "tests" / "test.sh").write_text(
        TEST_SH.format(reset="\n".join(filter(None, [
            f"git checkout HEAD -- {q(c['tests_modified'])}" if c["tests_modified"] else "",
            f"rm -f {q(c['tests_added'])}" if c["tests_added"] else ""])), files=q(tests)))
    (d / "solution" / "solve.sh").write_text(SOLVE_SH.format(patch=src_patch))
    (d / "task.toml").write_text(TASK_TOML.format(tid=tid, repo=repo, issue=issue["number"], commit=c["commit"][:12]))
    for f in (d / "tests" / "test.sh", d / "solution" / "solve.sh"):
        f.chmod(0o755)
    return tid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_dir")
    ap.add_argument("repo", help="owner/name on GitHub")
    ap.add_argument("out")
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--max", type=int, default=30)
    ap.add_argument("--python", default="3.12")
    ap.add_argument("--install", default="-e .", help="pip arguments, e.g. '-e .[tests]' or '-e . simplejson'")
    ap.add_argument("--skip-labels", default="feature,enhancement,rfc,refactor,breaking,backwards",
                    help="skip issues with a label containing any of these words (comma-separated)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cache", help="issue lookup cache (default ~/.cache/mine_fixes/<owner>__<name>.json)")
    a = ap.parse_args()
    gh, rows, seen = GitHub(a.repo, a.cache or os.path.expanduser(f"~/.cache/mine_fixes/{a.repo.replace('/', '__')}.json")), [], set()
    for c in candidates(a.repo_dir, a.since):
        issue = gh.issue_for(c["message"])
        if not issue or issue["number"] in seen:
            continue
        if "diff --git" in (issue.get("body") or ""):
            continue  # the report already contains a patch
        labels = [lb["name"] for lb in issue.get("labels") or []]
        if any(w and w in lb.lower() for lb in labels for w in a.skip_labels.lower().split(",")):
            continue  # a feature or a redesign, not a bug report
        if issue["title"].lower().lstrip("[(").startswith(("feature request", "rfc", "proposal")):
            continue  # the same, said in the title instead of a label
        seen.add(issue["number"])
        row = dict(issue=issue["number"], issue_title=issue["title"], labels=labels, commit=c["commit"], parent=c["parent"],
                   date=c["date"], src=c["src"], tests=c["tests_modified"] + c["tests_added"])
        if not a.dry_run:
            row["task"] = write_task(a.out, a.repo, c, issue, a)
        rows.append(row)
        print(f"{c['date']} {c['commit'][:10]} issue #{issue['number']}: {issue['title'][:70]}  "
              f"({len(c['src'])} source, {len(row['tests'])} test files; labels: {', '.join(labels) or '-'})")
        if len(rows) >= a.max:
            break
    gh.save()
    if not a.dry_run:
        Path(a.out).mkdir(parents=True, exist_ok=True)
        (Path(a.out) / "tasks.json").write_text(json.dumps(rows, indent=1))
    print(f"{len(rows)} tasks{' (dry run)' if a.dry_run else ' written to ' + a.out}")


if __name__ == "__main__":
    main()
