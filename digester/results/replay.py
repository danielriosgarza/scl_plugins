"""Replay a digester program on seeds; write per-seed scores and, optionally, trajectories.

Usage (from the digester folder's environment, so that soft_control_loop and microbesGYM import):

    python results/replay.py PROGRAM_DIR --seeds 7001-7050 [5061-5110 ...]
        [--decisions 400] [--workers 6] [--scores scores.csv] [--trajectories traj.csv[.gz]]
        [--program NAME] [--run RUN] [--attempt N] [--coder MODEL]

PROGRAM_DIR holds program.py and the library skills it imports (see results/programs/). Each
episode runs in its own worker process through the loop's own path (load_environment,
load_program, run_episode) with the wrapper A1Digester of the folder above this script, in
stochastic mode, with game over at the first breach. Seeds 1001-1008 and 6001-6020 use A1's
training draws, all others its validation draws, as in a1_digester.split_for_seed.

--scores writes one row per seed with the columns of results/scores.csv:
    program, run, attempt, coder_model, seed, seed_set, decisions, score, mean_ch4_flow,
    first_out, max_total_vfa, min_ph
--trajectories writes one row per decision (gzip if the name ends in .gz):
    seed, decision, day, feed_command, ch4_flow_true, total_vfa_true, ph_true,
    ch4_flow_observed, vfa_assay_sum_observed, assay_age
The *_true columns are A1's own decision row after the decision, as the wrapper reads it
(ch4_flow_true is the step reward). The *_observed columns are the readings the program sees
after that decision (its next observation); the VFA assays arrive every fourth decision and lag.
"""

import argparse
import csv
import gzip
import json
import os
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

DIGESTER = Path(__file__).resolve().parent.parent
VFA = ("vfa_s_va", "vfa_s_bu", "vfa_s_pro", "vfa_s_ac")
SCORE_COLUMNS = ["program", "run", "attempt", "coder_model", "seed", "seed_set", "decisions",
                 "score", "mean_ch4_flow", "first_out", "max_total_vfa", "min_ph"]
TRAJECTORY_COLUMNS = ["seed", "decision", "day", "feed_command", "ch4_flow_true",
                      "total_vfa_true", "ph_true", "ch4_flow_observed", "vfa_assay_sum_observed",
                      "assay_age"]


def seed_set(seed):
    """Name the seed range a seed belongs to, as in results/scores.csv."""
    if 5001 <= seed <= 5030:
        return "eval_5001_5030"
    if 5031 <= seed <= 5060:
        return "heldout_5031_5060"
    if 5061 <= seed <= 5110:
        return "heldout_5061_5110"
    if 7001 <= seed <= 7050:
        return "a1_7001_7050"
    return "other"


def play(program_dir, seed, decisions):
    """Play one episode in this process; return its score row fields and its trajectory rows."""
    sys.path.insert(0, str(DIGESTER))
    from soft_control_loop.environments import load_environment
    from soft_control_loop.programs import load_program
    from soft_control_loop.runtime import run_episode

    observables = json.loads((DIGESTER / "setup.json").read_text())["observables"]
    env = load_environment("a1_digester:A1Digester", decisions=decisions)
    program = load_program(program_dir)
    trace = run_episode(env, program, seed, observables, max_steps=decisions)
    final = trace.final_observation or {}
    rows = list(env._rows)  # A1's decision rows, one per decision played (see A1Digester.step)
    trajectory = []
    for k, step in enumerate(trace.steps):
        seen = trace.steps[k + 1].observation if k + 1 < len(trace.steps) else final
        assays = [seen.get(name) for name in VFA]
        row = rows[k]
        trajectory.append({
            "seed": seed, "decision": k + 1, "day": (k + 1) * 0.25,
            "feed_command": float(step.action[0]), "ch4_flow_true": float(step.reward),
            "total_vfa_true": float(row["total_vfa_kgCOD_m3"]), "ph_true": float(row["pH"]),
            "ch4_flow_observed": seen.get("ch4_flow"),
            "vfa_assay_sum_observed": sum(assays) if None not in assays else "",
            "assay_age": seen.get("assay_age"),
        })
    return {
        "seed": seed, "seed_set": seed_set(seed), "decisions": decisions,
        "score": final.get("score"), "mean_ch4_flow": final.get("mean_ch4_flow"),
        "first_out": final.get("first_out"), "max_total_vfa": final.get("max_total_vfa"),
        "min_ph": final.get("min_ph"), "failure": str(trace.failure) if trace.failure else "",
    }, trajectory


def seeds_of(spans):
    """Return the seeds named by spans, each a single seed such as 7001 or a range such as
    7001-7050."""
    seeds = []
    for span in spans:
        first, _, last = span.partition("-")
        seeds.extend(range(int(first), int(last or first) + 1))
    return seeds


def blank(value):
    """Return value, or an empty string for None, for a CSV cell."""
    return "" if value is None else value


def main():
    """Parse the arguments, replay the seeds in worker processes, and write and summarize the
    results."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("program_dir", type=Path)
    parser.add_argument("--seeds", nargs="+", required=True, help="seeds or ranges, e.g. 7001-7050")
    parser.add_argument("--decisions", type=int, default=400)
    parser.add_argument("--workers", type=int, default=min(6, os.cpu_count() or 1))
    parser.add_argument("--scores", type=Path)
    parser.add_argument("--trajectories", type=Path)
    parser.add_argument("--program", default=None,
                        help="name for the program column (default: the folder's name)")
    parser.add_argument("--run", default="")
    parser.add_argument("--attempt", default="")
    parser.add_argument("--coder", default="")
    args = parser.parse_args()
    program_dir = args.program_dir.resolve()
    name = args.program or program_dir.name
    seeds = seeds_of(args.seeds)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(play, [program_dir] * len(seeds), seeds,
                                [args.decisions] * len(seeds)))
    scores = [r for r, _ in results]
    for r in scores:
        r.update(program=name, run=args.run, attempt=args.attempt, coder_model=args.coder)
    if args.scores:
        with open(args.scores, "w", newline="") as out:
            writer = csv.DictWriter(out, SCORE_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for r in scores:
                writer.writerow({k: blank(r.get(k)) for k in SCORE_COLUMNS})
    if args.trajectories:
        opener = gzip.open if args.trajectories.suffix == ".gz" else open
        with opener(args.trajectories, "wt", newline="") as out:
            writer = csv.DictWriter(out, TRAJECTORY_COLUMNS)
            writer.writeheader()
            for _, trajectory in results:
                writer.writerows(trajectory)
    outs = [r for r in scores if r["first_out"] is not None]
    failures = [r for r in scores if r["failure"]]
    mean = statistics.mean(float(r["score"] or 0) for r in scores)
    print(f"{name}: {len(scores)} episodes, mean score {mean:.1f}, game overs {len(outs)} "
          f"{[(r['seed'], r['first_out']) for r in outs]}, failures {len(failures)}")
    for _, trajectory in results:
        seed = trajectory[0]["seed"] if trajectory else None
        r = next(x for x in scores if x["seed"] == seed) if seed is not None else None
        if r and r["first_out"] is None and r["mean_ch4_flow"] is not None:
            mean = statistics.mean(t["ch4_flow_true"] for t in trajectory)
            if abs(mean - r["mean_ch4_flow"]) > 1e-6:
                print(f"WARNING seed {seed}: trajectory mean {mean} differs from mean_ch4_flow "
                      f"{r['mean_ch4_flow']}")


if __name__ == "__main__":
    main()
