"""Baseline ramp_480_172_1: raise the concentrate by 1 m3/d at every decision to 172 m3/d, and the
sludge in step with it to 480 m3/d, then hold both.

The program reads where its two pumps stand and no sensor. At every decision it asks each pump
for a little more than the pump has, until the pump is at its rate. Both pumps arrive after
172 decisions, which is 43 days. The sludge pump starts at 85 m3/d and the carbohydrate pump
at 0.
"""

SLUDGE = 480.0
CARBOHYDRATE = 172.0
STEP = 1.0
SLUDGE_STEP = (SLUDGE - 85.0) * STEP / CARBOHYDRATE
SUBGOAL = "raise the pumps slowly to 480 and 172 m3/d and hold them"


def act(observation, memory):
    sludge = min(SLUDGE, observation["sludge_rate"] + SLUDGE_STEP)
    carbohydrate = min(CARBOHYDRATE, observation["carbohydrate_rate"] + STEP)
    return [sludge, carbohydrate], SUBGOAL
