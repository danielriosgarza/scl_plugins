import math
import statistics

from calibrate_by_bisection import calibrate_by_bisection  # available, not needed by this model
from discounted_origin_slope import discounted_origin_slope  # available, not needed by this model
from max_safe_command import max_safe_command
from rate_limited_step import rate_limited_step
from read_number import read_number
from total_vfa import total_vfa

SUBGOAL = 'survive_to_day40'
KEY = '_survive_to_day40'

HORIZON = 8
VFA_LIMIT = 0.78
PUMP_STEP = 34.0
RATE_DOWN = 25.0
RATE_UP = 6.0
CMD_LO = 100.0
CMD_HI = 255.0
OPENING_CUT = 55.0
IC_GUARD = 175.0
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
CEILINGS = {4: 2560.0, 5: 2620.0, 6: 2645.0, 7: 2645.0}


def _clip(x, lo, hi):
    return max(lo, min(hi, x))


def _params(state):
    return PRIOR_A * state['alpha'], PRIOR_B * state['beta']


def _replay(flows, start, end, value, a, b):
    for j in range(start + 1, end + 1):
        value = max(0.0, (1.0 - b) * value + a * flows[j])
    return value


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


def _assimilate(state, sample_step, observed):
    flows = state['flows']
    start = state['anchor_step']
    start_value = state['anchor_value']
    start_var = state['anchor_var']
    gap = sample_step - start
    a, b = _params(state)
    predicted = _replay(flows, start, sample_step, start_value, a, b)
    prior_var = ((1.0 - b) ** (2 * gap)) * start_var + PROCESS_Q * gap
    gain = prior_var / (prior_var + ASSAY_R)
    state['anchor_value'] = max(0.0, predicted + gain * (observed - predicted))
    state['anchor_var'] = (1.0 - gain) * prior_var
    state['anchor_step'] = sample_step
    _fit_update(state, start, start_value, sample_step, observed)


def _peak(flows, n, command, v_now, a, b):
    flow = flows[n]
    value = v_now
    peak = value
    for _ in range(HORIZON):
        flow = rate_limited_step(flow, command, PUMP_STEP)
        value = max(0.0, (1.0 - b) * value + a * flow)
        peak = max(peak, value)
    return peak


def _fresh_state():
    prior_precision = 1.0 / (PRIOR_SD * PRIOR_SD)
    return {
        'last_n': -1,
        'last_action': 255.0,
        'flows': [85.0],
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

    methane = max(0.0, read_number(observation, 'ch4_flow', 1700.0))
    co2 = read_number(observation, 'co2_flow', -1.0)
    pressure = read_number(observation, 'ch4_pressure', -1.0)
    state['ic'] = read_number(observation, 'inorganic_carbon', 0.0)

    age = int(read_number(observation, 'assay_age', -1.0))
    if age >= 0:
        arrival = n - age
        sample = arrival - 4
        observed = total_vfa(observation)
        if (observed is not None and sample >= 0
                and sample >= state['anchor_step']
                and arrival > state['last_arrival']):
            _assimilate(state, sample, observed)
            state['last_arrival'] = arrival

    a_nom, b_nom = _params(state)
    v_now = _replay(flows, state['anchor_step'], n, state['anchor_value'], a_nom, b_nom)
    a_f = a_nom * MARGIN_A
    b_f = b_nom * MARGIN_B

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

    if n < 4:
        command = 255.0
    else:
        prev = state['last_action']
        lo = max(CMD_LO, prev - RATE_DOWN)
        hi = min(CMD_HI, prev + RATE_UP)
        ceiling = CEILINGS.get(n)
        if ceiling is not None and methane > ceiling:
            hi = min(hi, prev - OPENING_CUT)
            lo = max(CMD_LO, prev - OPENING_CUT)
        lo = min(lo, hi)
        hi = max(hi, lo)

        command = max_safe_command(
            lambda c: _peak(flows, n, c, v_now, a_f, b_f),
            VFA_LIMIT,
            high=int(math.floor(hi)),
            low=int(math.ceil(lo)),
            fallback=lo)

        if not state['fit_ok'] and n >= 16:
            if fired:
                command = min(command, prev - RATE_DOWN)
            elif n < state['lock_until']:
                command = min(command, prev)

        if state['ic'] >= IC_GUARD:
            command = min(command, prev)

    command = float(_clip(command, CMD_LO, CMD_HI))
    state['last_n'] = n
    state['last_action'] = command
    flows.append(rate_limited_step(flows[n], command, PUMP_STEP))
    return [command], SUBGOAL
