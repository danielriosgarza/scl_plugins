"""Baseline hold_255: command 255 m3/d at every decision, ignoring the observation."""

FEED = 255.0
SUBGOAL = "hold the pump feed at 255 m3/d"


def act(observation, memory):
    return [FEED], SUBGOAL
