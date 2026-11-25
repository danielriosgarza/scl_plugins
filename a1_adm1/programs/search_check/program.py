"""A check of the loop's search of constants, written by hand: two loops of feedback whose ten
numbers are all left to the search.

The form is that of the benchmark's own PI controller (microbesGYM,
`results/a1_adm1/loading/pi`): the carbohydrate pump follows the pH, and the sludge pump follows
the sum of the four acids at each new result of the laboratory. Each loop has a setpoint, a gain,
an integral time, a filter time and a rate at which it starts. With the ten values that the
benchmark's search chose, this program scores what the benchmark's scorecard says, 12 268.8 on
the training seed 6001.

Here every number is declared at the middle of the range of the benchmark's search
(`plan.json` there), and a range that spans more than a factor of ten is declared as a logarithm.
So `scl tune setup.json programs/search_check --workdir NEW` gives the loop's search the same
ten numbers and ranges that the benchmark's search had, and shows what it makes of them and how
long it takes on a computer. It asks no agent.

This program is not in the baseline. No agent of the loop is shown it, its form or its result.
"""
import math

TUNED = {
    "ph_setpoint": 7.15,
    "log_ph_gain": 2.477,
    "log_ph_ti": 1.73,
    "ph_tf": 36.0,
    "carb_start": 150.0,
    "log_acids_setpoint": -3.199,
    "log_acids_gain": 5.0,
    "log_acids_ti": 2.03,
    "acids_tf": 72.0,
    "sludge_start": 500.0,
}

RANGES = {
    "ph_setpoint": [6.7, 7.6],
    "log_ph_gain": [1.477, 3.477],
    "log_ph_ti": [0.778, 2.681],
    "ph_tf": [0.0, 72.0],
    "carb_start": [0.0, 300.0],
    "log_acids_setpoint": [-4.222, -2.046],
    "log_acids_gain": [4.0, 6.0],
    "log_acids_ti": [1.38, 2.681],
    "acids_tf": [0.0, 144.0],
    "sludge_start": [0.0, 1000.0],
}

ACIDS = ("vfa_s_va", "vfa_s_bu", "vfa_s_pro", "vfa_s_ac")


def _loop(state, value, setpoint, gain, ti, tf, start, hours, stands, low, high):
    first = state["filtered"] is None
    if first:
        state["filtered"] = value
    else:
        share = 1.0 if tf <= 0.0 else 1.0 - math.exp(-hours / tf)
        state["filtered"] += share * (value - state["filtered"])
    error = state["filtered"] - setpoint
    if not first:
        behind, push = state["output"] - stands, gain * error
        tolerance = 1e-9 * (high - low)
        if not ((behind > tolerance and push > 0.0) or (behind < -tolerance and push < 0.0)):
            state["integral"] += error * hours
    state["output"] = start + gain * (error + state["integral"] / ti)


def act(observation, memory):
    if not memory:
        memory["carb"] = {"output": TUNED["carb_start"], "integral": 0.0, "filtered": None}
        memory["sludge"] = {"output": TUNED["sludge_start"], "integral": 0.0, "filtered": None}
    _loop(memory["carb"], observation["ph"], TUNED["ph_setpoint"], 10 ** TUNED["log_ph_gain"],
          10 ** TUNED["log_ph_ti"], TUNED["ph_tf"], TUNED["carb_start"], 6.0,
          observation["carbohydrate_rate"], 0.0, 300.0)
    if observation["lab_age"] == 4:
        acids = sum(observation[name] for name in ACIDS)
        _loop(memory["sludge"], acids, 10 ** TUNED["log_acids_setpoint"],
              -(10 ** TUNED["log_acids_gain"]), 10 ** TUNED["log_acids_ti"], TUNED["acids_tf"],
              TUNED["sludge_start"], 24.0, observation["sludge_rate"], 0.0, 1000.0)
    sludge = min(max(memory["sludge"]["output"], 0.0), 1000.0)
    carb = min(max(memory["carb"]["output"], 0.0), 300.0)
    return [sludge, carb], "two loops"
