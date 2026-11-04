# snake/snake_plugin.py
"""This plugin adapts the Snake game of the gymnasium-snake-game package to soft_control_loop.

In Snake, a snake moves on a square grid, one cell per step, and grows each time it eats the food.
The game ends when the snake runs into a wall or into its own body. The package gymnasium-snake-game
already implements the game as a Gymnasium environment, so this plugin wraps it instead of writing
it again. The setup file in this folder names the environment "snake_plugin:SnakeEnv", and
load_setup puts this folder on sys.path, so the runtime and its child processes can import this
module.

The game needs two adaptations. Its observation is an image, an array of size by size by 3 numbers
that shows where the snake is but not the order of its cells or its heading, and an array is not
JSON-safe. SnakeEnv therefore reads the game's state and builds a dict of JSON-safe values. The game
also ignores the seed of reset and places the food with Python's random module, and the first food
of an episode depends on where the last episode's food was. SnakeEnv therefore makes a new game for
each episode and seeds the random module with the episode's seed, so that the same seed and the same
actions replay the same game.

Cells are [x, y] lists, with x from 0 (left) to size - 1 and y from 0 (top) to size - 1. The snake
starts with length 5, its head in the middle of the grid, heading right. An action is a heading: 0
up, 1 down, 2 left, 3 right.

This module defines SnakeEnv.

Rules:
- An action along the current axis, the same heading or its reverse, keeps the current heading.
- The snake may move into the cell that its tail leaves on the same step.
- Eating the food gives reward 1 and grows the snake by one cell. Running into a wall or the body
  gives reward -10 and terminates the episode. Every other step gives reward 0.
- The episode is truncated after max_step steps.
- SnakeEnv reads the game's internal state, so the game's version is pinned in pyproject.toml.
- The game cannot place food on a full grid and then never returns; the runtime's timeout ends
  such an episode.
"""

import random

from gymnasium_snake_game import SnakeEnv as SnakeGame

from soft_control_loop.environments import Discrete, Environment


class SnakeEnv(Environment):
    """The Snake game of gymnasium-snake-game as an environment with dict observations.

    size: the width and height of the grid, in cells. max_step: the number of steps after which
    the episode is truncated.
    """

    action_space = Discrete(4)
    observation_keys = ("head", "food", "body", "heading", "length")

    def __init__(self, size=16, max_step=1000):
        self.size = size
        self.max_step = max_step
        self.game = None

    def reset(self, seed=None):
        """Start a new game, with the food placed by seed, and return (observation, info)."""
        self.game = SnakeGame(width=self.size, height=self.size, max_step=self.max_step)
        random.seed(seed)  # the game ignores reset's seed and places food with the random module
        self.game.reset()
        return self.observation(), {}

    def step(self, action):
        """Move the snake one cell; return (observation, reward, terminated, truncated, info)."""
        _, reward, terminated, truncated, _ = self.game.step(action)
        return self.observation(), float(reward), bool(terminated), bool(truncated), {}

    def observation(self):
        """Return the game's state as a dict of JSON-safe values.

        The game keeps the body as a list from the tail to the neck, so the list is reversed.
        """
        snake = self.game.snake
        return {
            "head": [snake.head.x, snake.head.y],
            "food": [snake.food.block.x, snake.food.block.y],
            "body": [[cell.x, cell.y] for cell in reversed(snake.body)],
            "heading": snake.direction,
            "length": len(snake.body) + 1,
        }
