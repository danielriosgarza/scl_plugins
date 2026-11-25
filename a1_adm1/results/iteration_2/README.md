# Iteration 2: the setup for run 2 (2026-11-24)

This file records what was changed after iteration 1 and why, the first round of run 2, and
what was changed after that round. Iteration 1 was not tested: the maintainer stopped it before
any test seed was played (`../iteration_1/README.md`).

## Why the setup changed

Run 1 selected a program with a mean of 10 046 m3/d on its evaluation seeds. The benchmark's own
controllers stand between 14 953 and 15 879 on the training seeds. Four causes were found:

1. **The description taught fixed rates.** It gave the agents what three fixed pairs of rates
   score and said that a good pair and a collapse lie close together. All programs of run 1
   settled near those rates. Programs that read no sensor and load slowly score 11 658 with no
   collapse on the same 20 seeds, and single digesters make 13 300 to 14 040
   (`../README.md`, "Programs that read no sensor").
2. **No number of any program was searched.** A coding agent estimated every setpoint, limit
   and step. The benchmark's PI controller had 21 200 training episodes for its ten numbers.
3. **58 % of the dollars bought no program**, because the loop refused answers that held a
   program as a block of code.
4. **The dollar limit was compared only before a round**, so the setup had to stop well below it.

## What changed

| | Run 1 | Run 2 | Why |
|---|---|---|---|
| soft_control_loop | 0.3.0 | 0.4.0 | Tuning, the dollar limit inside a round, reused child processes, and a program given as a block of code |
| Description | Fixed rates | Fixed rates, nine slow rises, how digesters differ, the readings before each of the two ways to collapse, and what the programs of run 1 did | Cause 1 |
| Baseline | `hold_85_0`, `hold_200_100`, `hold_200_110` | `hold_200_100`, `ramp_300_130_3`, `ramp_400_150_3`, `ramp_480_172_1` | The agents read the episodes of slow rises: one that every digester of the baseline bears and two that only some bear |
| Tuning | None | Up to 8 constants of a program, at most 9 candidates x 6 generations on the 16 seeds 31001 to 31016 | Cause 2 |
| Evaluation seeds | 6021 to 6080 | 6021 to 6100 | In run 1 a program failed none of 60 evaluation episodes and 5 of 100 selection episodes |
| Selection seeds | 6081 to 6100, 30001 to 30080 | 30001 to 30100 | The 20 listed seeds went to the evaluation |
| Milestones | The fixed rates, and 5 to 30 % above them, up to 11 982 | The fixed rates (9277), then every 1000 from 10 000 to 17 000 | The marks of run 1 ended below what a slow rise scores without a sensor |
| Engine | Backend `reference`, a child process for every episode | Backend `jax`, child processes that play one episode after another | An episode takes about 11 s of one core in place of 27 s, and tuning plays many episodes |
| Coordinator | `opus` | `fable` | The maintainer's choice |
| Dollar limit | 50, with the setup's stop at 42 | 100, with the setup's stop at 97 | The maintainer's choice. The loop now holds the limit inside a round |

The five coding agents, the reviewer, the skill agent, the three rules, the goal, the
observables, `explore` (5), `patience` (3) and the largest number of attempts (50) are those of
run 1.

Nothing here used a test seed or a validation seed. Every episode behind the new description is a
training episode.

## A second review, before the run (2026-11-24)

The maintainer asked for a critical review of why the loop does not work on this task. It found
three more causes, and the setup changed again before any agent was asked.

5. **The description told the agents what to do, and partly wrongly.** On top of the task it
   carried the setup's own conclusions, such as "load slowly", drawn from programs that all
   raised both pumps together. The programs of the agents followed them. Later experiments
   showed that this picture was wrong: after a start with the sludge pump at zero, the rates
   400 and 130 hold in 100 of 100 digesters, where 11 of 20 collapsed when both pumps rose
   together (`../README.md`, "A start without sludge"). An agent that is told the challenge
   and not a recipe is free to find this.
6. **A coding agent never saw an episode of its own program.** Each program of run 1 was one
   answer. soft_control_loop 0.5.0 can show a coding agent the result of its program and let it
   write the program again (`revise`). It also cuts the summaries where the setup says
   (`phases`).
7. **A coding agent's prompt was about 110 000 tokens**, most of them the summaries of 60
   baseline episodes that differed little. With 0.5.0 the agents read a table of all baseline
   episodes of a condition and the summaries of two.

A check of the plugin itself found nothing wrong: the benchmark's PI controller, written as a
program of the loop, scores what its scorecard says, 14 953.0 on the 100 training seeds
(`../README.md`, "The plugin against the benchmark's own PI controller").

| | After the first review | Now | Why |
|---|---|---|---|
| soft_control_loop | 0.4.0 | 0.5.0 | Causes 6 and 7 |
| Description | The task, nine rises of both pumps together and the conclusions drawn from them | The task's own document in short: the challenge, the pumps, the sensors, the score and the task's trial episodes with fixed rates; then what a program decides and what it may leave to the search | Cause 5, and the maintainer's decision below |
| Baseline | `hold_200_100`, `ramp_300_130_3`, `ramp_400_150_3`, `ramp_480_172_1` | `hold_85_0`, `hold_200_100`, `hold_200_110`, the three pairs of the task's document | The same |
| Phases of a summary | 4 or 8 equal parts | Cut at the decisions 8, 16, 24, 32, 40, 48, 64, 80, 160, 240 and 400 | Cause 6: the start and a collapse take days, and a part of 71 decisions hides both |
| Constants of a tuning | Up to 8 | Up to 10 | A program with two loops of feedback has about ten numbers |
| Revise | | Not set: the maintainer decides, since each revision costs one more answer of a coding agent | Cause 6 |

**The maintainer's decision (2026-11-24).** A first form of this setup told the agents what the
experiments with a start without sludge had shown, and what the designer of the benchmark's PI
controller had chosen before its search. The maintainer rejected both: an agent needs to
understand the challenge, what tools it has and what it may tune, and it is shown no solution.
So the description holds nothing that came from a controller of the benchmark, and none of the
plugin's own findings, which had steered the programs of the agents and were partly wrong. What
the experiments showed stays in `../README.md` as a record.

**The true state of training episodes (the maintainer, 2026-11-24).** "During training it is ok
to see the true state as long as when officially executing the task the state is hidden." Until
then the agents read only what a program reads, late and with errors, and the score. Now the
summaries and tables of training episodes also show the true pH, the true acids, the true methane
outflow, the nitrogen, four groups of microorganisms, the feed that no controller sets, and the
sludge of the episode (`../../README.md`, "What the agents read that no program gets"). The
setup names them as `hidden`, an option of soft_control_loop 0.5.0: they are recorded in every
trace and given to no program. The benchmark allows the same to a training
(README of `mgym-bench`, "Rules for a fair comparison"), and asks that the result be stated
together with this fact.

## What a tuning costs in computer time

In round 1 a program with constants played at most 9 x 6 x 16 = 864 tuning episodes, then 80
evaluation episodes with its declared values and 80 with the tuned ones, and 80 more if the
halfway values were tried. On the 14 cores of the computer that played the run, a tuning took 42
to 45 minutes and an attempt about an hour.

## Run 2, round 1

Run 2 started on 2026-11-24 with soft_control_loop 0.5.0, without `revise`. The coordinator
planned the first milestone, `hold` (a mean of 9277 with no failed episode), in three subgoals:
`start_up` (decisions 1 to 80), `raise_load` (decisions 81 to 400) and `safe_run_out`. Round 1
tried five strategies for `start_up`. Each program played the 80 evaluation episodes of the
seeds 6021 to 6100, and no program failed one.

| Attempt | Coding agent | Strategy | Mean with the declared values | Mean kept | What the search did | Selection seeds |
|---|---|---|---|---|---|---|
| 1 | gemini-4-neon | `feed_follows_methane` | 10 432 | 10 930.0 | Tuned values kept | 11 017.7 |
| 2 | gpt-6.2-astra | `ph_stat_feed` | 9 600 | 9 835.1 | Tuned values kept | Not replayed |
| 3 | gemini-4-carbon | `gas_share_pacer` | 10 118 | 10 638.4 | Tuned values kept | 10 753.5 |
| 4 | claude haiku | `acid_setpoint_ramp` | 10 600.6 | 10 600.6 | Tuned values scored 11 262 and the halfway values 10 909, each with 1 failed episode of 80, so the declared values were kept | 10 682.6 |
| 5 | gemini-4-hydrogen | `retain_then_dilute` | 10 450 | 11 253.4 | Tuned values kept | 11 375.3 |

No program failed an episode of the 100 selection seeds either. Attempt 5 was the best of the
round and met the milestones `hold`, `reach_10000` and `reach_11000`. Attempts 3 and 5 met the
subgoal `start_up`. The search moved the ceiling of attempt 5 for the concentrate from 115 to
124 m3/d, inside its range, and every episode of the program ends with the pumps at 276 and 124.
The coordinator wrote after the round that "the score is limited by the ceiling". The skill
agent admitted one skill, `read_total_acids`. No answer of an agent was refused.

The round took 5 hours and 15 minutes and cost 7.16 dollars, after 2.12 dollars for the plan:
9.28 dollars in all, of which 4.43 were the coordinator's three answers. The computer played
4320 tuning episodes in 3.6 hours, 880 evaluation episodes in 45 minutes and 400 selection
episodes in 19 minutes. The maintainer had the run stopped at the end of round 1, before round 2
asked any agent. The folder of the run and a copy of its checkpoint are kept.

The agents read the true values of training episodes, as the maintainer allowed (above). No
program received one.

## A third review, after round 1 (2026-11-24)

The maintainer had the run stopped after round 1, to find where the loop failed before any more
was spent. Three more causes were found, all in soft_control_loop, and 0.6.0 changes each.

8. **The loop told the agents to keep every range narrow.** Its text on tuning said that each
   constant gets "a range that is safe at both ends". The coordinator passed this on as "each
   range narrow and safe at both ends", and every strategy of its plan named a ceiling for the
   concentrate of "about 100 to 140" m3/d, around the 100 and 110 of the task's trials with
   fixed rates. So the ranges for the ceiling were 108 to 126, 109 to 117, 105 to 118 and 100 to
   140, and every episode of two programs ended at one pair of rates. A program whose feed is
   capped near the rates of the baseline scores near the baseline, whatever it reads.
9. **The search could not leave such a range, and was small.** It changed one constant at a
   time by a tenth of its range: 54 candidates on 16 episodes each, 864 episodes. It gained 2 to
   5 %, all four searches were still rising in their last generation, and the tuned values of
   one program failed 1 of 80 evaluation episodes after passing all 16 tuning episodes, so its
   gain of 6 % was dropped.
10. **An attempt took an hour**, most of it the search, which played one episode at a time in
    each of 14 processes. With `revise`, a coding agent would have read how its program played
    only after that hour, and each revision would have cost another search.

| | Round 1 | Now | Why |
|---|---|---|---|
| soft_control_loop | 0.5.0 | 0.6.0 | Causes 8 to 10 |
| What the agents are told about ranges | Safe at both ends | As wide as the constant keeps its meaning, up to the limits of the pumps where it is a rate. The search and its rank find what is safe. The rates of the task's trials are no limits for a program that reads its sensors | Cause 8 |
| Search of the constants | One constant at a time, at most 9 candidates x 6 generations on 16 seeds | Candidates drawn across all ranges around the best of the generation before: 24 candidates x 6 generations, the first 4 each on 8 of the 48 seeds 31001 to 31048 and the last 2 on all 48, and a final on all 48 | Cause 9, and cause 11 below |
| How a search plays its episodes | One at a time in each process, and new processes for every generation | Up to 16 side by side in each process, in the engine's lanes, and the processes live for the whole search | Cause 10 |
| Revise | Not set | 2, the maintainer's choice. A coding agent reads the episodes of its program with the values it declared and may write it again, before the search | Cause 10 |

Two more things were found while the rebuilt search was checked at no dollars on a program
written by hand (`../README.md`, "The loop's search on the ten numbers of two loops of
feedback"):

11. **Generations on a few episodes end at the edge of a collapse.** A search with every
    generation on 8 of 48 episodes reached a mean of 14 515, and each of its finalists failed 1
    or 2 of the 48 episodes. The loop would have kept none. With `full_generations`, the last
    generations rank on all the tuning seeds, and the same search then gave 14 434 with no
    failed episode on the 100 listed training seeds.
12. **Every generation started its processes again**, and each compiled the model again. The
    processes now live for a whole search and a whole run.

**What a search costs now.** On the 14 cores that play the runs, a generation of 28 candidates
on 8 episodes took 6 to 7.5 minutes and one on all 48 episodes 26 to 32 minutes. The setup's
search, 4 generations of 24 candidates on 8 episodes and 2 on all 48, takes about 75 minutes.
With the evaluations, an attempt takes about an hour and a half, and a round of 5 attempts
about 8 hours.

No test seed and no validation seed was played.
