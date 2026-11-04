# snake/programs/square/program.py
CYCLE = [3] * 4 + [1] * 4 + [2] * 4 + [0] * 4


def act(observation, memory):
    step = memory.get("step", 0)
    memory["step"] = step + 1
    return CYCLE[step % len(CYCLE)], "square"
