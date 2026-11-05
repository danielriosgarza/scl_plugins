"""Baseline step_64_192: 64 m3/d for decisions 0 to 199, 192 m3/d from decision 200 (day 50).

Ignores the observation; counts its decisions in its memory.
"""

SWITCH = 200


def act(observation, memory):
    decision = int(memory.get("decision", 0))
    memory["decision"] = decision + 1
    if decision < SWITCH:
        return [64.0], "hold 64 m3/d until decision 200 (day 50)"
    return [192.0], "hold 192 m3/d from decision 200 (day 50)"
