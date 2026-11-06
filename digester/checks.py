"""The stage checks of the digester: one batch check for each stage of the 40-day episode,
then three on the whole episode.

A stage ends after decision last. An episode reaches it if it ran at least last decisions and
had not left the limits by then (first_out is None or above last). The stage is met when every
evaluation episode reaches it and the mean over the episodes of the mean step reward (true
methane, m3/d) over decisions 1 to last is at least the stage's mark. The checks on the whole
episode are stages that end after decision 160, with higher marks.
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


check_day_2 = stage(8, 2419)
check_day_4 = stage(16, 2528)
check_day_6 = stage(24, 2536)
check_day_8 = stage(32, 2534)
check_day_10 = stage(40, 2566)
check_day_13 = stage(52, 2593)
check_day_16 = stage(64, 2614)
check_day_19 = stage(76, 2650)
check_day_22 = stage(88, 2662)
check_day_25 = stage(100, 2692)
check_day_28 = stage(112, 2707)
check_day_31 = stage(124, 2732)
check_day_34 = stage(136, 2753)
check_day_37 = stage(148, 2770)
check_day_40 = stage(160, 2793)
check_plus_6 = stage(160, 2847)
check_plus_8 = stage(160, 2900)
check_plus_10 = stage(160, 2954)
