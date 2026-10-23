# Qwen3.6-35B-A3B: H3 "Listen" vs H0 — findings (provisional: H3 bug)

Runs: `qwen36-35b-a3b/harness0-attempt5/2026-10-02__21-45-56` vs `qwen36-35b-a3b/harness3-attempt5/2026-10-05__09-51-41`.

| Per trial (median unless noted) | H0 | H3 |
|---|---|---|
| Score (harbor Mean) | 0.197 (0.107–0.301) | 0.195 (0.100–0.302) |
| Paired difference | | −0.002 (−0.065 to +0.059), P(≤0) = 0.54 |
| Reward = 1 | 15.5% | 14.0% |
| pass@5 | 35.0% | 22.5% |
| Agent time | 12.2 min | 11.6 min |
| Model time | 2.6 min | 1.8 min |
| Non-model time (waiting + harness overhead) | 8.9 min | 8.4 min |
| Turns | 50 | 36 |
| Output / input tokens | 26.6k / 1,501k | 19.5k / 673k |
| Timeouts (40-min cap) | 54 | 52 |
| Cost / trial (with caching) | $0.0927 | $0.0964 |

## The bug

H3 typed the agent's keys and waited for the prompt in **one** container command, whose command line
contained the keystrokes. `pkill -f <pattern>` / `pgrep -f` match process command lines, so an agent
command such as `pkill -f chromium` killed H3's own waiting command. H3 then told the model the command
"timed out after 180 seconds", dropped the rest of that turn's commands, and switched the hook off for
the trial. Fix: send the keys and wait in separate container commands.

| | Qwen3.6 H3 | qwen3.8 H3 |
|---|---|---|
| Trials hit by the bug | 36 (15 tasks) | 10 (5 tasks) |
| Other hook fallbacks | 9 (`exec bash`, bash `!` history-expansion errors, long GUI commands, 1 install failure) | 1 |

Affected Qwen3.6 tasks: 016, 025, 029, 030, 034, 038, 039, 042, 043, 044, 045, 048, 059, 089, 109.
Affected qwen3.8 tasks: 018, 025, 059, 089, 109.

## Why Listen saved little time on Qwen3.6

On qwen3.8, Listen cut non-model time from 1.7 to 0.3 min. On Qwen3.6 it went from 8.9 to 8.4 min,
because Qwen3.6 often starts commands that never return (a browser or server in the foreground,
interactive programs). Listen waits the full 180 s for each: **343 such 180 s timeouts in 102 trials,
about 5 minutes per trial** (qwen3.8 H3: 72 in 200 trials). Stock terminus-2 returns after the model's
short guessed duration instead. A shorter `max_wait_sec` or an early return when output goes quiet
would recover most of this.

## Reading

No score difference (harbor Mean 0.195 vs 0.197). On the stricter reward = 1 rate, the bug-affected
tasks are unchanged on balance (+1.3 pts vs H0) and the small drop is in the 25 unaffected tasks (−3.2 pts). Fewer turns and tokens, but the same wall time
because of the 180 s waits.
