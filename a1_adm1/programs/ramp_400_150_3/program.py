"""Baseline ramp_400_150_3: raise the concentrate by 3 m3/d at every decision to 150 m3/d, and the
sludge in step with it to 400 m3/d, then hold both.

The program reads where its two pumps stand and no sensor. At every decision it asks each pump
for a little more than the pump has, until the pump is at its rate. Both pumps arrive after
50 decisions, which is 12.5 days. The sludge pump starts at 85 m3/d and the carbohydrate pump
at 0.
"""

SLUDGE = 400.0
CARBOHYDRATE = 150.0
STEP = 3.0
SLUDGE_STEP = (SLUDGE - 85.0) * STEP / CARBOHYDRATE
SUBGOAL = "raise the pumps slowly to 400 and 150 m3/d and hold them"


def act(observation, memory):
    sludge = min(SLUDGE, observation["sludge_rate"] + SLUDGE_STEP)
    carbohydrate = min(CARBOHYDRATE, observation["carbohydrate_rate"] + STEP)
    return [sludge, carbohydrate], SUBGOAL
