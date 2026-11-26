"""Extremum-seeking hold at digester net-methane capacity after acetate-regulated startup."""

from carbonate_ph_fusion import carbonate_ph_fusion
from ic_settling_forecast import ic_settling_forecast
from lab_acid_nowcast import lab_acid_nowcast
from startup_vfa_wave_done import startup_vfa_wave_done

TUNED = {
    "acetate_work": 2.93478,
    "vfa_limit_ss": 0.967516,
    "cut_gain": 15.2439,
    "ph_target": 6.59845,
    "ph_gain": 35.1956,
    "sludge_max": 479.519,
    "sludge_per_carb": 1.59599,
    "hold_move": 0.621007,
    "hold_avg_len": 16.0147,
    "hold_deadband": 232.908,
}

RANGES = {
    "acetate_work": [0.6, 6.0],
    "vfa_limit_ss": [0.55, 1.25],
    "cut_gain": [4.0, 40.0],
    "ph_target": [6.0, 7.35],
    "ph_gain": [10.0, 100.0],
    "sludge_max": [85.0, 1000.0],
    "sludge_per_carb": [0.65, 6.5],
    "hold_move": [0.05, 2.0],
    "hold_avg_len": [8.0, 40.0],
    "hold_deadband": [10.0, 400.0],
}

SUBGOAL_NAME = "hold_the_capacity"

# Physical constants of the digester (ADM1 / BSM2)
V_LIQ = 3400.0         # liquid volume, m3
DT = 0.25              # 6-hour decision interval, days
S_IN_MEAN = 84.0       # mean unobserved incoming sludge, m3/d
P_H2O_35C = 0.0557     # water vapor pressure at 35 C, bar
P_ATM = 1.01325        # atmospheric pressure, bar

# Stoichiometric acid mass-balance coefficients (kgCOD_acid per m3)
A_CARB = 143.5         # organic acid COD produced per m3 concentrate
K_CH4 = 2.238          # organic acid COD consumed per m3 atmospheric CH4

# Startup and hold-guard constants
STARTUP_PH_FLOOR = 6.63835
VFA_LOOKAHEAD = 1.35264
EXIT_VFA = 1.80583
STARTUP_SLUDGE_SHARE = 0.671386
P_GAS_RISE_BAND = 0.015
IC_SAFE_FLOOR = 52.0


def _clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def act(observation, memory):
    curr_sludge = observation.get("sludge_rate")
    if curr_sludge is None:
        curr_sludge = 85.0
    curr_carb = observation.get("carbohydrate_rate")
    if curr_carb is None:
        curr_carb = 0.0

    ph_raw = observation.get("ph")
    ch4_flow = observation.get("ch4_flow")
    co2_flow = observation.get("co2_flow")
    ch4_pressure = observation.get("ch4_pressure")
    vfa_va = observation.get("vfa_s_va")
    vfa_bu = observation.get("vfa_s_bu")
    vfa_pro = observation.get("vfa_s_pro")
    vfa_ac = observation.get("vfa_s_ac")
    ic_raw = observation.get("inorganic_carbon")
    lab_age = observation.get("lab_age")

    # 1. Median-of-3 + EMA filter on probe pH
    if ph_raw is not None:
        ph_win = memory.get("ph_win", [])
        ph_win.append(ph_raw)
        if len(ph_win) > 3:
            ph_win = ph_win[-3:]
        memory["ph_win"] = ph_win
        ph_med = sorted(ph_win)[len(ph_win) // 2]
        if "ema_ph" not in memory:
            memory["ema_ph"] = ph_med
        else:
            alpha_ph = 0.20 if memory.get("hold_active", False) else 0.24
            memory["ema_ph"] = alpha_ph * ph_med + (1.0 - alpha_ph) * memory["ema_ph"]
    ema_ph = memory.get("ema_ph", 7.35)

    # 2. Pressure-corrected atmospheric methane flow, CO2 partial pressure, and gas pressure
    if ch4_flow is not None and co2_flow is not None and ch4_pressure is not None:
        total_gas = max(ch4_flow + co2_flow, 1.0)
        co2_share = co2_flow / total_gas
        p_co2 = ch4_pressure * (co2_flow / max(ch4_flow, 1.0))
        p_gas = ch4_pressure * (total_gas / max(ch4_flow, 1.0)) + P_H2O_35C
        ch4_atm = ch4_flow * (p_gas / P_ATM)
        if "ema_ch4_atm" not in memory:
            memory["ema_ch4_atm"] = ch4_atm
            memory["ema_ch4_slow"] = ch4_atm
            memory["ema_co2_share"] = co2_share
            memory["ema_pco2"] = p_co2
            memory["ema_pgas"] = p_gas
        else:
            memory["ema_ch4_atm"] = 0.60 * ch4_atm + 0.40 * memory["ema_ch4_atm"]
            memory["ema_ch4_slow"] = 0.28 * ch4_atm + 0.72 * memory["ema_ch4_slow"]
            memory["ema_co2_share"] = 0.50 * co2_share + 0.50 * memory["ema_co2_share"]
            memory["ema_pco2"] = 0.55 * p_co2 + 0.45 * memory["ema_pco2"]
            memory["ema_pgas"] = 0.25 * p_gas + 0.75 * memory["ema_pgas"]
    else:
        ch4_atm = memory.get("ema_ch4_atm", 1800.0)
        p_gas = memory.get("ema_pgas", 1.07)
    ema_ch4_atm = memory.get("ema_ch4_atm", ch4_atm)
    ema_ch4_slow = memory.get("ema_ch4_slow", ch4_atm)
    ema_co2_share = memory.get("ema_co2_share", 0.38)
    ema_pco2 = memory.get("ema_pco2")

    # 3. Laboratory inorganic carbon fast EMA & daily trend
    ic_rate = memory.get("ic_rate", 0.0)
    if ic_raw is not None:
        if "ema_ic" not in memory:
            memory["ema_ic"] = ic_raw
            memory["ic_prev"] = ic_raw
        elif lab_age == 4:
            memory["ema_ic"] = 0.60 * ic_raw + 0.40 * memory["ema_ic"]
            ic_prev = memory.get("ic_prev", ic_raw)
            ic_rate = 0.40 * (ic_raw - ic_prev) + 0.60 * ic_rate
            memory["ic_rate"] = ic_rate
            memory["ic_prev"] = ic_raw
    ema_ic = memory.get("ema_ic", 145.0)

    # 4. Present-time acid forecast via mass balance from last lab sample
    last_pro = memory.get("last_pro", 0.02)
    lab_vfa = None
    if (
        vfa_va is not None
        and vfa_bu is not None
        and vfa_pro is not None
        and vfa_ac is not None
        and lab_age is not None
    ):
        lab_vfa = 1000.0 * (vfa_va + vfa_bu + vfa_pro + vfa_ac)
        last_pro = 1000.0 * vfa_pro
        memory["last_pro"] = last_pro
    vfa_est, a_sludge = lab_acid_nowcast(
        memory, curr_carb, curr_sludge, ch4_atm, lab_vfa, lab_age
    )
    ema_vfa = memory.get("ema_vfa", vfa_est)
    ema_vfa = 0.45 * vfa_est + 0.55 * ema_vfa
    memory["ema_vfa"] = ema_vfa

    # Daily-smoothed pump rates and inorganic-carbon settling forecast
    carb_day = memory.get("carb_day", curr_carb)
    sludge_day = memory.get("sludge_day", curr_sludge)
    carb_day = 0.25 * curr_carb + 0.75 * carb_day
    sludge_day = 0.25 * curr_sludge + 0.75 * sludge_day
    memory["carb_day"] = carb_day
    memory["sludge_day"] = sludge_day

    ic_forecast = ic_settling_forecast(
        memory,
        ic_raw,
        lab_vfa,
        lab_age == 4,
        curr_carb,
        curr_sludge,
        carb_day,
        sludge_day,
    )

    # Measured net methane at atmospheric pressure minus 0.395 * acids leaving
    outflow = curr_sludge + curr_carb + S_IN_MEAN
    acids_for_nm = lab_vfa if lab_vfa is not None else vfa_est
    nm_inst = ch4_atm - 0.395 * acids_for_nm * outflow

    # Track reserve corrected for acid protons
    reserve_rate = memory.get("reserve_rate", 0.0)
    if lab_age == 4 and lab_vfa is not None and ic_raw is not None:
        reserve = ic_raw + 15.6 * lab_vfa
        reserve_rate = 0.45 * (reserve - memory.get("reserve", reserve)) + 0.55 * reserve_rate
        memory["reserve"] = reserve
        memory["reserve_rate"] = reserve_rate

    # 4b. Carbonate-equilibrium chemical pH estimate fused with probe pH
    if (
        ic_raw is not None
        and lab_age is not None
        and lab_vfa is not None
        and ema_pco2 is not None
        and ema_pco2 > 0.02
    ):
        ic_drop = _clamp(reserve_rate + 1.5, -14.0, 0.0) * lab_age * DT
        ic_for_ph = ic_raw
        if memory.get("startup_complete", False):
            reserve = memory["reserve"]
            if lab_age == 4 or "filtered_reserve" not in memory:
                previous = memory.get("filtered_reserve", reserve)
                memory["filtered_reserve"] = 0.45 * reserve + 0.55 * previous
            ic_for_ph += _clamp(memory["filtered_reserve"] - reserve, -6.0, 6.0)
        ph_fused, ph_safety = carbonate_ph_fusion(
            ema_ph, ic_for_ph, ema_pco2, vfa_est - lab_vfa, ic_drop
        )
    else:
        ph_fused = ema_ph
        ph_safety = ema_ph

    if "ema_ph_slow" not in memory:
        memory["ema_ph_slow"] = ph_fused
    else:
        memory["ema_ph_slow"] = 0.14 * ph_fused + 0.86 * memory["ema_ph_slow"]
    ema_ph_slow = memory["ema_ph_slow"]

    # Current instantaneous net acid accumulation rate (kgCOD/m3 per day)
    q_s_now = curr_sludge + S_IN_MEAN
    d_est = (q_s_now + curr_carb) / V_LIQ
    vfa_rate = (
        A_CARB * curr_carb
        + a_sludge * q_s_now
        - K_CH4 * ema_ch4_atm
        - (q_s_now + curr_carb) * vfa_est
    ) / V_LIQ
    # Smoothed acid accumulation rate for hold-phase noise immunity
    vfa_rate_slow = (
        A_CARB * curr_carb
        + a_sludge * q_s_now
        - K_CH4 * ema_ch4_slow
        - (q_s_now + curr_carb) * ema_vfa
    ) / V_LIQ

    if not memory.get("startup_complete", False):
        if lab_vfa is not None:
            ac = 1000.0 * vfa_ac
            ac_share = ac / max(lab_vfa, 0.01)
            if lab_age == 4:
                previous = memory.get("lab_acid_pair", (ac, lab_vfa))
                memory["composition_trend"] = (ac - previous[0]) - ac_share * (lab_vfa - previous[1])
                memory["lab_acid_pair"] = (ac, lab_vfa)
            acetate = _clamp(
                ac + ac_share * (vfa_est - lab_vfa)
                + 0.5 * lab_age * DT * memory.get("composition_trend", 0.0),
                0.0,
                vfa_est,
            )
        else:
            ac_share = 0.70
            acetate = ac_share * vfa_est

        feed = curr_sludge + curr_carb
        feed_history = (memory.get("recent_feed", []) + [feed])[-5:]
        memory["recent_feed"] = feed_history
        sampled_feed = feed_history[0]
        if lab_age == 4 and lab_vfa is not None and lab_vfa > memory.get("startup_vfa_peak", 0.0):
            memory["wave_feed"] = sampled_feed
        wave_done = startup_vfa_wave_done(memory, lab_vfa, lab_age == 4)
        if (
            wave_done
            and lab_vfa is not None
            and max(lab_vfa, vfa_est) < EXIT_VFA
            and min(feed, sampled_feed) >= memory.get("wave_feed", feed)
        ):
            memory["startup_complete"] = True

    if not memory.get("startup_complete", False):
        floor = STARTUP_PH_FLOOR
        predicted = acetate + ac_share * VFA_LOOKAHEAD * max(-0.5, vfa_rate)
        target = TUNED["acetate_work"] * _clamp((ph_safety - floor) / 0.22, 0.20, 1.0)
        target = min(
            target,
            0.65 + TUNED["acetate_work"] * _clamp((0.19 - d_est) / 0.065, 0.0, 1.0),
        )
        if ic_raw is not None:
            target = min(
                target,
                0.65 + TUNED["acetate_work"] * _clamp((ema_ic - 63.0) / 43.0, 0.0, 1.0),
            )
        change = 10.0
        if predicted >= target:
            recovery = _clamp(1.0 + vfa_rate / 0.45, 0.0, 1.0)
            change = -min(10.0, 4.0 * (predicted - target)) * recovery
        ph_lead = ph_fused + min(0.0, ph_fused - ema_ph_slow)
        buffer_margin = 0.10 * _clamp((curr_carb - 100.0) / 65.0, 0.0, 1.0)
        change = max(-10.0, min(change, 85.0 * (min(ph_safety, ph_lead) - floor - buffer_margin)))
        carb = _clamp(curr_carb + change, 0.0, 300.0)
        share = STARTUP_SLUDGE_SHARE
        sludge = TUNED["sludge_max"]
        if share < 1.0:
            sludge = _clamp(carb * share / (1.0 - share) - S_IN_MEAN, 85.0, sludge)
        sludge = _clamp(sludge, curr_sludge - 34.0, curr_sludge + 34.0)
        return [float(sludge), float(carb)], SUBGOAL_NAME

    # Post-startup: update two-window history of net methane and gas pressure
    half_win = max(4, int(round(TUNED["hold_avg_len"])))
    win2 = 2 * half_win
    nm_hist = memory.get("nm_hist", [])
    pg_hist = memory.get("pg_hist", [])
    nm_hist.append(nm_inst)
    pg_hist.append(p_gas)
    if len(nm_hist) > win2:
        nm_hist = nm_hist[-win2:]
    if len(pg_hist) > win2:
        pg_hist = pg_hist[-win2:]
    memory["nm_hist"] = nm_hist
    memory["pg_hist"] = pg_hist

    # Forecasted acid level & effective limit
    ph_target = TUNED["ph_target"]
    ic_falling = _clamp((-ic_rate - 4.0) / 8.0, 0.0, 1.0) if (lab_vfa is None or lab_vfa < 1.35) else 0.0
    ph_falling = _clamp((ema_ph_slow - ph_fused - 0.030) / 0.050, 0.0, 1.0)
    drop_risk = max(ic_falling, ph_falling)

    in_hold = memory.get("hold_active", False)
    urgent = (
        ph_safety < 6.68
        or (ema_ph_slow - ph_fused > 0.045 and ph_safety < 6.72)
        or (lab_vfa is not None and lab_vfa >= 1.05)
        or (
            vfa_est >= 1.38
            and (ph_safety < 6.72 or (lab_vfa is not None and lab_vfa >= 0.88))
        )
    )
    if in_hold and not urgent:
        vfa_base = ema_vfa
        rate_for_guard = vfa_rate_slow
    else:
        vfa_base = max(ema_vfa, vfa_est) if (in_hold and urgent) else vfa_est
        rate_for_guard = max(vfa_rate_slow, vfa_rate) if (in_hold and urgent) else vfa_rate
    vfa_forecast = (
        vfa_base
        + 0.45 * VFA_LOOKAHEAD * max(0.0, rate_for_guard)
        + 0.35 * max(0.0, last_pro - 0.25)
    )

    startup_frac = (
        _clamp((0.175 - d_est) / 0.050, 0.0, 1.0)
        * _clamp((ph_fused - 6.89) / 0.15, 0.0, 1.0)
    )
    high_ph_margin = max(0.0, min(ph_fused, ema_ph_slow) - max(ph_target + 0.08, 6.72))
    ic_margin = _clamp((ema_ic - 68.0) / 16.0, 0.0, 1.0)
    vfa_ss_eff = min(
        1.18,
        TUNED["vfa_limit_ss"]
        + _clamp(1.8 * high_ph_margin, 0.0, 0.24) * ic_margin * (1.0 - drop_risk),
    )
    if ph_safety < 6.68:
        vfa_ss_eff = max(0.45, vfa_ss_eff - _clamp(2.0 * (6.68 - ph_safety), 0.0, 0.22))
    vfa_eff_limit = vfa_ss_eff + startup_frac * max(0.0, 2.00 - vfa_ss_eff)
    vfa_excess = max(0.0, vfa_forecast - vfa_eff_limit)

    acid_error = vfa_eff_limit - vfa_base
    acid_change = TUNED["cut_gain"] * (acid_error - VFA_LOOKAHEAD * rate_for_guard)
    ph_lead = ph_fused + min(0.0, ph_fused - ema_ph_slow)
    ph_change = TUNED["ph_gain"] * (ph_lead - ph_target)
    if ph_safety < ph_target - 0.03:
        ph_change = min(ph_change, 160.0 * (ph_safety - ph_target))
    if ema_co2_share > 0.504 and ph_safety < 6.76:
        ph_change -= 800.0 * (ema_co2_share - 0.504)

    # Track recent organic load
    sludge_equiv = a_sludge / A_CARB
    avg_carb = memory.get("avg_carb", curr_carb)
    avg_sludge = memory.get("avg_sludge", q_s_now)
    memory["avg_carb"] = avg_carb + 0.10 * (curr_carb - avg_carb)
    memory["avg_sludge"] = avg_sludge + 0.10 * (q_s_now - avg_sludge)
    recent_load = avg_carb + sludge_equiv * avg_sludge
    buffer_headroom = max(0.0, min(ph_fused, ema_ph_slow) - ph_target)
    load_limit = recent_load * (1.012 + min(0.14, 0.30 * buffer_headroom))
    load_limit += V_LIQ * max(0.0, 0.202 - d_est)

    # Stress latch: only on genuine pH crisis or confirmed acute VFA surge
    stressed = memory.get("hold_stressed", False)
    if in_hold:
        if (
            ph_safety < ph_target - 0.04
            or (ema_ph_slow - ph_fused > 0.075 and ph_safety < 6.64)
            or (vfa_est > 1.55 and ema_vfa > 1.35)
        ):
            stressed = True
        elif (
            stressed
            and ph_safety > ph_target + 0.04
            and vfa_excess <= 0.0
            and rate_for_guard <= 0.05
            and (lab_vfa is None or lab_vfa < vfa_eff_limit)
        ):
            stressed = False
            memory["hold_stressed"] = False
            if curr_carb < memory.get("pre_stress_carb", curr_carb) - 6.0:
                memory["hold_active"] = False
                in_hold = False
            else:
                memory["carb_es"] = curr_carb
                memory["flip_carb"] = curr_carb
                memory["drift_dir"] = 1.0
        if stressed and not memory.get("hold_stressed", False):
            memory["pre_stress_carb"] = curr_carb
        memory["hold_stressed"] = stressed

    if not in_hold:
        # Post-startup ramp up to capacity
        d_carb = _clamp(min(acid_change, ph_change), -10.0, 6.5)
        next_carb = _clamp(curr_carb + d_carb, 0.0, 300.0)
        next_carb = max(
            curr_carb - 10.0,
            0.0,
            min(next_carb, load_limit - sludge_equiv * (curr_sludge + S_IN_MEAN)),
        )
        if (
            len(nm_hist) >= win2
            and vfa_est < vfa_eff_limit
            and (lab_vfa is None or lab_vfa < vfa_eff_limit)
            and ph_safety > ph_target + 0.05
            and startup_frac < 0.15
            and abs(curr_carb - avg_carb) < 6.0
            and abs(curr_sludge - sludge_day) < 15.0
        ):
            memory["hold_active"] = True
            memory["hold_stressed"] = False
            memory["drift_dir"] = 1.0
            memory["carb_es"] = next_carb
            memory["flip_carb"] = next_carb
    else:
        # Hold phase: slow extremum-seeking drift with safe ceilings
        drift_dir = memory.get("drift_dir", 1.0)
        flip_carb = memory.get("flip_carb", curr_carb)
        req_move = TUNED["hold_move"] * half_win
        deadband = TUNED["hold_deadband"]

        if stressed:
            d_stress = _clamp(min(acid_change, ph_change, -3.0), -10.0, -2.0)
            next_carb = _clamp(curr_carb + d_stress, 0.0, 300.0)
            drift_dir = -1.0
            memory["flip_carb"] = next_carb
        else:
            signed_move = (curr_carb - flip_carb) * drift_dir
            if signed_move < -0.5:
                memory["flip_carb"] = curr_carb
            elif len(nm_hist) >= win2 and signed_move >= req_move:
                nm_prev = sum(nm_hist[:half_win]) / half_win
                nm_recent = sum(nm_hist[half_win:]) / half_win
                pg_prev = sum(pg_hist[:half_win]) / half_win
                pg_recent = sum(pg_hist[half_win:]) / half_win
                d_nm = nm_recent - nm_prev
                d_pg = pg_recent - pg_prev
                if drift_dir > 0.0:
                    near_peak = vfa_base > 0.72 * vfa_eff_limit or ph_safety < ph_target + 0.10
                    if near_peak and (
                        d_nm < -deadband
                        or (d_pg > P_GAS_RISE_BAND and d_nm <= 0.0)
                    ):
                        drift_dir = -1.0
                else:
                    if d_nm < -0.35 * deadband or (
                        vfa_base < 0.90 * vfa_eff_limit
                        and ph_safety > ph_target + 0.05
                        and d_nm <= 0.25 * deadband
                    ):
                        drift_dir = 1.0
                memory["flip_carb"] = curr_carb

            carb_es = memory.get("carb_es", curr_carb) + drift_dir * TUNED["hold_move"]
            if drift_dir > 0.0 and (
                (vfa_forecast > vfa_eff_limit - 0.02 and acid_change < 0.0)
                or (ph_lead < ph_target + 0.02 and ph_change < 0.0)
                or urgent
            ):
                carb_es = min(carb_es, curr_carb)
            next_carb = _clamp(carb_es, max(0.0, curr_carb - 10.0), min(300.0, curr_carb + 10.0))

            # Safety ceilings: gentle trim when healthy+mild, moderate when pH>=6.68, full -10 on pH<6.68
            healthy_state = (
                not urgent
                and lab_vfa is not None
                and lab_vfa < 0.88
                and ph_safety > 6.70
            )
            mild_excess = (
                not urgent
                and vfa_excess < 0.18
                and ph_safety > ph_target + 0.04
            )
            if vfa_forecast > vfa_eff_limit and acid_change < 0.0:
                if healthy_state:
                    max_acid_cut = -0.6
                elif mild_excess:
                    max_acid_cut = -1.5
                elif ph_safety >= 6.68 and vfa_est < 1.45:
                    max_acid_cut = -3.5
                else:
                    max_acid_cut = -10.0
                safe_acid = max(0.0, curr_carb + _clamp(acid_change, max_acid_cut, 0.0))
                if safe_acid < next_carb:
                    next_carb = safe_acid
                    if max_acid_cut <= -3.5:
                        memory["flip_carb"] = next_carb

            if ph_lead < ph_target or ph_safety < ph_target:
                p_ref = min(ph_lead, ph_safety) if ph_safety < ph_target + 0.04 else ph_lead
                ph_cut = TUNED["ph_gain"] * (p_ref - ph_target)
                if ph_safety < ph_target - 0.03:
                    ph_cut = min(ph_cut, 160.0 * (ph_safety - ph_target))
                if ema_co2_share > 0.504 and ph_safety < 6.76:
                    ph_cut -= 800.0 * (ema_co2_share - 0.504)
                max_ph_cut = -2.0 if (ph_safety > ph_target + 0.03 and ph_fused >= ema_ph_slow - 0.03) else -10.0
                safe_ph = max(0.0, curr_carb + _clamp(ph_cut, max_ph_cut, 0.0))
                if safe_ph < next_carb:
                    next_carb = safe_ph
                    if ph_safety < ph_target - 0.02:
                        memory["flip_carb"] = next_carb

            if ic_forecast < IC_SAFE_FLOOR:
                ic_cap = max(0.0, curr_carb - min(2.5, 0.35 * (IC_SAFE_FLOOR - ic_forecast)))
                if ic_cap < next_carb:
                    next_carb = ic_cap
                    memory["flip_carb"] = next_carb

        next_carb = _clamp(next_carb, max(0.0, curr_carb - 10.0), min(300.0, curr_carb + 10.0))
        memory["drift_dir"] = drift_dir
        memory["carb_es"] = next_carb

    # Sludge rate control: keep buffering when healthy, damp buffer push only when genuinely overloaded
    sludge_high = TUNED["sludge_max"]
    ic_buf = min(ic_forecast, ema_ic) if in_hold else (
        min(ic_raw, ema_ic) if ic_raw is not None else ema_ic
    )
    need_ph_buf = _clamp((ph_target + 0.22 - ph_safety) / 0.20, 0.0, 1.0)
    need_ic_buf = _clamp((108.0 - ic_buf) / 38.0, 0.0, 1.0) * _clamp(
        (7.04 - ph_fused) / 0.10, 0.0, 1.0
    )
    acid_climb = max(
        _clamp((vfa_base - 0.98) / 0.30, 0.0, 1.0) if rate_for_guard > 0.06 else 0.0,
        _clamp((vfa_excess - 0.08) / 0.18, 0.0, 1.0),
        _clamp((ph_falling - 0.40) / 0.60, 0.0, 1.0),
    )
    buf_need = max(need_ph_buf, need_ic_buf * (1.0 - 0.85 * acid_climb))

    if buf_need < 0.15 and curr_carb < 95.0:
        desired_sludge = 90.0 + 1.15 * curr_carb
    else:
        sludge_from_carb = TUNED["sludge_per_carb"] * max(curr_carb, next_carb * 0.90)
        sludge_from_buf = 180.0 + buf_need * (sludge_high - 180.0)
        desired_sludge = max(sludge_from_carb, sludge_from_buf)

    max_q_tot = 720.0 + 60.0 * _clamp((ema_ph_slow - ph_target) / 0.14, 0.0, 1.0) * _clamp((ema_ic - 66.0) / 14.0, 0.0, 1.0)
    hyd_sludge_cap = max(220.0, max_q_tot - S_IN_MEAN - next_carb)
    desired_sludge = _clamp(desired_sludge, 85.0, min(sludge_high, hyd_sludge_cap))

    if (stressed or vfa_excess > 0.15 or ph_safety < 6.59) and startup_frac < 0.25:
        acute = max(
            1.0 if stressed else 0.0,
            _clamp((vfa_excess - 0.45) / 0.75, 0.0, 1.0),
            _clamp((6.59 - ph_safety) / 0.12, 0.0, 1.0),
        )
        relief_floor = 380.0 - 120.0 * acute
        if curr_sludge > relief_floor:
            sludge_cut = 160.0 * max(0.0, vfa_excess - 0.15) + 120.0 * acute
            desired_sludge = max(relief_floor, desired_sludge - sludge_cut)
            max_dn_s = -34.0 if acute > 0.25 else -28.0
            d_sludge = _clamp(desired_sludge - curr_sludge, max_dn_s, 6.0)
        else:
            d_sludge = _clamp(desired_sludge - curr_sludge, -20.0, 28.0)
    elif vfa_excess > 0.35 and ph_safety > ph_target + 0.10:
        d_sludge = _clamp(desired_sludge - curr_sludge, -12.0, 4.0)
    else:
        d_sludge = _clamp(desired_sludge - curr_sludge, -16.0, 24.0)
    next_sludge = _clamp(curr_sludge + _clamp(d_sludge, -34.0, 34.0), 0.0, 1000.0)

    if not in_hold:
        if next_sludge > curr_sludge:
            next_carb = max(
                0.0,
                curr_carb - 10.0,
                next_carb - (next_sludge - curr_sludge) * sludge_equiv,
            )
        next_carb = max(
            curr_carb - 10.0,
            0.0,
            min(next_carb, load_limit - sludge_equiv * (next_sludge + S_IN_MEAN)),
        )
        buffer_supply = min(avg_sludge, next_sludge + S_IN_MEAN)
        ph_margin = min(ph_lead, ema_ph_slow) - ph_target
        ratio_limit = avg_carb * (buffer_supply / avg_sludge) * 10.0 ** ph_margin
        next_carb = max(curr_carb - 10.0, 0.0, min(next_carb, ratio_limit))

    next_sludge = _clamp(next_sludge, max(0.0, curr_sludge - 34.0), min(1000.0, curr_sludge + 34.0))
    next_carb = _clamp(next_carb, max(0.0, curr_carb - 10.0), min(300.0, curr_carb + 10.0))
    return [float(next_sludge), float(next_carb)], SUBGOAL_NAME
