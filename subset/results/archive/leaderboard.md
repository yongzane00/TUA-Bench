# Harness leaderboard — 40-task TUA-Bench subset × 5 attempts

Updated 2026-10-21. One row per finished run, ranked by score. Plot: `harness-compare-accuracy-cost.svg` (data in `harness-compare-accuracy-cost.json`).

**Score = harbor's Mean**: the reward averaged over every trial, partial credit included, a missing reward counted as 0 (the "Mean" harbor prints at the end of a run).

| Model | Harness | Score (95% CI) | Leak-adjusted | Stratified S | Reward = 1 | pass@5 | Solved in all 5 | Attempts 1–5 | Cost / trial |
|---|---|---|---|---|---|---|---|---|---|
| qwen3.8-flash-next | H7 time budget (3600 s clock) | **0.571** (0.441–0.696) | 0.506 | 0.572 | 52.0% | 72.5% | 30.0% | .573 · .577 · .590 · .635 · .481 | $0.0147 |
| qwen3.8-flash-next | H7 time budget (2400 s clock) | 0.539 (0.414–0.664) | 0.499 | 0.539 | 49.5% | 70.0% | 27.5% | .448 · .576 · .535 · .535 · .598 | $0.0116 |
| qwen3.8-flash-next | H0 + hidden 12000 s stop † | 0.534 (0.407–0.658) | 0.469 | 0.535 | 47.5% | 67.5% | 32.5% | .448 · .555 · .639 · .531 · .498 | $0.0337 |
| qwen3.8-flash-next | H2 reasoning kept | 0.478 (0.352–0.605) | 0.353 | 0.492 | 44.5% | 67.5% | 25.0% | .456 · .494 · .514 · .431 · .494 | $0.0161 |
| qwen3.8-flash-next | H6 turn budget (40 turns) | 0.476 (0.344–0.610) | 0.426 | 0.488 | 45.5% | 62.5% | 27.5% | .443 · .494 · .531 · .444 · .469 | $0.0120 |
| qwen3.8-flash-next | H7 time budget (1800 s clock) | 0.467 (0.340–0.594) | 0.447 | 0.472 | 43.5% | 65.0% | 22.5% | .502 · .344 · .398 · .535 · .556 | $0.0100 |
| qwen3.8-flash-next | H0 + hidden 1800 s stop † | 0.463 (0.330–0.599) | 0.393 | 0.474 | 44.0% | 60.0% | 25.0% | .431 · .443 · .519 · .430 · .494 | $0.0096 |
| qwen3.8-flash-next | H3 Listen ⚠ | 0.462 (0.331–0.597) | 0.357 | 0.466 | 43.5% | 60.0% | 27.5% | .543 · .448 · .469 · .444 · .406 | $0.0127 |
| qwen3.8-flash-next | H0 + hidden 2400 s stop (H0 re-run) † | 0.459 (0.321–0.595) | 0.399 | 0.466 | 43.5% | 55.0% | 27.5% | .443 · .393 · .456 · .519 · .481 | $0.0117 |
| qwen3.8-flash-next | H5 snapshot verifier | 0.456 (0.325–0.585) | 0.406 | 0.464 | 43.0% | 62.5% | 20.0% | .444 · .506 · .481 · .406 · .443 | $0.0138 |
| qwen3.8-flash-next | H4 observation window (`none`) | 0.446 (0.316–0.580) | 0.366 | 0.453 | 42.0% | 57.5% | 25.0% | .456 · .469 · .418 · .431 · .456 | $0.0120 |
| qwen3.8-flash-next | H0 stock terminus-2 | 0.445 (0.310–0.576) | 0.355 | 0.452 | 42.0% | 57.5% | 27.5% | .487 · .481 · .481 · .381 · .393 | $0.0110 |
| qwen3.8-flash-next | H7 time budget (1200 s clock) | 0.443 (0.307–0.583) | 0.403 | 0.443 | 40.5% | 55.0% | 32.5% | .435 · .523 · .385 · .435 · .435 | $0.0077 |
| qwen3.8-flash-next | H0 + hidden 3600 s stop † | 0.434 (0.304–0.565) | 0.394 | 0.441 | 41.0% | 60.0% | 20.0% | .393 · .456 · .419 · .419 · .481 | $0.0163 |
| qwen3.8-flash-next | H1 instruction re-check | 0.416 (0.285–0.544) | 0.336 | 0.422 | 39.0% | 57.5% | 17.5% | .356 · .444 · .356 · .444 · .481 | $0.0120 |
| qwen3.8-flash-next | H8 cost budget ($0.030) | 0.401 (0.275–0.532) | 0.376 | 0.393 | 35.5% | 57.5% | 20.0% | .414 · .397 · .405 · .431 · .356 | $0.0076 |
| qwen3.8-flash-next | H0 + hidden 1200 s stop † | 0.366 (0.240–0.499) | 0.311 | 0.367 | 34.5% | 50.0% | 20.0% | .344 · .330 · .394 · .393 · .369 | $0.0077 |
| Qwen3.6-35B-A3B | H0 + hidden $0.16 stop † | 0.229 (0.134–0.338) | 0.219 | 0.225 | 19.0% | 40.0% | 2.5% | .235 · .235 · .223 · .231 · .222 | $0.0526 |
| Qwen3.6-35B-A3B | H8 cost budget ($0.16) | 0.229 (0.128–0.340) | 0.209 | 0.217 | 18.0% | 32.5% | 7.5% | .248 · .190 · .298 · .135 · .273 | $0.0477 |
| Qwen3.6-35B-A3B | H7 time budget (2400 s clock) | **0.227** (0.131–0.334) | 0.222 | 0.223 | 18.0% | 35.0% | 5.0% | .179 · .239 · .186 · .331 · .202 | $0.0939 |
| Qwen3.6-35B-A3B | H7 time budget (4800 s clock) | 0.218 (0.123–0.319) | 0.208 | 0.216 | 16.0% | 37.5% | 5.0% | .152 · .259 · .267 · .288 · .125 | $0.1299 |
| Qwen3.6-35B-A3B | H7 time budget (1800 s clock) | 0.218 (0.123–0.320) | 0.218 | 0.210 | 17.0% | 35.0% | 2.5% | .206 · .210 · .247 · .221 · .206 | $0.0668 |
| Qwen3.6-35B-A3B | H7 time budget (3600 s clock) | 0.208 (0.117–0.307) | 0.203 | 0.206 | 15.5% | 35.0% | 2.5% | .121 · .230 · .204 · .239 · .245 | $0.1183 |
| Qwen3.6-35B-A3B | H2 reasoning kept (+ `preserve_thinking`) | 0.208 (0.115–0.307) | 0.198 | 0.200 | 16.5% | 35.0% | 5.0% | .177 · .247 · .194 · .223 · .197 | $0.0969 |
| Qwen3.6-35B-A3B | H0 + hidden 2400 s stop (H0 re-run) † | 0.200 (0.113–0.298) | 0.195 | 0.198 | 15.0% | 32.5% | 2.5% | .192 · .231 · .164 · .189 · .222 | $0.0847 |
| Qwen3.6-35B-A3B | H0 stock terminus-2 | 0.197 (0.107–0.301) | 0.187 | 0.192 | 15.5% | 35.0% | 5.0% | .181 · .198 · .231 · .220 · .155 | $0.0937 |
| Qwen3.6-35B-A3B | H3 Listen ⚠ | 0.195 (0.100–0.302) | 0.175 | 0.188 | 14.0% | 22.5% | 5.0% | .184 · .206 · .165 · .229 · .189 | $0.0979 |
| Qwen3.6-35B-A3B | H5 snapshot verifier | 0.192 (0.106–0.286) | 0.192 | 0.188 | 14.5% | 32.5% | 0.0% | .198 · .218 · .147 · .181 · .218 | $0.0955 |
| Qwen3.6-35B-A3B | H0 + hidden 3600 s stop † | 0.187 (0.095–0.293) | 0.182 | 0.180 | 14.0% | 27.5% | 5.0% | .171 · .155 · .204 · .219 · .187 | $0.1226 |
| Qwen3.6-35B-A3B | H0 + hidden 1800 s stop † | 0.185 (0.099–0.278) | 0.180 | 0.181 | 14.0% | 32.5% | 0.0% | .135 · .289 · .147 · .148 · .206 | $0.0714 |
| Qwen3.6-35B-A3B | H6 turn budget (40 turns) ‡ | 0.174 (0.089–0.272) | 0.169 | 0.178 | 13.5% | 30.0% | 5.0% | .206 · .129 · .144 · .193 · .198 | **$0.0260** |

⚠ Both H3 runs contain a harness bug (`pkill -f` / `pgrep -f` commands killed H3's own wait, giving a
false timeout and switching the hook off): 36 Qwen3.6 trials in 15 tasks, 10 qwen3.8 trials in 5 tasks.
See `qwen36-harness3-findings.md`. Treat both H3 rows as provisional until re-run with the fix.

† Hidden-stop runs = stock H0 with the H7/H8 stop and nothing told to the model (`show_budget: false`). Each budget-sweep run with a setup failure (docker compose failed before the agent ran) counts it as 0 until its re-run is merged: Qwen3.6 hidden $0.16 (042, 1 trial), Qwen3.6 H7 1800 s (088 + 119, 2 trials). Qwen3.6 hidden 1800 s: 016 ended in `VerifierOutputParseError` because the agent left `Invoices.xlsx` unreadable, so the grader wrote no number; that is the agent's failure and stays 0. qwen3.8 hidden 2400 s: its 1 failed trial (119) was re-run and merged on 2026-10-12 (`MERGED.md`). qwen3.8 hidden 1800 s: its setup failure (088) and the 70 trials that finished after the model server's machine (.65) started dropping off the network were re-run and merged on 2026-10-13 (71 trials, `MERGED.md`); before the merge it scored 0.433.

Other errors count as 0: qwen3.8 hidden 12000 s, one tmux failure (`109`); Qwen3.6 hidden 3600 s, 3 tmux failures and `025`, whose agent ran `kill -9 -1` and killed its own container; Qwen3.6 H7 4800 s, `045`, whose container ended after 2 turns (no reward file; a re-run candidate).

‡ Qwen3.6 H6: 4 trials whose `docker compose build` failed (012, 016, 021, 119) were re-run with an identical config on 2026-10-08 and merged in (`MERGED.md` in the run folder).

## Paired differences in score (bootstrap over the 40 tasks)

| Comparison | Difference | 95% CI | P(diff ≤ 0) | Reading |
|---|---|---|---|---|
| qwen3.8 H7 (2400 s clock) − H0 | **+0.094** | **+0.040 to +0.151** | **0.00** | **first real gain**: timeouts 64 → 35; 34 trials finish in the last 10 min (H0: 4), half of them scoring; vs H6 (similar server speed, 16.4 vs 16.9 tok/s) still +0.062 (+0.007 to +0.121), P 0.014 (`harness7-findings.md`) |
| qwen3.8 H2 − H0 | +0.033 | −0.028 to +0.096 | 0.15 | inside noise |
| qwen3.8 H3 − H0 | +0.017 | −0.026 to +0.059 | 0.21 | inside noise; 37% less time per trial |
| qwen3.8 H4 (`none`) − H0 | +0.001 | −0.051 to +0.050 | 0.47 | no difference; 22% less main-loop input, +9% cost |
| qwen3.8 H5 − H0 | +0.011 | −0.030 to +0.053 | 0.28 | inside noise; +4.2 min per trial (snapshots + 41 s verifier calls), 70 vs 64 timeouts |
| qwen3.8 H6 (40 turns) − H0 | +0.031 | −0.015 to +0.085 | 0.11 | inside noise; the cap rarely binds (5 trials); gain mostly on tasks where H0 is the low outlier, server faster (16.9 vs 13.5 tok/s) (`qwen38-harness6-findings.md`) |
| qwen3.8 H1 − H0 | −0.029 | −0.060 to +0.003 | 0.96 | likely slightly worse |
| Qwen3.6 H7 (2400 s clock) − H0 | +0.030 | −0.013 to +0.074 | 0.08 | inside noise, leaning positive; same cost and timeouts (57 vs 54); the model notices the clock only in its last ~5 min (`harness7-findings.md`) |
| qwen3.8 H7 (2400 s) − hidden 2400 s | **+0.080** | **+0.017 to +0.148** | **0.01** | **telling the model helps**: same stop, same server speed (16.4 vs 16.7 tok/s); timeouts 59 → 35; unchanged without stalled trials, +0.083 (+0.017 to +0.156) (`budget-sweep-findings.md`) |
| qwen3.8 hidden 2400 s − H0 | +0.014 | −0.036 to +0.067 | 0.31 | H0 re-run on today's server: same score, so the H7 gain is not server speed |
| qwen3.8 H7 (1800 s) − hidden 1800 s | +0.004 | −0.068 to +0.080 | 0.47 | no difference, after the hidden run's 71 network-hit trials were re-run (before: +0.034); without stalled trials −0.017 (−0.095 to +0.061). The shown run is unusually uneven across attempts (.344 to .556, chance P 0.02): its attempts 2–3 wrote ~40% more output on a healthy server (`budget-sweep-findings.md`) |
| qwen3.8 H7 (3600 s) − H7 (2400 s) | +0.033 | −0.010 to +0.077 | 0.07 | inside noise, leaning positive; out-of-time failures 34 → 23, solved 99 → 104, `cost_usd` +44%; without stalled trials +0.056 (+0.005 to +0.109) |
| qwen3.8 H7 (3600 s) − hidden 3600 s | **+0.137** | **+0.063 to +0.217** | **0.00** | **largest gain from telling the model**: same server speed (15.4 vs 16.1 tok/s), no network dropouts in the hidden run; without stalled trials +0.174 (+0.091 to +0.264). Of the trials that ran past 1800 s, hidden lets 45 of 69 run into the stop, shown 23 of 68; shown costs 16% less `cost_usd` ($0.0454 vs $0.0542) (`budget-sweep-findings.md`) |
| qwen3.8 hidden 3600 s − hidden 2400 s | −0.025 | −0.070 to +0.020 | 0.84 | the extra 1200 s without the clock adds nothing: 61 trials ran past 2400 s, 7 solved |
| qwen3.8 hidden 12000 s − hidden 3600 s | **+0.100** | **+0.031 to +0.171** | **0.00** | given 3.3 h, H0 does gain: about +0.06 from trials solved after the first hour (016, 025, 042, 088, 094, 100), about +0.04 run-to-run luck in the first hour, when both runs behave identically (attempts .448–.639, chance P 0.05); `cost_usd` 2.7× ($0.147 vs $0.054); 16 trials still unfinished at 12000 s (`budget-sweep-findings.md`) |
| qwen3.8 H7 (3600 s) − hidden 12000 s | +0.037 | −0.041 to +0.115 | 0.17 | the clock gets in 1 h what H0 needs 3.3 h for, at a third of the `cost_usd` ($0.045 vs $0.147) |
| qwen3.8 H7 (1200 s) − hidden 1200 s | **+0.077** | **+0.005 to +0.152** | **0.02** | gain at the tightest budget; +0.064 (−0.015 to +0.143), P 0.055, on the hard-stop footing |
| qwen3.8 hidden 1200 s − hidden 1800 s | −0.097 | −0.162 to −0.037 | 1.00 | 20 minutes is too short without the clock |
| qwen3.8 shown − hidden gap, 3600 s minus 1800 s | **+0.134** | **+0.050 to +0.218** | **0.00** | the clock's value grows with the budget: +0.004 → +0.080 → +0.137 |
| qwen3.8 H8 ($0.030) − H0 | −0.044 | −0.124 to +0.035 | 0.86 | probably slightly worse at 59% of `cost_usd`; timeouts 64 → 7; hidden $0.030 pair queued |
| Qwen3.6 H7 (2400 s) − hidden 2400 s | +0.028 | −0.045 to +0.105 | 0.23 | inside noise |
| Qwen3.6 H7 (1800 s) − hidden 1800 s | +0.033 | −0.005 to +0.073 | 0.05 | borderline, leaning positive; +0.038 (−0.002 to +0.083), P 0.04, without the shown run's 2 setup failures; same server speed (175 tok/s), no stalls, `cost_usd` $0.111 vs $0.119; spread thinly over tasks, not fewer timeouts (`budget-sweep-findings.md`) |
| Qwen3.6 H7 (3600 s) − H7 (2400 s) | −0.020 | −0.088 to +0.040 | 0.72 | no gain from the extra 1200 s at +30% `cost_usd` ($0.208 vs $0.160): 62 trials ran past 2400 s and 2 of them solved; out-of-time failures 56 → 39 become wrong answers, not solves |
| Qwen3.6 H7 (3600 s) − hidden 3600 s | +0.021 | −0.037 to +0.074 | 0.23 | inside noise; hidden 3600 s is no better than hidden 2400 s (−0.013) |
| Qwen3.6 H7 (4800 s) − H7 (3600 s) | +0.010 | −0.054 to +0.077 | 0.39 | no gain from more time with the clock either; vs hidden 3600 s +0.031 (−0.030 to +0.097) |
| Qwen3.6 H8 ($0.16) − hidden $0.16 | −0.000 | −0.063 to +0.061 | 0.51 | no difference: showing the spend adds nothing |
| Qwen3.6 hidden $0.16 − H0 | +0.032 | −0.013 to +0.082 | 0.09 | inside noise, leaning positive, at about half the `cost_usd` ($0.1585 → $0.0852); timeouts 54 → 7 |
| Qwen3.6 H2 − H0 | +0.011 | −0.044 to +0.063 | 0.35 | inside noise |
| Qwen3.6 H3 − H0 | −0.002 | −0.065 to +0.059 | 0.54 | no difference |
| Qwen3.6 H5 − H0 | −0.005 | −0.061 to +0.051 | 0.56 | no difference; verifier finds problems, model rarely fixes them |
| Qwen3.6 H6 (40 turns) − H0 | −0.023 | −0.077 to +0.027 | 0.82 | probably slightly worse, at **28% of the cost** ($0.0937 → $0.0260) and 54% of the time per trial; the counter did not change pacing (`qwen36-harness6-findings.md`) |
| Qwen3.6 H0 − qwen3.8 H0 | −0.248 | −0.363 to −0.138 | 1.00 | real gap |

Noise scale: two identical qwen3.8 H2 runs differed by about 0.016 in reward = 1 rate, and per-task swings of 2 of 5 attempts occur between identical runs.

## Definitions

- **Score**: harbor's Mean, as above. **Attempts 1–5**: the k-th trial of every task scored as its own 40-task run.
- **Reward = 1**: share of trials fully solved (the stricter metric used in earlier reports).
- **Stratified S**: reward re-weighted to the 120-task difficulty mix (22 easy / 90 medium / 8 hard).
- **Leak-adjusted**: score with trials that ran `chrome_state.py solved` counted as 0.
- **pass@5**: tasks fully solved in at least one of 5 attempts. **Solved in all 5**: tasks fully solved in every attempt.
- **Cost / trial**: with prefix caching (each turn's previous prompt at the cache-read price), plus calls outside the main turns (H4 summarizer, terminus-2 summarization) at the uncached price. For H4 the caching estimate is optimistic: rewriting old messages breaks the prompt cache from that point. Per 1M input / output / cache-read tokens: qwen3.8-flash-next $0.15 / $0.47 / $0.016; Qwen3.6-35B-A3B $0.05 / $0.70 / $0.025.

## Protocol notes

- Qwen3.6 runs: 262K context, 32,768-token output cap per call (`llm_call_kwargs.max_tokens`); qwen3.8 runs had no output cap.
- Qwen3.6 H2 sets `chat_template_kwargs.preserve_thinking: true` as well as `interleaved_thinking: true`; without it the Qwen3.6 template drops earlier reasoning and H2 would equal H0.
- `reasoning_effort: xhigh` is sent for both models; Qwen3.6 ignores it.
- Excluded: the accidental qwen3.8 H2 re-run (`harness2-attempt5/2026-09-29__17-27-49`) and `jobs/qwen36-35b-a3b/aborted/`.
- H4 `low` / `medium` / `high` / `xhigh` summary-effort runs: not run yet.
