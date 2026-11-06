import math

from soft_control_loop.programs import skill


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


@skill
def vfa_pi_feed(observation, memory, k, setpoint=0.5, kp=80.0, ki=48.0,
                step_down=48.0, step_up=16.0, start=128.0, high=255.0,
                early_high=128.0, early_until=12, cut_sum=0.8, cut_step=64.0):
    """Return the feed level set by an incremental PI controller on summed VFA.

    k is the caller's decision index. On each call with assay_age == 0, the
    function sums vfa_s_va, vfa_s_bu, vfa_s_pro and vfa_s_ac. A missing key
    counts as 0.0. It then applies the velocity-form PI law
    du = kp * (err - prev_err) + ki * err, where err = setpoint - sum.
    The derivative term is 0 on the first arrival. du is clamped to
    [-step_down, step_up].
    - If the sum is above cut_sum, the new feed is
      min(feed - cut_step, feed + du), a hard safety cut.
    - Otherwise the new feed is feed + du.
    The new feed is clamped to [0, early_high] while k < early_until and to
    [0, high] after that. This clamping also gives anti-windup.
    When there is no arrival, the feed is not changed. A value that is
    present but non-numeric or non-finite also leaves the feed unchanged.
    The feed starts at start. State is kept in memory under the keys
    'vfa_pi_feed', 'vfa_pi_prev_err' and 'vfa_pi_last_sum', so it starts
    fresh with each episode's memory. Returns the current feed level.
    """
    if 'vfa_pi_feed' not in memory:
        memory['vfa_pi_feed'] = float(start)
        memory['vfa_pi_prev_err'] = None
        memory['vfa_pi_last_sum'] = 0.0
    obs = observation if isinstance(observation, dict) else {}
    if obs.get('assay_age') == 0:
        vals = [_num(obs.get(key, 0.0)) for key in ('vfa_s_va', 'vfa_s_bu', 'vfa_s_pro', 'vfa_s_ac')]
        if all(v is not None for v in vals):
            vfa_sum = vals[0] + vals[1] + vals[2] + vals[3]
            memory['vfa_pi_last_sum'] = vfa_sum
            err = setpoint - vfa_sum
            prev_err = memory['vfa_pi_prev_err']
            d_err = 0.0 if prev_err is None else (err - prev_err)
            memory['vfa_pi_prev_err'] = err
            du = kp * d_err + ki * err
            du = max(-float(step_down), min(float(step_up), du))
            try:
                early = k < early_until
            except TypeError:
                early = False
            upper_bound = float(early_high) if early else float(high)
            feed = memory['vfa_pi_feed']
            if vfa_sum > cut_sum:
                new_feed = min(feed - cut_step, feed + du)
            else:
                new_feed = feed + du
            memory['vfa_pi_feed'] = max(0.0, min(upper_bound, new_feed))
    return memory['vfa_pi_feed']
