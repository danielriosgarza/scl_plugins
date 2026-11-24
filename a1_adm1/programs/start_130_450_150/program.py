"""Baseline start_130_450_150: a start without sludge. Lower the sludge pump to 0 and raise the
concentrate by 6.5 m3/d at every decision to 130.0 m3/d. Then raise the sludge by 7.5 and the
concentrate by 0.35 m3/d at every decision to 450.0 and 150.0 m3/d, and hold both.

The program reads where its two pumps stand and no sensor. The sludge pump starts at 85 m3/d and
is at 0 after three decisions. The concentrate is at 130.0 m3/d after 20 decisions, which is
5 days, and both pumps are at their rates 60 decisions later, which is 15 days.
"""

FIRST = 130.0
STEP = 6.5
SLUDGE = 450.0
SLUDGE_STEP = 7.5
CARBOHYDRATE = 150.0
CARBOHYDRATE_STEP = 0.35


def act(observation, memory):
    sludge, carbohydrate = observation["sludge_rate"], observation["carbohydrate_rate"]
    if not memory.get("fed"):
        if carbohydrate >= FIRST - 1e-9:
            memory["fed"] = True
        else:
            return ([max(0.0, sludge - 34.0), min(FIRST, carbohydrate + STEP)],
                    "start without sludge")
    return ([min(SLUDGE, sludge + SLUDGE_STEP),
             min(CARBOHYDRATE, carbohydrate + CARBOHYDRATE_STEP)], "raise both pumps and hold them")
