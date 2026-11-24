# Iteration 1: run 1 (2026-11-24)

Run 1 is the first training of the loop on `a1_adm1/loading`. It played training seeds only.

| | |
|---|---|
| Setup | `setup.json` in this folder, the plugin's setup at commit `845e3b1` |
| Code | soft_control_loop `939b16d` (0.3.0), microbesGYM `43491a5` |
| Computer | The maintainer's, 14 processor cores |
| Time | 07:11 to 12:07 (Europe/Paris), 4 h 56 min |
| End | The dollar budget is spent: 43.52 dollars at list prices, with the setup's stop at 42 and the maintainer's limit at 50 |
| Size | 3 rounds, 15 attempts |

## Result

**The selected program is attempt 2.** It is in `program/`, byte for byte as the run left it:
`program.py` (SHA-256 `6bd46c61…d1b8a3`) and the skill it imports, `ewma_update.py`
(`c9d9281a…f485a2`).

| | Seeds | Mean score (m3/d) | Failed | Lowest pH |
|---|---|---:|---:|---:|
| Attempt 2, evaluation | 6021 to 6080 | 10046.0 | 0 of 60 | 6.70 |
| Attempt 2, selection | 6081 to 6100 and 30001 to 30080 | 10277.3 | 0 of 100 | |
| Best fixed rates, 200 and 100 m3/d | 6021 to 6080 | 9216.9 | 0 of 60 | 6.64 |

On the evaluation seeds the program is 9.0 % above the best fixed rates of the baseline. On the
selection seeds, which no agent saw, its scores run from 8922.3 (seed 30066) to 11104.7
(seed 30009). The fixed rates were not played on the selection seeds.

The loop picks its winner on the selection seeds, and a program with no failed episode ranks
above every program with one. Attempt 6 has the highest evaluation mean of the run, 11086.3 with
no failed episode, and a selection mean of 10693.4. But it failed 5 of the 100 selection episodes,
so the loop selected attempt 2.

`result.json` is the result as the run printed it.

## The attempts

All scores are the mean net methane in m3/d. "Start" is the attempt whose program the coding
agent was given to start from.

| Attempt | Round | Subgoal | Strategy | Coder | Start | Evaluation mean | Failed of 60 | Lowest pH | Selection mean | Failed of 100 |
|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | 1 | ramp_up | buffer_first_sludge | gpt-6.2-astra | | 6317.3 | 0 | 6.81 | 5205.5 | 0 |
| **2** | 1 | ramp_up | gas_composition_brake | gpt-6.2-astra | | 10046.0 | 0 | 6.70 | **10277.3** | **0** |
| 3 | 1 | ramp_up | cod_balance_observer | haiku | | 10083.9 | 2 | 4.47 | | |
| 4 | 1 | ramp_up | vfa_gated_staircase | haiku | | 9635.1 | 0 | 6.77 | 9863.9 | 0 |
| 5 | 1 | ramp_up | two_stage_acclimation | gpt-6.2-astra | | 10022.0 | 0 | 6.63 | 9157.7 | 0 |
| 6 | 2 | launch_high | alkalinity_ratio_feedforward | gpt-6.2-astra | 2 | 11086.3 | 0 | 6.74 | 10693.4 | 5 |
| 7 | 2 | launch_high | acid_slope_predictor | haiku | 2 | 3263.6 | 34 | 4.96 | | |
| 8 | 2 | launch_high | methane_yield_tracker | haiku | 2 | 10096.1 | 0 | 6.74 | 9337.2 | 0 |
| 9 | 2 | launch_high | sludge_first_launch | gpt-6.2-astra | 2 | 5571.5 | 0 | 6.78 | 4896.2 | 0 |
| 10 | 2 | launch_high | gas_fraction_brake_higher_ceiling | gpt-6.2-astra | 2 | 3080.5 | 0 | 6.89 | 3266.3 | 0 |
| 11 | 3 | launch_peak | ph_slope_predictor_fast_climb | gemini-4-carbon | 6 | -1516.1 | 53 | 4.86 | -2037.7 | 91 |
| 12 | 3 | launch_peak | alkalinity_ratio_setpoint | haiku | 6 | -2483.1 | 58 | 4.93 | -2191.1 | 92 |
| 13 | 3 | launch_peak | buffer_lead_lockstep | gemini-4-hydrogen | 6 | -3501.3 | 60 | 4.81 | -3839.0 | 100 |
| 14 | 3 | launch_peak | two_plateau_probe | gemini-4-neon | 6 | -4978.2 | 60 | 4.48 | | |
| 15 | 3 | launch_peak | cod_yield_matching | gpt-6.2-astra | 6 | -3620.1 | 60 | 4.73 | -3971.6 | 100 |

An empty selection cell means that the attempt was not replayed on the selection seeds: each
round replays its best four. No attempt needed a repair, and the reviewer found no attempt that
breaks a rule.

The fixed milestones `hold`, `plus_5`, `plus_10`, `plus_15` and `plus_20` were met, the first two
by attempt 2 and the others by attempt 6. `plus_25` and `plus_30` stayed open. The library holds
two skills: `ewma_update` from attempt 2 and `slew_limited_rate` from attempt 6.

Round 3 worked on a higher loading and started every program from attempt 6. All five programs
collapsed the digester in most or all episodes.

## The selected program

The program raises both pumps in steps and watches the gas. It smooths the methane fraction of
the gas, the methane pressure, the methane flow and the pH. It raises the carbohydrate pump to
90 m3/d and the sludge pump to 210 m3/d, and when the gas production has settled and the
laboratory acids are low, to 270 m3/d of sludge and 105 to 112 m3/d of carbohydrate. It cuts
the carbohydrate pump by 10 m3/d per decision when the methane fraction falls below a floor,
when the pH is below 6.58, or when a new laboratory result shows acids above its limit.

Read against the three rules of the setup, by the reviewer of the run and again by hand:

- **No clock.** The memory holds the two pump rates, four smoothed readings, the first methane
  fraction, the last eight smoothed fractions, and two flags of its own phases. Nothing counts
  decisions or grows with them. It reads `lab_age`, which is an observation.
- **Own memory.** Everything it keeps is in the memory dict. The skill writes there too.
- **Observation only.** It imports the skill and nothing else, reads no file, and draws no
  random number.

`evaluation_replay.json` is the program of `program/` played again on the 60 evaluation seeds,
through `bridge.py` and the benchmark's own runner, on another computer than the run's. Its mean
is 10046.0182, which differs from the run's evaluation mean by 2 x 10^-8 m3/d, with no failed
episode and the same lowest pH. So the copy in `program/` is the program of the run, and the
bridge scores a program as the loop does.

## Effort

| Kind | Episodes | Seconds of the run |
|---|---:|---:|
| Baseline | 60 | 158.7 |
| Debug | 30 | 481.8 |
| Evaluation | 900 | 2360.2 |
| Trial of a skill | 120 | 304.5 |
| Selection | 1200 | 2862.6 |

That is 2310 training episodes of 568 decisions each. `effort.json` holds the counts.

| Model | Role | Calls | Dollars at list prices |
|---|---|---:|---:|
| gemini-4-neon | Coder | 9 | 17.07 |
| gemini-4-carbon | Coder | 5 | 8.34 |
| opus | Coordinator, skill agent | 28 | 7.21 |
| gpt-6.2-astra | Coder | 7 | 6.09 |
| gemini-4-hydrogen | Coder | 5 | 3.73 |
| sonnet | Reviewer | 15 | 0.97 |
| haiku | Coder | 5 | 0.10 |
| All | | 74 | 43.52 |

`usage.json` holds the tokens. The rounds cost 18.33, 18.63 and 6.56 dollars and took 1 h 57 min,
1 h 55 min and 1 h 2 min.

## What went wrong

**58 % of the dollars bought no program.** In rounds 1 and 2 the three Gemini coders answered
eight times to write a program, and each time twice: 16 calls. Every answer was a block of
Python, once with a sentence before it, and no JSON object, also after the loop asked for one
JSON object only. The loop refused them all, and gpt-6.2-astra or haiku wrote each program again.
These calls cost about 25.45 dollars. In round 3, where the coders were given a program to start
from, the three Gemini coders answered with JSON in one call each.

So the programs of rounds 1 and 2 are the work of two coders, not five.

The setup's stop at 42 dollars held the run under the maintainer's 50: the run ended at 43.52.
After round 2 the run stood at 36.96, and a third round like the first two would have ended
near 55.

## Test

Not run. On 2026-11-24 the maintainer decided to stop here for now, so no test seed was played
for this iteration. When a program is tested, it is played on the seeds 7001 to 7050 with
`bridge.py`, after the benchmark's PI controller has given the benchmark's own number on the
same computer.

## What the run suggests for the next iteration

These are proposals. The maintainer decides them.

1. **Take a program that a coder gives as a block of code.** soft_control_loop 0.3.1 does
   (pull request 12 of that repository). With it, the 16 refused calls of this run would have
   been 8 programs.
2. **Sixty evaluation episodes did not show the risk of attempt 6.** It failed none of them and
   5 of the 100 selection episodes. The coordinator never sees the selection, by design, and
   built round 3 on attempt 6. More evaluation seeds, or a milestone that asks for a margin in
   pH, would show such a program earlier.
3. **`weigh` names the best attempt of a round by its total reward alone.** In round 1 that was
   attempt 3, which had two failed episodes. The ranking, the selection and `top` put failures
   first. `weigh` only decides whether a round made progress, so this changed nothing in run 1.
4. **The dollar limit is checked only before a round.** A limit that is also checked inside a
   round would let the setup hold the maintainer's number itself.

## What is not in this folder

The run's folder with the log, the traces, the map and every attempt is on the maintainer's
computer, in `/home/mcpu/GitHub/scl_run1/scl_plugins/a1_adm1/runs/run_1`. Copies of the progress
lines (`run_1.out`) and of `map.json` are there in `results/iteration_1/`.
