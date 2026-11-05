"""microbesGYM's A1 anaerobic digester as a soft_control_loop environment.

Wraps A1's own environment (study control_a1_loading, aligned experiment, reference backend)
without copying or changing it. The wrapper adapts only the interface:

- action: [feed] in m3/d, converted to A1's normalized feed_rate action (mL/h);
- observation: a dict of decoded noisy readings (no true state, no influent composition);
- reward: the true methane outflow after each step, read as A1's own evaluation reads it;
- episode record (mean_ch4_flow, min_ph, max_total_vfa, first_out, score): None at every step,
  filled in only in the observation that ends the episode.
"""

from __future__ import annotations

import math

from soft_control_loop.environments import Box, Environment

from mgym_engine.rl import GymEnv
from mgym_studies.control import documents
from mgym_studies.control.baselines import Slots
from mgym_studies.control.evaluation import _controls, _lane_ir
from mgym_studies.control.objectives import decision_row, episode_objective

STUDY = "control_a1_loading"

FEED_MIN = 0.0  # m3/d
FEED_MAX = 255.0  # m3/d
ML_H_PER_M3_D = 1e6 / 24  # feed_rate's unit is mL/h
DECISIONS = 400
DAYS_PER_DECISION = 0.25
PH_MIN = 6.5
VFA_MAX = 1.0  # kgCOD/m3

GAS = ("ch4_flow", "co2_flow", "ch4_pressure")
VFA = ("vfa_s_va", "vfa_s_bu", "vfa_s_pro", "vfa_s_ac")  # kgCOD/L in A1, kgCOD/m3 here
ASSAYS = VFA + ("inorganic_carbon",)
SIGNALS = GAS + ASSAYS
AGE_SIGNAL = "vfa_s_ac"  # the five assays always arrive together and share one age
RECORD = ("mean_ch4_flow", "min_ph", "max_total_vfa", "first_out", "score")
OBSERVATION_KEYS = ("day",) + SIGNALS + ("assay_age",) + RECORD


def split_for_seed(seed: int) -> str:
    """Seeds 1001-1008 and 6001-6020 use A1's training draws, every other seed its validation draws."""
    if 1001 <= seed <= 1008 or 6001 <= seed <= 6020:
        return "training"
    return "validation"


def _feed(action) -> float:
    """The commanded feed in m3/d from a one-float action, clipped to the pump's bounds."""
    try:
        values = list(action)
    except TypeError:
        values = [action]
    if len(values) != 1:
        raise ValueError(f"the action must be a list with one float (feed in m3/d), got {action!r}")
    feed = float(values[0])
    if not math.isfinite(feed):
        raise ValueError(f"the feed must be a finite number, got {feed!r}")
    return min(max(feed, FEED_MIN), FEED_MAX)


class A1Digester(Environment):
    """A1's digester: one decision every 6 hours, 400 decisions, feed of the controlled pump in m3/d."""

    action_space = Box([FEED_MIN], [FEED_MAX])
    observation_keys = list(OBSERVATION_KEYS)

    def __init__(self):
        super().__init__()
        payload = documents.experiment_payload(STUDY)  # the aligned experiment
        self._slots = Slots.from_experiment(payload)
        self._env = GymEnv(payload, documents.load_model_document(STUDY), backend="reference")
        self._decision = 0
        self._rows = []
        self._split = None
        self._done = True

    def reset(self, seed):
        seed = int(seed)
        self._split = split_for_seed(seed)
        vector, info = self._env.reset(
            seed=seed, options={"split": self._split, "evaluation_mode": "stochastic"}
        )
        self._decision = 0
        self._rows = []
        self._done = False
        observation = self._observation(vector, info, None)
        return observation, {"seed": seed, "split": self._split, "decision": 0}

    def step(self, action):
        if self._done:
            raise RuntimeError("the episode has ended; call reset before step")
        feed = _feed(action)
        engine_action = self._slots.vector({"feed_rate": feed * ML_H_PER_M3_D})
        vector, _engine_reward, terminated, truncated, info = self._env.step(engine_action)
        terminated = bool(terminated)
        truncated = bool(truncated)
        self._decision += 1

        # The true state after the step, read as A1's own evaluation (run_episode) reads it.
        state = self._env.state
        row = decision_row(
            STUDY, _lane_ir(self._env, state), self._env.simulated_time, state.y,
            _controls(self._env, state),
        )
        self._rows.append(row)
        reward = float(row["ch4_flow_m3_d"])

        if not terminated and self._decision >= DECISIONS:
            truncated = True
        ended = terminated or truncated
        record = self._record() if ended else None
        self._done = ended
        observation = self._observation(vector, info, record)
        return observation, reward, terminated, truncated, {
            "decision": self._decision,
            "feed_command": feed,
        }

    def _observation(self, vector, info, record):
        observation = {"day": float(self._decision * DAYS_PER_DECISION)}
        for name in SIGNALS:
            value = self._slots.physical(vector, name)
            if value is None:
                observation[name] = 0.0
            else:
                value = float(value)
                if name in VFA:
                    value *= 1000.0  # kgCOD/L -> kgCOD/m3
                observation[name] = value
        age = float(info["measurement_age"][AGE_SIGNAL])
        has_assay = self._slots.physical(vector, AGE_SIGNAL) is not None
        observation["assay_age"] = int(round(age)) if has_assay and age >= 0 else -1
        for key in RECORD:
            observation[key] = None if record is None else record[key]
        return observation

    def _record(self):
        objective = episode_objective(STUDY, self._rows)
        first_out = None
        for number, row in enumerate(self._rows, start=1):
            if float(row["pH"]) < PH_MIN or float(row["total_vfa_kgCOD_m3"]) > VFA_MAX:
                first_out = number
                break
        return {
            "mean_ch4_flow": float(objective["mean_ch4_flow"]),
            "min_ph": float(objective["min_ph"]),
            "max_total_vfa": float(objective["max_total_vfa"]),
            "first_out": first_out,
            "score": float(objective["mean_ch4_flow_constrained"]),
        }
