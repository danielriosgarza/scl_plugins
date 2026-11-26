# Iteration 3: run 3, rounds of ten independent coding agents (2026-11-25 and 26)

This file records what was changed after run 2 and why, the rounds of run 3, what the run
showed to be wrong in the loop, and what is changed for the next round. Rounds 1 and 2 ran
first, and the run ended. The maintainer then let it go on for rounds 3 and 4, with the
changes of the section "What is changed for the next round". The run ended after round 4, on
26 November at 18:08. The files of the run
are beside it: the setup, the result, the log, the selected program and the library of skills.

## Why the loop changed

Run 2 ended with a best program of 13152.8 m3/d on the evaluation seeds. The maintainer asked
why the loop was not working as it was meant to, and eight points followed
(soft_control_loop 0.7.0, `CHANGES.md`):

| | Run 2 | Run 3 |
|---|---|---|
| Coding agents of a round | Asked one after another | All at the same time (`together`) |
| Strategies | One coding agent for each | Two coding agents of different models for each (`writers`) |
| What a coding agent knows of other attempts | The coordinator's guidance from them | Nothing: its subgoal, its strategy and the skills (`independent`) |
| How a program is written | One answer to one prompt | A session of 30 minutes at a desk, where the agent plays its program on 96 experiment episodes (`experiments`, `work`) |
| Review | A reviewer after the attempt | A second coding agent, of another model, plays and critiques the program before each revision (`pairs`) |
| Skills | The skill agent's judgement | Admitted only with a measured effect against a plain piece in its place (`curate`) |
| Search of constants | Every program | The 4 best programs of a round (`tuning.best`) |
| Engine | Children of the engine with all processors each | Each child holds one processor (`pin`) |

The round was tried twice before the run and stopped both times
(`../README.md`, "Two tries of the round of run 3"). The third try ran without an error, and the
maintainer let it go on as run 3. Its folder on the computer of the runs is `runs/test_c`.

## The run

Four rounds, 40 attempts, from 25 November 17:33 to 26 November 18:08, 723.22 dollars. Round 1
ran with a limit of 197 dollars and 10 attempts. The maintainer then raised the limit to 500
dollars as long as the dollars are those of the Gemini models, and the run was resumed with 480
dollars and 50 attempts. It ended after round 2: "the dollar budget has no room for a round like
the last, which cost $183.14". The maintainer then let it go on for two more rounds, with a
ceiling of 800 dollars and then 850, and 40 attempts. Rounds 1 to 3 ran with no error. In round
4 the sign-in of the Gemini tool was lost and later the credits of `gpt-6.2-astra` ran out
(below). The run ended by itself after round 4: "the attempts budget is spent".

All scores are the mean net methane in m3/d on the 80 evaluation seeds 6021 to 6100, with the
failed episodes of 80 behind the bar. The selection replays the 4 best of a round on the 100
seeds 30001 to 30100.

### Round 1 (17:33 to 22:56), milestone `hold`

| Attempt | Model | Subgoal and strategy | First version | Revision 1 | Revision 2 | After the search | Selection |
|---:|---|---|---:|---|---|---|---|
| 4 | gemini-4-carbon | keep_a_margin, graded_alarm_levels | 11568.7 / 0 | 11901.4 / 0 kept | 12130.9 / 0 kept | 13699.3 / 0, second best values | 14107.5 / 1 |
| 5 | gemini-4-hydrogen | hold_the_load, latch_after_climb | 12802.5 / 0 | 11120.0 / 17 dropped | 13201.5 / 0 kept | 13644.0 / 0, tuned | 13842.6 / 2 |
| 10 | gemini-4-hydrogen | find_the_load, marginal_yield_climb | 12565.5 / 0 | 12576.5 / 0 kept | 12583.5 / 0 kept | 12687.3 / 0, tuned | 12923.2 / 1 |
| 8 | gemini-4-carbon | ride_the_start, growth_matched_ramp | 10265.9 / 0 | 11601.7 / 0 kept | 12679.5 / 0 kept | 12679.5 / 0, declared: every searched set failed 1 or 2 of 80 | 13161.8 / 1 |
| 2 | gemini-4-neon | keep_a_margin, trend_guard | 12013.2 / 0 | 11454.5 / 15 dropped | 12403.7 / 1 dropped | not searched | |
| 9 | haiku | find_the_load, marginal_yield_climb | 7878.1 / 0 | 8499.5 / 0 kept | 11995.4 / 0 kept | not searched | |
| 7 | gemini-4-neon | ride_the_start, growth_matched_ramp | 11744.4 / 0 | 12414.1 / 1 dropped | 11979.8 / 0 kept | not searched | |
| 1 | gpt-6.2-astra | keep_a_margin, trend_guard | 12879.7 / 1 | 11824.3 / 0 kept | 11915.1 / 0 kept | not searched | |
| 6 | haiku | hold_the_load, latch_after_climb | 9097.8 / 3 | 11151.6 / 3 kept | 11460.2 / 0 kept | not searched | |
| 3 | haiku | keep_a_margin, graded_alarm_levels | 9406.2 / 0 | 9517.0 / 0 kept | 9617.2 / 0 kept | not searched | |

Selected: attempt 4. Milestones met: `hold` and `reach_10000` to `reach_13000`. 158.83 dollars.

### Round 2 (22:58 to 04:35), milestone `reach_14000`

Attempts 11 to 16 started from the program of attempt 4, attempts 17 to 20 from nothing
(`start: "mix"`).

| Attempt | Model | Subgoal and strategy | Revision 1 | Revision 2 | After the search | Selection |
|---:|---|---|---|---|---|---|
| 11 | gemini-4-neon | margin_at_high_load, delay_compensated_acid_guard | 14894.2 / 0 kept | 15079.2 / 1 dropped | 14894.2 / 0, declared: the search reached 15408.7 on its seeds, and every searched set failed evaluation episodes | **15327.6 / 0** |
| 16 | gemini-4-neon | fast_start, spend_the_initial_reserve | 14543.0 / 0 kept | 14556.4 / 0 kept | 14807.1 / 0, tuned | 15041.6 / 2 |
| 15 | haiku | fast_start, spend_the_initial_reserve | 13767.9 / 0 kept | 13805.0 / 0 kept | 14290.8 / 0, tuned | 14657.8 / 1 |
| 20 | gpt-6.2-astra | load_each_digester, score_rate_hill_climb | 13398.6 / 2 dropped | 13932.7 / 0 kept | 14038.0 / 0, tuned | 14299.4 / 1 |
| 13 | gemini-4-carbon | keep_the_high_load, extrapolated_reserve_hold | 14075.8 / 2 dropped | 14096.2 / 1 dropped | not searched, 13770.1 / 0 | |
| 17 | gemini-4-carbon | load_each_digester, sludge_strength_feedforward | 13878.2 / 1 dropped | kept | not searched, 13757.2 / 0 | |
| 12 | haiku | margin_at_high_load, delay_compensated_acid_guard | 13675.6 dropped | 13699.3 / 0 | not searched, 13699.3 / 0: the program of attempt 4, unchanged | |
| 19 | gemini-4-hydrogen | load_each_digester, score_rate_hill_climb | kept | 13914.7 / 4 dropped | not searched, 13676.2 / 1 | |
| 14 | gemini-4-hydrogen | keep_the_high_load, extrapolated_reserve_hold | kept | 13999.0 / 1 dropped | not searched, 13646.6 / 0 | |
| 18 | haiku | load_each_digester, sludge_strength_feedforward | unchanged | | not searched, 7340.9 / 0 | |

Selected: attempt 11. It is the only finalist of rounds 1 to 3 with no failed selection
episode. Milestone met: `reach_14000`. 183.14 dollars by the loop's count of the round.

### Round 3 (05:10 to 11:09), milestone `reach_15000`

The run was resumed with soft_control_loop `eb97470` and the setup of scl_plugins `0bc40aa`:
800 dollars, 40 attempts, and 48 experiment episodes added at each revision. Attempts 21, 22,
25, 26, 29 and 30 started from the program of attempt 11 with its declared values, the others
from nothing. Every revision session played at its desk, 16 to 88 episodes.

| Attempt | Model | Subgoal and strategy | Revision 1 | Revision 2 | After the search | Selection |
|---:|---|---|---|---|---|---|
| 29 | gpt-6.2-astra | brisk_start, acid_setpoint_start | 15276.4 / 1 kept | 15260.3 / 0 kept | 15479.8 / 0, second | **15980.4 / 1** |
| 30 | gemini-4-neon | brisk_start, acid_setpoint_start | 15291.4 / 0 kept | 15369.4 / 0 kept | 15428.1 / 0, quarter | 15509.7 / 6 |
| 25 | gemini-4-neon | hold_the_edge, asymmetric_deadband_hold | 14988.8 / 1 dropped | 15100.4 / 0 kept | 15200.0 / 0, third | 15502.6 / 2 |
| 24 | haiku | load_by_sludge, inhibition_window_balance | 12180.5 / 0 kept | unchanged | 12860.8 / 0, third | 13248.0 / 0 |
| 22 | gemini-4-carbon | guard_the_edge, joint_ph_acid_margin | 15030.6 / 1 kept | 15115.4 / 1 kept | not searched, 15115.4 / 1 | |
| 21 | haiku | guard_the_edge, joint_ph_acid_margin | unchanged | | not searched, 14710.9 / 3 | |
| 28 | gemini-4-hydrogen | hold_the_edge, zero_drift_hold | 14534.0 / 1 kept | 14565.0 / 1 kept | not searched, 14565.0 / 1 | |
| 26 | gemini-4-carbon | hold_the_edge, asymmetric_deadband_hold | 14797.9 / 2 dropped | 14825.6 / 1 dropped | not searched, 14836.7 / 1 | |
| 23 | gemini-4-hydrogen | load_by_sludge, inhibition_window_balance | 13466.5 / 7 dropped | 14362.9 / 2 dropped | not searched, 14290.7 / 1 | |
| 27 | haiku | hold_the_edge, zero_drift_hold | 7086.4 / 4 dropped | 10301.7 / 0 kept | not searched, 10301.7 / 0 | |

Selected: attempt 29. Milestone met: `reach_15000`. The quarter step of the search was kept for
the first time (attempt 30), and those values failed 6 of the 100 selection episodes. One skill
was admitted, `carb_linked_sludge_floor` from attempt 24: 12860.8 with it and 12245.9 with the
plain piece, both with no failed episode. 204.996 dollars by the loop's count of the round,
207.30 by the usage of the models: `gemini-4-carbon` 126.02, `gemini-4-neon` 38.01,
`gemini-4-hydrogen` 23.71, `gpt-6.2-astra` 8.29, `fable` 6.82, `opus` 4.11, `haiku` 0.34.
551.78 dollars for rounds 1 to 3.

In 11 of 17 revisions of round 3 that were evaluated an episode failed, against 8 of 18 in
round 2. The programs stand closer to the edge: 7 were above 14500, against 2 in round 2. The
fourth place of the search went to attempt 24 with 12860.8, while attempts 22 and 28, with
15115.4 and 14565.0, had one failed episode each.

### Round 4 (from 11:10), milestone `reach_16000`

Before round 4 the run was stopped at its checkpoint and resumed with the setup of `964cb53`:
the ceiling of 850 dollars, which the maintainer chose during round 3, and the coordinator
`opus` with the effort xhigh in place of `fable`, whose weekly allowance of the maintainer was
ending. A copy of the run at the end of round 3 is kept on the computer of the run.

Round 4 started at 11:20, and the six sessions of the Gemini models failed in 0.2 s each: the
file of the Gemini tool's sign-in was gone. A window of that tool, opened on 25 November to
sign it in and never closed, had renewed the sign-in every 55 minutes all night, and the file
was gone between two of its renewals; its log does not show who removed it. The loop gave
those attempts to the next coding agents, of other models. The maintainer chose to stop the
run, signed the tool in again and closed the old window. The run was stopped at 11:29 and
resumed at 11:32 with soft_control_loop `bdc6520`, which has `halt`: a round now stops by
itself when 3 sessions of coding agents fail within 60 s, and a resumed run plays it again.
The ten attempts of the first try are set aside in `interrupted/`. The round was planned
again, with other strategies, and its Gemini sessions ran.

The plan of the restarted round, by `opus` with the effort xhigh, set the milestone
`reach_16000`. Attempts 35 to 40 started from the program of attempt 29 with its declared
values, attempts 31 to 34 from nothing. At 12:40 the workspace of `gpt-6.2-astra` ran out of
credits, and its two running sessions ended with "Your workspace is out of credits". The
maintainer chose not to add credits and to go on without it. A failed astra session left its
program without that revision, and the reviews went to the next model. Fewer than three astra
sessions at a desk failed within 60 s after that (revision 2 of attempt 38 failed in 5 s), so
the halt did not stop the round. The coding agents played 16 to 96 episodes at their desks in each session.

| Attempt | Model | Subgoal and strategy | Revision 1 | Revision 2 | At the search |
|---:|---|---|---|---|---|
| 40 | haiku | guard_the_capacity, buffer_injection_rescue | 15556.3 / 0 kept | 15560.4 / 0 kept | 15560.4 / 0 |
| 37 | gemini-4-hydrogen | hold_the_capacity, net_methane_drift_hold | 15539.3 / 0 kept | unchanged | 15539.3 / 0 |
| 38 | gpt-6.2-astra | hold_the_capacity, net_methane_drift_hold | 15501.0 / 0 kept | failed (out of credits) | 15501.0 / 0 |
| 36 | haiku | hold_the_capacity, probe_and_revert_hold | 15479.8 / 0 kept, the score of 29 | 15352.2 / 1 dropped | 15479.8 / 0 |
| 39 | gemini-4-neon | guard_the_capacity, buffer_injection_rescue | 15275.5 / 1 kept | 15351.1 / 0 kept | 15351.1 / 0, fifth, not searched |
| 35 | gemini-4-carbon | hold_the_capacity, probe_and_revert_hold | 15184.7 / 2 dropped | 15217.0 / 1 kept | 15217.0 / 1, not searched |
| 32 | gemini-4-hydrogen | load_to_capacity, dual_loop_ph_ic | 14556.2 / 5 dropped | 14509.3 / 0 kept | 14509.3 / 0, not searched |
| 34 | gemini-4-neon | swift_start, buffer_charge_first | 13700.4 / 1 kept | 14123.9 / 0 kept | 14123.9 / 0, not searched |
| 31 | gemini-4-carbon | load_to_capacity, dual_loop_ph_ic | 14979.8 / 1 dropped | 15080.2 / 1 dropped | 12226.1 / 0, not searched |
| 33 | haiku | swift_start, buffer_charge_first | 11735.5 / 3 dropped | 9995.8 / 7 dropped | 11884.0 / 1, not searched |

Attempt 29 itself scores 15479.8 / 0 on these 80 seeds. In 10 of the 18 revisions that were
evaluated an episode failed (round 3: 11 of 17), and 11 were kept (round 3: 11 of 17). The
gains on attempt 29 are small, the largest 80.6. Attempt 31, written from nothing, reached
about 15000 in both of its revisions, but one failed episode in each kept both out. The search
began at 14:16 on attempts 40, 37, 38 and 36. 713.85 dollars in all at the end of the
revisions; 162.07 since the end of round 3, the first try included: `gemini-4-carbon` 79.84,
`gemini-4-neon` 42.77, `gemini-4-hydrogen` 30.13, `gpt-6.2-astra` 5.30, `opus` 3.64, `haiku`
0.39.

The search kept the halfway values of attempt 37, 15567.3 / 0 (on the way: tuned 15417.5 / 1,
second 15399.6 / 1, third 15394.7 / 1). For attempts 36, 38 and 40 it found no better values,
and they kept the declared ones.

| Attempt | After the search | Selection |
|---:|---|---|
| 37 | 15567.3 / 0, halfway | **16079.8 / 0** |
| 40 | 15560.4 / 0, declared | 16070.9 / 2 |
| 36 | 15479.8 / 0, declared | 15980.4 / 1 |
| 38 | 15501.0 / 0, declared | 15945.7 / 1 |

Selected: attempt 37, built on attempt 29 by `gemini-4-hydrogen`. Milestones met by the run:
`hold` and `reach_10000` to `reach_15000`; `reach_16000` was not met. Two skills were admitted
and one refused (see "Skills"). 168.145 dollars by the loop's count of the round, 171.43 by the
usage of the models from the end of round 3, the first try included: `gemini-4-carbon` 80.23,
`gemini-4-neon` 44.12, `gemini-4-hydrogen` 30.56, `opus` 10.82, `gpt-6.2-astra` 5.30, `haiku`
0.40. 723.22 dollars for the run. A copy of the run at the end of round 4 is kept on the
computer of the run, beside the one of round 3.

### Skills

Ten skills were admitted and two were refused, each by a measurement on the 80 evaluation
seeds: the program with the skill against the program with a plain piece in its place. The
library ends with the ten.

| Skill | From attempt | With the skill | With the plain piece |
|---|---:|---:|---:|
| `startup_vfa_wave_done` | 5 | 13644.0 / 0 | 9368.6 |
| `capped_share_trend` | 7 | 11979.8 / 0 | 11954.4 |
| `lab_acid_nowcast` | 11 | 14894.2 / 0 | 14403.3 |
| `carbonate_ph_fusion` | 11 | 14894.2 / 0 | 14845.8 |
| `gas_paced_carb_ramp` | 20 | 14038.0 / 0 | 6468.5 / 34 |
| `ic_settling_forecast` | 13 | 13770.1 / 0 | 13464.5 / 3 |
| `sludge_buffer_estimate` | 17 | 13757.2 / 0 | 13078.1 / 2 |
| `carb_linked_sludge_floor` | 24 | 12860.8 / 0 | 12245.9 / 0 |
| `sludge_washout_ceiling` | 34 | 14123.9 / 0 | 8839.5 / 41 |
| `asymmetric_ph_lookahead` | 34 | 14123.9 / 0 | 14084.0 / 2 |
| `settled_digester_gate`, refused | 4 | 13699.3 | 13699.4 |
| `buffer_ratio_carb_cap`, refused | 35 | 15217.0 / 1 | 15217.9 / 1 |

The programs of round 2 used the skills of round 1: `startup_vfa_wave_done` in 7 of them and
`capped_share_trend` in 5.

### Effort

| Model | Dollars at list prices, rounds 1 and 2 | Dollars at list prices, the run |
|---|---:|---:|
| gemini-4-carbon | 204.36 | 410.62 |
| gemini-4-neon | 72.08 | 154.21 |
| gemini-4-hydrogen | 34.28 | 88.54 |
| gpt-6.2-astra | 11.64 | 25.22 |
| opus (skill agent; coordinator in round 4) | 7.26 | 22.20 |
| fable (coordinator in rounds 1 to 3) | 14.20 | 21.02 |
| haiku | 0.67 | 1.41 |
| All | 344.48 | 723.22 |

In the run the Gemini models are 653.37 dollars and the others 69.85; `gemini-4-carbon` alone
is 57 %. The list price of `gemini-4-carbon` has no price for cached input, so its cached input
is counted at the input price: a session of it came to 6 to 20 dollars.

Episodes played in rounds 1 and 2: 4702 experiment, 5840 evaluation, 25056 tuning, 800
selection, 1200 trial of a skill, 116 debug, 60 baseline. In the run: 10960 experiment, 11920
evaluation, 49968 tuning, 1600 selection, 1760 trial of a skill, 230 debug, 60 baseline.

## Like for like with the benchmark, on training seeds

The selected programs were played through the benchmark's own runner on the 100 training seeds
6001 to 6100 (`training_check.json`, `bridge.py --split training`, backend `jax`, microbesGYM
43491a5): the one selected after round 2, and after the run the one selected after round 4 and
attempt 29, the best of round 3. 80 of these seeds are the evaluation seeds of the loop. The four lines of the
benchmark are read from its training scorecards and were not played again. Those were made on
another computer, so the last digits can differ.

| Controller | Net methane | Collapsed of 100 | Start phase | Middle phase | End phase | Run-out |
|---|---:|---:|---:|---:|---:|---:|
| **Selected program of run 3 (attempt 37)** | **15599.9** | 0 | 12624.7 | 16295.3 | 16392.2 | 16403.4 |
| Attempt 29, the best of round 3 | 15516.1 | 0 | 12502.7 | 16223.7 | 16315.1 | 16328.2 |
| Attempt 11, selected after round 2 | 14922.1 | 0 | 10943.6 | 15860.4 | 15973.2 | 15996.6 |
| PI | 14953.0 | 0 | 10850.5 | 15870.8 | 16086.4 | 16119.7 |
| MPC | 15028.6 | 0 | 10977.7 | 16011.4 | 16071.3 | 16178.2 |
| SAC | 15645.5 | 0 | 12714.6 | 16355.9 | 16400.6 | 16418.4 |
| DTQC | 15878.9 | 0 | 13543.3 | 16431.7 | 16493.9 | 16505.7 |

The selected program of the run is 647 above the PI controller and 571 above the MPC, 46 below
SAC and 279 below DTQC. Most of the gap to DTQC is in the start phase, 919; in the middle and
end phases and the run-out it is within 140. After round 2 the program was 31 below the PI
controller. This table is for the maintainer. No agent of the loop is shown it or any number of it.

## What the run showed to be wrong

1. **Revisions were written without a play.** The 96 experiment episodes of a writer covered
   its first version and both revisions, and most writers used them in the first session.
   Seven revisions of round 2 that could not be played raised the mean and failed 1 to 4 of
   the 80 evaluation episodes, and were dropped: among them attempt 11, revision 2, with
   15079.2 and one failed episode.
2. **The search does not see the rare failure.** Its 48 seeds showed no failed episode for
   values that then failed 1 or 2 of the 80 evaluation episodes (attempts 8 and 11), or 2 of
   the 100 selection episodes (attempt 16). About 1 to 2 % of the episodes of a program near
   the limit fail.
3. **A program can come back unchanged.** Attempt 12 handed in the program that it started
   from, and ended as a copy of attempt 4.
4. **One model is most of the dollars.** `gemini-4-carbon` is 59 % of the dollars of rounds 1
   and 2 (57 % of the run). It wrote the selected program of round 1, and none of its programs
   of round 2 reached the search.

Rounds 3 and 4, after the changes below, showed these:

5. **Revisions still fail rare episodes.** With 48 more desk episodes at each revision, an
   episode failed in 11 of 17 evaluated revisions of round 3 and 10 of 18 of round 4. The
   desk plays 16 episodes at a time and does not show a failure of 1 in 80.
6. **A program with one failed episode is kept out, however high it stands.** Attempt 31 of
   round 4, written from nothing, reached 14979.8 and 15080.2 in its revisions, each with one
   failed episode, and both were dropped; attempt 36, with the score of its parent, went to
   the search instead. In round 3 the same kept out attempts 22 and 28.
7. **Gains on one program get small.** Six attempts of round 4 started from attempt 29. The best
   gained 87.5 on the evaluation seeds and 83.8 on the benchmark's training seeds, and four
   of them were handed in unchanged, or in a version never played as it stands, at some
   session (36, 37, 39, 40).
8. **The run depends on the sign-ins and credits of outside tools.** In round 4 the sign-in of
   the Gemini tool was lost, and later the workspace of `gpt-6.2-astra` ran out of credits.
   The first is now caught by `halt`; the second only removed one model from the round.
9. **The gap to the benchmark is the start.** On the training seeds the selected program is
   within 140 of DTQC in the middle and end phases and 919 below it in the start phase.

## What is changed for the next round

- soft_control_loop has `experiments.revision`: every revision adds episodes to the budget of
  the writer's desk (point 1). The setup gives 48.
- The chain of searched values has one more step (point 2). When the tuned values, the next
  best of the search and the values halfway all rank worse on the evaluation seeds than the
  declared ones, the loop now also plays the values a quarter of the way from the declared to
  the tuned ones.
- Points 3 and 4 are open, and so is the rare failure that neither 48 nor 80 seeds show.

## The new step, measured after the run

The quarter step was measured on the two programs whose search was lost, with the loop's own
evaluation, on copies and at no dollars. The run's result is not changed by it: the selected
program of the run is the one with the declared values.

| Program | Declared | Tuned | Second | Third | Halfway | Quarter |
|---|---|---|---|---|---|---|
| Attempt 11, 80 evaluation seeds | 14894.2 / 0 | 15211.2 / 4 | 15246.7 / 1 | 15244.8 / 1 | 15100.5 / 1 | **15084.8 / 0** |
| Attempt 8, 80 evaluation seeds | 12679.5 / 0 | 13474.5 / 2 | 13446.4 / 2 | 13387.1 / 2 | 13311.8 / 1 | 13010.2 / 1 |

For attempt 11 the step would have kept the quarter values. That program has 15536.2 with no
failed episode on the 100 selection seeds, against 15327.6 for the declared values. On the
benchmark's 100 training seeds 6001 to 6100, through the benchmark's runner:

| Controller | Net methane | Collapsed of 100 | Start phase | Middle phase | End phase | Run-out |
|---|---:|---:|---:|---:|---:|---:|
| Attempt 11 with the quarter values | 15113.0 | 0 | 11258.1 | 16031.4 | 16122.1 | 16140.6 |
| Attempt 11 as the run selected it | 14922.1 | 0 | 10943.6 | 15860.4 | 15973.2 | 15996.6 |

This is 160 above the PI controller and 84 above the MPC, and 533 below SAC and 766 below
DTQC. For attempt 8 the quarter values still fail one episode, and the declared ones stay.

## Test

Not run. The test on the seeds 7001 to 7050 waits for the maintainer's word.
