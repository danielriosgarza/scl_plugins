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

The description in `setup.json` gives the agents these findings. The baseline of the setup plays
`hold_200_100`, `ramp_300_130_3`, `ramp_400_150_3` and `ramp_480_172_1`.

Computer time: on the backend `jax`, with child processes that each play one episode after
another, 80 episodes took 6 to 6.6 minutes on 4 processor cores, which is 18 to 20 s of one core
for an episode. The first episode of each child includes about 10 s in which the model is
compiled. On the backend `reference` an episode takes about 27 s. Sixteen episodes of
`hold_200_100` gave the same scores on both backends to within 0.0005 m3/d.

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
