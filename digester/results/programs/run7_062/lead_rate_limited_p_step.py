from soft_control_loop.programs import skill


@skill
def lead_rate_limited_p_step(
    base: float,
    measurement: float,
    previous,
    target: float,
    gain: float,
    lead: float,
    current: float,
    max_rise: float,
    low: float,
    high: float,
) -> float:
    """One update of a lead-compensated proportional controller with a rise limit.

    Args:
        base: The operating-point command, for example a classified feed plateau.
        measurement: The latest measurement, for example an acetate assay.
        previous: The measurement before it, or None if there is none yet.
        target: The setpoint for the measurement.
        gain: Proportional gain. The command rises when the estimate is below target.
        lead: Extrapolation factor applied to the last measurement change.
        current: The command now applied, which the rise limit is measured from.
        max_rise: The largest allowed increase over current in one update.
            Decreases are not limited.
        low: The lower actuator limit.
        high: The upper actuator limit.

    Returns:
        The new command. The estimate is measurement + lead * (measurement - previous),
        or measurement if previous is None. The candidate
        base + gain * (target - estimate) is capped at current + max_rise and then
        clamped to [low, high].
    """
    if previous is not None:
        estimate = measurement + lead * (measurement - previous)
    else:
        estimate = measurement
    candidate = base + gain * (target - estimate)
    candidate = min(candidate, current + max_rise)
    return max(low, min(high, candidate))
