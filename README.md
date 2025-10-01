# Compression Game

An interactive game where you compress sequences by grouping and clamping elements.

## Usage

Install dependencies:

uv sync

The game can be run in several modes:

### Random Game

Run with random initial state and hole position:

```bash
uv run game.py
```

### Specify Initial State

Provide a custom initial state and hole position:

```bash
uv run game.py --state "1,1,1,0,0,1,1,0,1" --hole 7
```

The `--state` argument takes a comma-separated string of 1s and 0s representing the initial state.
The `--hole` argument specifies which position should be treated as the hole (0-based index).

### Replay Mode

Replay a previously saved game:

```bash
uv run game.py --replay gameplays/game_20250204_184018
```

## Game Rules

1. The game state consists of a sequence of 1s and 0s, with one position designated as a "hole"
2. You can perform these actions:
   - Group consecutive identical elements
   - Clamp groups (once you've seen the same group pattern twice)
   - Move clamps into adjacent holes
3. The goal is to minimize the number of non-zero elements (excluding the hole position)

## Gameplay

During interactive play, you can:
- Choose actions by entering numbers 0-4
- View the current state and available moves
- See unlocked clamp patterns
- View the history of moves in layer view
- Save game progress automatically on exit

Games are automatically saved to timestamped directories under `gameplays/` for later replay.


### Solver

The solver is in `dfs_solver_v2.py`.

Run tests on the solver with:

```bash
uv run -m unittest test_dfs_solver.py -v
```
