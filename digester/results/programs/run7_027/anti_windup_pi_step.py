from soft_control_loop.programs import skill


@skill
def anti_windup_pi_step(
    base: float,
    proportional: float,
    integral: float,
    increment: float,
    derivative: float,
    low: float,
    high: float,
) -> tuple[float, float]:
    """One update of a PI(D) controller with conditional-integration anti-windup.

    Args:
        base: The feedforward or operating-point command, for example a
            classified feed plateau.
        proportional: The proportional term, already scaled (Kp * error).
        integral: The integral term accumulated so far, already scaled.
        increment: The proposed change to the integral term for this update
            (for example Ki * error * dt).
        derivative: The derivative or rate-penalty term, already scaled.
            Pass 0.0 for a pure PI controller.
        low: The lower actuator limit.
        high: The upper actuator limit.

    Returns:
        A pair (command, integral). The candidate command
        base + proportional + (integral + increment) + derivative is formed
        first. The increment is kept only if that candidate lies within
        [low, high], or if it lies above high and the increment is negative,
        or below low and the increment is positive. Otherwise the old integral
        is kept. The command is base + proportional + integral + derivative,
        using the integral that was kept, clamped to [low, high].
    """
    candidate_integral = integral + increment
    candidate = base + proportional + candidate_integral + derivative
    if (
        low <= candidate <= high
        or (candidate > high and increment < 0.0)
        or (candidate < low and increment > 0.0)
    ):
        integral = candidate_integral
    command = max(low, min(high, base + proportional + integral + derivative))
    return command, integral
