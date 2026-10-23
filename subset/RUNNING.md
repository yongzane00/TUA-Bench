# Running TUA-Bench on this machine (Windows + WSL2 + Docker Desktop)

**Base benchmark (H0):** `jobs/harness0-attempt5/2026-09-23__14-45-40` — results in
[`results/archive/harness0-attempt5.md`](results/archive/harness0-attempt5.md). Earlier runs cited below as
evidence are superseded; their raw job data is only under `~/work/TUA-Bench/jobs/`.

Two rules. Both are required for a run to finish **and** be graded correctly.

| | Rule | If you break it |
|---|---|---|
| 1 | **Run from ext4** — `cd ~/work/TUA-Bench` | The whole job crashes partway with `FileNotFoundError` |
| 2 | **Write job output to `/mnt/c`** — `-o /mnt/c/.../jobs/<name>` | Every `ubuntu:24.04` task finishes ungraded (`RewardFileNotFoundError`) |

```bash
cd ~/work/TUA-Bench
uv run harbor run -c subset/variants/<model>/<variant>.yaml \
  -o /mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/jobs/<variant> \
  --yes
```

**Do not add `--max-retries`.** It is not part of the published protocol — see
[Retries are not in the baseline](#retries-are-not-in-the-baseline).

Rule 2 is a **workaround**, not a fix. See [The real fix](#the-real-fix) — once harbor is
patched, both the working directory and the output can live on ext4.

---

## Rule 1 — run from ext4, never from `/mnt/c`

**Symptom.** A run dies after 1–16 minutes with an `ExceptionGroup` whose sub-exceptions
end in:

```
pathlib.py resolve → realpath:433 → abspath:420
FileNotFoundError: [Errno 2] No such file or directory
```

and the shell afterwards reports `Current directory does not exist`.

**Cause.** `/mnt/c` is a **9p** network filesystem (`mount | grep /mnt/c` → `type 9p`)
that WSL2 uses to reach `C:\`. Under heavy concurrent I/O — four Docker builds, bind
mounts and agent logs at once — it can transiently fail to resolve the working
directory's inode. `abspath:420` is literally `cwd = os.getcwd()`, reached because task
paths in the lockfile are relative (`tasks/003-...`). One failure inside `Trial.create()`
escapes harbor's retry loop (`queue.py:112`) and the `asyncio.TaskGroup` cancels every
other trial.

Ruled out by evidence: not RAM (the only OOM was a single-container
`CONSTRAINT_MEMCG` kill at a different time), not a WSL restart (VM uptime spanned every
crash), not a remount, nothing in `dmesg`.

**Evidence.** Three runs from `/mnt/c` died at 1.5, 2 and 16 minutes. The first run
from `~/work` — `~/work/TUA-Bench/jobs/harness0-attempt5/2026-09-22__17-33-26`, since
superseded — went 17+ hours and 190+ trials with zero occurrences, as did the base
benchmark run.

---

## Rule 2 — job output on `/mnt/c`

**Symptom.** Every task built on `ubuntu:24.04` ends with `RewardFileNotFoundError`. The
trial's `verifier/` directory is completely empty — not even `test-stdout.txt` — and
the verifier phase lasts about 0.35 s. Tasks on `debian:bookworm` grade normally.

**Cause — a UID collision.** Linux permissions are checked on numeric user IDs, not
names. A container shares the host kernel, so UID 1000 inside is UID 1000 outside,
but each image has its own `/etc/passwd` naming those numbers.

- `ubuntu:24.04` ships a stock user **`ubuntu` at UID 1000**. `debian:bookworm` ships none.
- Every task Dockerfile runs `useradd -m agent` with no `-u`, so `useradd` takes the lowest
  free UID: **1000 on debian, 1001 on ubuntu**.
- harbor bind-mounts the host's `<trial>/verifier` directory to `/logs/verifier`. On ext4
  it is created mode `755`, owned by the host user (UID 1000).
- The verifier runs as `agent`. On debian `agent` *is* 1000 — the owner — and can write.
  On ubuntu `agent` is 1001 and cannot.

The verifier's `test.sh > /logs/verifier/test-stdout.txt` redirect fails before the
script starts, so no score is ever computed. `verifier.py:184` does not check the exec
result, so this surfaces as a missing reward file.

**harbor tries to prevent this and fails.** `_reset_dirs_command` (`environments/base.py:189-192`)
builds:

```sh
rm -rf /logs/verifier /tests && mkdir -p /logs/verifier /tests && chmod 777 /logs/verifier
```

`rm -rf` cannot remove a bind-mount point and exits 1 with `Device or resource busy`,
so `&&` short-circuits and the `chmod 777` never runs. Reproduced directly: final mode
`755`.

**Why `/mnt/c` works.** drvfs has no concept of UNIX ownership and reports every file
as `777`, so UID 1001 can write. Verified 2026-09-23: a drvfs directory bind-mounted
into `ubuntu:24.04` shows `777 ubuntu:ubuntu`, and `agent` (UID 1001) wrote to it.

**Only `/logs` lands on drvfs.** The task's working files (`/app`, the spreadsheets, the
`.obj` outputs) live in the container's own filesystem with real permissions, so task
behaviour is not affected by this workaround.

**Scale.** 18 of the 40 tasks in `subset/baseline.yaml` are `ubuntu:24.04`. In
`~/work/TUA-Bench/jobs/harness0-attempt5/2026-09-22__17-33-26` (superseded), 81 of 89 ungraded trials were ubuntu tasks.

### Caveats

- **Stability under load is unverified.** Rule 2 puts 9p back into the write path. The
  crash in Rule 1 was specifically `getcwd()` on the working directory, which is gone —
  but the underlying 9p flakiness could still hit a write. The permission behaviour is
  proven; a full clean run using this setup has not yet been done.
- **Not portable.** The UID mismatch is still there; drvfs just ignores it. On native
  Linux, CI, or anyone else's machine, the 18 ubuntu tasks break again.
- **This bug was always present.** Earlier runs from `/mnt/c` graded fine only because
  drvfs wasn't enforcing permissions. Moving to ext4 exposed it; it did not cause it.

---

## The real fix

Any one of these removes the need for Rule 2:

1. **Patch harbor** (preferred — one line, fixes every task). In
   `../harbor/src/harbor/environments/base.py`, don't chain the `chmod` behind `rm -rf`;
   run it unconditionally, e.g. `rm -rf ... ; mkdir -p ... && chmod 777 ...`. harbor is an
   editable install (`pyproject.toml` → `[tool.uv.sources] harbor = { path = "../harbor" }`),
   so the change takes effect on the next run with no reinstall.
2. **Pin the UID in the task Dockerfiles** — remove the stock `ubuntu` user and
   `useradd -u 1000 agent`. Touches all 18 ubuntu tasks.
3. **Run the verifier as root** — `[verifier] user = "root"` per task. Changes verifier
   semantics.

This path only exists for local environments. `capabilities.mounted=True` is set by
`docker`, `apple_container` and `singularity`; cloud environments default to
`mounted=False` and copy logs out instead of bind-mounting, so they never hit it.

---

## Retries are not in the baseline

`baseline.yaml` pins the protocol for comparability with the published leaderboard, so
`--max-retries` stays at harbor's default of **0**.

- The upstream README's run command has no retry flag.
- The paper (arXiv 2606.28480) never mentions retries, runs 5 independent trials per task,
  and counts every trial in the denominator — timeouts included (its ablation reports
  "4 out of 600" timed out at 2400 s, i.e. 120 tasks × 5).

**Why it isn't a harmless add-on.** harbor retries by exception *type*, not by whether the
agent ran. The default `--retry-exclude` protects `AgentTimeoutError`,
`RewardFileNotFoundError`, `RewardFileEmptyError`, `VerifierTimeoutError` and
`VerifierOutputParseError`, but `RuntimeError` is retried wherever it happens. In
`~/work/TUA-Bench/jobs/harness0-attempt5/2026-09-22__17-33-26` (superseded):

| exception | agent phase | trials | retried by `--max-retries`? |
|---|---|---|---|
| `RuntimeError` | never started | 14 | yes — gives the agent its *first* attempt |
| `RuntimeError` | ran | 1 | yes — gives an agent that already ran a **second** attempt |

The second row inflates Pass@1, which is why it can't be added silently.

**Handling infrastructure failures instead.** Run without retries. Afterwards, identify
trials whose agent never started (`agent_execution.started_at` is null — e.g. an image-build
failure such as the ~6-minute DNS outage on 2026-09-22 20:09–20:15,
`Could not resolve 'archive.ubuntu.com'`). Those are not model outcomes. Report them
separately and, if needed, re-run *only those* — disclosed. That never gives any agent a
second attempt.

---

## Other things that will bite you

- **Line endings.** Clone with WSL's git. Git for Windows sets `core.autocrlf=true` at
  *system* scope (`C:/Program Files/Git/etc/gitconfig`) and rewrites every script to CRLF;
  containers then fail with exit 127 or `/tests/test.sh: cannot execute`.
  `git status` stays clean, so it is invisible. `git config --local core.autocrlf false`.
- **`.env` is gitignored.** A fresh clone has no `OPENAI_API_KEY`, and every trial fails with
  `AuthenticationError`. The endpoint accepts any value: `OPENAI_API_KEY=dummy`.
- **`009-repair-org-chart-layout` needs a real Gemini key for its grader.** Its verifier is an LLM
  judge — by default `TUA_BENCH_LLM_PROVIDER=gemini`, `TUA_BENCH_MODEL=gemini-3-flash-preview`
  (`tasks/009-.../task.toml`, `[verifier.env]`). Put `GEMINI_API_KEY=...` in `.env`. Without it, all 5
  attempts score 0 with `RuntimeError: Missing Gemini API key`, and because pytest reports that as an
  ordinary `FAILED` it looks like a model failure. Keep the default provider and model to match the
  published setup — a different judge measures something different. It's the only task in the subset
  whose grader needs a key; it cost the base benchmark 5 unjudged trials.
- **Pre-pull uncached base images.** The first pull of a large image under load has hit
  Docker credential-helper failures. `openfoam/openfoam11-paraview510` is the big one.
- **Don't copy `.venv` between locations.** It contains absolute paths, including
  `harbor.pth`. Exclude it and run `uv sync`.
