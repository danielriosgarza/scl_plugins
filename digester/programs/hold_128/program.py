"""Baseline hold_128: command 128 m3/d at every decision, ignoring the observation."""

FEED = 128.0
SUBGOAL = "hold the pump feed at 128 m3/d"


def act(observation, memory):
    return [FEED], SUBGOAL
