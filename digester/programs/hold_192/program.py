"""Baseline hold_192: command 192 m3/d at every decision, ignoring the observation."""

FEED = 192.0
SUBGOAL = "hold the pump feed at 192 m3/d"


def act(observation, memory):
    return [FEED], SUBGOAL
