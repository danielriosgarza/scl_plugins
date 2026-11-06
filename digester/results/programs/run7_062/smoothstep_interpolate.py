from soft_control_loop.programs import skill


@skill
def smoothstep_interpolate(x: float, knots) -> float:
    """Interpolate a scalar through a table of knots, easing smoothly between them.

    Args:
        x: The input value, for example a probe gain measured from the plant.
        knots: A sequence of (x_i, y_i) pairs sorted by x_i in ascending order.
            At least one knot is required.

    Returns:
        The first knot's y value if x <= x_0, and the last knot's y value if
        x >= x_last. Otherwise it returns y0 + s * (y1 - y0) for the bracketing
        pair, where t = (x - x0) / (x1 - x0) and s = t*t*(3 - 2t). This gives
        piecewise smooth curves with zero slope at every knot, so a small change
        in the measured input never makes the output jump.
    """
    knots = tuple(knots)
    if x <= knots[0][0]:
        return knots[0][1]
    if x >= knots[-1][0]:
        return knots[-1][1]
    for (x0, y0), (x1, y1) in zip(knots, knots[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            s = t * t * (3.0 - 2.0 * t)
            return y0 + s * (y1 - y0)
    return knots[-1][1]
