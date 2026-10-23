# Budget sweep: does telling the model its budget help? (updated 2026-10-21)

Each budget is run twice with the same stop: **hidden** (`harness0-<budget>-attempt5`, H0 + the cap, nothing told
to the model) and **shown** (H6 / H7 / H8: budget sentence + meter every turn). Shown − hidden is the value of
telling the model. Hidden − uncapped H0 is the value of the cap alone. Plan and status: `run-tracker.md`.

Score = harbor Mean, 95% CI by bootstrap over the 40 tasks; differences are paired by task. Cost here is harbor's
`cost_usd` (no cache discount), which is what H8 budgets against; the leaderboard's cost column uses the
prefix-caching estimate instead.

## Pairs finished so far

| Model | Budget | Hidden | Shown | Shown − hidden (95% CI) | P(≤ 0) | Reading |
|---|---|---|---|---|---|---|
| qwen3.8 | 1200 s | 0.366 (0.240–0.499) | H7 0.443 (0.307–0.583) | **+0.077 (+0.005 to +0.152)** | **0.02** | gain at the tightest budget (hard-stop footing +0.064, P 0.055) |
| qwen3.8 | 1800 s | 0.463 (0.330–0.599) | H7 0.467 (0.340–0.594) | +0.004 (−0.068 to +0.080) | 0.47 | no difference (hidden run's network-hit trials re-run; below) |
| qwen3.8 | 2400 s | 0.459 (0.321–0.595) | H7 0.539 (0.414–0.664) | **+0.080 (+0.017 to +0.148)** | **0.01** | real gain from telling the model |
| qwen3.8 | 3600 s | 0.434 (0.304–0.565) | H7 **0.571** (0.441–0.696) | **+0.137 (+0.063 to +0.217)** | **0.00** | largest gain from telling the model |
| qwen3.8 | 12000 s | **0.534** (0.407–0.658) | not run | — | — | hidden only: +0.100 over hidden 3600 s; H7 3600 s is +0.037 above it (below) |
| Qwen3.6 | 1800 s | 0.185 (0.099–0.278) | H7 0.218 (0.123–0.320) | +0.033 (−0.005 to +0.073) | 0.05 | borderline lean; +0.038 (P 0.04) without the shown run's 2 setup failures |
| Qwen3.6 | 2400 s | 0.200 (0.113–0.298) | H7 0.227 (0.131–0.334) | +0.028 (−0.045 to +0.105) | 0.23 | inside noise |
| Qwen3.6 | 3600 s | 0.187 (0.095–0.293) | H7 0.208 (0.117–0.307) | +0.021 (−0.037 to +0.074) | 0.23 | inside noise |
| Qwen3.6 | 4800 s | not run | H7 0.218 (0.123–0.319) | — | — | vs H7 3600 s +0.010 (−0.054 to +0.077); vs hidden 3600 s +0.031 |
| Qwen3.6 | $0.16 | 0.229 (0.134–0.338) | H8 0.229 (0.128–0.340) | −0.000 (−0.063 to +0.061) | 0.51 | no difference |

Cap alone (hidden − uncapped H0):

| Model | Budget | Hidden − H0 (95% CI) | P(≤ 0) | Reading |
|---|---|---|---|---|
| qwen3.8 | 2400 s | +0.014 (−0.036 to +0.067) | 0.31 | same as H0 (2400 s is harbor's own limit: this is an H0 re-run) |
| qwen3.8 | 1800 s | vs hidden 2400 s: +0.005 (−0.055 to +0.060) | 0.45 | cutting the last 600 s without telling the model costs nothing |
| qwen3.8 | 3600 s | vs hidden 2400 s: −0.025 (−0.070 to +0.020) | 0.84 | the extra 1200 s without the clock adds nothing |
| qwen3.8 | 1200 s | vs hidden 1800 s: −0.097 (−0.162 to −0.037) | 1.00 | 20 minutes is too short without the clock |
| qwen3.8 | 12000 s | vs hidden 3600 s: **+0.100 (+0.031 to +0.171)** | 0.00 | about +0.06 from trials solved after an hour, about +0.04 run-to-run (below) |
| Qwen3.6 | 2400 s | +0.003 (−0.055 to +0.058) | 0.47 | same as H0 |
| Qwen3.6 | 1800 s | vs hidden 2400 s: −0.015 (−0.055 to +0.027) | 0.75 | inside noise |
| Qwen3.6 | 3600 s | vs hidden 2400 s: −0.013 (−0.062 to +0.039) | 0.69 | inside noise |
| Qwen3.6 | $0.16 | +0.032 (−0.013 to +0.082) | 0.09 | inside noise, leaning positive, at about half the cost |

Qwen3.6 1800 s: both arms ran at the same server speed (175 tok/s) with no stalled calls, 3 days apart (Oct 11 and Oct 14).
The shown arm carries 2 setup failures as 0 (088, 119); dropping them gives +0.038 (−0.002 to +0.083), P 0.04. With +0.028
at 2400 s, both Qwen3.6 pairs now lean the same way, but each alone sits at the edge of the noise.

## Conclusion for time (qwen3.8)

| Budget | Hidden | Shown | Shown − hidden (95% CI) |
|---|---|---|---|
| 1200 s | 0.366 | 0.443 | **+0.077 (+0.005 to +0.152)** |
| 1800 s | 0.463 | 0.467 | +0.004 (−0.068 to +0.080) |
| 2400 s | 0.459 | 0.539 | **+0.080 (+0.017 to +0.148)** |
| 3600 s | 0.434 | 0.571 | **+0.137 (+0.063 to +0.217)** |
| 12000 s | **0.534** | not run | — |
| change 1800 → 3600 s | −0.030 (−0.085 to +0.025) | **+0.104 (+0.051 to +0.156)** | **+0.134 (+0.050 to +0.218)**, P 0.001 |

Uncapped H0 (ended by harbor's 2400 s kill) scores 0.445. The last row is bootstrapped over tasks like the pairs.

1. **Without the clock, time helps up to about 30 minutes, adds nothing for the next half hour, then helps slowly.** Hidden
   scores 0.366 at 1200 s, 0.463 at 1800 s (+0.097, −0.162 to −0.037 the other way round), stays flat to 3600 s (0.434), and
   reaches 0.534 at 12000 s (+0.100 over 3600 s, +0.031 to +0.171). The 12000 s gain has two parts. The hidden model never
   sees its budget, so the 3600 s and 12000 s runs behave identically for the first hour; the 12000 s run was already 0.038
   ahead by minute 60, which is run-to-run luck (its attempts range .448–.639; a spread that wide happens by chance 5% of the
   time). The rest, about +0.06, is trials solved after an hour: 10 of the 48 trials still running at 60 minutes solved by
   3.3 hours (016, 025, 042, 088, 094, 100), and 16 were still running at 12000 s, none solved.
2. **With the clock, time pays off sooner.** The shown arm rises +0.104 from 1800 s to 3600 s and the gap between the arms
   grows by +0.134. At 2400 s and 3600 s the shown arm is better on 17 and 18 of 40 tasks and worse on 6 and 5. At 1200 s the
   clock is worth +0.077 (P 0.02; +0.064, P 0.055, on the hard-stop footing).
3. **How: the clock makes long trials finish.** Of the trials that ran past 1800 s, the shown arm ends 45 of 68 itself (21
   solved); the hidden arm lets 45 of 69 run into the 3600 s stop. Given 3.3 hours the hidden model finishes some of them
   anyway, slowly.
4. **The clock is the cheap way to the same place.** H7 at 3600 s scores 0.571 against hidden at 12000 s 0.534: +0.037
   (−0.041 to +0.115), inside the noise, at a third of the `cost_usd` per trial ($0.0454 vs $0.1474) and about half the mean
   agent time (25.5 vs 45.3 min). At 3600 s the shown arm is also cheaper than the hidden arm ($0.0454 vs $0.0542).

Not settled: one run per arm per budget, each arm on a different day (same server speed; network dropouts logged below);
1800 s rests on an uneven shown run, and hidden 12000 s on an uneven run too; shown 4800 s and 12000 s are not run for qwen3.8
(configs exist); and it holds for one model only (Qwen3.6 shows at most +0.03 and no gain from more time, with or without the
clock, up to 4800 s).

Why the hidden arm stays flat, what long trials do, and what a faster server would do: `time-budget-mechanics.md`.

## Hard-stop-equivalent scores

The 2400 s runs end with harbor's hard kill at 2400 s, the official TUA-Bench setting. The 1200, 1800, 3600, 4800 and 12000 s runs
end with the harness's soft stop, which lets the turn under way finish. To put every budget on the 2400 s footing, each
soft-stopped trial that scored was re-judged from its final (in-flight) agent turn in `agent/trajectory.json`:
- If that turn did the decisive work (wrote or saved the graded output, applied the change the grader checks), a hard kill
  would have cut it, so its reward becomes 0.
- If it only verified or inspected a state already in place, the reward stays.

Trials that ended on their own, harbor kills, and soft-stopped trials with reward 0 are unchanged. The lower bound sets every
soft-stopped reward to 0. 39 trials were judged (list below).

| Model | Run | As run (soft stop) | Hard-stop lower bound | **Refined hard-stop** | Scoring soft-stopped trials (cut) |
|---|---|---|---|---|---|
| qwen3.8 | hidden 1200 s | 0.366 | 0.344 | **0.361** | 5 (1) |
| qwen3.8 | shown 1200 s | 0.443 | 0.414 | **0.425** | 7 (4) |
| qwen3.8 | hidden 1800 s | 0.463 | 0.441 | **0.463** | 5 (0) |
| qwen3.8 | shown 1800 s | 0.467 | 0.436 | **0.459** | 8 (2 to 0, 1 to 0.66) |
| qwen3.8 | hidden 2400 s | 0.459 | — | **0.459** | hard kill already |
| qwen3.8 | shown 2400 s | 0.539 | — | **0.539** | hard kill already |
| qwen3.8 | hidden 3600 s | 0.434 | 0.421 | **0.429** | 3 (1) |
| qwen3.8 | shown 3600 s | 0.571 | 0.567 | **0.571** | 2 (0) |
| qwen3.8 | hidden 12000 s | 0.534 | 0.527 | **0.534** | 2 (0) |
| Qwen3.6 | hidden 1800 s | 0.185 | 0.174 | **0.180** | 3 (1) |
| Qwen3.6 | shown 1800 s | 0.218 | 0.203 | **0.213** | 3 (1) |
| Qwen3.6 | hidden 2400 s | 0.200 | — | **0.200** | hard kill already |
| Qwen3.6 | shown 2400 s | 0.227 | — | **0.227** | hard kill already |
| Qwen3.6 | hidden 3600 s | 0.187 | 0.187 | **0.187** | 0 |
| Qwen3.6 | shown 3600 s | 0.208 | 0.208 | **0.208** | 0 |
| Qwen3.6 | shown 4800 s | 0.218 | 0.215 | **0.218** | 1 (0) |

Hidden 12000 s and Qwen3.6 shown 4800 s were added on 2026-10-21: their 3 scoring soft-stopped trials all keep their reward,
so the pairs below are unchanged for them.

Paired differences on the refined per-trial rewards (bootstrap over the 40 tasks, 10,000 resamples):

| Comparison | As run | **Refined hard-stop (95% CI)** | P(≤ 0) |
|---|---|---|---|
| qwen3.8 shown − hidden, 1200 s | +0.077 | +0.064 (−0.015 to +0.143) | 0.055 |
| qwen3.8 shown − hidden, 1800 s | +0.004 | −0.005 (−0.080 to +0.071) | 0.54 |
| qwen3.8 shown − hidden, 2400 s | +0.080 | **+0.080 (+0.017 to +0.148)** | 0.008 |
| qwen3.8 shown − hidden, 3600 s | +0.137 | **+0.142 (+0.070 to +0.221)** | 0.000 |
| qwen3.8 hidden 3600 s − hidden 2400 s | −0.025 | −0.030 (−0.075 to +0.010) | 0.91 |
| qwen3.8 H7 3600 s − H7 2400 s | +0.033 | +0.033 (−0.011 to +0.077) | 0.07 |
| qwen3.8 gap at 3600 s − gap at 1800 s | +0.134 | **+0.147 (+0.063 to +0.233)** | 0.000 |
| Qwen3.6 shown − hidden, 1800 s | +0.033 | +0.033 (−0.007 to +0.080) | 0.06 |
| Qwen3.6 shown − hidden, 2400 s | +0.028 | +0.028 (−0.045 to +0.105) | 0.23 |
| Qwen3.6 shown − hidden, 3600 s | +0.021 | +0.021 (−0.037 to +0.074) | 0.23 |
| Qwen3.6 hidden 3600 s − hidden 2400 s | −0.013 | −0.013 (−0.062 to +0.039) | 0.69 |
| Qwen3.6 H7 3600 s − H7 2400 s | −0.020 | −0.020 (−0.088 to +0.041) | 0.73 |
| Qwen3.6 gap at 3600 s − gap at 1800 s | −0.012 | −0.012 (−0.085 to +0.057) | 0.63 |

No conclusion changes on the hard-stop footing:
- qwen3.8: telling the model the budget still helps at 2400 s and 3600 s, and the gap still grows from 1800 s to 3600 s.
  Hidden 3600 s is still no better than hidden 2400 s.
- Qwen3.6 is unchanged: small leans and no trend.

The soft stop helps shown runs more at tight budgets. At 1200 s, 4 of the shown run's 7 scoring soft-stopped trials did
their decisive work in the last turn (hidden: 1 of 5), because the clock pushes the wrap-up into the final turn. That is why the
new 1200 s pair drops from +0.077 (P 0.02) to +0.064 (P 0.055).

Trial verdicts († the turn's commands started before the budget: the model's reply finished 4–62 s early, so a real hard
kill might have let them finish, and the refined score of that run may be low by up to 0.0075; ‡ judgement call):

| Run | Trial | Reward | Hard-stop | Reason |
|---|---|---|---|---|
| qwen3.8 hidden 1200 s | 034-turn-off-dark-mode__aepuUKC | 1.0 | 1.0 | final turn only read Preferences; light mode already set |
| qwen3.8 hidden 1200 s | 048-tamiflu-side-effects__R7t2ptY | 1.0 | **0** | final turn navigated Chrome to the side-effects page (the graded tab); reply ended 83 s after the budget |
| qwen3.8 hidden 1200 s | 054-prostate-label-obj__6HRuxz6 | 1.0 | 1.0 | final turn only confirmed done; OBJ written earlier |
| qwen3.8 hidden 1200 s | 054-prostate-label-obj__d65jFgJ | 0.5 | 0.5 | OBJ already exported; final turn only re-saved the optional scene file |
| qwen3.8 hidden 1200 s | 069-linux-ls-tutorial__Jetobgk | 1.0 | 1.0 | grader checks only `ls.png`, saved the turn before; final turn added a tutorial file |
| qwen3.8 shown 1200 s | 033-prostate-volume-est__AMvZTqb | 0.66 | 0.66 | fallback number written the turn before; final turn's script crashed |
| qwen3.8 shown 1200 s | 033-prostate-volume-est__hqiPJdT | 0.66 | 0.66 | final turn only confirmed done |
| qwen3.8 shown 1200 s | 038-zurich-rental-car__Aivi8i4 | 1.0 | **0** | final turn applied sort-by-price, the last required step |
| qwen3.8 shown 1200 s | 043-load-hello-extension__D2aWHPo | 1.0 | 1.0 | extension already loaded in the default profile; final turn only probed APIs |
| qwen3.8 shown 1200 s | 043-load-hello-extension__oZRqNxw | 1.0 | **0** | final turn found the registration gone, reloaded the extension and closed Chrome |
| qwen3.8 shown 1200 s | 050-mri-png-slices__PeQCeYT | 1.0 | **0** † | final turn wrote and ran the export of all 15 PNGs |
| qwen3.8 shown 1200 s | 054-prostate-label-obj__fVFp9jz | 0.5 | **0** † | the first working OBJ export ran in the final turn |
| qwen3.8 hidden 1800 s | 038-zurich-rental-car__EvTkYjP | 1.0 | 1.0 | final turn only confirmed done |
| qwen3.8 hidden 1800 s | 054-prostate-label-obj__3XEbRZk | 1.0 | 1.0 | final turn only checked bounds |
| qwen3.8 hidden 1800 s | 054-prostate-label-obj__ouesxJp | 0.5 | 0.5 | OBJ written the turn before; final turn measured variants without writing |
| qwen3.8 hidden 1800 s | 109-setup-outlook-account__PvrvQZc | 1.0 | 1.0 | final turn only toggled the Error Console; no form input |
| qwen3.8 hidden 1800 s | 109-setup-outlook-account__SXcUtF4 | 1.0 | 1.0 | final turn's typing never reached Thunderbird (screen unchanged) |
| qwen3.8 shown 1800 s | 007-reconstruct-prostate-obj__hfb4zzt | 0.33 | **0** | the OBJ (the one passing check) was first written in the final turn |
| qwen3.8 shown 1800 s | 016-count-invoice-pivot__GiQfaT5 | 1.0 | 1.0 | final turn only confirmed done |
| qwen3.8 shown 1800 s | 033-prostate-volume-est__KQtTqG9 | 0.66 | 0.66 | final script kept the fallback 25.0 written earlier |
| qwen3.8 shown 1800 s | 033-prostate-volume-est__Rxo4tTo | 0.66 | 0.66 | file already held a valid number (40.0, also worth 0.66); final turn replaced it with 57.9 |
| qwen3.8 shown 1800 s | 033-prostate-volume-est__uoy5MNP | 1.0 | **0.66** | final turn wrote the in-tolerance 48.2 over the 30.0 written the turn before, which is worth 0.66 |
| qwen3.8 shown 1800 s | 043-load-hello-extension__oWXS2mj | 1.0 | **0** | final turn closed Chrome and wrote the extension into Preferences |
| qwen3.8 shown 1800 s | 054-prostate-label-obj__fLDpJSP | 0.5 | 0.5 | an OBJ already existed (the 0.5); the final rewrite still failed similarity |
| qwen3.8 shown 1800 s | 109-setup-outlook-account__Jrwswh3 | 1.0 | 1.0 | final turn only confirmed done |
| qwen3.8 hidden 3600 s | 025-product-channel-pivots__KPnhvn8 | 1.0 | **0** | final turn ran the macro that created both pivots and saved |
| qwen3.8 hidden 3600 s | 054-prostate-label-obj__rws5678 | 0.5 | 0.5 | final turn only analysed the label and searched the disk |
| qwen3.8 hidden 3600 s | 109-setup-outlook-account__r7QLTvy | 1.0 | 1.0 | final turn's typing left the field empty; the graded state predates it |
| qwen3.8 shown 3600 s | 005-optimize-cold-plate__8ZDgMiA | 0.33 | 0.33 | final turn only confirmed done |
| qwen3.8 shown 3600 s | 054-prostate-label-obj__BeMLbLe | 0.5 | 0.5 | final turn only confirmed done |
| Qwen3.6 hidden 1800 s | 033-prostate-volume-est__f3bwrh5 | 0.66 | 0.66 | final turn explored data only; file written earlier |
| Qwen3.6 hidden 1800 s | 033-prostate-volume-est__tWvxnLi | 0.66 | 0.66 | number written the turn before; final turn failed to start Slicer |
| Qwen3.6 hidden 1800 s | 109-setup-outlook-account__vBsqjaA | 1.0 | **0** † ‡ | final turn typed the address and password; no earlier sign they ever reached a field |
| Qwen3.6 shown 1800 s | 043-load-hello-extension__Z4aFhjb | 1.0 | 1.0 ‡ | two turns earlier the extension was loaded and Chrome closed (which writes Preferences); final turn repeated it |
| Qwen3.6 shown 1800 s | 088-extract-presenter-photos__8GcNTW7 | 1.0 | **0** † | final turn created `presenter/` and copied the photos |
| Qwen3.6 shown 1800 s | 109-setup-outlook-account__EMtn5qD | 1.0 | 1.0 | final turn's script crashed before sending any input |
| qwen3.8 hidden 12000 s | 007-reconstruct-prostate-obj__3tavgZd | 0.66 | 0.66 | final turn only listed the artifacts; OBJ and render written earlier |
| qwen3.8 hidden 12000 s | 007-reconstruct-prostate-obj__ijbiKSi | 0.66 | 0.66 | OBJ and a valid render already existed; final turn only tried to make the render prettier |
| Qwen3.6 shown 4800 s | 033-prostate-volume-est__9N4KVBX | 0.66 | 0.66 | terminal stuck in an open heredoc since turn 68; the final "PYEOF" (its 96th such turn) changed nothing; the number was written earlier |

## Server stalls: sensitivity check

A stalled call (litellm's 600 s timeout) wastes a third of a 1800 s budget. Shown − hidden with every trial that had one
removed from both arms:

| Pair | Trials with a stall (hidden / shown) | Server speed (hidden / shown) | All trials | Without stalled trials |
|---|---|---|---|---|
| qwen3.8 1800 s | 16 / 13 | 15.7 / 16.5 tok/s | +0.004 (−0.068 to +0.080) | −0.017 (−0.095 to +0.061) |
| qwen3.8 2400 s | 10 / 11 | 16.7 / 16.4 tok/s | +0.080 (+0.017 to +0.148) | **+0.083 (+0.017 to +0.156)** |
| qwen3.8 3600 s | 9 / 16 | 16.1 / 15.4 tok/s | **+0.137 (+0.063 to +0.217)** | **+0.174 (+0.091 to +0.264)** |
| Qwen3.6 1800 s | 0 / 0 | 176 / 175 tok/s | +0.033 (−0.005 to +0.073) | same |
| Qwen3.6 2400 s | 0 / 0 | 171 / 164 tok/s | +0.028 (−0.045 to +0.105) | same |

Server speed is the analyze.py figure (stalled calls included); without stalled trials every qwen3.8 run here ran at
about 17 tok/s.

### Network dropouts and the hidden 1800 s re-run

The hidden 1800 s run first scored 0.433 with 36 stalled trials. The cause was not a slow server but the machine serving
qwen3.8 (<qwen38-vllm-host>) dropping off the network from 2026-10-12 morning. vllmtop, which scrapes the server about once a second
from the benchmark PC (`~/.local/share/vllmtop/usage.db`), shows each dropout as a gap in its scrapes:

| Window (SGT) | Run | Gaps ≥ 10 s | Effect |
|---|---|---|---|
| Oct 8 15:37 → Oct 9 | H7 2400 s | two blips (10 s, 15 s) | none |
| Oct 10 15:38–15:51 | hidden 2400 s | 6 gaps, 530 s | 038 and 088 stalled and timed out (both 0) |
| Oct 11 06:00 → 22:53 | H7 1800 s | **none**; no aborts, no preemptions, only our ≤ 4 requests | none |
| Oct 12 08:19 | hidden 1800 s (kept part) | 822 s | 009, 025, 067, 100 ran through it (2 stalled; all 0) |
| Oct 12 09:30 → 17:00 | hidden 1800 s | dozens, 10 s to 10 min | the 70 trials finished after 09:30 were re-run |
| Oct 13 17:44 → Oct 14 00:31 | hidden 1800 s re-run | 7 gaps, ~35 min | stall clusters at 18:22, 18:49, 21:08 follow them by 600 s |
| Oct 14 13:58–14:13 | H7 3600 s | 868 s | 4 trials ran through it, 2 stalled (one still solved) |
| Oct 15 15:17 → Oct 16 15:47 | hidden 3600 s | 6 blips (10–26 s) | none; its 9 stalled trials are long replies on hard tasks (005 ×3, 025 ×2, 100 ×2, 016, 059) |

The 70 trials that finished after 09:30 SGT on Oct 12, plus the 088 setup failure, were re-run with an identical config and
merged on 2026-10-13 (`MERGED.md`); within each task the re-run trials score +0.010 against the kept ones, at the same server
speed. The first dropout (08:19) came before the 09:30 cut-off, so 4 kept trials and 10 re-run trials still carry a stall.
Every leftover dropout sits in a hidden arm, so cleaning them out would raise the hidden score and make the 1800 s gap smaller,
not larger.

Checks that the hidden arm is really hidden: both hidden runs report `2.0.0+harness7-time-hidden` and `shown: false`, and none
of their 400 trajectories contains the meter line or the budget sentence (all 400 shown ones do). The configs differ only in
`show_budget`. The Oct 10 code change that added the switch left the shown path unchanged, so H7 2400 s (run Oct 8) and H7
1800 s ran the same code.

### Why 1800 s shows nothing

- **Noise width.** The 1800 s interval (−0.068 to +0.080) contains the 2400 s effect; the subset can only resolve about ±0.07.
- **The shown run is uneven.** H7 1800 s attempts score .502 · .344 · .398 · .535 · .556; shuffling trials within tasks gives
  a spread that wide only 2% of the time (other runs: 13–60%). Attempts 2–3 (Oct 11 09:00–15:35 SGT) ran on a healthy server
  (no gaps, normal speed and machine time) but wrote about 40% more output per trial (12.2k / 11.4k vs 7.9k–10.5k tokens), ran
  longer, and failed tasks solved everywhere else (029, 109, 089). Without attempts 2–3 the run would score 0.531; that is
  cherry-picked and not reported, but it shows 1800 s is undecided rather than a null. A second H7 1800 s run, ideally with
  both arms at once (2 + 2 trials), would settle it.
- **The clock costs thinking.** Shown runs write more output than hidden ones at the same budget (1800 s: 11.4k vs 7.2k tokens
  per trial; 2400 s: 10.6k vs 8.7k), about 3–4 extra minutes of model time per trial at 1800 s. At a tight budget that eats into
  the time the clock is meant to save.
- **Little to rescue.** The clock helps by turning "ran out of time" into "finished". At 2400 s it rescued 21 trials (55 → 34
  out-of-time failures); at 1800 s only 6 (58 → 52), while 7 more trials declared done and were wrong. Many tasks need more than
  1800 s at this model's speed whatever the pacing.

## Share of failures that ran out of time

Failures = trials with reward < 1; "ran out of time" = harbor timeout or the harness budget stop.

| Run | Failures | Ran out of time |
|---|---|---|
| qwen3.8 hidden 1200 s | 131 | 75 (57%) |
| qwen3.8 shown 1200 s | 119 | 53 (45%) |
| qwen3.8 hidden 1800 s | 112 | 58 (52%) |
| qwen3.8 shown 1800 s | 113 | 52 (46%) |
| qwen3.8 hidden 2400 s | 113 | 55 (49%) |
| qwen3.8 shown 2400 s | 101 | 34 (34%) |
| qwen3.8 hidden 3600 s | 118 | 43 (36%) |
| qwen3.8 shown 3600 s | 96 | 23 (24%) |
| qwen3.8 hidden 12000 s | 105 | 16 (15%) |
| Qwen3.6 hidden 1800 s | 172 | 56 (33%) |
| Qwen3.6 shown 1800 s | 166 | 58 (35%) |
| Qwen3.6 hidden 2400 s | 170 | 55 (32%) |
| Qwen3.6 shown 2400 s | 164 | 56 (34%) |
| Qwen3.6 hidden 3600 s | 172 | 47 (27%) |
| Qwen3.6 shown 3600 s | 169 | 39 (23%) |
| Qwen3.6 shown 4800 s | 168 | 33 (20%) |

Working hypothesis for the rest of the grid: the clock helps in proportion to how many failures run out of time.
qwen3.8 converts timeouts into finishes (49% → 34% at 2400 s, 36% → 24% at 3600 s); Qwen3.6 fails mostly by being wrong and the clock
does not change its timeout share; at 3600 s its out-of-time failures fall to 23%, but they turn into wrong answers, not solves.

## What changed mechanically

| Run | Agent min, median (mean) | Turns, median | Out tokens | `cost_usd` | Outcomes (solved / wrong / timeout / error) |
|---|---|---|---|---|---|
| qwen3.8 H0 (uncapped, Sep 23) | 13.4 (20.3) | 11 | 9.2k | $0.0302 | 81 / 55 / 64 / 0 |
| qwen3.8 hidden 1200 s | 11.4 (13.0) | 11 | 8.6k | $0.0190 | 69 / 129 / 2 / 0 |
| qwen3.8 H7 1200 s | 15.5 (13.7) | 11 | 10.2k | $0.0183 | 81 / 116 / 3 / 0 |
| qwen3.8 hidden 1800 s | 10.2 (16.8) | 12 | 7.2k | $0.0265 | 87 / 109 / 4 / 0 |
| qwen3.8 hidden 2400 s | 11.3 (18.9) | 13 | 8.7k | $0.0329 | 83 / 58 / 59 / 0 |
| qwen3.8 H7 2400 s | 14.1 (19.9) | 12 | 10.6k | $0.0316 | 98 / 67 / 35 / 0 |
| qwen3.8 H7 1800 s | 13.6 (16.9) | 12 | 11.4k | $0.0263 | 87 / 112 / 1 / 0 |
| qwen3.8 hidden 3600 s | 10.5 (25.2) | 13 | 8.2k | $0.0542 | 82 / 118 / 0 / 0 |
| qwen3.8 H7 3600 s | 16.5 (25.5) | 15 | 11.7k | $0.0454 | 104 / 93 / 3 / 0 |
| qwen3.8 hidden 12000 s | 10.5 (45.3) | 13 | 8.8k | $0.1474 | 95 / 102 / 2 / 1 |
| Qwen3.6 H0 (uncapped) | 12.2 (18.3) | 50 | 26.6k | $0.1585 | 30 / 116 / 54 / 0 |
| Qwen3.6 hidden 2400 s | 9.9 (17.4) | 40 | 17.9k | $0.1439 | 30 / 113 / 55 / 2 |
| Qwen3.6 hidden 1800 s | 10.7 (14.4) | 39 | 19.1k | $0.1194 | 28 / 169 / 2 / 1 |
| Qwen3.6 H7 1800 s | 13.7 (16.1) | 38 | 19.4k | $0.1112 | 34 / 159 / 5 / 2 |
| Qwen3.6 H7 2400 s | 13.6 (19.4) | 48 | 24.5k | $0.1599 | 35 / 107 / 57 / 1 |
| Qwen3.6 hidden 3600 s | 10.5 (24.5) | 42 | 23.6k | $0.2156 | 28 / 163 / 5 / 4 |
| Qwen3.6 H7 3600 s | 10.8 (24.7) | 45 | 20.9k | $0.2081 | 31 / 161 / 7 / 1 |
| Qwen3.6 H7 4800 s | 11.5 (27.8) | 42 | 18.1k | $0.2310 | 32 / 152 / 15 / 1 |
| Qwen3.6 hidden $0.16 | 12.2 (14.3) | 44 | 27.2k | $0.0852 | 38 / 154 / 7 / 1 |
| Qwen3.6 H8 $0.16 | 9.1 (12.1) | 41 | 19.2k | $0.0776 | 36 / 155 / 8 / 1 |

- **qwen3.8, 2400 s.** The fresh H0 re-run (server at 16.7 tok/s) scores the same as the old H0 (13.5 tok/s), so
  the earlier H7 gain is not a server-speed artifact. With the clock shown, timeouts fall 59 → 35 and solved
  trials rise 82 → 98: the model wraps up before harbor's limit instead of being cut off mid-work.
- **qwen3.8, 1200 s.** Shown − hidden +0.077 (+0.005 to +0.152). Most failures in both arms run out of time (57% hidden,
  45% shown); the shown arm solves 81 trials against 69 at the same `cost_usd` ($0.0183 vs $0.0190). Hidden 1200 s is 0.097
  below hidden 1800 s, so 20 minutes is too short for the model without the clock.
- **qwen3.8, 1800 s.** Both arms end cleanly at the harness stop (1 and 4 harbor timeouts) and score the same; see
  "Why 1800 s shows nothing" above.
- **qwen3.8, 3600 s.** Shown − hidden +0.137 (+0.063 to +0.217), the largest gap in the sweep, at the same server speed
  (15.4 vs 16.1 tok/s) and with no network dropouts in the hidden run. The difference is in the long trials: of those that ran
  past 1800 s, the hidden arm lets 45 of 69 run into the stop (2 of them had already solved), while the shown arm finishes 45
  of 68 itself and 21 of those solve. Hidden 3600 s scores no better than hidden 2400 s (−0.025): 61 trials ran past 2400 s
  and 7 solved. The stopped trials are also where the money goes: 54% of the hidden arm's `cost_usd` ($5.87 of $10.84) is
  spent on its 45 trials that hit the stop, against 23% ($2.12 of $9.09) in the shown arm, so the shown arm costs 16% less per
  trial ($0.0454 vs $0.0542). H7 3600 s over H7 2400 s: +0.033 (−0.010 to +0.077), inside the noise, leaning positive (+0.056,
  +0.005 to +0.109, without stalled trials); out-of-time failures fall 34 → 23 and solved trials rise 99 → 104, at 44% more
  `cost_usd`. Its stalls outside the opening dropout (14 trials) are long replies on hard tasks (003, 005, 016, 025).
- **qwen3.8, 12000 s hidden.** 0.534, +0.100 over hidden 3600 s (+0.031 to +0.171). By minute 60 it had earned 0.459,
  against 0.421 in the 3600 s run, so about +0.04 is run-to-run (both runs behave identically until then). After minute 60
  it adds about +0.075 (10 more solves plus partial credit), while the 3600 s run's stopped trials held 0.013. 184 of 200
  trials end on their own; 16 are stopped at 12000 s, none solved. Mean agent time 45.3 min and `cost_usd` $0.147 per trial,
  2.7× hidden 3600 s. Its 28 stalled calls in 17 trials are long replies; vllmtop shows no network gaps.
- **Qwen3.6, 2400 s.** The model notices the clock only near the end (see `harness7-findings.md`); timeouts are
  unchanged (55 vs 57). Small lean, no clear effect.
- **Qwen3.6, 1800 s.** Both arms end at the harness stop (2 and 5 harbor timeouts). Shown solves 34 trials against 28, with the
  same share of failures running out of time (35% vs 33%), so this is not the timeout rescue seen on qwen3.8. The gain is
  spread thinly: only 109 moves by 2 or more of 5 attempts. Shown runs work longer before answering at both budgets
  (median 13.7 vs 10.7 min at 1800 s, 13.6 vs 9.9 at 2400 s) and quit in under 5 minutes a little less often (72 vs 79
  trials at 1800 s, 68 vs 79 at 2400 s).
- **Qwen3.6, 3600 s shown.** No gain over 2400 s: −0.020 (−0.088 to +0.040), at 30% more `cost_usd` ($0.208 vs $0.160).
  The extra time goes to trials that are already lost: 62 trials ran past 2400 s (52 past 3000 s) and 2 of them solved
  (mean reward 0.04). Trials split in two: a quarter quit within 2 minutes, a quarter run 52 minutes or more. Out-of-time
  failures fall 56 → 39, but those trials end wrong (wrong 107 → 129, solved 36 → 31). Attempt 1 (Oct 15 09:18–13:20 SGT)
  scored 0.121 against 0.204–0.245 for the others, at the same server speed (159 tok/s), and lost 021, 029, 050, 088 and
  099, which the other attempts mostly solve; without it the run is about 0.230, still level with H7 2400 s. vllmtop shows
  the RTX server healthy the whole run: no gaps, no preemptions, only our ≤ 4 requests.
- **Qwen3.6, 3600 s pair.** Shown − hidden +0.021 (−0.037 to +0.074): inside the noise, the same small lean as at 1800 s and
  2400 s. Hidden 3600 s is no better than hidden 2400 s (−0.013).
- **Qwen3.6, 4800 s shown.** 0.218: +0.010 over H7 3600 s (−0.054 to +0.077) and −0.009 against H7 2400 s, so more time with
  the clock does not help Qwen3.6. Out-of-time failures fall to 20% (33 of 168); 15 of those are harbor kills, where the turn
  under way outran the 600 s margin (one trial summarized its context 384 times). Its attempts are uneven (.125–.288, chance
  P 0.02). One trial (`045`) lost its container after 2 turns and counts as 0.
- **Qwen3.6, $0.16.** The cap itself does the work: timeouts 54 → 7 and spend roughly halves versus uncapped H0,
  with the score no lower (slightly higher). Expensive Qwen3.6 trials rarely solve, so cutting them costs little.
  Showing the meter changes spend a bit (−9% cost, −15% mean agent time vs hidden) but not the score.

## Caveats

- Setup failures (docker compose failed before the agent ran) count as 0 until their re-runs are merged:
  Qwen3.6 hidden $0.16 `042` (1 trial), Qwen3.6 H7 1800 s `088` + `119` (2);
  re-runs are queued (`rerun_failed.py`). qwen3.8 hidden 2400 s `119` was re-run and merged on 2026-10-12 (it scored 1); qwen3.8 hidden 1800 s `088` was re-run with the network-hit trials (above). Each is at most 0.005 of score.
  The other errors (Qwen3.6 hidden 2400 s: 2, H7 2400 s: 1, H7 3600 s: 1; H8 $0.16: 1) are tmux agent failures and stay as 0.
  Qwen3.6 hidden 1800 s `016` ended in `VerifierOutputParseError` because the agent left `Invoices.xlsx` unreadable; it stays 0.
  Qwen3.6 hidden 3600 s: 3 tmux failures, and `025`, whose agent ran `kill -9 -1` and killed its own container. Qwen3.6 H7 4800 s:
  `045` lost its container after 2 turns (no reward file; a re-run candidate). qwen3.8 hidden 12000 s: one tmux failure (`109`).
  All count as 0.
- Hidden and shown arms of one budget ran 1–3 days apart on shared servers. Without stalled trials every recent qwen3.8 run
  ran at about 17 tok/s; the differences between runs are network dropouts (table above), not server speed.
- Noise scale: two identical qwen3.8 H2 runs differed by about 0.016; per-task swings of 2 of 5 attempts are common.
- The stop is not the same at every budget. At 1200, 1800, 3600, 4800 and 12000 s harbor's limit sits at least 600 s above
  the budget, so the
  harness stop ends the trial after the turn under way finishes (qwen3.8: a median 28–84 s past the budget). At 2400 s
  harbor's own 2400 s limit kills the trial mid-turn first (all out-of-time trials in both 2400 s arms). Shown − hidden is
  fair at every budget, since both arms of a budget end the same way. Across budgets the soft stop can only help: counting
  every point held by a soft-stopped trial as earned in its last turn, it is worth at most +0.013 (hidden 3600 s), +0.004
  (shown 3600 s), +0.022 (hidden 1800 s) and +0.031 (shown 1800 s). None of the conclusions change; hidden 3600 s is no
  better than hidden 2400 s even with that help. The trial-by-trial correction is in "Hard-stop-equivalent scores" above.

## Bottom line so far

For qwen3.8, telling the model its time budget helps at every budget except 1800 s (+0.077 at 1200 s, +0.080 at 2400 s,
+0.137 at 3600 s; 1800 s rests on an uneven shown run), and the gain grows from 1800 s to 3600 s. The clock works by making
long trials finish instead of running into the stop. Without the clock, time pays off only slowly: hidden scores stay flat
from 30 to 60 minutes (0.463, 0.459, 0.434) and reach 0.534 after 3.3 hours, about +0.06 of it from trials solved after the
first hour. H7 at one hour (0.571) matches that at a third of the cost. For Qwen3.6 the clock leans positive at every budget
(+0.033, +0.028 and +0.021 at 1800, 2400 and 3600 s), never clearly outside the noise, and more time does not help with or
without it (H7 4800 s 0.218). The spend meter changes nothing; the cost cap alone saves about half the spend at no loss.
