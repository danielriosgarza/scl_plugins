"""Forecast of the settling level of the inorganic-carbon reserve."""

import math

from soft_control_loop.programs import skill


def _clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


@skill
def ic_settling_forecast(
    memory,
    ic_raw,
    vfa_total,
    fresh,
    carb_rate,
    sludge_rate,
    carb_day,
    sludge_day,
    win=6,
    stride=5,
    volume=3400.0,
    inflow_mean=84.0,
    vfa_free=0.45,
    ic_per_vfa=13.0,
    start_ic=140.0,
    start_sludge=85.0,
):
    """Return the predicted settling level of inorganic carbon (mM).

    memory: the program's memory dict; keeps 'ic_buf', 'cb_buf', 'sl_buf'.
    ic_raw: lab inorganic carbon (mM), or None when the lab gave no value.
    vfa_total: latest lab total VFA (kgCOD/m3); acids above vfa_free have
        displaced about ic_per_vfa mM of bicarbonate per kgCOD/m3, which is
        added back so a transient acid wave does not look like lost reserve.
    fresh: True on the step a new lab sample arrives (lab_age at its smallest).
    carb_rate, sludge_rate: feed rates applied now (m3/d).
    carb_day, sludge_day: day-smoothed feed rates (EMA weight 0.25 per step).
    win, stride: length and spacing (in daily samples) of the three windows.
    volume, inflow_mean: liquid volume and mean unobserved inflow, which
        bound the decay ratio through the hydraulic residence time.
    start_ic: value returned before any lab sample.

    The IC reserve drifts slowly towards a level set by the feed. The
    instantaneous lab value lags that level and single samples are noisy.
    Window means y2, y1, y0 give two differences; their ratio, bounded by
    the hydraulic residence time, extrapolates the exponential approach.
    Small or inconsistent changes fall back to 0.7*y0 + 0.3*y1. A lead term
    then accounts for feed changes made after the newest window.
    """
    w = int(win)
    s = int(stride)
    buf_max = w + 2 * s
    rate_max = w + s
    if ic_raw is not None:
        excess = max(0.0, vfa_total - vfa_free) if vfa_total is not None else 0.0
        sample = ic_raw + ic_per_vfa * excess
        if "ic_buf" not in memory:
            memory["ic_buf"] = [sample] * buf_max
            memory["cb_buf"] = [0.0] * (rate_max - 1) + [carb_day]
            memory["sl_buf"] = [start_sludge] * (rate_max - 1) + [sludge_day]
        elif fresh:
            ic_buf = memory["ic_buf"]
            ic_buf.append(sample)
            memory["ic_buf"] = ic_buf[-buf_max:]
            cb_buf = memory["cb_buf"]
            cb_buf.append(carb_day)
            memory["cb_buf"] = cb_buf[-rate_max:]
            sl_buf = memory["sl_buf"]
            sl_buf.append(sludge_day)
            memory["sl_buf"] = sl_buf[-rate_max:]

    ic_buf = memory.get("ic_buf", [])
    cb_buf = memory.get("cb_buf", [])
    sl_buf = memory.get("sl_buf", [])
    if not ic_buf:
        return start_ic

    y0 = sum(ic_buf[-w:]) / w
    y1 = sum(ic_buf[-w - s : -s]) / w
    y2 = sum(ic_buf[-w - 2 * s : -2 * s]) / w

    d1 = y1 - y2
    d0 = y0 - y1
    net_two_stride = y0 - y2

    cb_w0 = sum(cb_buf[-w:]) / w
    cb_w1 = sum(cb_buf[-w - s : -s]) / w
    sl_w0 = sum(sl_buf[-w:]) / w

    tau_hrt = volume / max(250.0, sludge_day + carb_day + inflow_mean)
    r_min = math.exp(-s / (0.75 * tau_hrt))
    r_max = math.exp(-s / (1.65 * tau_hrt))

    if d0 < -0.6 and net_two_stride < -1.2:
        if d1 < -0.6:
            r = _clamp(d0 / d1, r_min, r_max)
        elif cb_w0 > cb_w1 + 2.0:
            r = 0.55 * r_min + 0.45 * r_max
        else:
            r = 0.50 * (r_min + r_max)
        ic_win_inf = y0 + (r / (1.0 - r)) * d0
    elif d0 > 0.8 and net_two_stride > 1.5:
        r_up = (d0 / d1) if d1 > 0.8 else r_min
        r = _clamp(r_up, r_min, 0.50)
        ic_win_inf = y0 + (r / (1.0 - r)) * d0
    else:
        ic_win_inf = 0.70 * y0 + 0.30 * y1

    cb_ref = 0.65 * carb_rate + 0.35 * carb_day
    sl_ref = 0.65 * sludge_rate + 0.35 * sludge_day
    dcb = cb_ref - cb_w0
    dsl = sl_ref - sl_w0
    cb_lead = -0.34 * dcb if dcb > 0.0 else -0.26 * dcb
    sl_lead = 0.06 * dsl if dsl > 0.0 else 0.09 * dsl

    return ic_win_inf + cb_lead + sl_lead
