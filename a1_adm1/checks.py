"""The fixed milestones of a1_adm1/loading: marks on the mean score with no failed episode.

A mark is met when no evaluation episode failed and the mean of their scores, the task's net
methane in m3/d, is at least the mark. An episode failed when its record says so (the digester
collapsed, or the episode did not run all its decisions) or when it has no record, because the
program failed before the end. The checks are batch checks: each judges all evaluation episodes
together, so it passes or fails as a whole whatever the setup's pass rate.

The first mark is BASE: what the fixed rates 200 and 100 m3/d (programs/hold_200_100) scored on
the evaluation seeds 6021 to 6100, with no failed episode (results/README.md). The further marks
are every 1000 m3/d from 10 000 to 17 000. Results of other controllers of the benchmark set no
mark.

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
