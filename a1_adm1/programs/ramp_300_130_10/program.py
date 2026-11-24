"""Baseline ramp_300_130_10: raise the concentrate by 10 m3/d at every decision to 130 m3/d, and the
sludge in step with it to 300 m3/d, then hold both.

The program reads where its two pumps stand and no sensor. At every decision it asks each pump
for a little more than the pump has, until the pump is at its rate. Both pumps arrive after
13 decisions, which is 3.25 days. The sludge pump starts at 85 m3/d and the carbohydrate pump
at 0.
"""

SLUDGE = 300.0
CARBOHYDRATE = 130.0
STEP = 10.0
SLUDGE_STEP = (SLUDGE - 85.0) * STEP / CARBOHYDRATE
SUBGOAL = "raise the pumps slowly to 300 and 130 m3/d and hold them"


def act(observation, memory):
    sludge = min(SLUDGE, observation["sludge_rate"] + SLUDGE_STEP)
    carbohydrate = min(CARBOHYDRATE, observation["carbohydrate_rate"] + STEP)
    return [sludge, carbohydrate], SUBGOAL
