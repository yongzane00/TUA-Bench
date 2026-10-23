# Qwen3.6 H6 "Turn budget" (40 turns, counter shown): findings

Run: `qwen36-35b-a3b/harness6-turns40-attempt5/2026-10-07__17-17-03` vs H0 `harness0-attempt5/2026-10-02__21-45-56`
(40 tasks × 5 attempts). H6 = stock terminus-2 with `max_turns: 40`, a budget sentence in the task ("You have at
most 40 turns for this task (one turn = one response from you). Each terminal update shows the current turn."),
and "[Turn N of 40]" on every update.

The 4 trials whose `docker compose build` failed (012, 016, 021, 119) were re-run on 2026-10-08 with an identical
config and merged in (`MERGED.md` in the run folder); the run now has 200 trials and no infrastructure errors.

## Score and cost

| | H0 | H6 | Change |
|---|---|---|---|
| Score (harbor Mean, 95% CI) | 0.197 (0.108–0.300) | 0.174 (0.089–0.272) | −0.023 (−0.077 to +0.027), P(≤0) 0.82 |
| Cost / trial (prefix-caching proxy) | $0.0937 | **$0.0260** | **−72%** |
| Cost / trial (harbor `cost_usd`, mean) | $0.1585 | $0.0389 | −75% |
| Agent time / trial (median) | 12.2 min | 6.6 min | −46% |
| Turns (median / mean) | 50 / 55.8 | 40 / 27.8 | |
| Input tokens / trial (median) | 1.50M | 0.44M | −71% |
| Timeouts (2400 s) | 54 | 1 | |
| Score per dollar (score ÷ proxy cost) | 2.1 | 6.7 | ×3.2 |

The score drop is probably real but small: P(diff ≤ 0) = 0.82, and the confidence interval includes 0.
It comes with a 3.6× cost cut.

## Where the score went

| | Trials | Mean reward | Solved |
|---|---|---|---|
| H0, ended within 40 turns | 91 | 0.275 | 21 |
| H0, used more than 40 turns | 109 | 0.131 | 10 |
| H6, ended before turn 40 | 96 | 0.305 | 24 |
| H6, reached turn 40 | 104 | 0.053 | 3 |

- More than half of H0's trials ran past 40 turns, and they were rarely worth it: 10 solves out of 109 trials,
  at the highest cost. H6 cuts those off. Ten H0 solves needed more than 40 turns; H6 recovered 3 solves at
  the cap.
- Trials that finish within the budget score about the same with or without the counter (0.305 vs 0.275).

## Does the model know its budget? Barely, and only at the very end

Every reply of both runs was searched for turn-budget language ("running out of turns", "last turn", "turns
left", "turn 40", "N/40", "many turns", ...) in the reasoning and the visible analysis.

| Replies that mention a turn count, by turn | 1–10 | 11–20 | 21–30 | 31–35 | 36–38 | 39–40 |
|---|---|---|---|---|---|---|
| H0 (no counter) | 0.1% | 0.0% | 0.4% | 0.5% | 0.6% | 0.5% |
| H6 (counter on every update) | 0.1% | 0.4% | 1.1% | 1.3% | 1.2% | **5.8%** |

1. **It does not plan around the budget.** No trial says anything like "I have 40 turns, so I'll do X first"
   at the start. Only 14 of 200 H6 trials ever show budget awareness, and 10 of those first do so at turn 37 or
   later. Example, turn 40 of 088: "I'm on the last turn (40/40). I need to act quickly." All 14 scored 0.
2. **It notices only when it is already stuck.** The typical case is a frozen terminal or a blocked website,
   noticed far too late: "I've used many turns trying to break free... Since this is the last turn, I need to
   make it count" (033, turn 40). "I'm running out of turns. Let me try a different approach" (034, 094, 100,
   turns 39–40).
3. **Awareness does not change how it works.** Long H6 trials and H0 trials past 40 turns, compared at the same
   turn numbers 21–40, look the same: 2.0 commands per reply, ~10 s wait, ~400 output tokens. It does not speed
   up, batch more commands, or reason less as the budget runs out.
4. **The one visible effect is a late "done" gamble.** At turns 39–40, capped H6 trials claim the task is done
   14 times, against 2 times for H0 trials at the same turns. 16 H6 trials first claim done at turns 36–40
   (H0: 7). Ten capped trials claim done on their very last reply; these are mostly wrong (mean reward
   0.13: 095 0.75, 054 0.5, eight scored 0), e.g. "The task is complete!" on 034 at turn 40, which scored 0.
5. **It uses the counter as a clock for its own history.** In 8 trials the model refers back to earlier work by
   turn number ("the xvfb-run Slicer command from Turn 4 is still running in the foreground", 007, repeated 20
   times). That is the counter being used as a timestamp, not as a budget.

In short: Qwen3.6 reads the counter but does not pace itself by it. The cost saving comes from the hard cap; the
counter's only measurable effect is a burst of unverified "done" claims on the final turns, which rarely pay off.

## Per-task movers (checked against all Qwen3.6 runs)

- **109 setup-outlook-account** 3 → 1: a real cap effect. Its H0 solves needed 44–104 turns, and all 5 H6
  attempts stopped at turn 40.
- **043 load-hello-extension** 5 → 2: not the cap (9–15 turns). It falls steadily by run date whatever the
  harness (H0 5, H2 4, H3 3, H5 2, H6 2, Oct 2 → Oct 7), which suggests the task or its environment changed
  over time. Worth a look before reading any harness effect on 043.
- **099 professor-contact-info** 1 → 3: noise. It ranges 0–4 across runs.

## Bottom line

On Qwen3.6, a 40-turn cap keeps most of the score (0.174 vs 0.197) at about a quarter of the cost, the best
accuracy-per-dollar of any Qwen3.6 run so far. The saving comes from the cap stopping long, rarely successful
trials; the counter itself does not make the model pace its work.

## Next

- qwen3.8 H6 is running. qwen3.8's median is 11 turns, so the cap should rarely bind there.
- To separate the cap from the counter, run `max_turns: 40` without the counter (stock terminus-2), or
  H6 at 60 turns, to find where the score/cost curve bends.
- H7–H9 show a richer meter (time, dollars, pace forecast "about N turns fit"). Given the above, look first at
  whether a forecast changes behaviour earlier than a bare counter, not only at the stop.
