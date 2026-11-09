import math

from soft_control_loop.programs import skill


@skill
def read_number(observation, key, default=0.0):
    """Read one observation value as a finite float, or a default.

    Looks up ``key`` in the observation mapping, using ``default`` when the
    key is missing, and converts the value to float. If the conversion
    fails (TypeError or ValueError) or the result is not finite (NaN or
    infinite), ``default`` is returned unchanged. Unlike ``total_vfa``,
    negative values are accepted, so the reader also works for signed
    fields and sentinel values such as ``assay_age == -1``.

    Typical use: read the decision clock (``4 * day``), the methane flow or
    the assay age without letting a bad value crash or poison the
    controller, for example ``read_number(observation, 'ch4_flow', 1700.0)``.

    Args:
        observation: mapping of observation names to values.
        key: the observation name to read.
        default: the value returned when the reading is missing or invalid.

    Returns:
        float: the finite reading, or ``default``.
    """
    try:
        value = float(observation.get(key, default))
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default
