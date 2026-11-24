"""Tests of the a1_adm1 plugin against microbesGYM's own code and the numbers of its TASK.md.

The fast tests play a few decisions. The tests marked slow play whole episodes of 568 decisions,
about half a minute each, and compare the scores with the numbers that TASK.md publishes for the
fixed rates 200 and 100 m3/d ("What the score does not see"): 8768, 9654 and 8839 on the seeds
6001, 6002 and 6008.
"""

import json
from pathlib import Path

import pytest
from mgym_bench.episode import Episode, EpisodeError
from soft_control_loop import config, runtime, traces
from soft_control_loop.programs import load_program

import a1_adm1
import bridge
import checks

FOLDER = Path(__file__).parent.parent
HOLD = FOLDER / "programs" / "hold_200_100"
SENSORS = ["ch4_flow", "co2_flow", "ch4_pressure", "vfa_s_va", "vfa_s_bu", "vfa_s_pro",
           "vfa_s_ac", "inorganic_carbon", "ph"]
LAB = SENSORS[3:8]
RECORD = ["net_methane", "net_methane_start", "net_methane_middle", "net_methane_end",
          "net_methane_run_out", "collapsed", "mean_ch4_flow", "mean_acids_out", "min_ph",
          "max_total_vfa", "end_ph", "end_total_vfa", "failed"]
# The hash of the task document when the plugin was tested. It changes when the task, its model
# or its seeds change in microbesGYM (commit 43491a5).
TASK_SHA256 = "89609ceb844ba4cef4f4ab724a83803872cfe093172afc04f1cec2d29672bfb0"


@pytest.fixture(scope="module")
def env():
    return a1_adm1.Loading()


def test_the_task_is_the_one_the_plugin_was_tested_with():
    assert a1_adm1.load_task().sha256 == TASK_SHA256, (
        "a1_adm1/loading changed in microbesGYM since the plugin was tested: read its TASK.md "
        "again, check the setup's description against it, and then update this hash")


def test_the_observation_holds_what_the_task_gives_a_controller(env):
    assert env.observation_keys == (SENSORS + ["lab_age", "sludge_rate", "carbohydrate_rate"]
                                    + RECORD)
    assert (env.action_space.low, env.action_space.high) == ([0.0, 0.0], [1000.0, 300.0])
    observation, info = env.reset(6001)
    assert info == {"seed": 6001}
    assert all(isinstance(observation[name], float) for name in SENSORS if name not in LAB)
    assert all(observation[name] is None for name in LAB + ["lab_age"] + RECORD)
    assert (observation["sludge_rate"], observation["carbohydrate_rate"]) == (85.0, 0.0)


def test_laboratory_values_arrive_late_and_pumps_move_by_their_limits(env):
    env.reset(6001)
    ages, rates, acetate = [], [], []
    for _ in range(12):
        observation, reward, terminated, truncated, info = env.step([200.0, 100.0])
        ages.append(observation["lab_age"])
        rates.append((round(observation["sludge_rate"], 6),
                      round(observation["carbohydrate_rate"], 6)))
        acetate.append(observation["vfa_s_ac"])
        assert (terminated, truncated, info) == (False, False, {})
        assert all(observation[key] is None for key in RECORD)
        values = env._episode.values[-1]
        assert reward == pytest.approx(values["ch4_flow_true"] - 0.395 * values["acids_out_true"])
    assert ages == [None, None, None, 4, 5, 6, 7, 4, 5, 6, 7, 4]
    assert rates[:5] == [(119.0, 10.0), (153.0, 20.0), (187.0, 30.0), (200.0, 40.0), (200.0, 50.0)]
    assert acetate[:3] == [None, None, None] and acetate[3] == acetate[6] != acetate[7]


def test_the_loop_cannot_play_a_test_or_a_validation_seed(env):
    for seed in (7001, 7050, 12001, 12050):
        with pytest.raises(EpisodeError, match="training episode must not use it"):
            env.reset(seed)


def test_a_program_reads_the_same_observation_in_the_bridge_as_in_the_loop(env, tmp_path):
    (tmp_path / "program.py").write_text(
        "def act(observation, memory):\n"
        "    memory.setdefault('seen', []).append(dict(observation))\n"
        "    return [150.0 + 10 * len(memory['seen']), 40.0], 'record'\n")
    observables = env.observation_keys
    trace = runtime.run_episode(env, load_program(tmp_path), 6003, observables, max_steps=10)
    episode = Episode(a1_adm1.load_task())
    controller = bridge.ProgramController(load_program(tmp_path), observables,
                                          a1_adm1.record_keys(episode.rules))
    controller.reset(episode.interface)
    observation = episode.reset(6003, "training")
    for _ in range(10):
        observation = episode.step(controller.act(observation))
    assert controller._memory["seen"] == [step.observation for step in trace.steps]


def test_the_bridge_refuses_what_the_runtime_would_reject(tmp_path):
    episode = Episode(a1_adm1.load_task())
    for body in ("return [200.0, 301.0], 'x'", "return [200.0, 100.0]", "return [200.0], 'x'"):
        (tmp_path / "program.py").write_text(f"def act(observation, memory):\n    {body}\n")
        controller = bridge.ProgramController(load_program(tmp_path), ["ph"], [])
        controller.reset(episode.interface)
        with pytest.raises(ValueError):
            controller.act(episode.reset(6001, "training"))


def test_the_setup_loads_and_keeps_away_from_the_test_and_validation_seeds():
    setup = config.load_setup(FOLDER / "setup.json")
    used = {*setup.seeds["debug"], *setup.seeds["evaluation"], *setup.baseline["seeds"],
            *setup.selection["seeds"], *setup.tuning["seeds"]}
    assert not used & {*range(7001, 7051), *range(12001, 12051), *range(11001, 11051)}
    judged = {*setup.seeds["evaluation"], *setup.selection["seeds"]}
    assert not judged & {*setup.tuning["seeds"], *setup.baseline["seeds"], *setup.seeds["debug"]}
    assert not {*setup.seeds["evaluation"]} & {*setup.selection["seeds"]}
    assert (setup.kwargs, setup.reuse) == ({"backend": "jax"}, True)
    assert all((FOLDER / path / "program.py").is_file()
               for path in setup.baseline["conditions"].values())
    assert setup.observables == a1_adm1.Loading().observation_keys
    assert (setup.score, setup.failure) == ("net_methane", "failed")
    assert [rule["name"] for rule in setup.rules] == ["no_clock", "own_memory", "observation_only"]
    assert setup.budgets["max_steps"] is None
    found = {name for name in dir(checks) if name.startswith("check_")}
    assert {f"check_{milestone['name']}" for milestone in setup.milestones} == found


def test_the_first_mark_is_what_the_fixed_rates_scored(env):
    assert checks.check_hold([_trace(checks.BASE, False)])
    assert not checks.check_hold([_trace(checks.BASE - 1.0, False)])
    assert not checks.check_reach_10000([_trace(9999.9, False)])


def test_a_slow_rise_moves_both_pumps_in_proportion_and_then_holds_them(env):
    program = load_program(FOLDER / "programs" / "ramp_300_130_3")
    trace = runtime.run_episode(env, program, 6001, env.observation_keys, max_steps=50)
    rates = [(step.observation["sludge_rate"], step.observation["carbohydrate_rate"])
             for step in trace.steps]
    assert rates[0] == (85.0, 0.0) and trace.failure is None
    assert rates[1] == pytest.approx((85.0 + 215.0 * 3 / 130, 3.0))
    assert rates[10] == pytest.approx((85.0 + 215.0 * 30 / 130, 30.0))
    assert rates[44] == rates[49] == pytest.approx((300.0, 130.0))


def _trace(score, failed):
    return traces.Trace({"seed": 0}, final_observation={"net_methane": score, "failed": failed})


def test_a_mark_needs_the_mean_score_and_no_failed_episode():
    check = checks.mark(100.0)
    assert check([_trace(90.0, False), _trace(110.0, False)])
    assert not check([_trace(90.0, False), _trace(109.0, False)])
    assert not check([_trace(500.0, False), _trace(500.0, True)])
    assert not check([_trace(500.0, False), traces.Trace({"seed": 0})])
    assert not check([_trace(500.0, False), _trace(None, None)])


@pytest.mark.slow
def test_fixed_rates_give_the_scores_of_task_md():
    played = runtime.run_in_children([
        {"environment": "a1_adm1:Loading", "program_path": str(HOLD), "seed": seed,
         "observables": a1_adm1.Loading().observation_keys, "timeout": 900}
        for seed in (6001, 6002, 6008)])
    for trace, score in zip(played, (8768, 9654, 8839)):
        final = trace.final_observation
        assert trace.failure is None and len(trace.steps) == 568
        assert traces.ending(trace) == "truncated"
        assert final["net_methane"] == pytest.approx(score, abs=0.5)
        assert (final["failed"], final["collapsed"]) == (False, 0.0)
        rewards = [step.reward for step in trace.steps]
        assert sum(rewards[:400]) / 400 == pytest.approx(final["net_methane"], rel=1e-9)
        assert sum(rewards[400:]) / 168 == pytest.approx(final["net_methane_run_out"], rel=1e-9)
        assert final["net_methane"] == pytest.approx(
            0.2 * final["net_methane_start"] + 0.4 * final["net_methane_middle"]
            + 0.4 * final["net_methane_end"], rel=1e-9)


@pytest.mark.slow
def test_the_bridge_gives_the_score_of_the_loop(tmp_path):
    result = bridge.play("program", HOLD, "training", seeds=[6001], backend="reference")
    assert result["episodes"][0]["metrics"]["net_methane"] == pytest.approx(8768, abs=0.5)
    assert (result["failed"], result["task"]["sha256"]) == (0, TASK_SHA256)
    assert result["episodes"][0]["outcome"] == "horizon"
    assert json.loads(json.dumps(result)) == result
