from soft_control_loop.programs import skill


@skill
def ewma_update(memory, key, reading, weight):
    """Update an exponentially weighted moving average kept in memory.

    Args:
        memory: mutable dict that persists between control steps.
        key: memory key that holds the smoothed value.
        reading: the new raw measurement.
        weight: smoothing weight in [0, 1]. A larger weight follows the reading faster.

    On the first call for a key, the average starts at the reading, so the change is 0.

    Returns:
        (current, change): the new smoothed value, and current minus the previous
        smoothed value. The change is a filtered trend signal for detecting a
        rising or falling observable.
    """
    previous = memory.get(key, reading)
    current = previous + weight * (reading - previous)
    memory[key] = current
    return current, current - previous
