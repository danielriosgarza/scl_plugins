from soft_control_loop.programs import skill


@skill
def calibrate_by_bisection(predict, target, lo, hi, iterations=28):
    """Fit a scalar parameter so that a prediction matches an observed value.

    Bisects the interval [``lo``, ``hi``] for ``iterations`` steps. At each
    step the midpoint ``mid`` is evaluated. If ``predict(mid) < target`` the
    lower bound moves up to ``mid``, otherwise the upper bound moves down to
    ``mid``. The midpoint of the final interval is returned. This assumes
    ``predict`` does not decrease as the parameter grows. If the target lies
    outside the predicted range, the result settles at the nearest bound.

    Typical use: calibrate a process strength or rate so that replaying a
    model from one lab assay to the next reproduces the later assay, for
    example total VFA.

    Args:
        predict: callable(parameter: float) -> float. Gives the model
            prediction for a candidate parameter value.
        target: the observed value that the prediction should match.
        lo: the lower bound of the parameter search interval.
        hi: the upper bound of the parameter search interval.
        iterations: the number of bisection steps.

    Returns:
        float: the calibrated parameter, which is the midpoint of the final
        interval.
    """
    lo = float(lo)
    hi = float(hi)
    for _ in range(int(iterations)):
        mid = 0.5 * (lo + hi)
        if predict(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
