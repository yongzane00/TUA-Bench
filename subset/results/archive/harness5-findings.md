# H5 "Snapshot verifier": findings (both models)

Runs: qwen3.8 `harness5-attempt5/2026-10-06__17-30-32`, Qwen3.6 `harness5-attempt5/2026-10-06__17-30-29`,
each vs its H0 (40 tasks × 5 attempts). The verifier is the same model as the agent, max 2 checks, run
with the URL-path fix (the first runs with the path-finder bug were stopped and discarded).

## Score (harbor Mean)

| Model | H0 | H5 | H5 − H0 (95% CI) | Reading |
|---|---|---|---|---|
| qwen3.8 | 0.445 | 0.456 | +0.011 (−0.030 to +0.053), P(≤0) 0.28 | inside noise |
| Qwen3.6 | 0.197 | 0.192 | −0.005 (−0.061 to +0.051), P(≤0) 0.56 | no difference |

Leak-adjusted, qwen3.8 H5 is 0.406 vs 0.365 for H0. Cost per trial: qwen3.8 $0.0110 → $0.0138,
Qwen3.6 $0.0937 → $0.0955 (prefix-caching proxy, verifier calls included).

## What the verifier did

| | qwen3.8 | Qwen3.6 |
|---|---|---|
| Never said done (timeouts, verifier never ran) | 57 | 61 |
| PASS at first claim | 103 → 68 solved, **35 wrong let through** | 85 → 20 solved, **65 wrong let through** |
| FAIL then PASS | 18 → 14 solved | 16 → 3 solved |
| FAIL twice, graded anyway | 16 → 2 solved | 36 → 5 solved |
| FAIL, then timed out | 6 | 2 |
| Share of first claims that got a FAIL | 28% | 39% |
| Tokens per check | ~1.0k in / 0.7k out | ~2.6k in / 1.3k out |
| Verifier latency per check | 41 s | 6 s |
| Failed checks (snapshot or call) | 0 | 0 |

Against H0 on the same tasks (these groups are selected by H5's outcome, so this is suggestive only):

| H5 group | qwen3.8: H5 vs H0 same tasks | Qwen3.6: H5 vs H0 same tasks |
|---|---|---|
| PASS first | 0.675 vs 0.678 | 0.290 vs 0.260 |
| FAIL then PASS | 0.778 vs 0.611 | 0.216 vs 0.122 |
| FAIL twice | 0.313 vs 0.199 | 0.242 vs 0.241 |
| never claimed done | 0.000 vs 0.063 | 0.027 vs 0.096 |

## Reading

1. **Its objections are right.** Work it failed twice was almost never accepted by the grader (2/16, 5/36).
2. **It misses about half of the wrong work.** Estimate: ~52% caught on qwen3.8, ~43% on Qwen3.6. The prompt
   tells it to PASS when the evidence is not enough to tell, and it sees only the before/after diff, so it can
   see that a file changed but often not whether its content is right.
3. **Its value depends on the agent fixing the problem.** qwen3.8 fixed 14 of 18 flagged trials, but
   Qwen3.6 fixed only 3 of 16.
4. **The overhead costs time on qwen3.8.**
   - Agent time per trial rose from 13.4 to 17.6 min (median). Non-model time went from 1.7 to 3.8 min
     (snapshots plus 41 s verifier calls with `reasoning_effort: xhigh`).
   - Timeouts went from 64 to 70, and qwen3.8's main failure is already timeouts, which H5 cannot address.
5. **Per-task moves look like noise.** Qwen3.6 043 dropped 5 → 2 solved, but the verifier passed all five
   attempts, so the model simply did worse on that task this run.

## Bottom line

The before/after verifier is precise but low-recall. It helps only when the agent can act on its objection,
and it adds time a timeout-bound model cannot spare. Net effect: within noise on both models.

## Next experiments

- Stricter prompt: PASS only when the evidence shows each requirement is met.
- Verifier at `reasoning_effort: low` on qwen3.8, to cut the 41 s per check.
- A stronger verifier model on the same agent. This tests whether verifier strength, not the idea, is the
  limit, and it fits the project brief's expensive-model comparison.
- Let the verifier run a few read-only checks (open the file, query the browser) instead of judging from
  the diff alone.
