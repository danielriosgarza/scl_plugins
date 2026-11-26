# Iteration 3: run 3, rounds of ten independent coding agents (2026-11-25 and 26)

This file records what was changed after run 2 and why, the two rounds of run 3, what the run
showed to be wrong in the loop, and what is changed for the next round. The files of the run
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

Two rounds, 20 attempts, 11 hours, no error, no session stopped at its time, no uncounted
session. Round 1 ran with a limit of 197 dollars and 10 attempts. The maintainer then raised the
limit to 500 dollars as long as the dollars are those of the Gemini models, and the run was
resumed with 480 dollars and 50 attempts. It ended by itself: "the dollar budget has no room for
a round like the last, which cost $183.14".

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

Selected: attempt 11, the selected program of the run. It is the only finalist of the run with
no failed selection episode. Milestone met: `reach_14000`. 183.14 dollars by the loop's count
of the round.

### Skills

Seven skills were admitted and one was refused, each by a measurement on the 80 evaluation
seeds: the program with the skill against the program with a plain piece in its place.

| Skill | From attempt | With the skill | With the plain piece |
|---|---:|---:|---:|
| `startup_vfa_wave_done` | 5 | 13644.0 / 0 | 9368.6 |
| `capped_share_trend` | 7 | 11979.8 / 0 | 11954.4 |
| `lab_acid_nowcast` | 11 | 14894.2 / 0 | 14403.3 |
| `carbonate_ph_fusion` | 11 | 14894.2 / 0 | 14845.8 |
| `gas_paced_carb_ramp` | 20 | 14038.0 / 0 | 6468.5 / 34 |
| `ic_settling_forecast` | 13 | 13770.1 / 0 | 13464.5 / 3 |
| `sludge_buffer_estimate` | 17 | 13757.2 / 0 | 13078.1 / 2 |
| `settled_digester_gate`, refused | 4 | 13699.3 | 13699.4 |

The programs of round 2 used the skills of round 1: `startup_vfa_wave_done` in 7 of them and
`capped_share_trend` in 5.

### Effort

| Model | Dollars at list prices |
|---|---:|
| gemini-4-carbon | 204.36 |
| gemini-4-neon | 72.08 |
| gemini-4-hydrogen | 34.28 |
| fable (coordinator) | 14.20 |
| gpt-6.2-astra | 11.64 |
| opus (skill agent) | 7.26 |
| haiku | 0.67 |
| All | 344.48 |

The Gemini models are 310.72 dollars and the others 33.76. The list price of
`gemini-4-carbon` has no price for cached input, so its cached input is counted at the input
price: a session of it came to 6 to 13.5 dollars.

Episodes played: 4702 experiment, 5840 evaluation, 25056 tuning, 800 selection, 1200 trial of a
skill, 116 debug, 60 baseline.

## Like for like with the benchmark, on training seeds

The selected program was played through the benchmark's own runner on the 100 training seeds
6001 to 6100 (`training_check.json`, `bridge.py --split training`, backend `jax`, microbesGYM
43491a5). 80 of these seeds are the evaluation seeds of the loop. The four lines of the
benchmark are read from its training scorecards and were not played again. Those were made on
another computer, so the last digits can differ.

| Controller | Net methane | Collapsed of 100 | Start phase | Middle phase | End phase | Run-out |
|---|---:|---:|---:|---:|---:|---:|
| Selected program of run 3 | 14922.1 | 0 | 10943.6 | 15860.4 | 15973.2 | 15996.6 |
| PI | 14953.0 | 0 | 10850.5 | 15870.8 | 16086.4 | 16119.7 |
| MPC | 15028.6 | 0 | 10977.7 | 16011.4 | 16071.3 | 16178.2 |
| SAC | 15645.5 | 0 | 12714.6 | 16355.9 | 16400.6 | 16418.4 |
| DTQC | 15878.9 | 0 | 13543.3 | 16431.7 | 16493.9 | 16505.7 |

The program is 31 below the PI controller and 107 below the MPC. It is not above the benchmark.
This table is for the maintainer. No agent of the loop is shown it or any number of it.

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
4. **One model is most of the dollars.** `gemini-4-carbon` is 59 % of the dollars. It wrote the
   selected program of round 1, and none of its programs of round 2 reached the search.

## What is changed for the next round

- soft_control_loop has `experiments.revision`: every revision adds episodes to the budget of
  the writer's desk (point 1).
- Points 2 to 4 are open.

## Test

Not run. The test on the seeds 7001 to 7050 waits for the maintainer's word.
