from soft_control_loop.programs import skill


@skill
def vfa_pi_handoff(memory, feed, latest_sum, setpoint=0.5):
    """Seed vfa_pi_feed's memory so that it continues from a running feed.

    Call this once, at the decision where control passes from another feed
    rule (a ramp, for example) to vfa_pi_feed. Pass vfa_pi_feed the same
    setpoint on later calls. The function changes memory as follows:
    - 'vfa_pi_feed' is set to feed, unchanged, so vfa_pi_feed starts from
      the current feed and does not reset to its own start value;
    - 'vfa_pi_prev_err' is set to setpoint - latest_sum, or to None when
      latest_sum is None. On the next assay arrival the derivative term
      then uses the last known error, or is 0 if there is none;
    - 'vfa_pi_last_sum' is set to latest_sum, but only when latest_sum is
      not None.
    latest_sum is the most recent valid summed VFA assay
    (vfa_s_va + vfa_s_bu + vfa_s_pro + vfa_s_ac), or None if none is known.
    The function does not decide when to hand off, and it does not update
    the feed on the hand-off decision itself. Returns feed.
    """
    memory['vfa_pi_feed'] = feed
    memory['vfa_pi_prev_err'] = None if latest_sum is None else setpoint - latest_sum
    if latest_sum is not None:
        memory['vfa_pi_last_sum'] = latest_sum
    return feed
