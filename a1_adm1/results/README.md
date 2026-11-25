# Results of the a1_adm1 plugin

This folder is the record of the work on `a1_adm1/loading`: the baseline, every iteration of the
loop with its test result, and what was changed after it. The rule for seeds of microbesGYM asks
that every iteration and its test result stay on record.

All numbers are the task's score, net methane in m3/d, computed by the benchmark's own code. An
episode failed when the digester collapsed (true pH below 6.0 at the end of a decision, the
run-out included) or the episode did not run all its 568 decisions.

## Baseline (2026-11-24)

Three open-loop programs, each holding both pumps at one pair of rates. They were played on
training seeds only, on the backend `reference`, with microbesGYM at commit `43491a5`.
`baseline.csv` has one line per episode with all metrics of the task.

On the baseline seeds 6001 to 6020, which are the seeds of the table of fixed rates in `TASK.md`:

| Program | Sludge, concentrate (m3/d) | Mean score | Failed | Lowest pH | Start | Middle | End | Run-out |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `hold_85_0` | 85, 0 | 1755.3 | 0 of 20 | 7.35 | 1766 | 1754 | 1751 | 1755 |
| `hold_200_100` | 200, 100 | 9330.1 | 0 of 20 | 6.67 | 8747 | 9475 | 9477 | 9480 |
| `hold_200_110` | 200, 110 | 3886.1 | 7 of 20 | 4.10 | 5335 | 3545 | 3502 | 3491 |

The last four columns are the mean net methane of the start phase (days 0 to 20), the middle
phase (days 20 to 60), the end phase (days 60 to 100) and the run-out (days 100 to 142).

`TASK.md` gives 1760, 9330 and 3890 m3/d for these rows, 0, 0 and 7 collapsed episodes, and the
lowest pH 7.35, 6.67 and 4.10. The adapter therefore reproduces the benchmark's own trial
episodes. With 200 and 110 m3/d the seven failed episodes are the seeds 6002, 6004, 6005, 6009,
6012, 6013 and 6016, and the 13 others have a mean of 9704.

On the evaluation seeds 6021 to 6080:

| Program | Mean score | Failed | Lowest pH | Lowest score | Highest score | Start | Middle | End | Run-out |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `hold_200_100` | 9216.9 | 0 of 60 | 6.64 | 8704.1 | 9958.8 | 8653 | 9358 | 9358 | 9361 |

This number is the base of the fixed milestones in `checks.py`: the first mark is 9217 with no
failed episode, and the further marks are 5, 10, 15, 20, 25 and 30 % above it.

Computer time: 60 episodes took 7.5 minutes on 4 processor cores, which is 30 s of one core for
an episode of 568 decisions.

The bridge was checked on four training seeds, 6001 to 6004, with the backend `jax`: it replayed
the benchmark's PI controller file and gave the scores of the benchmark's own training scorecard
of that controller to within 2 x 10^-11 m3/d. No development seed and no final seed was played.

## Programs that read no sensor (2026-11-24, for iteration 2)

Run 1 ended at 10 046 m3/d, a third below the benchmark's own controllers, with programs that
settled near 200 to 270 m3/d of sludge and 90 to 112 of concentrate. The description of run 1
had told the agents only what fixed rates give, and that a good pair of rates and a collapse lie
close together. So nine more programs were played that read no sensor. Each raises the
carbohydrate pump by a fixed step per decision to its end rate, raises the sludge pump in
proportion from 85 m3/d, and then holds both (`programs/ramp_S_C_step`).

They were played on training seeds only, through the loop's runtime, on the backend `jax`, with
microbesGYM at commit `43491a5`. `ramps.csv` has one line per episode with all metrics of the
task. On the baseline seeds 6001 to 6020:

| Program | Sludge, concentrate at the end (m3/d) | Step of the concentrate (m3/d per decision) | Days of the rise | Mean score | Failed | Mean of the others | Start | Middle | End | Run-out |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `ramp_300_130_10` | 300, 130 | 10 | 3 | -7851.3 | 20 of 20 |  | -3934 | -8828 | -8833 | -8850 |
| `ramp_300_130_3` | 300, 130 | 3 | 11 | 11657.9 | 0 of 20 |  | 9161 | 12280 | 12284 | 12287 |
| `ramp_300_130_1` | 300, 130 | 1 | 33 | 10571.8 | 0 of 20 |  | 4985 | 11653 | 12284 | 12287 |
| `ramp_400_150_3` | 400, 150 | 3 | 13 | 219.9 | 13 of 20 | 13050.9 | 6085 | -234 | -2258 | -2275 |
| `ramp_400_150_1` | 400, 150 | 1 | 38 | 9727.9 | 4 of 20 | 12138.5 | 5123 | 11794 | 9965 | 9948 |
| `ramp_480_172_1` | 480, 172 | 1 | 43 | 7309.8 | 8 of 20 | 13451.2 | 5179 | 9568 | 6117 | 6114 |
| `ramp_200_130_3` | 200, 130 | 3 | 11 | 6528.2 | 8 of 20 | 11108.6 | 8673 | 7253 | 4731 | 4705 |
| `ramp_400_130_3` | 400, 130 | 3 | 11 | 390.3 | 11 of 20 | 11811.3 | 4629 | -607 | -732 | -740 |
| `ramp_550_130_3` | 550, 130 | 3 | 11 | -9894.9 | 20 of 20 |  | -1595 | -11937 | -12002 | -12011 |

**The speed of loading decides.** The rates 300 and 130 collapse every digester when they are
reached in 3 days and none when they are reached in 11. The rise in 33 days is safe too but scores
1086 less, because the start phase counts a fifth of the score.

**Digesters differ, and in two ways.** The table below gives the score of every episode, with the
seeds ordered by `hold_85_0`. That score is close to the methane flow before the pumps move, which
a program reads at its first decision.

| Seed | `hold_85_0` | `hold_200_110` | `ramp_300_130_3` | `ramp_400_130_3` | `ramp_200_130_3` | `ramp_400_150_3` | `ramp_400_150_1` | `ramp_480_172_1` |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| 6001 | 1424 |  | 10920 | 11480 | collapsed | collapsed | collapsed | collapsed |
| 6011 | 1468 |  | 11009 | 11588 | collapsed | collapsed | collapsed | collapsed |
| 6017 | 1470 |  | 10971 | 11534 | collapsed | collapsed | collapsed | collapsed |
| 6008 | 1486 |  | 11004 | 11557 | collapsed | 12633 | 11216 | collapsed |
| 6010 | 1584 |  | 11313 | 11935 | 10585 | 13036 | 11591 | 12636 |
| 6006 | 1609 |  | 11354 | 12009 | collapsed | 13079 | 11621 | collapsed |
| 6019 | 1644 |  | 11368 | 12012 | collapsed | 13086 | 11633 | collapsed |
| 6007 | 1656 |  | 11389 | 12070 | collapsed | collapsed | collapsed | collapsed |
| 6018 | 1657 |  | 11432 | collapsed | 10695 | 13157 | 11726 | 12815 |
| 6020 | 1663 |  | 11439 | 12116 | collapsed | 13156 | 11696 | collapsed |
| 6003 | 1687 |  | 11485 | collapsed | 10739 | 13210 | 11785 | 12880 |
| 6014 | 1832 |  | 11814 | collapsed | 10989 | collapsed | 12162 | 13293 |
| 6015 | 1836 |  | 11844 | collapsed | 11013 | collapsed | 12192 | 13305 |
| 6002 | 1940 | collapsed | 12090 | collapsed | 11193 | collapsed | 12477 | 13625 |
| 6004 | 1971 | collapsed | 12136 | collapsed | 11230 | collapsed | 12531 | 13697 |
| 6012 | 2009 | collapsed | 12271 | collapsed | 11319 | collapsed | 12691 | 13874 |
| 6005 | 2013 | collapsed | 12280 | collapsed | 11353 | collapsed | 12656 | 13710 |
| 6016 | 2041 | collapsed | 12304 | collapsed | 11361 | collapsed | 12715 | 13866 |
| 6009 | 2055 | collapsed | 12324 | collapsed | 11406 | collapsed | 12677 | 13674 |
| 6013 | 2060 | collapsed | 12410 | collapsed | 11421 | collapsed | 12849 | 14039 |

- Digesters with a rich sludge, the lower rows, collapse when both pumps rise fast toward much
  sludge. Loaded slowly they bear the most: 13 300 to 14 040 at 480 and 172 m3/d, with a lowest
  pH of 6.83 to 6.90. In the end phase the twelve digesters that bore `ramp_480_172_1` made
  15 560 to 17 250.
- Digesters with a lean sludge, the upper rows, survive the fast rise with much sludge. Most of
  them collapse under a slow rise to much concentrate, between day 40 and day 50. With 400 m3/d
  of sludge in place of 300 for the same concentrate, they make about 600 more and their lowest
  pH is 0.1 higher.
- No pair of rates and no speed is right for every digester.

**Two ways to collapse, and the readings that announce them.** These are the readings as a
program gets them, with the noise and the delay of the task.

- Overload by speed: seed 6013 under `ramp_400_150_3`. The acetate of the laboratory rose with
  every result: 0.2 kgCOD/m3 on day 1, 0.8 on day 3, 1.8 on day 5, 2.7 on day 7, 3.6 on day 9
  and 3.8 on day 11. The inorganic carbon fell from 152 to 73 mM and the pH from 7.5 to 6.7.
  Over day 12 the pH readings averaged 5.6. Under `ramp_480_172_1` the same digester kept its
  acetate below 1.25 and settled at a pH of 6.87.
- Loss of buffer: seed 6001 under `ramp_480_172_1`. The acids stayed between 0.4 and 0.6
  kgCOD/m3 and gave no warning. The inorganic carbon fell steadily: 152 mM on day 1, 124 on
  day 9, 107 on day 17, 85 on day 25, 64 on day 33 and 55 on day 41. The pH fell from 7.45 to
  6.74 over days 32 to 40, and the digester collapsed between day 41 and day 45. Under
  `ramp_300_130_3` the same digester settled at 58 mM and a pH of 6.67 and did not collapse.

In every surviving episode of these programs the lowest true pH was 6.59 or higher, and in every
collapsed one it was between 4.0 and 4.4.

On the evaluation seeds 6021 to 6100:

| Program | Mean score | Failed | Mean of the others | Lowest pH | Lowest score | Highest score | Start | Middle | End | Run-out |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `hold_200_100` | 9277.5 | 0 of 80 |  | 6.64 | 8704.1 | 10239.3 | 8701 | 9421 | 9422 | 9426 |
| `ramp_300_130_3` | 11484.9 | 1 of 80 | 11595.2 | 4.09 | 2765.5 | 12827.9 | 9112 | 12174 | 11982 | 11981 |

The rise to 300 and 130, which no digester of the 20 baseline seeds failed, lost one digester of
80, seed 6040, late in the episode. The fixed rates lost none, and their mean of 9277.5 is the
first mark of the fixed milestones in `checks.py`. The further marks are every 1000 m3/d from
10 000 to 17 000.

Computer time: on the backend `jax`, with child processes that each play one episode after
another, 80 episodes took 6 to 6.6 minutes on 4 processor cores, which is 18 to 20 s of one core
for an episode. The first episode of each child includes about 10 s in which the model is
compiled. On the backend `reference` an episode takes about 27 s. Sixteen episodes of
`hold_200_100` gave the same scores on both backends to within 0.0005 m3/d.

## A start without sludge (2026-11-24, for iteration 2)

All nine programs above raise the sludge pump from the first decision on, and so did every
program of run 1. A review of the loop before run 2 found that this was the wrong picture of the
digester. The benchmark's record of its PI controller reports that this controller holds the
sludge pump at zero during the first days of every training episode, while its concentrate rises
(`results/a1_adm1/loading/pi/README.md` of microbesGYM, "Feedback or a ramp"). So the idea came
from that record. The numbers below come from five programs of this plugin that read no sensor,
on training seeds (`programs/start_F_S_C`, `starts.csv`).

A program `start_F_S_C` lowers the sludge pump to 0, where it is after 3 decisions, and raises the
concentrate by a fixed step per decision to F m3/d. Then it raises both pumps to S and C m3/d and
holds them. It keeps no clock: it reads where its pumps stand, and a flag in its memory says that
the concentrate has reached F. On the baseline seeds 6001 to 6020:

| Program | Concentrate first (m3/d), step | Sludge, concentrate at the end (m3/d) | Mean score | Failed | Mean of the others | Start | Middle | End | Of the others: start | Of the others: middle |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `start_110_300_130` | 110, 5.5 | 300, 130 | 11597.1 | 0 of 20 |  | 8855 | 12281 | 12284 | | |
| `start_110_400_130` | 110, 5.5 | 400, 130 | 12288.7 | 0 of 20 |  | 9228 | 13052 | 13056 | | |
| `start_110_480_150` | 110, 5.5 | 480, 150 | 10104.5 | 5 of 20 | 13974.3 | 9895 | 11432 | 8882 | 10018 | 14960 |
| `start_130_450_150` | 130, 6.5 | 450, 150 | 10982.2 | 4 of 20 | 13956.2 | 10418 | 12173 | 10074 | 10538 | 14808 |
| `start_110_480_172` | 110, 5.5 | 480, 172 | 7023.5 | 8 of 20 | 15344.6 | 10075 | 6407 | 6114 | 10548 | 16535 |

On the evaluation seeds 6021 to 6100, `start_110_400_130` scored 12209.4 with no failed episode
of 80, a lowest pH of 6.69 and scores from 11326 to 13602.

**The start decides, and the sludge pump endangers it.** The rates 400 and 130 collapsed 11 of 20
digesters when both pumps rose together in 11 days (`ramp_400_130_3`). After a start without
sludge they held in all 100 digesters played. With the sludge pump at 0 the liquid of the tank is
replaced by about 190 m3/d in place of 500, so the likely reason is that the microorganisms
multiply on the concentrate faster than they are washed out. This reason was not tested.

**The readings during such a start**, as means over the 20 digesters under `start_110_400_130`,
as a program gets them:

| Day | Sludge pump (m3/d) | Carbohydrate pump (m3/d) | Methane flow (m3/d) | pH | Acids (kgCOD/m3) | Inorganic carbon (mM) |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0 | 30 | 2538 | 7.31 | 0.24 | 155 |
| 3 | 0 | 52 | 3540 | 7.24 | 0.27 | 155 |
| 5 | 0 | 96 | 5527 | 7.10 | 0.78 | 143 |
| 8 | 67 | 113 | 7210 | 7.06 | 1.22 | 116 |
| 10 | 123 | 116 | 7578 | 7.01 | 0.51 | 110 |
| 13 | 207 | 120 | 8085 | 6.92 | 0.35 | 96 |
| 20 | 398 | 130 | 9465 | 6.86 | 0.44 | 83 |
| 30 | 400 | 130 | 9615 | 6.88 | 0.54 | 87 |
| 100 | 400 | 130 | 9671 | 6.89 | 0.55 | 86 |

**What a digester holds under a known load tells what it bears.** At 400 and 130 the 20 digesters
ended at a pH between 6.72 and 7.05. The 8 that ended at 6.72 to 6.80 (the seeds 6001, 6006,
6007, 6008, 6011, 6017, 6019 and 6020) all collapsed under `start_110_480_172`, between day 18
and day 20. The 12 that ended at 6.87 to 7.05 all bore it, with a lowest pH of 6.70 to 6.91 and
scores from 14455 to 15959.

**The readings tell the two kinds apart days before the collapse.** Under `start_110_480_172` all
20 digesters had the same pump rates at every decision. Means of the readings of the 8 that
collapsed and of the 12 that did not:

| Day | pH: collapsed later | pH: did not | Inorganic carbon (mM): collapsed later | Inorganic carbon: did not | Acids (kgCOD/m3): collapsed later | Acids: did not |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 7.02 | 7.06 | 114 | 116 | 1.14 | 1.34 |
| 10 | 6.94 | 7.02 | 104 | 111 | 0.50 | 0.67 |
| 13 | 6.83 | 6.92 | 86 | 99 | 0.37 | 0.46 |
| 16 | 6.73 | 6.88 | 74 | 91 | 0.40 | 0.46 |
| 20 | 5.88 | 6.83 | 59 | 85 | 0.77 | 0.66 |

The acids gave no warning. The pH and the inorganic carbon did, from day 10 on.

**What was not tried.** No program has raised the concentrate faster than by 6.5 m3/d per
decision with the sludge pump at 0, or to a higher first rate than 130, and none has brought the
sludge back faster than by 8 m3/d per decision. The limits of the pumps allow 10 and 34. No
program has loaded a digester beyond 480 and 172.

**These findings are not shown to the agents.** The idea of a start without sludge came from
the record of a controller of the benchmark, and the maintainer decided on 2026-11-24 that an
agent is to understand the challenge, its tools and what it may tune, and is shown no solution.
The same holds for the findings of the section before this one, which were the setup's own and
partly misleading. The description in `setup.json` is now the task's own document in short, and
the baseline of the setup plays the three pairs of fixed rates of that document: `hold_85_0`,
`hold_200_100` and `hold_200_110`. This section and the one before it stay as a record of what
the environment does.

## The plugin against the benchmark's own PI controller (2026-11-24)

The two PI loops of the benchmark's record, with the ten numbers of its `controller.json`, were
written as a program of the loop: 40 lines that read the pH, the four acids, `lab_age` and where
the pumps stand. Played through the loop's runtime on the training seeds 6001 to 6100, on the
backend `jax`, the program scored 14953.0 m3/d with no failed episode. The scorecard of the
benchmark gives 14953.0 for the same seeds, and the 100 scores of the episodes differ from those
of the scorecard by at most 0.0000000001 m3/d.

This shows two things. The episodes of the plugin are the episodes of the benchmark. And nothing
in the form of a program of the loop, the late laboratory values, the missing clock or the limits
of the pumps keeps a program from the level of the benchmark's controllers: what run 1 lacked was
in the programs.

No agent sees this program or its ten numbers. It is in no file of the plugin: the test
`test_the_benchmarks_own_pi_controller_scores_in_the_plugin_what_its_scorecard_says` builds it
from microbesGYM's record when it runs, and compares two training episodes.

## The loop's search on the ten numbers of two loops of feedback (2026-11-25)

After round 1 of run 2 the search of soft_control_loop was rebuilt (`iteration_2/README.md`,
"A third review"). This check asks what the rebuilt search makes of a program whose form is
known to be good and whose numbers are bad. It asks no agent and costs no dollars.

`programs/search_check` has the form of the benchmark's PI controller. Its ten numbers are
declared at the middle of the ranges of the benchmark's own search, and with them every one of
the 48 tuning episodes collapses. The search plays training episodes only, in the engine's
lanes.

| Stage | Episodes | Result |
|---|---|---|
| 12 generations of 30 candidates, each on 8 of the 48 tuning episodes | 2880 | The best candidate of a generation rose from 7715 to between 13 790 and 16 369 from generation 6 on |
| Final on all 48 tuning episodes | 240 | A mean of 14 515, but each of the five finalists failed 1 or 2 of the 48 episodes |
| 2 generations of 20 candidates on all 48 tuning episodes | 1920 | No clean candidate at the start. 1 of 20 in the first generation and 6 of 20 in the second failed no episode. The best: 14 394 |
| The values found, on the training seeds 6001 to 6100, each episode alone | 100 | **14 434.2, no failed episode** |

The benchmark's PI controller scores 14 953.0 on the same 100 seeds, after a search of 21 200
training episodes. The best program of round 1 of run 2 scored 11 253 on its evaluation seeds.

What the check showed:

- The search finds the level of the benchmark's controller in a quarter of the episodes, from
  numbers that collapse every digester.
- Generations on 8 episodes cannot see a collapse that 1 episode in 48 has, and the best
  candidate on 8 episodes is the one closest to it. So the first form of the search ended with
  no finalist that the loop could keep. With `full_generations`, the last generations rank on
  all the tuning seeds, and the search moves to where no episode fails. The benchmark's own
  search ends in the same way, with 4 generations on all 100 training seeds.
- The first two stages ran here before `full_generations` existed, and the third stage
  continued them by hand with the same rule.

No agent sees this program, its form or these numbers. No test seed and no validation seed was
played.

## Prices (2026-11-24)

The loop counts the dollars of a run from list prices, in dollars per million tokens. These are
the prices of the providers on 2026-11-24 for the models of run 1 and run 2, as `setup.json` holds
them:

| Model in the setup | Priced as | Input | Output | Cached input | Source |
|---|---|---:|---:|---:|---|
| `fable` | Claude Fable 5.2, from run 2 | 8.00 | 40.00 | 0.20 | The model reference of Claude Code's own documentation; not read from the pricing page |
| `opus` | Claude Opus 5.5 | 4.00 | 20.00 | 0.20 | [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| `sonnet` | Claude Sonnet 5.5 | 2.00 | 10.00 | 0.10 | the same page |
| `haiku` | Claude Haiku 5.5, prompts up to 100,000 tokens | 0.10 | 0.50 | 0.01 | the same page |
| `gpt-6.2-astra` | GPT-6.2 Astra, standard | 8.00 | 40.00 | 0.40 | [OpenAI pricing](https://developers.openai.com/api/docs/pricing) |
| `gemini-4-neon` | Gemini 4 Neon, global | 3.00 | 15.00 | 0.15 | [Google Cloud pricing](https://cloud.google.com/model-garden/pricing) |
| `gemini-4-carbon` | Gemini 4 Carbon, global, until 2026-11-30 | 2.00 | 10.00 | none listed | the same page |
| `gemini-4-hydrogen` | Gemini 4 Hydrogen, global | 1.50 | 7.50 | 0.075 | the same page |

What the dollars of a run do not hold:

- Gemini 4 Carbon costs 4.00 and 20.00 from 2026-12-01. A run after that date needs the new
  prices.
- Claude Haiku 5.5 costs 0.50 and 2.50 for a prompt of more than 100,000 tokens. The prompts of
  a coding agent are far shorter.
- Claude Code writes part of a prompt to the cache at 1.25 times the input price. The loop counts
  those tokens at the input price.
- The Antigravity tool reports no cached tokens, so all input of the three Gemini models is
  counted at the input price.
- `opus`, `sonnet` and `haiku` are names that Claude Code resolves to a model. The prices
  here hold only if they resolve to Opus 5.5, Sonnet 5.5 and Haiku 5.5 on the computer of the run.
  Before run 1 the tool's own answers named `claude-opus-5-5`, `claude-sonnet-5-5` and
  `claude-haiku-5-5` there (Claude Code 2.1.322).
- `fable` is new in run 2. Its price holds only if the name resolves to Claude Fable 5.2 on the
  computer of the run. `uv run scl agents setup.json` shows before a run whether the agent
  answers.

The dollars measure use at list prices. A subscription charges differently.

## Iterations

Each iteration gets a folder `iteration_N/` with the setup that trained it, the result of the
run, the selected program, its test result on the seeds 7001 to 7050 from `bridge.py`, and a note
on what was changed for the next iteration and why.

| Iteration | Run | Selected program | Selection seeds: mean score, failed | Test seeds: mean score, failed | Dollars at list prices |
|---|---|---|---|---|---:|
| [1](iteration_1/README.md) | Run 1, 2026-11-24, 3 rounds, 15 attempts | Attempt 2, gpt-6.2-astra | 10277.3, 0 of 100 | Not run, by the maintainer's decision | 43.52 |
