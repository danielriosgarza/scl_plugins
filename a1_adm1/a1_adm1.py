"""The task loading of microbesGYM's environment a1_adm1 as a soft_control_loop environment.

microbesGYM is a benchmark of microbial control problems. Its environment a1_adm1 is a model of an
anaerobic digester, and its task loading asks a controller to feed that digester with two pumps
(TASK.md of the task in the microbesGYM repository). The benchmark runs every controller through
one class, mgym_bench.episode.Episode, which gives a controller the readings of its sensors and
computes the score from the true state of the simulation. This module wraps that class and
changes nothing of the task. A program of the loop is then a controller of the benchmark: it gets
what the task gives a controller, and it is scored by the benchmark's own code.

What the wrapper adapts:

- Action: a list of two numbers, the rate that the program asks for the sludge pump and for the
  carbohydrate pump, in m3/d, in the order of the task. The bounds of the action space are the
  limits of the two pumps.
- Observation: a dict with the newest reading of each of the task's nine sensors under the id
  and in the unit of the task; lab_age; and the rate at which each pump stands. A reading that
  has not arrived yet is None, as in the benchmark.
- lab_age: the five laboratory values are sampled together at every fourth decision and arrive
  four decisions later. lab_age is the number of decisions since the newest of them was sampled,
  and None before the first has arrived. The other four sensors are read at every decision
  without a delay, so their age is always 0 and has no key.
- Reward: the net methane of the decision, in m3/d: the true methane outflow minus 0.395 times the
  true outflow of acids at the end of the decision. The weights are read from the score rule of
  the task document. The score of the task is the mean of this number over decisions 1 to 400.
  The benchmark provides these true values for one use, the reward of a controller that learns
  (mgym_bench.episode, "The true values, for training"). A program never gets the reward.
- Episode record: the task's metrics of the episode and failed. They are None at every step and
  are filled in only in the observation that ends the episode, which no program acts on.
  net_methane is the score. failed is True when the episode is not a success by the rules of the
  task: the digester collapsed (the true pH was below 6.0 at the end of a decision, the run-out
  included), or the episode did not run all its decisions. This is the failure by which the
  benchmark's own searches rank a controller before the score.
- End: an episode has 568 decisions and no state of the digester ends it earlier. It is truncated
  after its last decision. It is terminated only when the engine could not compute a decision.
- True values (TRUE and DRAWN): what stands behind the sensors, for the agents of the loop and
  never for a program. The benchmark lets a training read the true state of the system and the
  values that are drawn for an episode, as long as the controller reads only its sensors
  (README of mgym-bench, "Rules for a fair comparison"; allowed by the maintainer for trainings
  on 2026-11-23, and for the agents of this loop on 2026-11-24). Every episode of the loop is a
  training episode. The keys of TRUE give, at every decision, the state in which the decision
  is taken: the true pH, the true total of the four acids, the true methane outflow, the
  inorganic nitrogen, four groups of microorganisms and the feed that no controller sets. The
  keys of DRAWN give the sludge of the episode, as multiples of the nominal recipe. They are
  None at every step and filled in with the episode record, since they do not change within an
  episode.

Rules:
- reset starts every episode in the benchmark's split training. The benchmark refuses a seed of
  its development split (7001 to 7050) or of its final split (12001 to 12050) there, so the loop
  cannot play a test or a validation seed. Those are played by hand with bridge.py.
- What observe returns holds nothing that the task withholds from a controller: no day, no count
  of decisions, no length of the episode, no seed and no true value. The task gives a controller
  no clock (TASK.md, "What the score does not see").
- The observation of a program here and of the same program in bridge.py come from one function,
  observe, so a program reads the same keys and values in a training episode of the loop and in
  an episode of the benchmark's runner.
- The true values are no part of what observe returns. Loading adds them to the observation
  under the keys of TRUE and DRAWN, and the setup names every one of these keys as hidden, so
  the loop records them and gives them to no program (the runtime module of soft_control_loop).
  A test fails if one of them is an observable of the setup. bridge.py plays the test and the
  validation seeds through observe alone, so no true value exists there.
- The true pH and the true methane outflow are the benchmark's own values of the score
  (Episode.values). The other true values are read from the state of the engine's episode,
  which Episode keeps in a private attribute; the benchmark's trainings read the same state
  (mgym_bench.training.lanes). The true pH and the true methane outflow have no value before
  the first decision has run, and a value that cannot be computed is None.
- The task, its sensors, its score and its seeds are read from the microbesGYM repository at run
  time and are never copied here. The README names the commit that the plugin was tested with.

This module defines ENVIRONMENT and TASK, the ids of the wrapped task; SPLIT, the split of every
episode of the loop; LAB_AGE and FAILED, the two keys that the wrapper adds to those of the task;
BACKEND, the default solver; TRUE and DRAWN, the keys of the true values with what each one is;
load_task; record_keys and observation_keys; observe; record_of; and the environment class
Loading.
"""

import math

import numpy as np

from soft_control_loop.environments import Box, Environment

from mgym_bench import registry, tasks
from mgym_bench.episode import Episode
from mgym_bench.training.lanes import theta_defaults

ENVIRONMENT = "a1_adm1"
TASK = "loading"
SPLIT = "training"
LAB_AGE = "lab_age"
FAILED = "failed"
BACKEND = "reference"
ACIDS = ("s_va", "s_bu", "s_pro", "s_ac")
SLUDGE = "influent_nominal"
TRUE = {
    "true_ph": "the true pH of the liquid, without the error of the probe",
    "true_acids": "the true total of valerate, butyrate, propionate and acetate, kgCOD/m3, "
                  "without the delay and the error of the laboratory",
    "true_ch4_flow": "the true methane outflow as a volume at atmospheric pressure, m3/d, the "
                     "methane that the score counts",
    "true_nitrogen": "the inorganic nitrogen in the liquid, mM, which every group of "
                     "microorganisms needs to grow",
    "true_x_su": "the microorganisms that take up the sugars, kgCOD/m3",
    "true_x_pro": "the microorganisms that take up propionate, kgCOD/m3",
    "true_x_ac": "the methanogens that use acetate, kgCOD/m3",
    "true_x_h2": "the methanogens that use hydrogen, kgCOD/m3",
    "true_incoming_sludge": "the rate of the feed of sludge that no controller sets, m3/d",
}
DRAWN = {
    "sludge_carbohydrates": "the carbohydrates of the sludge of this episode, as a multiple of "
                            "the nominal recipe",
    "sludge_proteins": "its proteins, as a multiple of the nominal recipe",
    "sludge_lipids": "its lipids, as a multiple of the nominal recipe",
}


def load_task():
    """Read and check the task from the microbesGYM repository and return it."""
    return tasks.load(registry.get(ENVIRONMENT), TASK)


def _lab(interface):
    """Return the ids of the sensors that are not read at every decision without a delay.

    Raise ValueError unless they all share one period and one delay, since lab_age is one age
    for all of them.
    """
    late = [sensor for sensor in interface.sensors if sensor.every != 1 or sensor.delay != 0]
    if len({(sensor.every, sensor.delay) for sensor in late}) > 1:
        raise ValueError("the laboratory sensors of the task no longer share one period and delay")
    return [sensor.id for sensor in late]


def record_keys(rules):
    """Return the keys of the episode record: the ids of the task's metrics, then failed."""
    return [metric.id for metric in rules.metrics] + [FAILED]


def observation_keys(interface, rules):
    """Return every key of an observation, in order: the sensors, lab_age, the actuators and the
    episode record."""
    return ([sensor.id for sensor in interface.sensors] + [LAB_AGE]
            + [actuator.id for actuator in interface.actuators] + record_keys(rules))


def observe(interface, observation, record=None):
    """Return the observation dict of a program from an observation of the benchmark.

    interface is what the benchmark tells a controller about the task, and observation what it
    gives a controller at one decision (mgym_bench.episode.Interface and Observation). The dict
    holds the value of each sensor's newest reading, lab_age and the setting of each actuator.
    With a record, the dict of the episode record, it also holds the record's values; without
    one, the keys of the record are left out.
    """
    lab = _lab(interface)
    ages = {observation.readings[name].age for name in lab}
    if len(ages) > 1:
        raise ValueError(f"the laboratory values have different ages: {sorted(map(str, ages))}")
    result = {sensor.id: observation.readings[sensor.id].value for sensor in interface.sensors}
    result[LAB_AGE] = ages.pop() if ages else None
    for actuator in interface.actuators:
        result[actuator.id] = float(observation.settings[actuator.id])
    return {**result, **(record or {})}


def record_of(result):
    """Return the episode record from the metrics of an ended episode of the benchmark
    (mgym_bench.score.EpisodeScore): each metric by its id, and failed."""
    return {**{name: float(value) for name, value in result.metrics.items()},
            FAILED: not result.success}


def _number(value):
    """Return value as a float, or None when it is not a finite number."""
    value = float(value)
    return value if math.isfinite(value) else None


class Loading(Environment):
    """One episode of a1_adm1/loading at a time: 568 decisions, one every 6 hours.

    backend is the solver of the benchmark's engine, "reference" or "jax". The observation holds
    the keys of observation_keys and then those of TRUE and DRAWN, which a setup must name as
    hidden (see the rules of this module).
    """

    def __init__(self, backend=BACKEND):
        super().__init__()
        self._episode = Episode(load_task(), backend=backend)
        interface, rules = self._episode.interface, self._episode.rules
        self.action_space = Box([actuator.low for actuator in interface.actuators],
                                [actuator.high for actuator in interface.actuators])
        self.observation_keys = observation_keys(interface, rules) + [*TRUE, *DRAWN]
        self._actuators = [actuator.id for actuator in interface.actuators]
        self._empty = dict.fromkeys(record_keys(rules))
        engine = self._episode._env.core.ir
        spaces, offsets = engine.spaces, engine.layout.offsets
        self._volume = offsets["V"][0]
        self._components = {name: offsets["N"][0] + i for i, name in enumerate(spaces.components)}
        self._microbes = {name: offsets["B"][0] + i
                          for i, name in enumerate(spaces.subpopulations)}
        self._per_m3 = 1.0 / engine.unit_scales["kgCOD/m3"]
        self._m3_per_day = engine.unit_scales["m3/d"]
        self._defaults = np.asarray(theta_defaults(engine), dtype=float)
        self._recipe = spaces.media.index(SLUDGE)
        self._recipes = len(spaces.media) - 1
        score = self._episode.task.document["extensions"]["mgym/score"]
        self._terms = [(term["variable"], float(term["weight"]))
                       for term in score["rules"][score["score"]]["terms"]]
        self._decisions = 0

    def reset(self, seed=None):
        """Start the training episode of seed and return (observation, info)."""
        observation = self._episode.reset(seed, SPLIT)
        self._decisions = 0
        found = observe(self._episode.interface, observation, self._empty)
        return {**found, **self._true(found), **dict.fromkeys(DRAWN)}, {"seed": seed}

    def _true(self, found):
        """Return the true values of the state in which the episode stands, by the keys of TRUE.

        found is the observation of this moment, which gives the rates of the two pumps.
        """
        state, values = self._episode._env.state, self._episode.values
        amounts = np.asarray(state.y, dtype=float)
        volume = amounts[self._volume]
        now = values[-1] if len(values) == self._decisions and values else {}
        inflow = float(np.sum(np.asarray(state.inflow_rate, dtype=float))) / self._m3_per_day
        true = {
            "true_ph": now.get("ph_true"),
            "true_acids": sum(amounts[self._components[name]] for name in ACIDS)
            / volume * self._per_m3,
            "true_ch4_flow": now.get("ch4_flow_true"),
            "true_nitrogen": amounts[self._components["s_in"]] / volume * 1000.0,
            **{f"true_{name}": amounts[self._microbes[name]] / volume * self._per_m3
               for name in ("x_su", "x_pro", "x_ac", "x_h2")},
            "true_incoming_sludge": inflow - sum(found[name] for name in self._actuators),
        }
        return {key: None if true[key] is None else _number(true[key]) for key in TRUE}

    def _drawn(self):
        """Return the sludge of the episode by the keys of DRAWN: the carbohydrates, proteins
        and lipids of the recipe SLUDGE, each divided by its nominal value.

        Raise ValueError unless the episode draws three values for each recipe of sludge, in the
        order of the recipes, which is how this method finds those of SLUDGE.
        """
        theta = np.asarray(self._episode._env.state.theta, dtype=float)
        drawn = np.flatnonzero(theta != self._defaults)
        if len(drawn) != len(DRAWN) * self._recipes:
            raise ValueError(f"the task draws {len(drawn)} values for an episode, not "
                             f"{len(DRAWN)} for each of its {self._recipes} recipes of sludge")
        mine = drawn[self._recipe * len(DRAWN):(self._recipe + 1) * len(DRAWN)]
        return {key: _number(theta[i] / self._defaults[i]) for key, i in zip(DRAWN, mine)}

    def step(self, action):
        """Run one decision with the two rates of action and return (observation, reward,
        terminated, truncated, info).

        The reward is 0.0 for a decision that the engine could not compute. info gives the
        outcome of an episode that has ended, as the benchmark names it.
        """
        observation = self._episode.step(dict(zip(self._actuators, action)))
        values = self._episode.values
        computed = len(values) > self._decisions
        self._decisions = len(values)
        reward = sum(weight * values[-1][name] for name, weight in self._terms) if computed else 0.0
        interface = self._episode.interface
        if not self._episode.ended:
            found = observe(interface, observation, self._empty)
            return ({**found, **self._true(found), **dict.fromkeys(DRAWN)}, reward, False, False,
                    {})
        result = self._episode.result()
        horizon = result.outcome == "horizon"
        found = observe(interface, observation, record_of(result))
        return ({**found, **self._true(found), **self._drawn()}, reward, not horizon, horizon,
                {"outcome": result.outcome})
