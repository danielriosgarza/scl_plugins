import math

from soft_control_loop.programs import skill

_VFA_KEYS = ('vfa_s_va', 'vfa_s_bu', 'vfa_s_pro', 'vfa_s_ac')


def _vfa_sum(obs):
    total = 0.0
    for key in _VFA_KEYS:
        try:
            v = float(obs.get(key, 0.0))
        except (TypeError, ValueError):
            return None
        if not math.isfinite(v):
            return None
        total += v
    return total


@skill
def vfa_gated_ramp(observation, memory, k, target, start_feed=128.0,
                   ramp_start=12, every=4, step=16.0, cut=64.0,
                   sum_max=0.6, cut_sum=0.8):
    """Return a feed level that ramps towards target, gated by summed VFA.

    k is the caller's decision index and target is the feed to ramp to.
    The caller may pass a different target on each call.

    On each call with assay_age == 0, the function sums vfa_s_va, vfa_s_bu,
    vfa_s_pro and vfa_s_ac and stores the sum as the latest assay sum.
    A missing key counts as 0.0. A value that is present but non-numeric
    or non-finite leaves the stored sum unchanged.

    On calls with k >= ramp_start and (k - ramp_start) % every == 0, the
    function acts on the latest stored sum, if there is one:
    - a sum above cut_sum lowers the feed by cut, with a floor of 0;
    - a sum below sum_max raises a feed that is below target by step,
      without going past target.
    On other calls, or when no sum has been seen, the feed is not changed.
    A non-numeric k means no ramp step.

    The feed starts at start_feed. State is kept in memory under the keys
    'vfa_ramp_feed' and 'vfa_ramp_sum', so it starts fresh with each
    episode's memory. Returns the current feed level.
    """
    if 'vfa_ramp_feed' not in memory:
        memory['vfa_ramp_feed'] = float(start_feed)
        memory['vfa_ramp_sum'] = None
    obs = observation if isinstance(observation, dict) else {}
    if obs.get('assay_age') == 0:
        s = _vfa_sum(obs)
        if s is not None:
            memory['vfa_ramp_sum'] = s
    feed = memory['vfa_ramp_feed']
    try:
        on_step = k >= ramp_start and (k - ramp_start) % every == 0
    except TypeError:
        on_step = False
    if on_step:
        s = memory['vfa_ramp_sum']
        if s is not None:
            if s > cut_sum:
                feed = max(0.0, feed - cut)
            elif s < sum_max and feed < target:
                feed = min(target, feed + step)
    memory['vfa_ramp_feed'] = feed
    return feed
