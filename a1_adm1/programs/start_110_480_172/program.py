"""Baseline start_110_480_172: a start without sludge. Lower the sludge pump to 0 and raise the
concentrate by 5.5 m3/d at every decision to 110.0 m3/d. Then raise the sludge by 8.0 and the
concentrate by 1.0 m3/d at every decision to 480.0 and 172.0 m3/d, and hold both.

The program reads where its two pumps stand and no sensor. The sludge pump starts at 85 m3/d and
is at 0 after three decisions. The concentrate is at 110.0 m3/d after 20 decisions, which is
5 days, and both pumps are at their rates 62 decisions later, which is 15.5 days.
"""

FIRST = 110.0
STEP = 5.5
SLUDGE = 480.0
SLUDGE_STEP = 8.0
CARBOHYDRATE = 172.0
CARBOHYDRATE_STEP = 1.0


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
