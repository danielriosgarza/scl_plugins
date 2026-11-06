"""The stage checks of the digester: one batch check for each stage of the episode, then
three on the whole episode.

A stage ends after decision last. An episode reaches it if it ran at least last decisions and
had not left the limits by then (first_out is None or above last). The stage is met when every
evaluation episode reaches it and the mean over the episodes of the mean step reward (true
methane, m3/d) over decisions 1 to last is at least the stage's mark. The checks on the whole
episode are stages that end after decision 400, with higher marks.
"""


def stage(last, mark):
    """Return the batch check of the stage that ends after decision last, with its mark."""

    def check(traces):
        """Return True if every episode reached the stage and their mean methane up to it is
        at least the mark."""
        for trace in traces:
            out = (trace.final_observation or {}).get("first_out")
            if len(trace.steps) < last or (out is not None and out <= last):
                return False
        means = [sum(step.reward for step in trace.steps[:last]) / last for trace in traces]
        return sum(means) / len(means) >= mark

    return check


check_day_2 = stage(8, 2416)
check_day_4 = stage(16, 2522)
check_day_6 = stage(24, 2527)
check_day_8 = stage(32, 2522)
check_day_10 = stage(40, 2551)
check_day_13 = stage(52, 2573)
check_day_16 = stage(64, 2589)
check_day_19 = stage(76, 2620)
check_day_22 = stage(88, 2627)
check_day_25 = stage(100, 2652)
check_day_28 = stage(112, 2662)
check_day_31 = stage(124, 2682)
check_day_34 = stage(136, 2698)
check_day_37 = stage(148, 2710)
check_day_40 = stage(160, 2728)
check_day_43 = stage(172, 2736)
check_day_46 = stage(184, 2751)
check_day_49 = stage(196, 2758)
check_day_52 = stage(208, 2767)
check_day_55 = stage(220, 2776)
check_day_58 = stage(232, 2784)
check_day_61 = stage(244, 2797)
check_day_64 = stage(256, 2800)
check_day_67 = stage(268, 2809)
check_day_70 = stage(280, 2813)
check_day_73 = stage(292, 2821)
check_day_76 = stage(304, 2827)
check_day_79 = stage(316, 2832)
check_day_82 = stage(328, 2840)
check_day_85 = stage(340, 2843)
check_day_88 = stage(352, 2850)
check_day_91 = stage(364, 2853)
check_day_94 = stage(376, 2859)
check_day_97 = stage(388, 2864)
check_day_100 = stage(400, 2869)
check_plus_6 = stage(400, 2924)
check_plus_8 = stage(400, 2979)
check_plus_10 = stage(400, 3034)
