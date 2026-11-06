import math

from vfa_gated_ramp import vfa_gated_ramp
from vfa_pi_feed import vfa_pi_feed
from vfa_pi_handoff import vfa_pi_handoff


VFA_KEYS = ('vfa_s_va', 'vfa_s_bu', 'vfa_s_pro', 'vfa_s_ac')
SUBGOAL = 'early_ramp_2000'
HANDOFF = 48


def _number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def act(observation, memory):
    obs = dict(observation) if isinstance(observation, dict) else {}
    day = _number(obs.get('day'))
    decision = max(0, int(round(day * 4.0))) if day is not None else memory.get('next_decision', 0)

    if memory.get('last_decision') == decision:
        return [memory['command']], SUBGOAL

    feed = memory.get('command', 128.0)
    arrival = obs.get('assay_age') == 0
    values = [_number(obs.get(key)) for key in VFA_KEYS]
    valid = all(value is not None for value in values)
    if not valid:
        obs['assay_age'] = -1
        arrival = False

    total = sum(values) if valid and arrival else None
    previous = memory.get('last_assay_sum')
    rise = total - previous if total is not None and previous is not None else 0.0

    if not memory.get('pi_mode', False):
        increment = 0.0
        if arrival and decision >= 8:
            increment = max(0.0, min(40.0, 80.0 * (0.5 - total)))
            if decision == 8 and values[3] < 0.2 and total < 0.5:
                increment = 40.0
            if rise > 0.08:
                increment = 0.0

        memory['vfa_ramp_feed'] = feed
        feed = vfa_gated_ramp(
            obs, memory, decision, 255.0,
            start_feed=128.0, ramp_start=8, every=4,
            step=increment, cut=32.0,
            sum_max=0.5, cut_sum=0.7,
        )

        if total is not None and total > 0.85:
            feed = max(0.0, min(128.0, feed))
        memory['vfa_ramp_feed'] = feed

        if decision >= HANDOFF:
            memory['pi_mode'] = True
            latest = total if total is not None else previous
            vfa_pi_handoff(memory, feed, latest, setpoint=0.55)
    else:
        feed = vfa_pi_feed(
            obs, memory, decision,
            setpoint=0.55, kp=80.0, ki=48.0,
            step_down=48.0, step_up=16.0,
            start=feed, high=255.0,
            early_high=255.0, early_until=0,
            cut_sum=0.8, cut_step=64.0,
        )
        if total is not None and total > 0.85:
            feed = max(0.0, min(128.0, feed))
        memory['vfa_pi_feed'] = feed

    if total is not None:
        memory['last_assay_sum'] = total

    command = float(max(0.0, min(255.0, feed)))
    memory['command'] = command
    memory['last_decision'] = decision
    memory['next_decision'] = decision + 1
    return [command], SUBGOAL
