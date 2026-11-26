"""Carbonate-equilibrium pH estimate fused with the probe pH."""

import math

from soft_control_loop.programs import skill


@skill
def carbonate_ph_fusion(probe_ph, inorganic_carbon, p_co2, acid_shift=0.0,
                        ic_drop=0.0, pka1=6.280, kh_co2=27.1,
                        mm_per_cod=15.6, probe_weight=0.50):
    """Return (ph_fused, ph_safety).

    probe_ph: smoothed probe pH.
    inorganic_carbon: lab inorganic carbon (mM), or None.
    p_co2: smoothed CO2 partial pressure of the gas (bar), or None.
    acid_shift: estimated acids now minus the lab acids (kgCOD/m3); each
        unit consumes about mm_per_cod mM of bicarbonate.
    ic_drop: projected change of inorganic carbon since the lab sample (mM).
    probe_weight: weight of the probe in the fused pH.

    pH_chem = pKa1 + log10(HCO3 / CO2_aq) with CO2_aq = kh_co2 * p_co2 and
    HCO3 = IC + ic_drop - CO2_aq - acid protons. The fused pH has lower
    noise than the probe. ph_safety = min(probe, chemical), so multi-step
    positive probe-noise streaks cannot blind safety guards. Without valid
    inputs both values are the probe pH.
    """
    if inorganic_carbon is None or p_co2 is None or p_co2 <= 0.02:
        return probe_ph, probe_ph
    co2_aq = kh_co2 * p_co2
    shift = acid_shift
    if shift < -2.5:
        shift = -2.5
    if shift > 5.0:
        shift = 5.0
    dvfa_mm = mm_per_cod * shift
    hco3_est = max(1.0, inorganic_carbon + ic_drop - co2_aq - dvfa_mm)
    ph_chem = pka1 + math.log10(hco3_est / max(co2_aq, 0.1))
    ph_fused = probe_weight * probe_ph + (1.0 - probe_weight) * ph_chem
    ph_safety = min(probe_ph, ph_chem)
    return ph_fused, ph_safety
