# The digester's results so far

This folder holds the best control programs that soft_control_loop has written for A1's anaerobic
digester, their scores seed by seed, two of them played decision by decision, and a script that
replays any of them. Everything here was produced on Daniel's PC with this folder's wrapper,
`a1_digester.py`, and checked by replaying the exported files.

## How the numbers were made

- Every row is a 100-day episode (400 decisions, one every 6 hours) of A1's aligned experiment, in
  stochastic mode, with the wrapper's game over: an episode ends at the first decision whose true
  state leaves the limits (pH below 6.5 or total VFA above 1.0 kgCOD/m3).
- `score` is A1's score, `mean_ch4_flow_constrained`: the mean true methane outflow (m3/d) over the
  episode, or 0 if the episode left the limits. A1 scores such an episode 0 too, so `score` compares
  directly with A1's own results. `mean_ch4_flow` does not: in a game over it covers only the
  decisions played.
- Seeds 1001-1008 and 6001-6020 use A1's training draws; every seed here uses its validation draws.
  7001-7050 are the seeds on which A1's study reports its own approaches.

## Seed sets

| seed_set | Seeds | Role |
|---|---|---|
| `eval_5001_5030` | 5001-5030 | evaluation seeds of runs 5 to 7, used to select programs |
| `heldout_5031_5060` | 5031-5060 | held out |
| `heldout_5061_5110` | 5061-5110 | held out, never looked at before attempt 027 was chosen |
| `a1_7001_7050` | 7001-7050 | A1's own seeds, held out |

Runs 1 to 4 evaluated on 5001-5010 only. Their rows for 5011-5030 come from later held-out
replays but carry the label `eval_5001_5030`. Those replays predate game over, but none of their
episodes left the limits, so their values are the same with it.

## Results on A1's seeds 7001-7050

| program | written by | mean score | game overs of 50 |
|---|---|---|---|
| run7_062 | haiku | 2801.6 | 1 |
| **run7_027** | gemini-4-argon | **2793.6** | **0** |
| run7_022 | haiku | 2742.7 | 1 |
| run2_018 | haiku | 2713.8 | 0 |
| run1_015 | gpt-6.1-sol | 2707.7 | 0 |
| run7_023 | gemini-4-argon | 2680.8 | 0 |
| run7_026 | haiku | 2669.8 | 2 |
| run7_064 | gpt-6.1-sol | 2668.6 | 3 |
| run7_065 | gemini-4-argon | 2664.1 | 3 |
| run7_025 | gemini-4-argon | 2646.2 | 2 |
| run7_029 | gemini-4-argon | 2632.5 | 3 |
| run7_066 | haiku | 2565.6 | 5 |

`scores.csv` has the coder of every program, and all seed sets.

**run7_027 is the program to keep.** It stayed within the limits on all 160 seeds it has played
(5001-5110 and 7001-7050). Paired seed by seed with run1_015, it is +85.9 on 7001-7050 (se 12.9,
t 6.7, better on 43 of 50) and +82.4 on 5031-5060 (se 17.7, t 4.7). run7_062 scores a little higher
on 7001-7050 but left the limits on 5 of the 130 held-out seeds, all at decisions 12 to 18.

A1's own approaches on the same seeds are reported in microbesGYM, in
`docs/studies/control_a1_loading/report.md` and `docs/plans/a1-deep-rl/reviews/CR5.md`.

## Files

- `scores.csv`: one row per program and seed, 2,020 rows. The columns are program
  (`run<N>_<attempt>`), run, attempt, coder_model, seed, seed_set, decisions, score, mean_ch4_flow,
  first_out (the decision of the game over, empty if none), max_total_vfa and min_ph. A field is
  empty where its source recorded only the score, first_out and max VFA.
- `trajectories/run7_027_a1_7001_7050.csv` and `trajectories/run1_015_a1_7001_7050.csv`: one row per
  decision of each 100-day episode on 7001-7050.
  - The columns are seed, decision, day, feed_command (m3/d), ch4_flow_true (the step reward),
    total_vfa_true and ph_true, all from A1's own decision row after the decision.
  - Then come ch4_flow_observed, vfa_assay_sum_observed and assay_age, the readings the program
    sees after that decision. The VFA assays arrive every fourth decision and describe the
    digester as it was 4 to 7 decisions earlier; their sum is empty before the first one arrives.
  - The mean of each episode's ch4_flow_true equals its score in `scores.csv`.
- `programs/run7_027`, `programs/run1_015` and `programs/run7_062`: each holds program.py and the
  library skills it imports, byte for byte, with a SHA256SUMS file. A program is
  `act(observation, memory)`, which returns the feed in m3/d (0 to 255) for the next 6 hours.
- `replay.py`: replays a program folder on any seeds and writes rows in the formats above.

## The three programs

- **run7_027** (gemini-4-argon, run 7, round 3).
  - It probes at the pump's maximum (255) for decisions 1 to 3.
  - At decision 4 it maps the rise in methane during the probe to a plateau feed through five
    knots (`smoothstep_interpolate`). A strong rise means a rich influent and a low plateau.
  - It holds that plateau until decision 8, then hands over to a PI on the assayed total VFA
    (setpoint 0.55, `anti_windup_pi_step`).
  - After that it climbs 12 m3/d after every two clean assays. At the first warning it backs off
    24 and waits 16 decisions, and above a total VFA of 0.85 a PI brake cuts the feed.
- **run1_015** (gpt-6.1-sol, run 1).
  - It has no probe. It ramps from 128 by an assay-gated rule (`vfa_gated_ramp`).
  - From decision 48 it hands over to a plain VFA PI (`vfa_pi_handoff`, `vfa_pi_feed`).
- **run7_062** (haiku, run 7, round 7).
  - It has the same probe and plateau as 027.
  - Then a proportional controller on the ratio of total VFA to inorganic carbon raises the feed by
    up to 20 per assay. On a few rich influents that lifts the feed too soon after the plateau.

## Replaying

From an environment where soft_control_loop and microbesGYM import (for example this digester
folder's own environment):

```bash
cd digester
python results/replay.py results/programs/run7_027 --seeds 7001-7050 --decisions 400 --workers 6 \
    --scores my_scores.csv --trajectories my_traj.csv \
    --program run7_027 --run 7 --attempt 27 --coder gemini-4-argon
```

- `--seeds` takes single seeds and ranges.
- `--decisions 160` plays 40-day episodes, as the loop's run 9 does.
- A trajectory file whose name ends in `.gz` is compressed.
- The script prints the mean score and the game overs.
- Replaying the exported folders reproduces the scores in `scores.csv` exactly.
