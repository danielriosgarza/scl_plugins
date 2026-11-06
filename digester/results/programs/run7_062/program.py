from smoothstep_interpolate import smoothstep_interpolate
from lead_rate_limited_p_step import lead_rate_limited_p_step
from clipped_total_vfa import clipped_total_vfa

SUBGOAL = 'safe_400'

_KNOTS = (
    (4.9, 255.0),
    (6.2, 200.0),
    (7.4, 190.0),
    (8.3, 152.0),
    (9.2, 128.0),
)

_BASE_TARGET_RATIO = 0.0045
_MAX_TARGET_VFA = 0.75
_RATIO_GAIN = 4000.0
_PLATEAU_MIN = 110.0
_FEED_MAX = 255.0
_FEED_FLOOR_START = 80.0
_FEED_FLOOR_MIN = 60.0
_FEED_CEILING_START = 255.0
_MAX_RISE_PER_ASSAY = 20.0
_RECORD_ACETATE = 0.80
_RECORD_MIN_TOTAL_VFA = 0.85
_MAX_RECORD_CUTS = 3
_CEILING_CUT = 15.0
_FLOOR_CUT = 10.0
_TARGET_CUT_FACTOR = 0.95


def _clamp_plateau(value):
    return max(_PLATEAU_MIN, min(_FEED_MAX, value))


def act(observation, memory):
    completed = int(round(float(observation['day']) * 4.0))
    decision = completed + 1

    if completed == 0 or 'plateau_state' not in memory:
        memory['plateau_state'] = {
            'ch4': [],
            'last_assay_step': None,
            'command': 255.0,
            'plateau': None,
            'max_acetate': 0.0,
            'cuts': 0,
            'ceiling': _FEED_CEILING_START,
            'floor': _FEED_FLOOR_START,
            'target_base': _BASE_TARGET_RATIO,
        }
    state = memory['plateau_state']
    state['ch4'].append(float(observation['ch4_flow']))

    fresh_assay = (
        int(observation['assay_age']) == 0
        and completed >= 4
        and state['last_assay_step'] != completed
    )

    if decision <= 3:
        return [255.0], SUBGOAL

    if state['plateau'] is None:
        history = state['ch4']
        ch4_start = 0.5 * (history[0] + 1650.0)
        gain = (history[3] - ch4_start) / 68.0
        state['plateau'] = _clamp_plateau(float(smoothstep_interpolate(gain, _KNOTS)))
        state['command'] = state['plateau']

    if fresh_assay:
        state['last_assay_step'] = completed
        total_vfa = clipped_total_vfa(observation)
        acetate = max(0.0, float(observation['vfa_s_ac']))
        carbon = max(1.0, float(observation['inorganic_carbon']))

        if acetate > state['max_acetate']:
            is_record = acetate > _RECORD_ACETATE
            state['max_acetate'] = acetate
            if (
                is_record
                and total_vfa >= _RECORD_MIN_TOTAL_VFA
                and state['cuts'] < _MAX_RECORD_CUTS
            ):
                state['cuts'] += 1
                state['ceiling'] = state['ceiling'] - _CEILING_CUT
                state['floor'] = max(_FEED_FLOOR_MIN, state['floor'] - _FLOOR_CUT)
                state['target_base'] = state['target_base'] * _TARGET_CUT_FACTOR

        target_ratio = min(state['target_base'], _MAX_TARGET_VFA / carbon)
        ratio = total_vfa / carbon
        current = float(state['command'])
        state['command'] = lead_rate_limited_p_step(
            current,
            ratio,
            None,
            target_ratio,
            _RATIO_GAIN,
            0.0,
            current,
            _MAX_RISE_PER_ASSAY,
            state['floor'],
            state['ceiling'],
        )

    command = min(float(state['command']), state['ceiling'])
    command = max(state['floor'], command)
    state['command'] = command
    return [command], SUBGOAL
