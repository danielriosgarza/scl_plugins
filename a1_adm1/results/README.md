# Results of the a1_adm1 plugin

This folder is the record of the work on `a1_adm1/loading`: the baseline, every iteration of the
loop with its test result, and what was changed after it. The rule for seeds of microbesGYM asks
that every iteration and its test result stay on record.

All numbers are the task's score, net methane in m3/d, computed by the benchmark's own code. An
episode failed when the digester collapsed (true pH below 6.0 at the end of a decision, the
run-out included) or the episode did not run all its 568 decisions.

## Baseline (2026-11-24)

Three open-loop programs, each holding both pumps at one pair of rates. They were played on
training seeds only, on the backend `reference`, with microbesGYM at commit `43491a5`.
`baseline.csv` has one line per episode with all metrics of the task.

On the baseline seeds 6001 to 6020, which are the seeds of the table of fixed rates in `TASK.md`:

| Program | Sludge, concentrate (m3/d) | Mean score | Failed | Lowest pH | Start | Middle | End | Run-out |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `hold_85_0` | 85, 0 | 1755.3 | 0 of 20 | 7.35 | 1766 | 1754 | 1751 | 1755 |
| `hold_200_100` | 200, 100 | 9330.1 | 0 of 20 | 6.67 | 8747 | 9475 | 9477 | 9480 |
| `hold_200_110` | 200, 110 | 3886.1 | 7 of 20 | 4.10 | 5335 | 3545 | 3502 | 3491 |

The last four columns are the mean net methane of the start phase (days 0 to 20), the middle
phase (days 20 to 60), the end phase (days 60 to 100) and the run-out (days 100 to 142).

`TASK.md` gives 1760, 9330 and 3890 m3/d for these rows, 0, 0 and 7 collapsed episodes, and the
lowest pH 7.35, 6.67 and 4.10. The adapter therefore reproduces the benchmark's own trial
episodes. With 200 and 110 m3/d the seven failed episodes are the seeds 6002, 6004, 6005, 6009,
6012, 6013 and 6016, and the 13 others have a mean of 9704.

On the evaluation seeds 6021 to 6080:

| Program | Mean score | Failed | Lowest pH | Lowest score | Highest score | Start | Middle | End | Run-out |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `hold_200_100` | 9216.9 | 0 of 60 | 6.64 | 8704.1 | 9958.8 | 8653 | 9358 | 9358 | 9361 |

This number is the base of the fixed milestones in `checks.py`: the first mark is 9217 with no
failed episode, and the further marks are 5, 10, 15, 20, 25 and 30 % above it.

Computer time: 60 episodes took 7.5 minutes on 4 processor cores, which is 30 s of one core for
an episode of 568 decisions.

The bridge was checked on four training seeds, 6001 to 6004, with the backend `jax`: it replayed
the benchmark's PI controller file and gave the scores of the benchmark's own training scorecard
of that controller to within 2 x 10^-11 m3/d. No development seed and no final seed was played.

## Iterations

None yet. Each iteration gets a folder `iteration_N/` with the setup that trained it, the result
of the run, the selected program, its test result on the seeds 7001 to 7050 from `bridge.py`, and
a note on what was changed for the next iteration and why.
