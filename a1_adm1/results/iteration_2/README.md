# Iteration 2: the setup for run 2 (2026-11-24)

Run 2 has not been made yet. This file records what was changed after iteration 1 and why, so
that the run can be read against it. Iteration 1 was not tested: the maintainer stopped it before
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

## What a tuning costs in computer time

A program with constants plays at most 9 x 6 x 16 = 864 tuning episodes, then 80 evaluation
episodes with its declared values and 80 with the tuned ones, and 80 more if the halfway values
are tried. At about 11 s of one core for an episode, that is up to 3.4 hours of one core for an
attempt, or about 15 minutes on 14 cores.

## Run 2

Not made yet. Its result, its attempts, its cost and its test go here.
