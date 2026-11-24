"""The fixed milestones of a1_adm1/loading: marks on the mean score with no failed episode.

A mark is met when no evaluation episode failed and the mean of their scores, the task's net
methane in m3/d, is at least the mark. An episode failed when its record says so (the digester
collapsed, or the episode did not run all its decisions) or when it has no record, because the
program failed before the end. The checks are batch checks: each judges all evaluation episodes
together, so it passes or fails as a whole whatever the setup's pass rate.

The marks rise from the loop's own baseline. Its best fixed rates, 200 and 100 m3/d, scored a
mean of BASE on the evaluation seeds 6021 to 6080, with no failed episode (results/README.md).
The first mark is BASE, and each further mark is BASE times a factor. Results of other
controllers of the benchmark set no mark.

This module defines BASE; mark, which returns the check of one mark; and one check for each fixed
milestone of the setup.
"""

BASE = 9216.9


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


check_hold = mark(9217)
check_plus_5 = mark(9678)
check_plus_10 = mark(10139)
check_plus_15 = mark(10599)
check_plus_20 = mark(11060)
check_plus_25 = mark(11521)
check_plus_30 = mark(11982)
