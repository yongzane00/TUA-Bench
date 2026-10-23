# qwen3.8-flash-next: H4 observation window (`none` summary effort) vs H0 — findings

Runs: `qwen38-flash-next/harness0-attempt5/2026-09-23__14-45-40` vs `qwen38-flash-next/harness4-none-attempt5/2026-10-05__10-16-38`
(H4: last 3 terminal outputs verbatim, older ones replaced by ≤8-bullet summaries from the same model with thinking off; 3 concurrent trials).

| Per trial (median unless noted) | H0 | H4 |
|---|---|---|
| Score (harbor Mean) | 0.445 (0.310–0.576) | 0.446 (0.316–0.580) |
| Paired difference | | +0.001 (−0.051 to +0.050), P(≤0) = 0.47 |
| Leak-adjusted | 0.355 | 0.366 |
| Reward = 1 / pass@5 / solved in all 5 | 42.0% / 57.5% / 27.5% | 42.0% / 57.5% / 25.0% |
| Agent time | 13.4 min | 13.7 min |
| Model time / non-model time | 11.2 / 1.7 min | 10.4 / 1.9 min |
| Turns | 12 | 14 |
| Main-loop input tokens (all trials) | 32.3M | 25.3M (−22%) |
| Timeouts (40-min cap) | 64 | 63 |
| Cost / trial | $0.0110 | $0.0120 (+9%) |

## The summarizer

- 1,674 calls (8.4 per trial); 1,621 ok, 0 failed, 28 not shorter than the original, 834 outputs too short to summarize.
- 1,502 summaries applied: replaced text shrank from 3.80M to 0.96M characters (−75%).
- Summarizer tokens: 2.44M in, 0.30M out. These cost more than the input they saved, so H4 is 9% more expensive per trial.
  (The caching estimate is also optimistic for H4: rewriting old messages invalidates the prompt cache from that point.)
- The main loop waited on summaries for 5 minutes in total over 200 trials: prefetching hid almost all of the latency.

## Reading

H4 works as built: no failures, large compression, almost no waiting. But it changes neither the score nor
the time. qwen3.8's contexts were already small (median peak prompt about 12K, no summarization in H0), so
dropping old terminal output has little to gain, and the summary calls cost more than they save.

Per task, 5 tasks moved up and 6 down. Three of the four larger moves are H0 outliers (054 and 059 were 0/5 in
H0 but 1–3/5 in every other harness; 099 varies 2–5/5 across runs). The exception is `069-linux-ls-tutorial`:
0/5 under H4 against 2–3/5 in every other harness, the one task where losing old output may have hurt.
Not yet inspected.

H4 is a better fit for Qwen3.6, whose contexts reach hundreds of thousands of tokens.
