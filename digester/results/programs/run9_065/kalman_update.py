from soft_control_loop.programs import skill


@skill
def kalman_update(predicted, prior_var, observed, observation_var):
    """One scalar Kalman measurement update.

    Computes the gain ``prior_var / (prior_var + observation_var)``. It then
    returns the posterior estimate ``predicted + gain * (observed - predicted)``
    and the posterior variance ``(1 - gain) * prior_var``. When the total
    variance is not positive, so that no gain can be formed, the prediction
    and the prior variance are returned unchanged. The caller applies any
    physical bounds afterwards, for example ``max(0.0, value)`` for a
    concentration.

    Typical use: correct a model-replayed state, such as total VFA at the
    sample time of a delayed lab assay, with the assay value. Propagate the
    variance through the model from the last anchor, add process noise, and
    pass it here with the assay variance.

    Args:
        predicted: the model prediction of the state at the measurement time.
        prior_var: the variance of that prediction (non-negative).
        observed: the measured value.
        observation_var: the measurement noise variance (positive).

    Returns:
        tuple(float, float): the posterior value and the posterior variance.
    """
    total = prior_var + observation_var
    if not total > 0.0:
        return float(predicted), float(prior_var)
    gain = prior_var / total
    value = predicted + gain * (observed - predicted)
    variance = (1.0 - gain) * prior_var
    return value, variance
