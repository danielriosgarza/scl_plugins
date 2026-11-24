"""The bridge plays a program of the loop as a controller of microbesGYM's own runner.

The loop plays training episodes only (see a1_adm1.py). The rule for seeds of microbesGYM has two
more steps: a test of the finished program on the development seeds, 7001 to 7050, which may lead
to another training, and one validation on the final seeds, 12001 to 12050, after which nothing is
changed. A person runs both steps by hand, with this module. It plays each episode with
mgym_bench.run.run_episode, the function that plays every controller of the benchmark, so the
result of a program stands next to the benchmark's scorecards like for like.

    uv run python bridge.py program RUN/attempts/065 --skills RUN/library \
        --split development --backend jax --workers 4 --out results/iteration_1/test.json

    uv run python bridge.py controller GYM/results/a1_adm1/loading/pi/controller.json \
        --split development --backend jax --workers 4 --out results/iteration_1/pi_check.json

GYM is the folder of the microbesGYM repository. The second command replays a controller file of
the benchmark through the same code. Run it first
on the computer of a test: its mean score must equal the mean of the benchmark's own scorecard of
that controller on the same split and backend, or the computer, the backend or the code differs
and the program's numbers cannot stand next to the benchmark's.

The result is written as JSON: the task with the hash of its document, which changes when the
task, its model or its seeds change, the commit of the microbesGYM repository and whether its
files differ from it, the split, the seeds, the backend,
what was played with its SHA-256 hash, one record per episode (seed, outcome, success, decisions
and the task's metrics), the mean of each metric, the number of failed episodes, and the seconds
that the episodes took.

This module defines ProgramController, which gives a program the form of a controller of the
benchmark; play, which plays one program or one controller file on seeds of one split; and main,
the command line.

Rules:
- A program reads the same observation here as in a training episode of the loop: the dict that
  a1_adm1.observe makes, cut to the observables of the setup, as a copy. It keeps one memory dict
  for the episode, and every episode loads the program anew and gets a new memory.
- An action that the loop's runtime would reject, anything but a list of two finite numbers inside
  the limits of the pumps, raises ValueError. The runner then stops with the seed and the
  decision, and no result is written, because a result without one of its episodes would not be
  the result of the program on the split.
- The split final needs --final, and the bridge refuses to write over an existing result of that
  split. The validation is run once.
- The episodes do not depend on each other, on their order or on the number of workers: each
  worker process builds the task once, and each episode gets a new controller.
"""

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

from mgym_bench import run
from mgym_bench.episode import Episode
from soft_control_loop.config import load_setup
from soft_control_loop.environments import Box
from soft_control_loop.programs import load_program

import a1_adm1

SETUP = Path(__file__).parent / "setup.json"


class ProgramController:
    """A program of the loop in the form of a controller of the benchmark (reset and act).

    program is the module that soft_control_loop.programs.load_program returns, observables the
    keys that the program may see, in the setup's order, and record the keys of the episode
    record, which a program reads as None at every decision.
    """

    def __init__(self, program, observables, record):
        self._program = program
        self._observables = list(observables)
        self._record = dict.fromkeys(record)
        self._interface = None
        self._space = None
        self._memory = None

    def reset(self, interface):
        """Take the interface of the task and start with an empty memory."""
        self._interface = interface
        self._space = Box([actuator.low for actuator in interface.actuators],
                          [actuator.high for actuator in interface.actuators])
        self._memory = {}

    def act(self, observation):
        """Return the rates that the program asks for, by the id of each pump.

        Raise ValueError when act() of the program does not return (action, subgoal) with an
        action inside the limits of the pumps.
        """
        seen = a1_adm1.observe(self._interface, observation, self._record)
        result = self._program.act(copy.deepcopy({key: seen[key] for key in self._observables}),
                                   self._memory)
        if not (isinstance(result, tuple) and len(result) == 2):
            raise ValueError(f"act() must return (action, subgoal), got {result!r}")
        if not self._space.contains(result[0]):
            raise ValueError(f"{result[0]!r} is not in the action space")
        return {actuator.id: float(value)
                for actuator, value in zip(self._interface.actuators, result[0])}


_EPISODE = None


def _start(backend, final):
    """Build the episode of a worker process once."""
    global _EPISODE
    _EPISODE = Episode(a1_adm1.load_task(), backend=backend, final=final)


def _one(job):
    """Play one episode in a worker and return its record. job is (kind, path, skills,
    observables, seed, split)."""
    kind, path, skills, observables, seed, split = job
    if kind == "program":
        controller = ProgramController(load_program(path, skills), observables,
                                       a1_adm1.record_keys(_EPISODE.rules))
    else:
        controller = run.load_controller(Path(path)).create()
    result = run.run_episode(_EPISODE, controller, seed, split)
    return {"seed": seed, "outcome": result.outcome, "success": result.success,
            "decisions": result.decisions, "metrics": dict(result.metrics)}


def _sha256(paths):
    """Return the SHA-256 hash of the bytes of the files, in the order of their names."""
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _commit(folder):
    """Return the commit of the git repository that holds folder, and whether its files differ
    from that commit; (None, None) when git cannot tell."""
    try:
        commit = subprocess.run(["git", "-C", str(folder), "rev-parse", "HEAD"], check=True,
                                capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(folder), "status", "--porcelain"],
                                    check=True, capture_output=True, text=True).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return None, None
    return commit, dirty


def play(kind, path, split, seeds=None, backend="jax", workers=1, skills=(), final=False):
    """Play a program folder (kind "program") or a controller file of the benchmark (kind
    "controller") on seeds of split and return the result as a JSON-safe dict.

    Without seeds, every seed of the split is played. skills are the folders of the skills that
    a program imports. The top of this module lists what the result holds.
    """
    task = a1_adm1.load_task()
    path = Path(path)
    seeds = list(run.seeds_of(task, split) if seeds is None else seeds)
    observables = load_setup(SETUP).observables
    skills = [str(Path(folder)) for folder in skills]
    jobs = [(kind, str(path), skills, observables, seed, split) for seed in seeds]
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("spawn"),
                             initializer=_start, initargs=(backend, final)) as pool:
        episodes = list(pool.map(_one, jobs))
    seconds = round(time.perf_counter() - start, 1)
    files = [path / "program.py", *(file for folder in skills
                                    for file in Path(folder).glob("*.py"))] \
        if kind == "program" else [path]
    commit, dirty = _commit(Path(run.__file__).parent)
    names = list(episodes[0]["metrics"])
    return {
        "task": {"id": task.full_id, "sha256": task.sha256},
        "microbesgym": {"commit": commit, "differs_from_commit": dirty},
        "split": split, "seeds": seeds, "backend": backend,
        "played": {"kind": kind, "path": str(path), "sha256": _sha256(files)},
        "episodes": episodes,
        "mean": {name: sum(e["metrics"][name] for e in episodes) / len(episodes)
                 for name in names},
        "failed": sum(1 for e in episodes if not e["success"]),
        "seconds": seconds,
    }


def main(argv=None):
    """Run the command line and return its exit status."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("kind", choices=("program", "controller"))
    parser.add_argument("path", help="a program folder, or a controller file of the benchmark")
    parser.add_argument("--split", required=True, choices=("training", "development", "final"))
    parser.add_argument("--seeds", type=int, nargs="+", help="by default all seeds of the split")
    parser.add_argument("--backend", default="jax", choices=("reference", "jax"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--skills", action="append", default=[],
                        help="a folder of skills that the program imports; may be repeated")
    parser.add_argument("--final", action="store_true",
                        help="allow the split final: the one validation run")
    parser.add_argument("--out", required=True, help="the JSON file of the result")
    args = parser.parse_args(argv)
    out = Path(args.out)
    if args.split == "final" and not args.final:
        parser.error("the split final is the one validation run and needs --final")
    if args.split == "final" and out.exists():
        parser.error(f"{out} exists: the validation is run once and is not written over")
    result = play(args.kind, args.path, args.split, args.seeds, args.backend, args.workers,
                  args.skills, final=args.final)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    score = next(iter(result["mean"]))
    print(f"{args.split}, {len(result['seeds'])} episodes, backend {args.backend}: mean {score} "
          f"{result['mean'][score]:.1f}, failed {result['failed']}, {result['seconds']} s",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
