import math

from soft_control_loop.programs import skill


def _solve_linear(mat, rhs):
    d = len(rhs)
    a = [row[:] + [rhs[i]] for i, row in enumerate(mat)]
    for i in range(d):
        piv = i
        for r in range(i + 1, d):
            if abs(a[r][i]) > abs(a[piv][i]):
                piv = r
        if abs(a[piv][i]) < 1e-12:
            return None
        a[i], a[piv] = a[piv], a[i]
        inv = 1.0 / a[i][i]
        for c in range(i, d + 1):
            a[i][c] *= inv
        for r in range(d):
            if r != i:
                factor = a[r][i]
                for c in range(i, d + 1):
                    a[r][c] -= factor * a[i][c]
    return [a[i][d] for i in range(d)]


@skill
def ridge_linear_fit(xs, ys, ridge):
    """Fit y = intercept + sum(w_j * x_j) by ridge least squares.

    The regressors and the response are centered on their sample means.
    The normal equations of the centered data, with ``ridge`` added to
    every diagonal entry, are solved by Gauss-Jordan elimination with
    partial pivoting. The weights are the solution. The intercept is
    ``mean(y) - sum(w_j * mean(x_j))``, so it is not penalized. Only the
    paired prefix of ``xs`` and ``ys`` is used. The dimension is the length
    of the first regressor vector, and all vectors must share it.

    Typical use: learn an online model of the methane flow from the last
    few feed commands (``xs`` holds the lagged command vectors and ``ys``
    the measured ch4_flow). A gap between the measured and the predicted
    gas then hints at a VFA build-up between lab assays. Refit when new
    data arrive and keep the previous model when this returns None.

    Args:
        xs: sequence of regressor vectors (sequences of floats).
        ys: sequence of response values, one per regressor vector.
        ridge: the non-negative penalty added to the diagonal.

    Returns:
        tuple(float, list of float) or None: ``(intercept, weights)``.
        None when there are no samples, when a pivot falls below 1e-12,
        or when a weight is not finite.
    """
    n = min(len(xs), len(ys))
    if n < 1:
        return None
    d = len(xs[0])
    x_mean = [sum(xs[i][j] for i in range(n)) / n for j in range(d)]
    y_mean = sum(ys[:n]) / n
    mat = [[0.0] * d for _ in range(d)]
    rhs = [0.0] * d
    for i in range(n):
        dx = [xs[i][j] - x_mean[j] for j in range(d)]
        dy = ys[i] - y_mean
        for j in range(d):
            rhs[j] += dx[j] * dy
            for k in range(d):
                mat[j][k] += dx[j] * dx[k]
    for j in range(d):
        mat[j][j] += ridge
    weights = _solve_linear(mat, rhs)
    if weights is None or not all(math.isfinite(w) for w in weights):
        return None
    intercept = y_mean - sum(weights[j] * x_mean[j] for j in range(d))
    return intercept, weights
