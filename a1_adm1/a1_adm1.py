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

Rules:
- reset starts every episode in the benchmark's split training. The benchmark refuses a seed of
  its development split (7001 to 7050) or of its final split (12001 to 12050) there, so the loop
  cannot play a test or a validation seed. Those are played by hand with bridge.py.
- The observation holds nothing that the task withholds from a controller: no day, no count of
  decisions, no length of the episode, no seed and no true value. The task gives a controller no
  clock (TASK.md, "What the score does not see").
- The observation of a program here and of the same program in bridge.py come from one function,
  observe, so a program reads the same keys and values in a training episode of the loop and in
  an episode of the benchmark's runner.
- The task, its sensors, its score and its seeds are read from the microbesGYM repository at run
  time and are never copied here. The README names the commit that the plugin was tested with.

This module defines ENVIRONMENT and TASK, the ids of the wrapped task; SPLIT, the split of every
episode of the loop; LAB_AGE and FAILED, the two keys that the wrapper adds to those of the task;
BACKEND, the default solver; load_task; record_keys and observation_keys; observe; record_of; and
the environment class Loading.
"""

from soft_control_loop.environments import Box, Environment

from mgym_bench import registry, tasks
from mgym_bench.episode import Episode

ENVIRONMENT = "a1_adm1"
TASK = "loading"
SPLIT = "training"
LAB_AGE = "lab_age"
FAILED = "failed"
BACKEND = "reference"


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


class Loading(Environment):
    """One episode of a1_adm1/loading at a time: 568 decisions, one every 6 hours.

    backend is the solver of the benchmark's engine, "reference" or "jax".
    """

    def __init__(self, backend=BACKEND):
        super().__init__()
        self._episode = Episode(load_task(), backend=backend)
        interface, rules = self._episode.interface, self._episode.rules
        self.action_space = Box([actuator.low for actuator in interface.actuators],
                                [actuator.high for actuator in interface.actuators])
        self.observation_keys = observation_keys(interface, rules)
        self._actuators = [actuator.id for actuator in interface.actuators]
        self._empty = dict.fromkeys(record_keys(rules))
        score = self._episode.task.document["extensions"]["mgym/score"]
        self._terms = [(term["variable"], float(term["weight"]))
                       for term in score["rules"][score["score"]]["terms"]]
        self._decisions = 0

    def reset(self, seed=None):
        """Start the training episode of seed and return (observation, info)."""
        observation = self._episode.reset(seed, SPLIT)
        self._decisions = 0
        return observe(self._episode.interface, observation, self._empty), {"seed": seed}

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
            return observe(interface, observation, self._empty), reward, False, False, {}
        result = self._episode.result()
        horizon = result.outcome == "horizon"
        return (observe(interface, observation, record_of(result)), reward, not horizon, horizon,
                {"outcome": result.outcome})
