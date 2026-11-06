from soft_control_loop.programs import skill


@skill
def clipped_total_vfa(observation: dict) -> float:
    """Total volatile fatty acids from an assay observation, with negatives clipped to zero.

    Args:
        observation: A mapping that holds the assay channels "vfa_s_va",
            "vfa_s_bu", "vfa_s_pro" and "vfa_s_ac". Values may be any type
            that float() accepts.

    Returns:
        max(0, va) + max(0, bu) + max(0, pro) + max(0, ac), added in that
        order, as a float. Clipping each channel keeps a negative or
        sentinel reading from lowering the total, for example in a VFA/IC
        ratio or a total-VFA safety limit.
    """
    return (
        max(0.0, float(observation["vfa_s_va"]))
        + max(0.0, float(observation["vfa_s_bu"]))
        + max(0.0, float(observation["vfa_s_pro"]))
        + max(0.0, float(observation["vfa_s_ac"]))
    )
