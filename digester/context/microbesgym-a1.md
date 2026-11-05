# microbesGYM's A1 digester: the calls a wrapper needs

These calls were run and checked on mgym-engine 0.1.0 and mgym-studies 0.4.0 (Python 3.12). Both
packages are installed by the plugin's pyproject.toml. The study's name is "control_a1_loading".

## Building the environment

```python
from mgym_engine.rl import GymEnv
from mgym_studies.control import documents
from mgym_studies.control.baselines import Slots

STUDY = "control_a1_loading"
payload = documents.experiment_payload(STUDY)          # the aligned experiment, a dict
slots = Slots.from_experiment(payload)                 # decodes observations, encodes actions
env = GymEnv(payload, documents.load_model_document(STUDY), backend="reference")
```

Build the GymEnv once, in the wrapper's `__init__`; `reset` starts a new episode on it. Pass the
parsed model document as above: a plain dict raises AttributeError.

## Reset

```python
vector, info = env.reset(seed=seed, options={"split": split, "evaluation_mode": "stochastic"})
```

- `split` is "training" or "validation" (the scenario draws). The same seed replays the same
  episode bit for bit.
- `vector` is a numpy array of 54 floats, A1's normalized observation. Do not give it to programs;
  decode it as below.

## Step

```python
action = slots.vector({"feed_rate": feed_m3_d * 1e6 / 24})   # feed_rate's unit is mL/h
vector, engine_reward, terminated, truncated, info = env.step(action)
```

- `feed_rate` is A1's only action. 1 m³/d is 1e6 / 24 mL/h; the pump's bounds are 0 to 255 m³/d.
- The engine moves the pump at most 34 m³/d per decision towards the command, from 85 m³/d at
  the reset.
- `engine_reward` is A1's training reward. The plugin does not use it.
- `terminated` is True when the digester soured (A1's termination); `truncated` is True after
  decision 400. Convert both with `bool(...)`.

## Decoding the signals

```python
SIGNALS = ("ch4_flow", "co2_flow", "ch4_pressure", "vfa_s_va", "vfa_s_bu", "vfa_s_pro",
           "vfa_s_ac", "inorganic_carbon")
value = slots.physical(vector, name)     # newest reading in the experiment's unit, or None
age = info["measurement_age"][name]      # float: decisions since the newest value arrived
```

- Units of `slots.physical`: ch4_flow and co2_flow m³/d, ch4_pressure bar, the four vfa_* kgCOD/L
  (multiply by 1000 for kgCOD/m³), inorganic_carbon mM.
- `slots.physical` returns None while a signal has no value. `info["measurement_age"][name]` is
  -1.0 then. The four VFA assays and inorganic_carbon have no value at the reset and at decisions 1
  to 3; the first arrives at decision 4 with age 0, the next at decision 8. The gas signals have a
  value at every decision, with age 0.
- `info` has the same keys after a reset and after a step.
- No signal goes missing at random: the gas signals always have age 0, and the five assays
  always arrive together, so they always share one age.
- Return Python floats and ints (`float(...)`, `int(...)`), not numpy numbers.

Checked values (seed 6002, constant 192 m³/d, training split): at the reset ch4_flow 1679.7,
co2_flow 965.6, ch4_pressure 0.654, the assays None with age -1; at decision 4 vfa_s_ac
0.186 kgCOD/m³ with age 0.

## The true state after each step

```python
from mgym_studies.control.evaluation import _controls, _lane_ir
from mgym_studies.control.objectives import decision_row, episode_objective

state = env.state
row = decision_row(STUDY, _lane_ir(env, state), env.simulated_time, state.y,
                   _controls(env, state))
# row: {"t_h", "pH", "total_vfa_kgCOD_m3", "ch4_flow_m3_d"}, all floats, from the true state
```

This is how A1's own evaluation (`mgym_studies.control.evaluation.run_episode`) reads each decision.
`_lane_ir` and `_controls` are its helpers. Read one row after every step, never at the reset.

## The episode's score

```python
objective = episode_objective(STUDY, rows)   # rows: the rows of every step of the episode
# {"mean_ch4_flow_constrained", "mean_ch4_flow", "soured", "min_ph", "max_total_vfa"}
```

- `mean_ch4_flow_constrained` is A1's score: `mean_ch4_flow` if pH >= 6.5 and total VFA <= 1.0
  kgCOD/m³ in every row, and 0 otherwise. `soured` is 1.0 if the episode left those limits, and
  0.0 otherwise.
- The first decision outside the limits is the first row (counted from 1) with `pH < 6.5` or
  `total_vfa_kgCOD_m3 > 1.0`.

Checked against A1's `run_episode` with a wrapper built from these calls and played through
soft_control_loop's runtime: seed 6002, constant 192 m³/d, 400 decisions in 32 s, mean CH4
3089.05 m³/d, lowest pH 7.405, highest total VFA 1.291, first decision outside the limits 12,
score 0.

## Timing

An episode of 400 decisions takes about 30 seconds on the reference backend, and importing the
packages about 2 seconds.
