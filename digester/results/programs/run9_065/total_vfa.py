import math

from soft_control_loop.programs import skill


VFA_KEYS = ('vfa_s_va', 'vfa_s_bu', 'vfa_s_pro', 'vfa_s_ac')


@skill
def total_vfa(observation):
    """Total VFA from the four assay observations, or None if the assay is invalid.

    Reads ``vfa_s_va``, ``vfa_s_bu``, ``vfa_s_pro`` and ``vfa_s_ac`` from the
    observation mapping and adds them in that order. If any value is
    missing, cannot be converted to float, is not finite, or is negative,
    the assay is treated as unavailable and None is returned. Missing
    values count as invalid, so a partial assay never gives a total.

    Typical use: read the delayed lab assay when ``assay_age`` is 0 and
    feed the total VFA to a controller or a model calibration.

    Args:
        observation: mapping of observation names to values.

    Returns:
        float or None: the summed total VFA, or None when the assay is
        invalid.
    """
    total = 0.0
    for name in VFA_KEYS:
        try:
            value = float(observation.get(name, -1.0))
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value) or value < 0.0:
            return None
        total += value
    return total
