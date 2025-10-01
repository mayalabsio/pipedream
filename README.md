# Compression Game

Pipedream is an extremely hackable text-based compression game where the core goal is write an automated solver script that can solve arbitrary levels of the game in the fewest number of steps.

interactive game where you compress sequences by grouping and clamping elements.

## Game Rules : 

The initial state of the game is a 'leaky roof' - a single array that looks like : ["1,1,1,0,0,1,1,0,1"]. The 1s are the holes, each of which is dripping water down to the ground, one drop for every step of the game. In this case there are six 1s, so six holes strewn around the roof, so at this state, 6 drops of water are getting lost at every step of the game. 

There's a bucket on the floor that can be used collect this water and stem this loss. If we had only 1 (hole) at position 7 in the roof state array, and the bucket was also at position 7, then there would be no water loss and the game would be 'solved'. But for the non-trivial case, the way to do this is to reduce N holes to 1 hole as quickly as possible - by creating a (inverted) pyramid of pipes from the roof to the bucket on the floor. Similar groupings of narrow pipes can be combined into a single (higher order) pipe that can be moved around to create even higher order pipes. In each step of the game, you can either move a pipe left or right or group pipes in similar sequences together  'grouping pattern' reduces the 'rate of loss' by however many pipes it combines into a higher pipe. (for example, for initial state [1,1,1,0,0,1,1,0,1] it would make sense to make the grouping `[1, (1,1), 0, 0, (1, 1), 0,1]`. This unlocks a higher order pipe of type `(1,1)` that can reduce 2 hole leak to a 1 hole leak, reducing 'rate of loss' from 6 drops/step to 4 drops/step.

The goal of the game is to bring down the 'rate of loss' to 0 - by basically constructing a single higher-order pipe that is located right over the hole location in the fewer number of steps. The feedback (to the player, scripted or otherwise), is the 'rate of loss' at each step. Here's an example of this 'gameplay' where you see how each step gradually stems the rate of loss :

```
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       0       |       1       |       2       |       3       |       4       |       5       |       6       |       7       |       8       | Idx
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       1       |       0       |       1       |       1       |       0       |       1       |       0       |       1       |       1       | Roof
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       1       |       0       |       1       |       1       |       0       |       1       |       0       |    g(1, 1)    |    g(1, 1)    | L0 (loss=5)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       1       |       0       |    g(1, 1)    |    g(1, 1)    |       0       |       1       |       0       |    g(1, 1)    |    g(1, 1)    | L1 (loss=5)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       1       |       0       |    g(1, 1)    |    g(1, 1)    |       0       |       1       |       0       |    c(1, 1)    |       0       | L2 (loss=4)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       1       |       0       |    c(1, 1)    |       0       |       0       |       1       |       0       |    c(1, 1)    |       0       | L3 (loss=4)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       1       |    c(1, 1)    |       0       |       0       |       0       |       1       |       0       |    c(1, 1)    |       0       | L4 (loss=4)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       1       |    c(1, 1)    |       0       |       0       |       0       |       1       |    c(1, 1)    |       0       |       0       | L5 (loss=4)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
| g(1, c(1, 1)) | g(1, c(1, 1)) |       0       |       0       |       0       |       1       |    c(1, 1)    |       0       |       0       | L6 (loss=4)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
| g(1, c(1, 1)) | g(1, c(1, 1)) |       0       |       0       |       0       | g(1, c(1, 1)) | g(1, c(1, 1)) |       0       |       0       | L7 (loss=4)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
| c(1, c(1, 1)) |       0       |       0       |       0       |       0       | g(1, c(1, 1)) | g(1, c(1, 1)) |       0       |       0       | L8 (loss=3)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
| c(1, c(1, 1)) |       0       |       0       |       0       |       0       | c(1, c(1, 1)) |       0       |       0       |       0       | L9 (loss=2)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       0       | c(1, c(1, 1)) |       0       |       0       |       0       | c(1, c(1, 1)) |       0       |       0       |       0       | L10 (loss=2)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       0       |       0       | c(1, c(1, 1)) |       0       |       0       | c(1, c(1, 1)) |       0       |       0       |       0       | L11 (loss=2)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|       0       |       0       |       0       | c(1, c(1, 1)) |       0       | c(1, c(1, 1)) |       0       |       0       |       0       | L12 (loss=1)
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
|               |               |               |       B       |               |               |               |               |               | Floor
+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+---------------+
```
```
```

You can initialize the game state like this :

```bash
```
uv run game.py --state "1,1,1,0,0,1,1,0,1" --bucket 3
```
```

But the way to this is to create a (inverted) pyramid of pipes from the roof to the bucket on the floor.  

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
