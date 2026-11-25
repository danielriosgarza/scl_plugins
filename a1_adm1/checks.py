"""The fixed milestones of a1_adm1/loading: marks on the mean score with no failed episode.

A mark is met when no evaluation episode failed and the mean of their scores, the task's net
methane in m3/d, is at least the mark. An episode failed when its record says so (the digester
collapsed, or the episode did not run all its decisions) or when it has no record, because the
program failed before the end. The checks are batch checks: each judges all evaluation episodes
together, so it passes or fails as a whole whatever the setup's pass rate.

The first mark is BASE: what the fixed rates 200 and 100 m3/d (programs/hold_200_100) scored on
the evaluation seeds 6021 to 6100, with no failed episode (results/README.md). The further marks
are every 1000 m3/d from 10 000 to 50 000, a ladder that the maintainer fixed and that ends
far above what any program has scored, so that a run never meets its last mark. Results of
other controllers of the benchmark set no mark.

This module defines BASE; mark, which returns the check of one mark; and one check for each fixed
milestone of the setup.
"""

BASE = 9277.5


def mark(score):
    """Return the batch check that no episode failed and the mean score is at least score."""

    def check(traces):
        """Return True if every episode has a record that says it did not fail, and the mean of
        their scores is at least the mark."""
        finals = [trace.final_observation or {} for trace in traces]
        if any(final.get("failed") is not False for final in finals):
            return False
        return sum(final["net_methane"] for final in finals) / len(finals) >= score

    return check


check_hold = mark(9277)
check_reach_10000 = mark(10000)
check_reach_11000 = mark(11000)
check_reach_12000 = mark(12000)
check_reach_13000 = mark(13000)
check_reach_14000 = mark(14000)
check_reach_15000 = mark(15000)
check_reach_16000 = mark(16000)
check_reach_17000 = mark(17000)
check_reach_18000 = mark(18000)
check_reach_19000 = mark(19000)
check_reach_20000 = mark(20000)
check_reach_21000 = mark(21000)
check_reach_22000 = mark(22000)
check_reach_23000 = mark(23000)
check_reach_24000 = mark(24000)
check_reach_25000 = mark(25000)
check_reach_26000 = mark(26000)
check_reach_27000 = mark(27000)
check_reach_28000 = mark(28000)
check_reach_29000 = mark(29000)
check_reach_30000 = mark(30000)
check_reach_31000 = mark(31000)
check_reach_32000 = mark(32000)
check_reach_33000 = mark(33000)
check_reach_34000 = mark(34000)
check_reach_35000 = mark(35000)
check_reach_36000 = mark(36000)
check_reach_37000 = mark(37000)
check_reach_38000 = mark(38000)
check_reach_39000 = mark(39000)
check_reach_40000 = mark(40000)
check_reach_41000 = mark(41000)
check_reach_42000 = mark(42000)
check_reach_43000 = mark(43000)
check_reach_44000 = mark(44000)
check_reach_45000 = mark(45000)
check_reach_46000 = mark(46000)
check_reach_47000 = mark(47000)
check_reach_48000 = mark(48000)
check_reach_49000 = mark(49000)
check_reach_50000 = mark(50000)
