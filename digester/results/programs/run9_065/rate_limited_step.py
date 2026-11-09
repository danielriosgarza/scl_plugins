from soft_control_loop.programs import skill


@skill
def rate_limited_step(current, target, max_step):
    """Advance a rate-limited quantity one decision toward a target.

    Computes ``target - current``, clips that change to the range
    [-``max_step``, ``max_step``], and adds it to ``current``. This
    models an actuator whose output cannot change by more than
    ``max_step`` per decision. A typical case is a feed pump that
    follows the commanded rate.

    Typical use: rebuild the actual pump feed history from past commands
    (``flows.append(rate_limited_step(flows[-1], command, 34.0))``). The
    history can then scale assay-based projections or drive a forecast
    model with the real feed instead of the command.

    Args:
        current: the value during the previous decision.
        target: the commanded value.
        max_step: the largest allowed change per decision (non-negative).

    Returns:
        float: the value after one decision.
    """
    delta = target - current
    delta = max(-max_step, min(max_step, delta))
    return current + delta
