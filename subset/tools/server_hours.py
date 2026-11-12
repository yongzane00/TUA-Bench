#!/usr/bin/env python3
"""Self-hosted cost of finished runs on the shared model server: the share of the server's time each run used, from
the vllmtop history (plan p9: report GPU occupancy hours for a self-hosted model, not token-equivalent dollars).

    python3 server_hours.py <run dir> [<run dir> ...] [--endpoint rpt-isp-dgx]

The server serves other users at the same time, so a run is charged a share of the server's time:
  window        first trial start to last trial end, wall hours
  busy          hours in the window with at least one request running on the server (`running` >= 1)
  out share     the run's output tokens / the server's output tokens in the window (vllmtop counters; a counter
                that drops, i.e. a server restart, is counted from its new value)
  in share      the same for prompt tokens; the server counts every prompt token, cached prefixes included, as the
                run does (Harbor's n_input_tokens; the qwen3.8 server reports no cached tokens)
  server-hours  busy hours x out share: the server time attributed to the run (decoding dominates the time of long
                agent replies); GPU-hours = server-hours x the server's GPU count, cost = GPU-hours x price per GPU-hour
  per solved    server-hours / trials with reward 1
  coverage      share of the window with `running` samples at most 10 s apart (vllmtop was on and the server answered)
"""
import glob
import json
import os
import sqlite3
import sys
from datetime import datetime

DB = os.path.expanduser("~/.local/share/vllmtop/usage.db")
GAP_MS = 10_000


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def run_stats(run_dir):
    t0, t1, out_tok, in_tok, solved, n = None, None, 0, 0, 0, 0
    for p in glob.glob(f"{run_dir}/*__*/result.json"):
        r = json.load(open(p))
        if not r.get("started_at") or not r.get("finished_at"):
            continue
        n += 1
        a, b = ts(r["started_at"]), ts(r["finished_at"])
        t0, t1 = min(t0 or a, a), max(t1 or b, b)
        ar = r.get("agent_result") or {}
        out_tok += ar.get("n_output_tokens") or 0
        in_tok += ar.get("n_input_tokens") or 0
        solved += (((r.get("verifier_result") or {}).get("rewards") or {}).get("reward") or 0) == 1
    return dict(t0=t0, t1=t1, out=out_tok, inp=in_tok, solved=solved, n=n)


def counter_delta(db, endpoint, metric, a_ms, b_ms):
    """Increase of a cumulative counter over [a, b], from the last sample before a to the first after b."""
    lo = db.execute("select max(ts_ms) from samples where endpoint=? and metric=? and ts_ms<=?",
                    (endpoint, metric, a_ms)).fetchone()[0] or a_ms
    hi = db.execute("select min(ts_ms) from samples where endpoint=? and metric=? and ts_ms>=?",
                    (endpoint, metric, b_ms)).fetchone()[0] or b_ms
    vals = [v for (v,) in db.execute("select value from samples where endpoint=? and metric=? and ts_ms between ? "
                                     "and ? order by ts_ms", (endpoint, metric, lo, hi))]
    return sum(b - a if b >= a else b for a, b in zip(vals, vals[1:]))


def busy_hours(db, endpoint, a_ms, b_ms):
    rows = db.execute("select ts_ms, value from samples where endpoint=? and metric='running' and ts_ms between ? "
                      "and ? order by ts_ms", (endpoint, a_ms, b_ms)).fetchall()
    busy = covered = 0
    for (t, v), (t2, _) in zip(rows, rows[1:]):
        if t2 - t <= GAP_MS:
            covered += t2 - t
            busy += (t2 - t) if v >= 1 else 0
    return busy / 3.6e6, covered / max(1, b_ms - a_ms)


def main():
    args = sys.argv[1:]
    endpoint = args[args.index("--endpoint") + 1] if "--endpoint" in args else "rpt-isp-dgx"
    runs = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--endpoint")]
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    print("| Run | Trials | Solved | Window (h) | Coverage | Busy (h) | Out share | In share | Server-hours | "
          "Server-hours per solved |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for run in runs:
        s = run_stats(run)
        name = "/".join(os.path.normpath(run).split(os.sep)[-2:])
        if not s["n"]:
            print(f"| {name} | 0 | | | | | | | | |")
            continue
        a, b = int(s["t0"] * 1000), int(s["t1"] * 1000)
        g = counter_delta(db, endpoint, "generation_tokens_total", a, b)
        p = counter_delta(db, endpoint, "prompt_tokens_total", a, b)
        busy, cov = busy_hours(db, endpoint, a, b)
        out_share = s["out"] / g if g else None
        in_share = s["inp"] / p if p else None
        sh = busy * out_share if out_share is not None else None
        f = lambda x, fmt: fmt.format(x) if x is not None else "-"
        print(f"| {name} | {s['n']} | {s['solved']} of {s['n']} | {(b - a) / 3.6e6:.1f} | {cov:.2f} | {busy:.1f} | "
              f"{f(out_share, '{:.2f}')} | {f(in_share, '{:.2f}')} | {f(sh, '{:.1f}')} | "
              f"{f(sh / s['solved'] if sh is not None and s['solved'] else None, '{:.3f}')} |")


if __name__ == "__main__":
    main()
