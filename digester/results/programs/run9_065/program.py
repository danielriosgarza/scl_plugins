import math
import statistics

from calibrate_by_bisection import calibrate_by_bisection
from discounted_origin_slope import discounted_origin_slope
from kalman_update import kalman_update
from max_safe_command import max_safe_command
from rate_limited_step import rate_limited_step
from read_number import read_number
from ridge_linear_fit import ridge_linear_fit
from total_vfa import total_vfa

SUBGOAL = 'full_room_day40'
KEY = '_full_room_day40'

HORIZON = 8
VFA_LIMIT = 0.80
IC_VFA_LIMIT = 0.77
POST_VFA_LIMIT = 0.84
POST_QUANTILE = 0.90
POST_QUANTILE_WEAK = 0.75
POST_START = 40
POST_START_WEAK = 24
POST_RATE_UP = 8.0
POST_RATE_UP_WEAK = 12.0
ENDGAME_START = 145
ENDGAME_STEP = 160
ENDGAME_LIMIT = 0.89
ENDGAME_LIMIT_MED = 0.875
MEDIUM_MEAN_THRESHOLD = 200.0
MEDIUM_MAX_RAISE = 30.0
PUMP_STEP = 34.0
RATE_DOWN = 25.0
RATE_UP = 6.0
CMD_LO = 100.0
CMD_LO_IC = 85.0
CMD_HI = 255.0
OPENING_CUT = 55.0
IC_WEAK = 150.0
IC_STRONG_POST = 165.0
IC_GUARD = 175.0
IC_SOFT_GUARD = 162.0
PRIOR_A = 0.00042
PRIOR_B = 0.15
PRIOR_SD = 0.5
DATA_SD = 0.15
PROCESS_Q = 0.0004
ASSAY_R = 0.0064
INIT_VFA = 0.245
INIT_VAR = 0.05
PARAM_LO = 0.3
PARAM_HI = 3.0
MARGIN_A = 1.10
MARGIN_B = 0.90
SOFT_MARGIN_A = 1.03
SOFT_MARGIN_B = 0.97
CEILINGS = {4: 2560.0, 5: 2620.0, 6: 2645.0, 7: 2645.0}
CLASS_K = (0.00260, 0.00285, 0.00308, 0.00328, 0.00365, 0.00415, 0.00490, 0.00610)
CLASS_CH4_OPEN = (2380.0, 2430.0, 2480.0, 2530.0, 2585.0, 2640.0, 2700.0, 2770.0)
RIDGE_LAGS = 6
RIDGE_PENALTY = 500.0


def _clip(x, lo, hi):
    return max(lo, min(hi, x))


def _params(state):
    return PRIOR_A * state['alpha'], PRIOR_B * state['beta']


def _replay(flows, start, end, value, a, b):
    for j in range(start + 1, end + 1):
        value = max(0.0, (1.0 - b) * value + a * flows[j])
    return value


def _normalize_log_probs(log_p):
    m = max(log_p)
    weights = [math.exp(max(-60.0, lp - m)) for lp in log_p]
    total = sum(weights)
    if not (math.isfinite(total) and total > 0.0):
        u = 1.0 / len(log_p)
        return [u for _ in log_p], [0.0 for _ in log_p]
    probs = [w / total for w in weights]
    return probs, [math.log(max(1e-12, p)) for p in probs]


def _posterior_quantile(ic):
    if ic < IC_WEAK:
        return POST_QUANTILE_WEAK
    if ic >= IC_STRONG_POST:
        return POST_QUANTILE
    frac = (ic - IC_WEAK) / (IC_STRONG_POST - IC_WEAK)
    return POST_QUANTILE_WEAK + frac * (POST_QUANTILE - POST_QUANTILE_WEAK)


def _quantile_k(probs, q=POST_QUANTILE):
    cum = 0.0
    prev_k = CLASS_K[0]
    for idx, p in enumerate(probs):
        next_cum = cum + p
        k = CLASS_K[idx]
        if next_cum >= q:
            if p > 1e-9 and idx > 0 and q > cum:
                frac = _clip((q - cum) / p, 0.0, 1.0)
                return prev_k + frac * (k - prev_k)
            return k
        cum = next_cum
        prev_k = k
    return CLASS_K[-1]


def _solve(state):
    m00, m01, m11 = state['M']
    h0, h1 = state['h']
    det = m00 * m11 - m01 * m01
    if not (math.isfinite(det) and det > 1e-9):
        state['fit_ok'] = False
        return
    alpha = (h0 * m11 - m01 * h1) / det
    beta = (m00 * h1 - m01 * h0) / det
    if not (math.isfinite(alpha) and math.isfinite(beta)):
        state['fit_ok'] = False
        return
    state['alpha'] = _clip(alpha, PARAM_LO, PARAM_HI)
    state['beta'] = _clip(beta, PARAM_LO, PARAM_HI)
    state['fit_ok'] = True


def _fit_update(state, start, start_value, end, observed):
    if end - start < 1:
        return
    alpha = state['alpha']
    beta = state['beta']
    flows = state['flows']

    def predict(al, be):
        return _replay(flows, start, end, start_value, PRIOR_A * al, PRIOR_B * be)

    base = predict(alpha, beta)
    step = 0.01
    ja = (predict(alpha * (1.0 + step), beta) - base) / (alpha * step)
    jb = (predict(alpha, beta * (1.0 + step)) - base) / (beta * step)
    if not (math.isfinite(ja) and math.isfinite(jb)):
        state['fit_ok'] = False
        return
    target = observed - base + ja * alpha + jb * beta
    w = 1.0 / (DATA_SD * DATA_SD)
    state['M'][0] += w * ja * ja
    state['M'][1] += w * ja * jb
    state['M'][2] += w * jb * jb
    state['h'][0] += w * target * ja
    state['h'][1] += w * target * jb
    _solve(state)


def _update_posterior_assay(state, start, start_value, sample_step, observed, predicted):
    flows = state['flows']
    err = observed - predicted
    state['vfa_mse'] = 0.80 * state['vfa_mse'] + 0.20 * (err * err)
    sigma_vfa = _clip(math.sqrt(state['vfa_mse']), 0.045, 0.12)

    _, b_nom = _params(state)
    b_use = _clip(b_nom, 0.08, 0.25)
    k_cal = calibrate_by_bisection(
        lambda k: _replay(flows, start, sample_step, start_value, b_use * k, b_use),
        observed,
        CLASS_K[0] * 0.7,
        CLASS_K[-1] * 1.3,
        iterations=24,
    )
    eff_flow = _replay(flows, 0, sample_step, 85.0, PRIOR_B, PRIOR_B)
    if sample_step >= 8:
        state['assay_flows'].append(max(80.0, eff_flow))
        state['assay_vals'].append(observed)
    if state['assay_flows']:
        k_slope = discounted_origin_slope(
            state['assay_flows'], state['assay_vals'], discount=0.85, min_denominator=100.0
        )
        k_est = 0.5 * k_cal + 0.5 * k_slope
    else:
        k_est = k_cal

    steady_cruise = flows[sample_step] >= 180.0 and observed >= start_value - 0.05
    decay = 0.92 if steady_cruise else 0.96
    log_p = [decay * lp for lp in state['log_p']]

    for idx, k_c in enumerate(CLASS_K):
        pred_local = _replay(flows, start, sample_step, start_value, b_use * k_c, b_use)
        pred_full = _replay(flows, 0, sample_step, INIT_VFA, PRIOR_B * k_c, PRIOR_B)
        pred_blend = 0.65 * pred_local + 0.35 * pred_full
        z_vfa = (observed - pred_blend) / sigma_vfa
        z_cal = (k_est - k_c) / max(0.00028, sigma_vfa / 220.0)
        log_p[idx] -= 0.5 * (0.75 * z_vfa * z_vfa + 0.25 * z_cal * z_cal)

    state['posterior'], state['log_p'] = _normalize_log_probs(log_p)


def _update_posterior_ch4(state, n, methane):
    flows = state['flows']
    log_p = list(state['log_p'])
    if 4 <= n <= 7:
        sigma_open = max(90.0, math.sqrt(state['ch4_mse']))
        for idx, ref in enumerate(CLASS_CH4_OPEN):
            z = (methane - ref) / sigma_open
            log_p[idx] -= 0.04 * z * z
        state['posterior'], state['log_p'] = _normalize_log_probs(log_p)
        return

    if n < RIDGE_LAGS:
        return

    x_vec = [flows[n - j] for j in range(RIDGE_LAGS)]
    ridge_model = state['ridge_model']
    if ridge_model is not None:
        intercept, weights = ridge_model
        pred_ch4 = intercept + sum(w * x for w, x in zip(weights, x_vec))
        res = methane - pred_ch4
        if math.isfinite(res):
            state['ch4_mse'] = 0.90 * state['ch4_mse'] + 0.10 * (res * res)
            sigma_ch4 = _clip(math.sqrt(state['ch4_mse']), 25.0, 180.0)
            if n >= 16:
                a_nom, b_nom = _params(state)
                k_obs = a_nom / max(1e-6, b_nom)
                stress = max(0.0, -res / sigma_ch4 - 0.5)
                k_ch4 = k_obs + 0.00018 * stress
                sigma_k = max(0.00035, 0.00030 * (sigma_ch4 / 60.0))
                for idx, k_c in enumerate(CLASS_K):
                    z = (k_ch4 - k_c) / sigma_k
                    log_p[idx] = 0.995 * log_p[idx] - 0.025 * z * z
                state['posterior'], state['log_p'] = _normalize_log_probs(log_p)

    state['ridge_xs'].append(x_vec)
    state['ridge_ys'].append(methane)
    if len(state['ridge_xs']) >= 8:
        fit = ridge_linear_fit(state['ridge_xs'][-48:], state['ridge_ys'][-48:], RIDGE_PENALTY)
        if fit is not None:
            state['ridge_model'] = fit


def _assimilate(state, sample_step, observed):
    flows = state['flows']
    start = state['anchor_step']
    start_value = state['anchor_value']
    start_var = state['anchor_var']
    gap = sample_step - start
    a, b = _params(state)
    predicted = _replay(flows, start, sample_step, start_value, a, b)
    prior_var = ((1.0 - b) ** (2 * gap)) * start_var + PROCESS_Q * gap
    value, variance = kalman_update(predicted, prior_var, observed, ASSAY_R)
    _update_posterior_assay(state, start, start_value, sample_step, observed, predicted)
    state['anchor_value'] = max(0.0, value)
    state['anchor_var'] = variance
    state['anchor_step'] = sample_step
    state['max_assay'] = max(state['max_assay'], observed)
    _fit_update(state, start, start_value, sample_step, observed)


def _peak(flows, n, command, v_now, a, b, horizon=HORIZON):
    flow = flows[n]
    value = v_now
    peak = value
    for _ in range(horizon):
        flow = rate_limited_step(flow, command, PUMP_STEP)
        value = max(0.0, (1.0 - b) * value + a * flow)
        peak = max(peak, value)
    return peak


def _medium_raise_cap(state, n):
    cmds = state['cmd_history']
    if n >= 120:
        win_121_144 = cmds[120:min(n, 144)]
        pre_121 = cmds[96:120]
        mean_121_144 = (
            statistics.mean(win_121_144)
            if win_121_144
            else (statistics.mean(pre_121) if pre_121 else 255.0)
        )
        base_win = state['base_cmd_121_144']
        base_mean = statistics.mean(base_win) if base_win else mean_121_144
        pre_mean = statistics.mean(pre_121) if pre_121 else mean_121_144
        ref_mean = min(mean_121_144, base_mean, pre_mean)
        if mean_121_144 < MEDIUM_MEAN_THRESHOLD or ref_mean < MEDIUM_MEAN_THRESHOLD:
            return min(mean_121_144, ref_mean) + MEDIUM_MAX_RAISE, ref_mean
        return CMD_HI, ref_mean
    if n >= POST_START:
        recent = cmds[max(16, n - 24):n]
        if len(recent) >= 8:
            r_mean = statistics.mean(recent)
            if r_mean < MEDIUM_MEAN_THRESHOLD:
                return r_mean + MEDIUM_MAX_RAISE, r_mean
            return CMD_HI, r_mean
    return CMD_HI, 255.0


def _fresh_state():
    prior_precision = 1.0 / (PRIOR_SD * PRIOR_SD)
    n_classes = len(CLASS_K)
    return {
        'last_n': -1,
        'last_action': 255.0,
        'flows': [85.0],
        'cmd_history': [],
        'base_cmd_121_144': [],
        'alpha': 1.0,
        'beta': 1.0,
        'M': [prior_precision, 0.0, prior_precision],
        'h': [prior_precision, prior_precision],
        'fit_ok': False,
        'anchor_step': 0,
        'anchor_value': INIT_VFA,
        'anchor_var': INIT_VAR,
        'last_arrival': -1,
        'ic': 0.0,
        'ratio_samples': [],
        'pressure_samples': [],
        'ratio_baseline': None,
        'pressure_baseline': None,
        'alarm_streak': 0,
        'lock_until': -1,
        'last_alarm': -100,
        'boosted': False,
        'log_p': [0.0] * n_classes,
        'posterior': [1.0 / n_classes] * n_classes,
        'vfa_mse': ASSAY_R,
        'ch4_mse': 3600.0,
        'ridge_xs': [],
        'ridge_ys': [],
        'ridge_model': None,
        'assay_flows': [],
        'assay_vals': [],
        'max_assay': 0.0,
        'min_cruise_cmd': 255.0,
    }


def act(observation, memory):
    # n decisions have completed; this call commands decision n + 1.
    n = max(0, int(round(4.0 * read_number(observation, 'day', 0.0))))
    state = memory.get(KEY)
    if state is None or n < state['last_n']:
        state = _fresh_state()
        memory[KEY] = state
    if n == state['last_n']:
        return [float(state['last_action'])], SUBGOAL

    flows = state['flows']
    while len(flows) <= n:
        flows.append(rate_limited_step(flows[-1], state['last_action'], PUMP_STEP))
    while len(state['cmd_history']) < n:
        state['cmd_history'].append(state['last_action'])

    methane = max(0.0, read_number(observation, 'ch4_flow', 1700.0))
    co2 = read_number(observation, 'co2_flow', -1.0)
    pressure = read_number(observation, 'ch4_pressure', -1.0)
    state['ic'] = read_number(observation, 'inorganic_carbon', 0.0)
    ic = state['ic']

    age = int(read_number(observation, 'assay_age', -1.0))
    if age >= 0:
        arrival = n - age
        sample = arrival - 4
        observed = total_vfa(observation)
        if (
            observed is not None
            and sample >= 0
            and sample >= state['anchor_step']
            and arrival > state['last_arrival']
        ):
            _assimilate(state, sample, observed)
            state['last_arrival'] = arrival

    _update_posterior_ch4(state, n, methane)

    a_nom, b_nom = _params(state)
    v_now = _replay(flows, state['anchor_step'], n, state['anchor_value'], a_nom, b_nom)
    a_f = a_nom * MARGIN_A
    b_f = b_nom * MARGIN_B
    a_soft = a_nom * SOFT_MARGIN_A
    b_soft = b_nom * SOFT_MARGIN_B

    ratio = co2 / methane if methane > 0.0 and co2 > 0.0 else None
    if 9 <= n <= 16:
        if ratio is not None:
            state['ratio_samples'].append(ratio)
            state['ratio_baseline'] = statistics.median(state['ratio_samples'])
        if pressure > 0.0:
            state['pressure_samples'].append(pressure)
            state['pressure_baseline'] = statistics.median(state['pressure_samples'])

    fired = False
    if n >= 16:
        base_q = state['ratio_baseline']
        base_p = state['pressure_baseline']
        raw_alarm = (
            (ratio is not None and base_q is not None and ratio > 1.04 * base_q)
            or (pressure > 0.0 and base_p is not None and pressure < base_p - 0.015)
        )
        state['alarm_streak'] = state['alarm_streak'] + 1 if raw_alarm else 0
        if state['alarm_streak'] >= 3 and v_now > 0.55:
            state['lock_until'] = max(state['lock_until'], n + 6)
            if n - state['last_alarm'] >= 6:
                fired = True
                state['last_alarm'] = n

    cmd_lo_now = CMD_LO_IC if ic >= IC_GUARD else CMD_LO

    if n < 4:
        command = 255.0
    else:
        prev = state['last_action']
        lo = max(cmd_lo_now, prev - RATE_DOWN)
        hi = min(CMD_HI, prev + RATE_UP)
        ceiling = CEILINGS.get(n)
        if ceiling is not None and methane > ceiling:
            hi = min(hi, prev - OPENING_CUT)
            lo = max(CMD_LO, prev - OPENING_CUT)
        elif 8 <= n <= 15:
            hi = min(hi, prev)
        if ic >= IC_GUARD:
            hi = min(hi, prev)
        lo = min(lo, hi)
        hi = max(hi, lo)

        obs_limit = IC_VFA_LIMIT if ic >= IC_GUARD else VFA_LIMIT
        command = max_safe_command(
            lambda c: _peak(flows, n, c, v_now, a_f, b_f, HORIZON),
            obs_limit,
            high=int(math.floor(hi)),
            low=int(math.ceil(lo)),
            fallback=lo,
        )

        if not state['fit_ok'] and n >= 16:
            if fired:
                command = min(command, prev - RATE_DOWN)
            elif n < state['lock_until']:
                command = min(command, prev)

        if 120 <= n < 144:
            state['base_cmd_121_144'].append(float(command))

        med_cap, ref_mean = _medium_raise_cap(state, n)
        q_post = _posterior_quantile(ic)
        k_q = _quantile_k(state['posterior'], q_post)

        weak_draw = ic > 0.0 and ic < IC_WEAK and state['min_cruise_cmd'] >= 200.0
        post_start_n = POST_START_WEAK if weak_draw else POST_START
        max_assay_gate = 0.85 if ic < IC_WEAK else 0.82
        v_now_gate = 0.84 if ic < IC_WEAK else 0.81
        min_cruise_gate = 185.0 if ic >= IC_SOFT_GUARD else 170.0

        if (
            n >= post_start_n
            and ic < IC_GUARD
            and state['fit_ok']
            and not fired
            and n >= state['lock_until']
            and state['min_cruise_cmd'] >= min_cruise_gate
            and state['max_assay'] < max_assay_gate
            and v_now <= v_now_gate
        ):
            a_q = b_nom * k_q
            rate_up_post = POST_RATE_UP_WEAK if ic < IC_WEAK else POST_RATE_UP
            post_hi = min(CMD_HI, prev + rate_up_post, med_cap)
            post_lo = max(lo, command)

            if ic < IC_WEAK:
                w_strict = 0.0
            elif ic >= IC_STRONG_POST:
                w_strict = 1.0
            else:
                w_strict = (ic - IC_WEAK) / (IC_STRONG_POST - IC_WEAK)

            def _post_peak(c):
                steady_q = k_q * c
                dyn_q = _peak(flows, n, c, v_now, a_q, b_nom, HORIZON)
                nom_obs = _peak(flows, n, c, v_now, a_nom, b_nom, HORIZON) - 0.012
                soft_strict = _peak(flows, n, c, v_now, a_soft, b_soft, HORIZON) - 0.005
                soft_obs = (1.0 - w_strict) * nom_obs + w_strict * soft_strict
                hard_off = (1.0 - w_strict) * 0.145 + w_strict * 0.085
                hard_obs = _peak(flows, n, c, v_now, a_f, b_f, HORIZON) - hard_off
                return max(steady_q, dyn_q, soft_obs, hard_obs)

            if (
                _post_peak(prev) > POST_VFA_LIMIT + 0.005
                or v_now > (0.82 if ic < IC_WEAK else 0.795)
                or state['max_assay'] >= (0.83 if ic < IC_WEAK else 0.805)
            ):
                post_hi = min(post_hi, prev)

            if post_hi >= post_lo:
                post_cmd = max_safe_command(
                    _post_peak,
                    POST_VFA_LIMIT,
                    high=int(math.floor(post_hi)),
                    low=int(math.ceil(post_lo)),
                    fallback=command,
                )
                if post_cmd > command:
                    command = post_cmd

        if (
            n >= ENDGAME_START
            and ic < IC_GUARD
            and state['fit_ok']
            and not fired
            and n >= state['lock_until']
        ):
            rem = max(1, ENDGAME_STEP - n)
            if (
                ic < IC_WEAK
                and ref_mean >= 215.0
                and state['min_cruise_cmd'] >= 200.0
                and k_q <= 0.00340
            ):
                a_end, b_end = a_soft, b_soft
                v_endgame = v_now
                end_limit = ENDGAME_LIMIT
            else:
                a_end, b_end = a_f, b_f
                v_endgame = max(
                    v_now,
                    _replay(flows, state['anchor_step'], n, state['anchor_value'], a_f, b_f),
                )
                end_limit = ENDGAME_LIMIT_MED if ref_mean < 215.0 or ic >= IC_WEAK else ENDGAME_LIMIT
            end_step_up = 20.0 if ref_mean < 215.0 else PUMP_STEP
            end_lo = max(CMD_LO, prev - PUMP_STEP)
            end_hi = min(CMD_HI, prev + end_step_up, med_cap)
            end_lo = min(end_lo, end_hi)
            end_cmd = max_safe_command(
                lambda c: _peak(flows, n, c, v_endgame, a_end, b_end, rem),
                end_limit,
                high=int(math.floor(end_hi)),
                low=int(math.ceil(end_lo)),
                fallback=end_lo,
            )
            if end_cmd > command:
                command = end_cmd
                state['boosted'] = True
            elif state['boosted']:
                command = min(command, end_cmd)

        if ic >= IC_GUARD:
            command = min(command, prev)

    command = float(_clip(command, cmd_lo_now, CMD_HI))
    if 16 <= n < POST_START:
        state['min_cruise_cmd'] = min(state['min_cruise_cmd'], command)
    elif n >= POST_START and command < 170.0:
        state['min_cruise_cmd'] = min(state['min_cruise_cmd'], command)
    state['last_n'] = n
    state['last_action'] = command
    state['cmd_history'].append(command)
    flows.append(rate_limited_step(flows[n], command, PUMP_STEP))
    return [command], SUBGOAL
