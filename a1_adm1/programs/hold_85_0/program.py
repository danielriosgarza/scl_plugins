"""Baseline hold_85_0: ask for 85 m3/d of sludge and 0 m3/d of concentrate at every decision.

The program ignores the observation. Each pump moves towards its rate by at most its largest
change per decision and then stays there.
"""

SLUDGE = 85.0
CARBOHYDRATE = 0.0
SUBGOAL = "hold the sludge pump at 85 m3/d and the carbohydrate pump at 0 m3/d"


def act(observation, memory):
    return [SLUDGE, CARBOHYDRATE], SUBGOAL
