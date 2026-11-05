"""Baseline hold_64: command 64 m3/d at every decision, ignoring the observation."""

FEED = 64.0
SUBGOAL = "hold the pump feed at 64 m3/d"


def act(observation, memory):
    return [FEED], SUBGOAL
