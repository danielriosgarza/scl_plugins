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

The ids and units are the task's. The agents that write the programs read the same late and sparse
readings, summarized over the phases of an episode, and after each training episode the task's
score and metrics: `net_methane` (the score), its four phase values, `collapsed`, `failed`, the
lowest pH, the highest acids, and the pH and acids at the end. They read no true value of a
decision.

## How the loop is set up for this task

- **Every episode runs all 568 decisions.** 400 are scored and 168 are the run-out, in which a
  collapse still fails the episode.
- **Failure.** `failed` is true when the digester collapsed or the episode did not run to its end.
  Attempts are ranked by failed episodes first and by mean score second, which is the rule of the
  benchmark's own searches (`"failure": "failed"` in the setup).
- **Rules that no episode can show.** The benchmark checks three rules by reading the code of a
  controller, and the setup gives them to the reviewer as `rules`: no clock, nothing kept outside
  the memory, and the observation as the only source. An attempt that breaks one is barred.
- **Milestones** are marks on the mean score with no failed episode (`checks.py`). The first is
  what the fixed rates 200 and 100 m3/d score on the evaluation seeds, and the others are every
  1000 m3/d from 10 000 to 17 000. Results of other controllers set no mark and are not shown to
  the agents.
- **Baseline.** Four programs that read no sensor: fixed rates, one that raises both pumps
  slowly together, and two that start without sludge, with the sludge pump at 0 while the
  concentrate rises, and then load to a pair of rates. The setup's description tells the agents
  what these and ten more such programs showed: that the start decides and the sludge pump
  endangers it, how digesters differ, and which readings tell a digester that will collapse from
  one that will not (`results/README.md`).
- **What the agents read of an episode.** The summaries cut an episode at the decisions 8, 16,
  24, 32, 40, 48, 64, 80, 160, 240 and 400 (`phases` in the setup), so the first 12 days are
  shown in parts of 2 days. Equal parts of 71 decisions would hide a collapse, which takes days.
- **Knowledge of the benchmark.** The description tells the agents what the designer of the
  task's PI controller chose before any search: which pump follows which reading, in which
  direction, how a loop computes, and the ranges of its ten numbers
  (`results/a1_adm1/loading/pi/README.md` of microbesGYM). It does not tell what any search of
  the benchmark found, and no score of another controller.
- **Tuning.** A program may declare up to 10 of its numbers as constants with a range. The loop
  then searches better values on 16 training episodes that no agent sees, and keeps them if the
  program ranks better with them on the evaluation seeds (`tuning` in the setup, and the README
  of soft_control_loop). No agent is asked, so a search costs computer time and no dollars.
- **Engine.** Every episode of the loop runs on the engine's backend `jax`, in child processes
  that each play one episode after another (`"reuse": true`), so the model is compiled once per
  child. An episode then takes about 11 s of one processor core. On the backend `reference` it
  takes about 27 s, and the scores differ by less than 0.001 m3/d.
- **Reward.** The reward of a decision is its true net methane, the number that the score
  averages. The benchmark provides it for trainings. No program sees it.

## The seeds

microbesGYM has one rule for seeds: train, test, validate.

| Use | Seeds | Split of the benchmark | Who reads the episodes |
|---|---|---|---|
| Baseline | 6001 to 6020 | training | The agents |
| Debug | 6001, 6002 | training | The coding agent |
| Evaluation | 6021 to 6100 | training | The agents |
| Tuning | 31001 to 31016 | training | No agent. The loop searches the constants of a program here |
| Selection | 30001 to 30100 | training | No agent. The loop picks its winner here |
| Test | 7001 to 7050 | development | A person, after a run has ended, with `bridge.py` |
| Validation | 12001 to 12050 | final | Nobody until the maintainer says so. Then once |

The loop starts every episode as a training episode, and the benchmark refuses a development or
a final seed there, so a run cannot play a test or a validation seed. The task lists the training
seeds 6001 to 6100. The seeds from 30001 and from 31001 are further training episodes, which the
benchmark's own trainings also play.

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
uv run scl agents setup.json                      # every agent answers once
uv run scl run setup.json --workdir runs/run_2    # add --resume to continue a stopped run
```

A run asks the agents of the setup through the command-line tools of your own subscriptions. The
agents, the limits of a run (`budgets`, `explore`, `patience`) and the `prices` in `setup.json`
are set by the maintainer for each run. The setup as it is here is that of run 2:

- **Agents.** The coordinator is `fable`. The five coding agents, the reviewer (`sonnet`) and the
  skill agent (`opus`) are those of run 1.
- **Dollars.** The maintainer's limit for run 2 is 100 dollars. The loop asks no agent once the
  dollars have reached `budgets.dollars`, and it starts a round only if there is room for one
  like the last. An answer that is on its way when the limit is reached is still paid, so the
  setup stops at 97.
- **Rounds.** A round tries 5 strategies, one for each coding agent (`explore`). A run has at most
  50 attempts, which is 10 rounds, and ends after 3 rounds in a row without progress (`patience`).
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
    --split development --backend jax --workers 4 --out results/iteration_2/pi_check.json

# 2. The program on the test seeds.
uv run python bridge.py program runs/run_2/attempts/NNN --skills runs/run_2/library \
    --split development --backend jax --workers 4 --out results/iteration_2/test.json
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
| `programs/` | Programs that read no sensor: three fixed pairs of rates from `TASK.md`, nine rises of both pumps together and five starts without sludge. The setup's baseline plays four of them |
| `bridge.py` | A program as a controller of the benchmark's runner, for the test and the validation |
| `results/` | The record: the baseline, every iteration and its test result |
| `tests/` | The adapter and the bridge against the benchmark's code and the numbers of `TASK.md` |

## The plugin that this one replaces

Until 2026-11-24 this repository held `digester/`, the plugin for an earlier form of A1: one pump,
hard limits on pH and acids, and a score of 0 outside them. microbesGYM removed that study on
2026-11-12, so the plugin could not run any more, and its task no longer exists. Its code and the
results of its runs are in the history of this repository, last at commit `63109fa`. It ran
with microbesGYM up to commit `003922b`. Its numbers cannot be compared with anything here.
