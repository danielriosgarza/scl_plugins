# The digester's results so far

This folder holds the best control programs that soft_control_loop has written for A1's anaerobic
digester, their scores seed by seed, five of them played decision by decision, and a script that
replays any of them. Everything here was produced on Daniel's PC with this folder's wrapper,
`a1_digester.py`, and checked by replaying the exported files.

**The program to keep is run9_065.** Run 9 ended on 2026-11-09 after 90 attempts. The loop's own
top pick, attempt 84, has the highest mean over its 40-day evaluation episodes, but on the 100
unseen seeds it scores 2661.9 with 9 game overs, so the program to keep was chosen on those seeds
(see below).

## How the numbers were made

- Every row is an episode of A1's aligned experiment, in stochastic mode, with the wrapper's game
  over: an episode ends at the first decision whose true state leaves the limits (pH below 6.5 or
  total VFA above 1.0 kgCOD/m3). A row with decisions 400 is A1's 100-day episode (one decision
  every 6 hours); a row with decisions 160 is a 40-day episode, as run 9 plays them.
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
| `new_5111_5250` | 5111-5250 | held out, 40-day episodes only (run 7's 027 and run 9's 035) |

Run 9 evaluated on 5001-5060 in 40-day episodes; this folder has no rows of run 9 on those seeds.
Runs 1 to 4 evaluated on 5001-5010 only. Their rows for 5011-5030 come from later held-out
replays but carry the label `eval_5001_5030`. Those replays predate game over, but none of their
episodes left the limits, so their values are the same with it.

## How the best program is chosen

A program is judged by A1's own score on seeds it never saw: the mean over the episodes of
`mean_ch4_flow_constrained`, where an episode that leaves the limits scores 0. A1 scores each of
its own approaches this way. The number of episodes that left the limits is given alongside. Daniel
chose this rule on 2026-11-06; before, a program had to stay within the limits on every unseen seed.

## Results on the 100 unseen seeds 7001-7050 and 5061-5110

| program | written by | mean score | 7001-7050 | 5061-5110 | game overs of 100 |
|---|---|---|---|---|---|
| **run9_065** | gemini-4-argon | **2818.2** | 2847.7 | 2788.7 | 2 |
| run9_067 | gemini-4-argon | 2813.0 | 2843.2 | 2782.7 | 2 |
| run9_043 | gemini-4-argon | 2806.1 | 2835.3 | 2776.9 | 2 |
| run9_059 | gpt-6.1-sol | 2806.1 | 2835.3 | 2776.8 | 2 |
| run9_048 | haiku | 2791.8 | 2821.3 | 2762.4 | 2 |
| run9_050 | gpt-6.1-sol | 2791.2 | 2822.7 | 2759.7 | 2 |
| run9_035 | haiku | 2790.8 | 2820.6 | 2760.9 | 2 |
| run9_053 | haiku | 2783.2 | 2836.9 | 2729.4 | 3 |
| run9_046 | gpt-6.1-sol | 2783.0 | 2810.5 | 2755.5 | 2 |
| run9_054 | gemini-4-argon | 2780.7 | 2811.3 | 2750.1 | 2 |
| run7_062 | haiku | 2772.1 | 2801.6 | 2742.6 | 2 |
| run9_052 | haiku | 2762.4 | 2789.3 | 2735.6 | 2 |
| run9_042 | gpt-6.1-sol | 2755.0 | 2782.9 | 2727.1 | 2 |
| run7_027 | gemini-4-argon | 2745.1 | 2793.6 | 2696.7 | 0 |

The other 25 programs scored on these seeds average 2474.8 to 2661.9, with 6 to 16 game overs each.

Programs scored on 7001-7050 only: run7_022 2742.7 (1 game over), run2_018 2713.8 (0), run1_015
2707.7 (0), run7_023 2680.8 (0), run7_026 2669.8 (2), run7_025 2646.2 (2), run7_029 2632.5 (3).
`scores.csv` has the coder of every program, and all seed sets.

Paired seed by seed on the 100 seeds:
- run9_065 against run9_043: +12.1 (se 2.0, t 5.9, better on 56).
- run9_065 against run9_035, the program its line of attempts started from: +27.4 (se 3.1, t 8.9,
  better on 86).
- run9_065 against run7_027: +73.1 (se 35.7, t 2.0, better on 91); on 7001-7050 +54.1 (t 1.1).
- run9_065 against run1_015 on 7001-7050: +140.0 (se 47.8, t 2.9, better on 49 of 50).

## Episodes that left the limits

- run9_065, run9_043 and every other run 9 program built on run9_035 leave the limits at decision
  8 on seeds 7005 and 5084. They feed at the maximum for the first decisions and cut only when the
  methane reading passes a ceiling. On these two seeds a protein-rich influent meets a low methane
  reading at decision 5, so the pump stays at the maximum one decision too long. Swapping the
  influent and the noise between seeds showed that neither alone does it.
- run7_027 stayed within the limits on all 160 seeds of 5001-5110 and 7001-7050, but in 40-day
  episodes on 5111-5250 it left them once, on seed 5177 at decision 16. run9_065 and run9_035
  stayed within them on all 140 of those seeds, where run9_065 averages 2787.0, run9_035 2770.6
  and run7_027 2628.9.
- Most of run 9's later programs leave the limits more often: at decisions 43 to 48 on a few
  influents that the loop's 60 evaluation seeds do not include, or after decision 160, the end of
  the loop's 40-day episodes, near which they push the feed.
- So no program here stays within the limits on every seed tested: run7_027 left them on 1 of the
  300 seeds it played, run9_065 and run9_035 on 2 of 300, and run9_043 on 2 of 160.

A1's own approaches on the same seeds are reported in microbesGYM, in
`docs/studies/control_a1_loading/report.md` and `docs/plans/a1-deep-rl/reviews/CR5.md`.

## Files

- `scores.csv`: one row per program, seed and episode length, 5,840 rows. The columns are program
  (`run<N>_<attempt>`), run, attempt, coder_model, seed, seed_set, decisions, score, mean_ch4_flow,
  first_out (the decision of the game over, empty if none), max_total_vfa and min_ph. A field is
  empty where its source recorded only the score, first_out and max VFA.
- `trajectories/`: one row per decision of each 100-day episode on 7001-7050, for run9_065,
  run9_043, run9_035, run7_027 and run1_015.
  - The columns are seed, decision, day, feed_command (m3/d), ch4_flow_true (the step reward),
    total_vfa_true and ph_true, all from A1's own decision row after the decision.
  - Then come ch4_flow_observed, vfa_assay_sum_observed and assay_age, the readings the program
    sees after that decision. The VFA assays arrive every fourth decision and describe the
    digester as it was 4 to 7 decisions earlier; their sum is empty before the first one arrives.
  - The mean of each episode's ch4_flow_true equals its score in `scores.csv`.
- `programs/run9_065`, `programs/run9_043`, `programs/run9_035`, `programs/run7_027`,
  `programs/run1_015` and `programs/run7_062`: each holds program.py and the library skills it
  imports, byte for byte, with a SHA256SUMS file. A program is `act(observation, memory)`, which
  returns the feed in m3/d (0 to 255) for the next 6 hours.
- `replay.py`: replays a program folder on any seeds and writes rows in the formats above.

## The programs

- **run9_065** (gemini-4-argon, run 9, round 7; its line of attempts is 035, 047, 058, 065).
  - It has the start-up and the VFA model of 043 (below), with a forecast limit of 0.80, or 0.77
    and a floor of 85 when inorganic carbon is at least 175 mM.
  - In place of 043's methane check, it keeps a posterior over eight classes of how strongly the
    influent loads the digester, updated from the opening methane readings, from each assay, and
    from decision 16 from a ridge model of methane on the last six pump flows.
  - From decision 40 (24 for weak influents), while its fit holds, no alarm is on and the assays
    stay below about 0.82 to 0.85, it may raise the feed by 8 per decision (12 for weak
    influents), if a worst-case forecast from the posterior stays at or below 0.84.
  - From decision 146 it raises the feed by up to 34 per decision while the forecast over the
    rest of the 40 days stays at or below 0.875 to 0.89. In 100-day episodes this stays on after
    decision 160 with a one-decision horizon; on the 100 unseen seeds it left the limits only at
    decision 8.
- **run9_043** (gemini-4-argon, run 9, built on run9_035).
  - Start-up: it feeds the maximum (255) for decisions 1 to 4. At decisions 5 to 8 it cuts the
    command by 55 whenever the methane reading is above a ceiling (2560, 2620, 2645, 2645), and
    from decision 9 to 16 it never raises the feed.
  - It estimates total VFA with a one-state model driven by the pump's flow, corrected by a Kalman
    update at each lagged assay, with its two parameters refitted by least squares.
  - From decision 16, a methane reading more than 3% below what the recent commands predict raises
    the VFA estimate, and one more than 3% above lowers it.
  - Each decision takes the largest command, from 100 to 255 and moving at most 25 down or 6 up,
    whose forecast VFA peak over the next 8 decisions stays at or below 0.82 (0.77 when inorganic
    carbon is high), with pessimistic parameters.
  - It freezes the feed when inorganic carbon is at least 175 mM, and gas alarms (the CO2 to CH4
    ratio or the CH4 pressure) hold or cut it while the model's fit has failed.
- **run9_035** (haiku, run 9, round 4). The same start-up, VFA model and guards as 043, with the
  VFA forecast limit at 0.78 for every inorganic carbon level and without 043's methane check.
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
python results/replay.py results/programs/run9_065 --seeds 7001-7050 5061-5110 --decisions 400 \
    --workers 6 --scores my_scores.csv --trajectories my_traj.csv \
    --program run9_065 --run 9 --attempt 65 --coder gemini-4-argon
```

- `--seeds` takes single seeds and ranges.
- `--decisions 160` plays 40-day episodes, as the loop's run 9 does.
- A trajectory file whose name ends in `.gz` is compressed.
- The script prints the mean score and the game overs.
- Replaying the exported folders reproduces the scores in `scores.csv`. Run 9's rows come from
  the held-out checks, which kept the score to 0.1 and the maximum VFA to 0.001, except those of
  run9_065, run9_043 and run9_035 on 7001-7050, which come from full replays.
