"""Baseline hold_200_100: ask for 200 m3/d of sludge and 100 m3/d of concentrate at every decision.

The program ignores the observation. Each pump moves towards its rate by at most its largest
change per decision and then stays there.
"""

SLUDGE = 200.0
CARBOHYDRATE = 100.0
SUBGOAL = "hold the sludge pump at 200 m3/d and the carbohydrate pump at 100 m3/d"


def act(observation, memory):
    return [SLUDGE, CARBOHYDRATE], SUBGOAL
