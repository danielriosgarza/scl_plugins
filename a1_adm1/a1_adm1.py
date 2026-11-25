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

- Lanes: the benchmark's engine can solve many episodes in one call, each in a lane, and the
  benchmark's own searches run their training episodes that way (mgym_bench.training.batch).
  Loading.lanes gives the loop the same: several training episodes side by side, each with the
  readings, the reward, the record and the true values that one episode has here, read with
  the benchmark's own functions. The episode of a lane is fixed by its seed and by the number
  of the lane. Lane 0 plays the episode that the seed has when it is played alone, and every
  other lane plays another training episode of the task, drawn in the way the task draws its
  training episodes (mgym_bench.training.batch, "Which episodes the lanes run"). The loop
  therefore plays in lanes only the episodes of its searches, where every candidate plays the
  same seeds in the same lanes, and plays every evaluation one episode at a time. Lanes run on
  the backend jax only.

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
load_task; record_keys and observation_keys; observe; record_of; the environment class Loading;
and Lanes, which plays several training episodes side by side.
"""

import math

import numpy as np

from soft_control_loop.environments import Box, Environment

from mgym_bench import registry, run, score, tasks
from mgym_bench.episode import (
    Episode, Observation, SettingsReader, _to_engine, interface_of, readings_of,
)
from mgym_bench.training.lanes import theta_defaults
from mgym_engine.rl.observations import observation_layout

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


class _Engine:
    """Where the true values stand in the state of the engine's episode of the task.

    core is the engine's compiled environment of the task, which one episode and a batch of
    lanes both have, and document the task document.
    """

    def __init__(self, core, document, actuators):
        engine = core.ir
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
        self._actuators = actuators
        rules = document["extensions"]["mgym/score"]
        self.terms = [(term["variable"], float(term["weight"]))
                      for term in rules["rules"][rules["score"]]["terms"]]

    def true(self, state, now, found):
        """Return the true values of state, the state of an episode of the engine, by the keys
        of TRUE.

        now holds the true values of the score at the end of the last decision, or is empty
        before the first decision has run. found is the observation of this moment, which
        gives the rates of the two pumps.
        """
        amounts = np.asarray(state.y, dtype=float)
        volume = amounts[self._volume]
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

    def drawn(self, state):
        """Return the sludge of the episode of state by the keys of DRAWN: the carbohydrates,
        proteins and lipids of the recipe SLUDGE, each divided by its nominal value.

        Raise ValueError unless the episode draws three values for each recipe of sludge, in the
        order of the recipes, which is how this method finds those of SLUDGE.
        """
        theta = np.asarray(state.theta, dtype=float)
        drawn = np.flatnonzero(theta != self._defaults)
        if len(drawn) != len(DRAWN) * self._recipes:
            raise ValueError(f"the task draws {len(drawn)} values for an episode, not "
                             f"{len(DRAWN)} for each of its {self._recipes} recipes of sludge")
        mine = drawn[self._recipe * len(DRAWN):(self._recipe + 1) * len(DRAWN)]
        return {key: _number(theta[i] / self._defaults[i]) for key, i in zip(DRAWN, mine)}


class Loading(Environment):
    """One episode of a1_adm1/loading at a time: 568 decisions, one every 6 hours.

    backend is the solver of the benchmark's engine, "reference" or "jax". The observation holds
    the keys of observation_keys and then those of TRUE and DRAWN, which a setup must name as
    hidden (see the rules of this module).
    """

    def __init__(self, backend=BACKEND):
        super().__init__()
        self._backend = backend
        self._episode = Episode(load_task(), backend=backend)
        interface, rules = self._episode.interface, self._episode.rules
        self.action_space = Box([actuator.low for actuator in interface.actuators],
                                [actuator.high for actuator in interface.actuators])
        self.observation_keys = observation_keys(interface, rules) + [*TRUE, *DRAWN]
        self._actuators = [actuator.id for actuator in interface.actuators]
        self._empty = dict.fromkeys(record_keys(rules))
        self._engine = _Engine(self._episode._env.core, self._episode.task.document,
                               self._actuators)
        self._terms = self._engine.terms
        self._decisions = 0
        self._lanes = {}

    def reset(self, seed=None):
        """Start the training episode of seed and return (observation, info)."""
        observation = self._episode.reset(seed, SPLIT)
        self._decisions = 0
        found = observe(self._episode.interface, observation, self._empty)
        return {**found, **self._true(found), **dict.fromkeys(DRAWN)}, {"seed": seed}

    def lanes(self, count):
        """Return count lanes that play training episodes of the task side by side (see Lanes
        and the top of this module). The lanes of one count are built once and kept. Raise
        ValueError on another backend than jax, which is the one that solves lanes."""
        if self._backend != "jax":
            raise ValueError(f"lanes run on the backend jax, and this environment has the "
                             f"backend {self._backend}")
        if count not in self._lanes:
            self._lanes[count] = Lanes(self._episode.task, count)
        return self._lanes[count]

    def _true(self, found):
        """Return the true values of the state in which the episode stands, by the keys of TRUE.

        found is the observation of this moment, which gives the rates of the two pumps.
        """
        values = self._episode.values
        now = values[-1] if len(values) == self._decisions and values else {}
        return self._engine.true(self._episode._env.state, now, found)

    def _drawn(self):
        """Return the sludge of the episode by the keys of DRAWN (see _Engine.drawn)."""
        return self._engine.drawn(self._episode._env.state)

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


class _Lane:
    """One lane of a batch, in the form in which the benchmark's score rules read an
    environment (mgym_bench.score.ScoreRules.read): its state, the compiled model that all
    lanes share, and the time at which its episode stands."""

    def __init__(self, env, lane):
        self._env, self._lane = env, lane

    @property
    def state(self):
        """The state of the episode of the lane."""
        return self._env.lane_state(self._lane)

    @property
    def core(self):
        """The compiled environment of the batch."""
        return self._env.core

    @property
    def simulated_time(self):
        """The time of the boundary at which the episode of the lane stands, in hours."""
        return float(self._env.core.program.bounds[self.state.decision])


class Lanes:
    """Several training episodes of a1_adm1/loading side by side, one in each lane.

    task is the task and count the number of lanes. What a lane gives is what Loading gives for
    one episode: the same keys, the same reward and, at the end, the same record. The readings
    and the settings come from the benchmark's own functions (readings_of and SettingsReader),
    and the true values of the score and the record from its score rules, as in
    mgym_bench.training.batch.BatchEpisodes. A seed of the development or of the final split
    is refused.
    """

    def __init__(self, task, count):
        from mgym_engine.rl.vector import VecGymEnv

        self._task, self._count = task, count
        self._interface, self._rules = interface_of(task), score.of(task)
        self._env = VecGymEnv(tasks.compose(task), task.model, num_envs=count)
        self._layout = observation_layout(self._env.core.plans)
        self._settings = SettingsReader(task, self._interface, self._env.core)
        self._views = [_Lane(self._env, lane) for lane in range(count)]
        self._actuators = list(self._interface.actuators)
        self._engine = _Engine(self._env.core, task.document,
                               [actuator.id for actuator in self._actuators])
        self._empty = dict.fromkeys(record_keys(self._rules))
        self._withheld = {other: frozenset(run.seeds_of(task, other))
                          for other in ("development", "final")}
        self._decisions = int(self._rules.decisions)
        self._rows, self._before, self._ended, self._asked = [], [], [], None

    def _observed(self, lane, vector, record=None):
        """Return the observation of lane from its vector of the engine, with the true values
        of its state, and with record and the sludge of the episode when the episode has
        ended."""
        state = self._env.lane_state(lane)
        observation = Observation(readings=readings_of(self._interface.sensors, self._layout,
                                                       vector),
                                  settings=self._settings.read(state))
        found = observe(self._interface, observation, record or self._empty)
        now = self._rows[lane][-1] if self._rows[lane] else {}
        drawn = self._engine.drawn(state) if record else dict.fromkeys(DRAWN)
        return {**found, **self._engine.true(state, now, found), **drawn}

    def reset(self, seeds):
        """Start in each lane the training episode of its seed and return the first observation
        of each lane. Raise ValueError unless there is one seed for each lane, and for a seed
        of the development or of the final split."""
        seeds = [int(seed) for seed in seeds]
        if len(seeds) != self._count:
            raise ValueError(f"{self._count} lanes need {self._count} seeds, not {len(seeds)}")
        for other, taken in self._withheld.items():
            found = sorted(set(seeds) & taken)
            if found:
                raise ValueError(f"the seed {found[0]} is a seed of the split {other} of the "
                                 f"task; a training episode must not use it")
        if self._rules.at_start:
            raise ValueError("the score of the task reads values at the start of an episode, "
                             "which these lanes do not read")
        vectors, _ = self._env.reset(seed=seeds, options={"split": SPLIT})
        self._rows = [[] for _ in range(self._count)]
        self._ended = [False] * self._count
        self._before = [self._env.lane_state(lane).y.copy() for lane in range(self._count)]
        self._asked = np.zeros((self._count, len(self._actuators)), dtype=np.float64)
        return [self._observed(lane, vectors[lane]) for lane in range(self._count)]

    def step(self, actions):
        """Run one decision in every lane and return (observation, reward, terminated,
        truncated, info) for each lane.

        actions holds for each lane the two rates that its program asks for, or None for a
        lane whose episode has ended or whose program has failed. Such a lane keeps the rates
        that it was last asked for, since the engine solves every lane, and None is returned
        for it. The reward is 0.0 for a decision that the engine could not compute, which
        ends the episode of that lane as terminated.
        """
        for lane, action in enumerate(actions):
            if action is None:
                self._ended[lane] = True
                continue
            for position, actuator in enumerate(self._actuators):
                self._asked[lane, position] = _to_engine(actuator, float(action[position]))
        vectors, _, terminated, truncated, info = self._env.step(self._asked)
        failures = np.asarray(info["solver_statistics"]["failure_reason"])
        results = []
        for lane in range(self._count):
            if self._ended[lane]:
                results.append(None)
                continue
            state = self._env.lane_state(lane)
            failed, reward = int(failures[lane]) != 0, 0.0
            if not failed:
                try:
                    values = self._rules.read(self._views[lane], self._before[lane])
                except score.READ_ERRORS:
                    failed = True
                else:
                    if all(math.isfinite(value) for value in values.values()):
                        self._rows[lane].append(values)
                        reward = sum(weight * values[name]
                                     for name, weight in self._engine.terms)
                    else:
                        failed = True
            self._before[lane] = state.y.copy()
            outcome = ("numerical_failure" if failed else "terminated" if terminated[lane]
                       else "horizon" if state.decision == self._decisions
                       else "truncated" if truncated[lane] else None)
            if outcome is None:
                results.append((self._observed(lane, vectors[lane]), reward, False, False, {}))
                continue
            self._ended[lane] = True
            if self._rows[lane]:
                record = record_of(self._rules.episode(self._rows[lane], outcome, {}))
            else:
                record = {**self._empty, FAILED: True}
            horizon = outcome == "horizon"
            results.append((self._observed(lane, vectors[lane], record), reward, not horizon,
                            horizon, {"outcome": outcome}))
        return results
