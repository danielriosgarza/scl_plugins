"""Baseline hold_0: command 0 m3/d at every decision, ignoring the observation."""

FEED = 0.0
SUBGOAL = "hold the pump feed at 0 m3/d"


def act(observation, memory):
    return [FEED], SUBGOAL
