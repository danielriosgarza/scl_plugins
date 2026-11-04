# snake/tests/test_snake_plugin.py
import json
from pathlib import Path

from soft_control_loop import agents, config, runtime
from snake_plugin import SnakeEnv

PLUGIN = Path(__file__).parent.parent


def started(seed=7):
    env = SnakeEnv()
    env.reset(seed=seed)  # seed 7 puts the food at [10, 4], away from the row the snake starts on
    return env


def test_the_observation_shows_the_start_in_json_safe_values():
    # Proves the adapter turns the game's image into the documented dict; programs and traces need JSON-safe values.
    observation, _ = SnakeEnv().reset(seed=7)
    assert json.loads(json.dumps(observation)) == observation
    assert tuple(observation) == SnakeEnv.observation_keys
    assert observation["head"] == [8, 8] and observation["body"] == [[7, 8], [6, 8], [5, 8], [4, 8]]
    assert observation["heading"] == 3 and observation["length"] == 5


def test_the_same_seed_replays_the_same_game():
    # Proves reset's seed fixes the food, even on a reused environment; the game alone ignores the seed.
    def play(env, seed):
        observations = [env.reset(seed=seed)[0]]
        for action in [3, 1, 1, 2, 2, 0, 0, 3]:
            observations.append(env.step(action)[0])
        return observations

    env = SnakeEnv()
    first = play(env, 7)
    assert play(env, 7) == first and play(SnakeEnv(), 7) == first
    assert play(env, 8)[0]["food"] != first[0]["food"]


def test_an_action_along_the_axis_keeps_the_heading():
    # Proves the turning rule the description states; a program that reverses would otherwise expect to turn back.
    env = started()
    observation, _, terminated, _, _ = env.step(2)
    assert not terminated and observation["heading"] == 3 and observation["head"] == [9, 8]
    observation, _, _, _, _ = env.step(1)
    assert observation["heading"] == 1 and observation["head"] == [9, 9]


def test_eating_gives_1_and_grows_the_snake():
    # Proves the reward and the growth reach the observation; progress in length would otherwise not show.
    env = started()
    env.game.snake.food.block.move_to(9, 8)  # put the food in front of the head
    observation, reward, terminated, _, _ = env.step(3)
    assert reward == 1.0 and not terminated
    assert observation["length"] == 6 and observation["body"][:2] == [[8, 8], [7, 8]]


def test_the_setup_loads_and_its_baseline_plays():
    # Proves the setup file and the plugin work together, in a child process too; a broken plugin would otherwise fail in the first live run.
    setup = config.load_setup(PLUGIN / "setup.json")
    assert setup.observables == list(SnakeEnv.observation_keys)
    assert isinstance(config.make_agents(setup, agents.Usage())["coordinator"].backend,
                      agents.ClaudeCode)
    trace = runtime.run_in_child(setup.environment, setup.baseline["conditions"]["straight"], 0,
                                 setup.observables, kwargs=setup.kwargs)
    assert trace.failure is None and len(trace.steps) == 8
    assert trace.steps[-1].terminated and trace.steps[-1].reward == -10.0
