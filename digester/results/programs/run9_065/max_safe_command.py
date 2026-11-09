from soft_control_loop.programs import skill


@skill
def max_safe_command(peak_of, limit, high=255, low=0, fallback=0.0):
    """Find the largest integer command whose forecast peak meets a limit.

    Tries integer candidates in order from ``high`` down to ``low``,
    inclusive. Each candidate is passed as a float to ``peak_of``. The first
    candidate with ``peak_of(candidate) <= limit`` is returned as a float.
    The search covers every candidate one by one, so it also works when the
    forecast is not monotonic in the command, for example when the model
    clips its dynamics.

    Args:
        peak_of: callable(command: float) -> float. Gives the forecast peak
            of the constrained quantity, such as total VFA, when the
            command is held for the forecast horizon.
        limit: the largest allowed forecast peak.
        high: the largest candidate command (integer).
        low: the smallest candidate command (integer).
        fallback: the command returned when no candidate meets the limit.

    Returns:
        float: the chosen command.
    """
    for candidate in range(int(high), int(low) - 1, -1):
        if peak_of(float(candidate)) <= limit:
            return float(candidate)
    return float(fallback)
