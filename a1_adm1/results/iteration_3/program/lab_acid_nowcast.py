"""Delay-compensated nowcast of digester acids from the last lab sample."""

from soft_control_loop.programs import skill

A_CARB = 143.5         # organic acid COD produced per m3 concentrate
A_SLUDGE_NOM = 23.6    # nominal organic acid COD produced per m3 sludge
K_CH4 = 2.238          # organic acid COD consumed per m3 atmospheric CH4


def _acid_step(vfa, carb, sludge, ch4_atm, a_sludge, inflow_mean, volume, dt):
    q_s = sludge + inflow_mean
    rate = (
        A_CARB * carb
        + a_sludge * q_s
        - K_CH4 * ch4_atm
        - (q_s + carb) * vfa
    )
    return max(0.0, vfa + rate * dt / volume)


@skill
def lab_acid_nowcast(memory, carb_rate, sludge_rate, ch4_atm, lab_vfa, lab_age,
                     fresh_age=4, inflow_mean=84.0, volume=3400.0, dt=0.25,
                     start_vfa=0.24):
    """Return (vfa_est, a_sludge): present-time total acids and sludge acid yield.

    memory: the program's memory dict; keeps 'acid_hist', 'a_sludge' and
        'prev_lab_vfa'.
    carb_rate, sludge_rate: the feed rates applied this step (m3/d).
    ch4_atm: pressure-corrected methane flow (m3/d at atmospheric pressure).
    lab_vfa: total lab VFA in kgCOD/m3 (sum of va, bu, pro, ac times 1000),
        or None when the lab has given no value.
    lab_age: steps since the lab sample was taken; fresh_age is its value on
        the step a new sample arrives.
    inflow_mean: mean unobserved incoming sludge flow; volume: liquid volume;
    dt: step length in days; start_vfa: acids before any lab value.

    The lab total is lab_age steps old. Integrating the acid balance forward
    from it over the recorded feeds and methane flows gives the acids now
    (RMSE about 0.16 kgCOD/m3). On each fresh sample the sludge acid yield
    is corrected from the error of the previous prediction, bounded to
    [14, 36].
    """
    span = 2 * int(fresh_age)
    hist = memory.get("acid_hist", [])
    hist.append((carb_rate, sludge_rate, ch4_atm))
    if len(hist) > span:
        hist = hist[-span:]
    memory["acid_hist"] = hist
    a_sludge = memory.get("a_sludge", A_SLUDGE_NOM)

    if lab_vfa is not None and lab_age is not None:
        if lab_age == fresh_age:
            prev_lab_vfa = memory.get("prev_lab_vfa")
            if prev_lab_vfa is not None and len(hist) == span:
                pred_lab = prev_lab_vfa
                sum_s = 0.0
                for ck, sk, ch4k in hist[0:int(fresh_age)]:
                    pred_lab = _acid_step(pred_lab, ck, sk, ch4k, a_sludge,
                                          inflow_mean, volume, dt)
                    sum_s += (sk + inflow_mean) * dt / volume
                da = (lab_vfa - pred_lab) / max(sum_s, 0.02)
                a_sludge = min(36.0, max(14.0, a_sludge + 0.35 * da))
                memory["a_sludge"] = a_sludge
            memory["prev_lab_vfa"] = lab_vfa
        vfa_est = lab_vfa
        for ck, sk, ch4k in hist[-int(lab_age):]:
            vfa_est = _acid_step(vfa_est, ck, sk, ch4k, a_sludge,
                                 inflow_mean, volume, dt)
    else:
        vfa_est = start_vfa
        for ck, sk, ch4k in hist[1:]:
            vfa_est = _acid_step(vfa_est, ck, sk, ch4k, a_sludge,
                                 inflow_mean, volume, dt)
    return vfa_est, a_sludge
