#!/usr/bin/env python3
"""Turn finished Harbor trials into the event log the plan asks for (p11), one JSON object per line.

    python3 event_log.py <trial dir | job dir> [-o events.jsonl]      (default: print to stdout)

Fields on every event: run_id (job id), trial, task_id, config_version (agent version string), model, provider,
event, start, end (ISO UTC), elapsed_s (real seconds since the agent started, at the event's end), budget_elapsed_s
and budget_left_s (on the budget's own clock: the monotonic clock runs slow inside WSL, so real seconds are scaled by
the trial's harness/real ratio), phase ("work", "wrap-up" after the wrap-up notice, "late" past the budget), plus
event-specific fields.

Events per trial:
  agent_start   the agent phase starts (Harbor's agent_execution start; the budget clock starts here)
  model_call    one model reply: tokens in/out, cost; start = previous step end, end = start + request time
  commands      what the agent typed after that reply (keystrokes, requested waits); ends at the step's end
  agent_end     exit_reason (budget stop, Harbor timeout, completion), replies cut, waits cut, artifact path,
                when the work stopped and how long the stop's cleanup took, and the local-process check
                (interrupt_at_stop: foreground process left running or not)
  verify        grading phase with the reward (the acceptance result)
The trajectory records one timestamp per step, at the end of the turn; reply durations come from
api_request_times_msec in the same order, so a turn splits into the reply and the commands that followed. Replies
that failed to parse are folded into the next turn by Terminus-2 and so are not separate events.
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timedelta, timezone


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso(d):
    return d.isoformat().replace("+00:00", "Z")


def trial_events(tdir):
    r = json.load(open(os.path.join(tdir, "result.json"), encoding="utf-8"))
    ae = r.get("agent_execution") or {}
    if not ae.get("started_at"):
        return []
    md = (r.get("agent_result") or {}).get("metadata") or {}
    bud = md.get("budget") or {}
    B = bud.get("time_budget_sec")
    wrap = bud.get("wrapup_at_sec")
    t0 = ts(ae["started_at"])
    # The budget runs on the agent's clock (monotonic by default, slow inside WSL); timestamps are real time.
    # Scale real seconds to budget seconds with this trial's own ratio, so budget_left_s matches the stop.
    ratio = 1.0
    if bud.get("clock", "monotonic") != "wall" and bud.get("elapsed_sec") and ae.get("finished_at"):
        wall = (ts(ae["finished_at"]) - t0).total_seconds()
        if wall > 0:
            ratio = min(1.0, bud["elapsed_sec"] / wall)
    base = dict(run_id=(r.get("config") or {}).get("job_id"), trial=r.get("trial_name"),
                task_id=(r.get("task_name") or "").split("/")[-1],
                config_version=(r.get("agent_info") or {}).get("version"),
                model=((r.get("agent_info") or {}).get("model_info") or {}).get("name"),
                provider=((r.get("agent_info") or {}).get("model_info") or {}).get("provider"))

    def ev(kind, start, end, **kw):
        el = (end - t0).total_seconds()
        bel = el * ratio  # on the budget's clock
        phase = "late" if B and bel > B else ("wrap-up" if wrap is not None and bel > wrap else "work")
        return dict(base, event=kind, start=iso(start), end=iso(end), elapsed_s=round(el, 1),
                    budget_elapsed_s=round(bel, 1), budget_left_s=None if not B else round(B - bel, 1),
                    phase=phase, **kw)

    out = [ev("agent_start", t0, t0, time_budget_s=B, feedback=bud.get("feedback"),
              hard_deadline=bud.get("hard_deadline"), finalize_reserve_s=bud.get("finalize_reserve_sec"),
              late_effort=bud.get("late_effort"))]
    tp = os.path.join(tdir, "agent", "trajectory.json")
    steps = json.load(open(tp, encoding="utf-8")).get("steps", []) if os.path.exists(tp) else []
    req = md.get("api_request_times_msec") or []
    prev = t0
    k = 0
    for s in steps:
        end = ts(s["timestamp"]) if s.get("timestamp") else None
        if s.get("source") != "agent" or end is None:
            if end is not None:
                prev = max(prev, end) if s.get("source") == "user" and k == 0 else prev
            continue
        dur = req[k] / 1000 if k < len(req) else None
        k += 1
        reply_end = min(end, prev + timedelta(seconds=dur)) if dur is not None else end
        m = s.get("metrics") or {}
        out.append(ev("model_call", prev, reply_end, request_s=None if dur is None else round(dur, 1),
                      tokens_in=m.get("prompt_tokens"), tokens_out=m.get("completion_tokens"),
                      cost_usd=m.get("cost_usd"), cut_by_deadline=dur is None and bool(bud.get("cut_replies"))))
        calls = s.get("tool_calls") or []
        keys = [((c.get("arguments") or {}).get("keystrokes") or "")[:120] for c in calls
                if c.get("function_name") != "mark_task_complete"]
        waits = sum(float((c.get("arguments") or {}).get("duration") or 0) for c in calls)
        out.append(ev("commands", reply_end, end, n_commands=len(keys), keystrokes=keys,
                      requested_wait_s=round(waits, 1),
                      declared_complete=any(c.get("function_name") == "mark_task_complete" for c in calls)))
        prev = end
    exc = (r.get("exception_info") or {}).get("exception_type")
    reason = ("budget stop" if bud.get("stop") == "time" else "harbor time limit" if exc == "AgentTimeoutError"
              else f"error: {exc}" if exc else "agent finished")
    diff = os.path.join(tdir, "agent", "final.diff")
    if ae.get("finished_at"):
        out.append(ev("agent_end", ts(ae["finished_at"]), ts(ae["finished_at"]), exit_reason=reason,
                      cut_replies=bud.get("cut_replies"), cut_waits=bud.get("cut_waits"),
                      wrapup_at_s=wrap, effort_switched_at_s=bud.get("effort_switched_at_sec"),
                      artifact=diff.replace("\\", "/") if os.path.exists(diff) else None,
                      final_diff=bud.get("final_diff"), stopped_at_s=bud.get("stopped_at_sec"),
                      cleanup_s=bud.get("cleanup_sec"), local_stop=bud.get("stop_interrupt")))
    v = r.get("verifier") or {}
    if v.get("started_at") and v.get("finished_at"):
        rw = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        e = ev("verify", ts(v["started_at"]), ts(v["finished_at"]), reward=rw, accepted=rw == 1)
        e["phase"] = "grading"
        out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    dirs = [a.path] if os.path.exists(os.path.join(a.path, "agent")) else sorted(
        os.path.dirname(p) for p in glob.glob(os.path.join(a.path, "*__*", "result.json")))
    f = open(a.out, "w", encoding="utf-8") if a.out else sys.stdout
    n = 0
    for d in dirs:
        for e in trial_events(d):
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
            n += 1
    if a.out:
        f.close()
        print(f"{n} events from {len(dirs)} trials -> {a.out}")


if __name__ == "__main__":
    main()
