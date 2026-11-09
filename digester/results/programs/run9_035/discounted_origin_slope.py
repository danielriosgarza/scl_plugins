from soft_control_loop.programs import skill


@skill
def discounted_origin_slope(xs, ys, discount=0.9, min_denominator=1.0):
    """Fit y = k * x through the origin with discounted least squares.

    The samples are ordered from oldest to newest. Sample ``i`` gets the
    weight ``discount ** (last - i)``, where ``last`` is the index of the
    newest sample, so the newest sample has weight 1. The slope is
    ``sum(w * x * y) / max(min_denominator, sum(w * x * x))``. The
    denominator floor stops the fit from blowing up when the regressor is
    near zero, for example when there is no recent feed. If ``xs`` and
    ``ys`` have different lengths, only the paired prefix is used. An
    empty input returns 0.0.

    Typical use: estimate a process strength online from the gas response
    to the feed. Here ``x`` is the feed-driven gas term and ``y`` is the
    measured gas increment. Clip the result to the plausible range
    afterwards.

    Args:
        xs: sequence of regressor values, oldest first.
        ys: sequence of response values, oldest first.
        discount: weight factor per step back in time, in (0, 1].
        min_denominator: the lower bound on the weighted sum of x squared.

    Returns:
        float: the fitted slope.
    """
    numerator = 0.0
    denominator = 0.0
    last = min(len(xs), len(ys)) - 1
    for i, (x, y) in enumerate(zip(xs, ys)):
        weight = discount ** (last - i)
        numerator += weight * x * y
        denominator += weight * x * x
    return numerator / max(min_denominator, denominator)
