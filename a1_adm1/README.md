# a1_adm1: feeding an anaerobic digester with two pumps

This plugin lets [soft_control_loop](https://github.com/danielriosgarza/soft_control_loop) grow
control programs for the task `loading` of the environment `a1_adm1` of
[microbesGYM](https://github.com/danielriosgarza/microbesGYM_v2). The folder has the name that
microbesGYM gives the environment, and its setup names the task.

In the task a controller sets the rates of a sludge pump and of a carbohydrate pump every 6 hours
for 142 days. More feed gives more methane, until the acids that the feed turns into are more than
the digester bears. Then the pH falls, the methane stops, and the digester does not recover. The
task's own description is `envs/a1_adm1/tasks/loading/TASK.md` in the microbesGYM repository.

A program of the loop is a controller of the benchmark. It gets what the task gives a controller,
and the benchmark's own code scores it.

## What a program gets

| | |
|---|---|
| Action | `[sludge_rate, carbohydrate_rate]` in m3/d, from 0 to 1000 and from 0 to 300 |
| Read at every decision | `ch4_flow`, `co2_flow`, `ch4_pressure`, `ph` |
| Laboratory values | `vfa_s_va`, `vfa_s_bu`, `vfa_s_pro`, `vfa_s_ac`, `inorganic_carbon`: sampled at every 4th decision, known 4 decisions later, so `None` during the first day and 4 to 7 decisions old afterwards. `lab_age` is that age |
| Its own pumps | `sludge_rate`, `carbohydrate_rate`: where each pump stands after the limit on its change |
| Not given | The day, the number of decisions, the length of an episode, the seed, every true value |

The ids and units are the task's.

## What the agents read that no program gets

Every episode of the loop is a training episode. The benchmark lets a training read the true
state of the simulation and the values that are drawn for an episode, as long as the controller
reads only its sensors (README of `mgym-bench`, "Rules for a fair comparison"), and the maintainer
allowed the same for the agents of this loop on 2026-11-24. So the agents read, in the summaries
and the tables of training episodes, beside the readings that the program had and the task's
score and metrics:

| Key | What it is |
|---|---|
| `true_ph` | The true pH of the liquid, without the error of the probe |
| `true_acids` | The true total of the four acids, kgCOD/m3, without the delay and the error of the laboratory |
| `true_ch4_flow` | The true methane outflow at atmospheric pressure, m3/d |
| `true_nitrogen` | The inorganic nitrogen in the liquid, mM |
| `true_x_su`, `true_x_pro`, `true_x_ac`, `true_x_h2` | The microorganisms that take up the sugars and propionate, and the methanogens that use acetate and hydrogen, kgCOD/m3 |
| `true_incoming_sludge` | The rate of the feed that no controller sets, m3/d |
| `sludge_carbohydrates`, `sludge_proteins`, `sludge_lipids` | The sludge of the episode as multiples of the nominal recipe, once per episode |

The setup names these keys as `hidden`: the loop records them in every trace and gives them to
no program, and a program that reads one fails at its first decision. `bridge.py`, which plays
the test and the validation seeds, has no true value at all. A result of the loop is to be
stated together with this fact, as the benchmark asks of a training that reads true values.

## How the loop is set up for this task

- **Every episode runs all 568 decisions.** 400 are scored and 168 are the run-out, in which a
  collapse still fails the episode.
- **Failure.** `failed` is true when the digester collapsed or the episode did not run to its end.
  Attempts are ranked by failed episodes first and by mean score second, which is the rule of the
  benchmark's own searches (`"failure": "failed"` in the setup).
- **Rules that no episode can show.** The benchmark checks three rules by reading the code of a
  controller, and the setup gives them as `rules` to the coding agent that judges an attempt: no
  clock, nothing kept outside the memory, and the observation as the only source. An attempt
  that breaks one is barred.
- **Milestones** are marks on the mean score with no failed episode (`checks.py`). The first is
  what the fixed rates 200 and 100 m3/d score on the evaluation seeds, and the others are every
  1000 m3/d from 10 000 to 50 000, a ladder that the maintainer fixed. It ends far above what
  any program has scored, so a run always has a mark ahead. Results of other controllers set no
  mark and are not shown to the agents.
- **What the agents are told.** The challenge, the tools and what may be tuned, and nothing
  else. The description in the setup is the task's own document in short: the digester, the aim,
  the two pumps and their limits, the three feeds, what differs between episodes, the nine
  sensors with their timing and errors, the episode, the score, and what the task's own trial
  episodes with fixed rates show. It then says that everything between the readings and the two
  rates is the program's choice, and that the numbers which the strategy does not fix are
  declared as constants and searched by the loop. It shows no controller of the benchmark, no
  design, no setting and no result of one, and no finding of the plugin's own experiments.
- **Baseline.** The three pairs of fixed rates of the task's document: the pumps left at 85 and
  0 m3/d, at 200 and 100, and at 200 and 110.
- **What the agents read of an episode.** The summaries cut an episode at the decisions 8, 16,
  24, 32, 40, 48, 64, 80, 160, 240 and 400 (`phases` in the setup), so the first 12 days are
  shown in parts of 2 days. Equal parts of 71 decisions would hide a collapse, which takes days.
- **Experiments.** A coding agent works at a desk, a folder of its own, and plays its program
  there before it hands it in: 96 episodes for one attempt, at most 16 in one play, on 32
  training seeds that nothing else uses (`experiments` in the setup). A play of 16 episodes
  takes a little over 2 minutes. The agent reads the mean score, the failed episodes, a table
  of the episodes and, on disk, every step of every episode with the true values of the section
  above. The repairs and the revisions of an attempt share its 96 episodes. A coding agent
  that writes a critique has a desk and 96 episodes of its own.
- **Tuning.** A program may declare up to 10 of its numbers as constants with a range. For the
  4 best programs of a round (`"best": 4`), as they stand with the values that they declare, the
  loop then searches the values on 48 training episodes that no agent sees: 6 generations of 24
  candidates, each drawn across the whole of its ranges around the best of the generation
  before. The first 4 generations each rank on 8 of the 48 episodes. The last 2 rank on all 48,
  because 8 episodes cannot show a collapse that 1 digester in 48 has, and a final on all 48
  decides. The loop keeps the values of the search if the program ranks better with them on
  the evaluation seeds (`tuning` in the setup, and the README of soft_control_loop). No agent
  is asked, so a search costs computer time and no dollars: about 75 minutes on the 14 cores
  that play the runs. The description tells a coding agent that the range of a constant is as
  wide as the constant keeps its meaning, because the search and not the range finds which
  values are safe.
- **Engine.** Every episode of the loop runs on the engine's backend `jax`, in child processes
  that each play one episode after another (`"reuse": true`), so the model is compiled once per
  child. An episode then takes about 11 s of one processor core. On the backend `reference` it
  takes about 27 s, and the scores differ by less than 0.001 m3/d.
  Every child holds itself to one processor (`"pin": true`). Without that a child of the
  engine starts 98 threads on the 14 processors of the computer of the runs. Measured there on
  2026-11-25 with about 9.5 processors free: 14 children played 16.9 episodes a minute without
  `pin` and 33.8 with it, and in batches of 16 lanes 56.7 and 83.6, with the same scores to
  every digit. `OMP_NUM_THREADS=1` and the flags of XLA for one thread changed no time.
- **Lanes.** A search plays the episodes of a candidate side by side, 16 in one call of the
  engine (`Loading.lanes`, and `"lanes": 16` in the setup). On 4 cores that is 1.5 s for an
  episode in place of 4.4 s. Lane 0 plays the episode of its seed, to 12 digits the same as
  alone. Every other lane plays another training episode, which the engine draws from the seed
  and the number of the lane. So a tuning seed stands for a fixed group of training episodes,
  the same for every candidate. The benchmark's own trainings play their episodes this way
  (`BatchEpisodes`). Lanes refuse a development or a final seed, as a single episode does.
- **Reward.** The reward of a decision is its true net methane, the number that the score
  averages. The benchmark provides it for trainings. No program sees it.

## The seeds

microbesGYM has one rule for seeds: train, test, validate.

| Use | Seeds | Split of the benchmark | Who reads the episodes |
|---|---|---|---|
| Baseline | 6001 to 6020 | training | The agents |
| Debug | 6001, 6002 | training | The coding agent |
| Evaluation | 6021 to 6100 | training | The agents |
| Experiments | 32001 to 32032 | training | The coding agent of an attempt, at its desk |
| Tuning | 31001 to 31048 | training | No agent. The loop searches the constants of a program here |
| Selection | 30001 to 30100 | training | No agent. The loop picks its winner here |
| Test | 7001 to 7050 | development | A person, after a run has ended, with `bridge.py` |
| Validation | 12001 to 12050 | final | Nobody until the maintainer says so. Then once |

The loop starts every episode as a training episode, and the benchmark refuses a development or
a final seed there, so a run cannot play a test or a validation seed. The task lists the training
seeds 6001 to 6100. The seeds from 30001, from 31001 and from 32001 are further training
episodes, which the benchmark's own trainings also play.

**Nothing may play a seed from 12001 to 12050 before the one validation run.** No iteration is
allowed after that run, and nothing is changed because of it.

## Install and check

The plugin expects the three repositories side by side:

```
soft_control_loop/
microbesGYM_v2/
scl_plugins/a1_adm1/
```

```bash
cd scl_plugins/a1_adm1
uv sync
uv run pytest -q -m "not slow"     # a few seconds
uv run pytest -q                   # also plays whole episodes, a few minutes
uv run scl check setup.json
```

The tests compare the adapter with the numbers that `TASK.md` publishes for fixed rates. One test
holds the hash of the task document. It fails when the task, its model or its seeds change in
microbesGYM, which is the sign to read `TASK.md` again before anything else is run. The plugin was
tested with microbesGYM at commit `43491a5`.

## Train

```bash
uv run scl agents setup.json                      # every agent answers once, and works once at a desk
uv run scl run setup.json --workdir runs/run_3    # add --resume to continue a stopped run
```

A run asks the agents of the setup through the command-line tools of your own subscriptions. The
agents, the limits of a run (`budgets`, `explore`, `patience`) and the `prices` in `setup.json`
are set by the maintainer for each run. The setup as it is here is that of run 3, whose round is
described in the README of soft_control_loop under "A round of independent coders":

- **Agents.** The coordinator is `fable` and the skill agent is `opus`. A round has 21 coding
  agents, which the maintainer chose on 2026-11-25: 2 of `gpt-6.2-astra`, 6 of `haiku` and 13 of
  Gemini (5 of `gemini-4-neon`, 4 of `gemini-4-carbon`, 4 of `gemini-4-hydrogen`). 10 of them
  write a program and 11 review one. There is no reviewer of its own: a coding agent of another
  model critiques a program before each revision, and one judges the attempt at its end.
- **Rounds.** A round tries 5 strategies, and 2 coding agents of different models write each, so
  a round has 10 attempts (`explore` and `writers`). All are worked on at the same time. The
  coordinator chooses the strategies from any open subgoal and writes no guidance, and a coding
  agent reads its subgoal, its strategy and the skills, and nothing of another attempt. A
  program may be revised 2 times. The maintainer chose on 2026-11-25 to test the new round
  once, with 10 attempts in the setup. When that round had run without an error he let the
  same run go on, for a second round and then for two more, so the setup now has 40
  attempts, which are four rounds. A run ends after 3 rounds in a row without progress
  (`patience`).
- **Skills.** The skill agent is offered every program of a round that broke no rule, the best
  first. A skill enters the library only if the program is clearly worse without it, and its
  measured effect is kept with it (`curate`).
- **Where a coding agent works.** Its tool runs confined to its desk. `work` in the setup names
  what the tool needs beside the desk: its own program to read, and of the folder of its sign-in
  only the named entries, so that no coding agent reads the sessions and the history that the
  tools keep there. A session at a desk may take 30 minutes, for every model: an attempt may
  play 96 episodes, which is 6 plays of 16 at about 2.4 minutes each, and longer when many
  desks play at once. Every result of a play tells the agent the minutes that it has left.
  Each revision adds 48 episodes (`experiments.revision`): in round 2 most writers had used
  their 96 in the first session, and seven revisions that were not played failed episodes.
- **Dollars.** The loop asks no agent once the dollars have reached `budgets.dollars`, and it
  starts a round only if there is room for one like the last. An answer that is on its way when
  the limit is reached is still paid, and with a round that works on all its attempts at once,
  up to 21 sessions can be on their way. The maintainer's limit for the test of the new round
  was 200 dollars, so the setup stopped at 197. Two tries of the test were stopped and had
  used 44.61, which the limit does not include. The round of the third try came to about 150
  dollars, of which about 140 were for the Gemini models, and the maintainer then raised the
  limit to 500 dollars as long as the dollars are those of the Gemini models, and the setup
  stopped at 480. Two rounds came to 344.48 dollars. For two more rounds the setup has a
  ceiling of 800 dollars, which the maintainer raised to 850 during round 3: the rounds cost
  159, 184 and about 209 dollars, and a round that the limit cuts off counts for nothing. One
  session at a desk cost 3.3 dollars for `gpt-6.2-astra`, 0.03
  for `haiku`, 2.2 for `gemini-4-neon`, 1.3 for `gemini-4-hydrogen` and 5 to 7 for
  `gemini-4-carbon`, whose list price has no cached price. The tokens of a session that is
  stopped at its time are counted from the turns that its tool had printed; the log says
  `uncounted` when it had printed none, and the output is kept in the folder `stopped` of the
  attempt.
- **Prices** are the list prices of the providers on 2026-11-24, in dollars per million tokens of
  input, output and input read from the provider's cache. `results/README.md` gives the table
  with its sources. The dollars measure use at these prices. They are not what a subscription
  charges, and the limits of a subscription still apply.

## Test and validate

After a run has ended, read the selected program against the three rules. Then play it through
the benchmark's own runner:

```bash
# 1. The computer gives the benchmark's numbers: this must print a mean of 14834.3.
uv run python bridge.py controller ../../microbesGYM_v2/results/a1_adm1/loading/pi/controller.json \
    --split development --backend jax --workers 4 --out results/iteration_3/pi_check.json

# 2. The program on the test seeds.
uv run python bridge.py program runs/run_3/attempts/NNN --skills runs/run_3/library \
    --split development --backend jax --workers 4 --out results/iteration_3/test.json
```

What the test shows may change the setup, and the loop then trains again. Every iteration and its
test result stay in `results/`. When the maintainer says that the iterations are done, the
finished program is played once on the final seeds, with `--split final --final`. The bridge
refuses to write over the result of that run.

## Files

| Path | What it holds |
|---|---|
| `a1_adm1.py` | The adapter: the benchmark's `Episode` as an environment of the loop |
| `setup.json` | The goal, what the agents are told about the task, the observables, the seeds, the failure, the rules, the agents and the limits |
| `checks.py` | The marks of the fixed milestones |
| `programs/` | Programs that read no sensor: three fixed pairs of rates from `TASK.md`, nine rises of both pumps together and five starts without sludge. The setup's baseline plays the three fixed pairs; the others are a record of experiments (`results/README.md`) and are not shown to the agents. `programs/search_check` is a check of the loop's search, written by hand, with ten numbers left to the search (its docstring, and `scl tune`); it is not shown to the agents either |
| `bridge.py` | A program as a controller of the benchmark's runner, for the test and the validation |
| `results/` | The record: the baseline, every iteration and its test result |
| `tests/` | The adapter and the bridge against the benchmark's code and the numbers of `TASK.md` |

## The plugin that this one replaces

Until 2026-11-24 this repository held `digester/`, the plugin for an earlier form of A1: one pump,
hard limits on pH and acids, and a score of 0 outside them. microbesGYM removed that study on
2026-11-12, so the plugin could not run any more, and its task no longer exists. Its code and the
results of its runs are in the history of this repository, last at commit `63109fa`. It ran
with microbesGYM up to commit `003922b`. Its numbers cannot be compared with anything here.
