from typing import List, Set, Optional, Union, Tuple
from game import (
    GroupAction,
    ClampAction,
    MoveAction,
    Group,
    Clamp,
    CompressionGame,
    print_state,
)
from solver import GameSolver, GameState
from copy import deepcopy
import heapq
from collections import defaultdict
from itertools import product
from copy import deepcopy
from game import print_all_layers, print_state
import time
import threading
import argparse
import sys

MAX_DEPTH = 10


# After solving, you can plot the losses:


def find_possible_groups(
    state: List[Union[int, Group, Clamp]], allow_zero: bool = False
) -> List[GroupAction]:
    """Find group actions based on repeating patterns (2-4 elements)

    Args:
        allow_zero: If True, allows patterns containing 0 (hole)
    """
    actions = []
    state_arr = state
    n = len(state_arr)

    non_zero_elements = [(i, e) for i, e in enumerate(state_arr) if e != 0]
    if (
        len(non_zero_elements) == 2
        and abs(non_zero_elements[0][0] - non_zero_elements[1][0])
        == 1  # Adjacent positions
        and isinstance(non_zero_elements[0][1], Clamp)
        and isinstance(non_zero_elements[1][1], Clamp)
        and non_zero_elements[0][1].contents == non_zero_elements[1][1].contents
    ):
        return [GroupAction(non_zero_elements[0][0], 2)]

    # Check all possible group lengths from 2 to 4
    for length in range(2, 5):
        # Check all possible starting positions
        for i in range(n - length + 1):
            # Extract current potential group
            pattern = []
            valid = True
            current_section = state_arr[i : i + length]

            for e in state_arr[i : i + length]:
                if isinstance(e, (Clamp)):
                    # Use group/clamp contents for pattern matching
                    pattern.append(repr(e))
                elif isinstance(e, int):
                    # Check zero allowance
                    if not allow_zero and e == 0:
                        valid = False
                        break
                    pattern.append(e)
                else:
                    valid = False
                    break

            # print(pattern)

            if not valid or len(pattern) != length:
                continue

            pattern = tuple(pattern)

            # Skip if any element is already grouped/clamped or contains 0 (when disabled)
            # if not all(isinstance(e, int) and (allow_zero or e != 0) for e in current_section):
            #     continue

            # pattern = tuple(current_section)

            # Check if this pattern appears again elsewhere
            has_duplicate = False
            for j in range(n - length + 1):
                if j == i:
                    continue  # Skip original position

                compare_pattern = []
                for e in state_arr[j : j + length]:
                    if isinstance(e, (Group, Clamp)):
                        compare_pattern.append(repr(e))
                    elif isinstance(e, int):
                        if not allow_zero and e == 0:
                            compare_pattern = None
                            break
                        compare_pattern.append(e)
                    else:
                        compare_pattern = None
                        break

                if compare_pattern and tuple(compare_pattern) == pattern:
                    has_duplicate = True
                    break

            if has_duplicate:
                actions.append(GroupAction(i, length))

    return actions


def find_possible_clamps(
    state: List[Union[int, Group, Clamp]], unlocked_clamps: Set[tuple]
) -> List[ClampAction]:
    """Find all possible clamp actions in current state"""
    actions = []
    print("Unlocked clamps: ", unlocked_clamps)
    # Remove the global game reference
    # Get all groups in the state
    groups = [(i, g) for i, g in enumerate(state) if isinstance(g, Group)]

    # If only 2 groups remain, allow clamping them regardless of unlocked patterns
    if len(groups) == 2 and groups[0][1].contents == groups[1][1].contents:
        # Add clamp action starting at the first group's position
        return [ClampAction(groups[0][0], 2)]

    # Otherwise, proceed with normal unlocked clamp checking
    for contents in unlocked_clamps:
        size = len(contents) if isinstance(contents, tuple) else 1
        for i in range(len(state) - size + 1):
            elements = state[i : i + size]
            if all(isinstance(e, Group) for e in elements):
                if all(e.contents == contents for e in elements):
                    actions.append(ClampAction(i, size))
    return actions


def find_possible_moves(state: GameState) -> List[MoveAction]:
    """Find all possible move actions in current state"""
    actions = []
    for i in range(len(state)):
        if isinstance(state[i], Clamp):
            if i > 0 and state[i - 1] == 0:
                actions.append(MoveAction(i, -1))
            if i < len(state) - 1 and state[i + 1] == 0:
                actions.append(MoveAction(i, 1))
    return actions


def group_moves_by_position(moves: List[MoveAction]) -> List[Set[MoveAction]]:
    """
    Creates sets of compatible moves from different positions.
    Each set contains at most one move from each position.

    Args:
        moves: List of MoveAction objects to analyze

    Returns:
        List of sets, where each set contains compatible MoveAction objects
    """
    # First group moves by position
    position_groups = defaultdict(list)
    for move in moves:
        position_groups[move.position].append(move)

    # Generate all possible combinations
    result = []

    # Get all possible combinations of moves from different positions
    for combination in product(*position_groups.values()):
        result.append(set(combination))

    return result


class DFSSolver(GameSolver):
    def __init__(
        self,
        initial_state: List[int],
        hole_idx: Optional[int] = None,
        preserve_moves_on_change: bool = True,
        max_calls: Optional[int] = None,
    ):
        super().__init__(initial_state, hole_idx)
        self.best_solution = None
        self.best_loss = float("inf")
        self.visited_states = set()
        self.original_initial_state = initial_state.copy()
        self.total_calls = 0
        self.max_calls = max_calls
        self.preserve_moves_on_change = preserve_moves_on_change
        # Add loss tracking
        self.loss_history = []  # Will store tuples of (total_loss, current_loss)

    def find_compatible_groups(
        self, actions: List[GroupAction]
    ) -> List[Set[GroupAction]]:
        """Find sets of non-conflicting group actions that can be applied together"""
        result = []

        for base_action in actions:
            compatible = {base_action}

            for other_action in actions:
                if other_action == base_action:
                    continue

                conflicts = False
                for existing_action in compatible:
                    if existing_action.conflicts_with(other_action):
                        conflicts = True
                        break

                if not conflicts:
                    compatible.add(other_action)

            if compatible not in result:
                result.append(compatible)

        return result

    def find_compatible_clamps(
        self, actions: List[ClampAction]
    ) -> List[Set[ClampAction]]:
        """Find sets of non-conflicting clamp actions that can be applied together"""
        result = []

        for base_action in actions:
            compatible = {base_action}
            for other_action in actions:
                if other_action == base_action:
                    continue

                conflicts = False
                for existing_action in compatible:
                    if existing_action.conflicts_with(other_action):
                        conflicts = True
                        break

                if not conflicts:
                    compatible.add(other_action)

            if compatible not in result:
                result.append(compatible)

        return result

    def solve_dfs(
        self,
        game: CompressionGame,
        current_depth: int,
        branch_idx: int,
        max_depth: int,
        lookahead: int,
        visited_states: Set[Tuple[int, ...]],
        desired_loss: int = 0,
    ) -> Optional[GameState]:
        self.total_calls += 1

        # Check if we've exceeded our call budget
        if self.max_calls and self.total_calls >= self.max_calls:
            print(f"\nReached maximum call budget of {self.max_calls}")
            return None

        # Record losses
        self.loss_history.append((game.total_loss, game.get_loss()))

        if self.total_calls % 10 == 0:  # Print progress every 10 calls
            print(f"\nRecursive calls so far: {self.total_calls}")

        time.sleep(0.1)  # Add small delay to slow down recursion

        # Add check for initial state change
        current_global_state = CompressionGame.get_global_initial_state()
        if current_global_state != self.original_initial_state:
            print("\n=== Initial State Change Detected! ===")
            # Add a marker in the loss history
            self.loss_history.append(
                (
                    self.total_calls,
                    game.total_loss,
                    game.get_loss(),
                    current_global_state,
                )
            )
            # self.original_initial_state = deepcopy(current_global_state)

            print(f"Original: {self.original_initial_state}")
            print(f"Changed to: {current_global_state}")
            print(f"Current depth: {current_depth}")
            print(f"Current moves: {game.moves}")
            print(f"Current state: {game.state}")
            print(f"Current loss: {game.total_loss}")
            print(f"Total calls: {self.total_calls}")

            print("\n=== Current Progress Before Reset ===")
            print("Visited states:", self.visited_states)
            print("Current game state:", game.state)
            print("Current layers:")
            print_all_layers(game.layers[1:], game.bucket_idx)

            # Create new game with changed initial state
            new_game = CompressionGame(current_global_state, game.bucket_idx)

            if self.preserve_moves_on_change:
                # Try to replay the moves that worked before
                valid_moves = []
                print("\n=== Replaying Valid Moves with New Initial State ===")
                for move in game.moves:
                    try:
                        new_game.step(move)
                        valid_moves.append(move)
                        print(f"Successfully replayed: {move}")
                        print(f"New state: {new_game.state}")
                    except ValueError as e:
                        print(f"Move {move} is no longer valid with new initial state")
                        break
            else:
                print("\n=== Starting Fresh with New Initial State ===")

            # Update solver's reference to new initial state
            self.original_initial_state = current_global_state.copy()

            # Clear visited states since we're starting fresh
            visited_states.clear()

            print("\n=== Continuing Search from Last Valid State ===")
            return self.solve_dfs(
                new_game,
                current_depth,
                branch_idx,
                max_depth,
                lookahead,
                visited_states,
                0,
            )

        if game.get_loss() == desired_loss:
            print("Found solution:", game.state)
            return game

        state_tuple = tuple(game.state)
        if state_tuple in visited_states:
            print(f"State {state_tuple} already visited")
            return None

        visited_states.add(state_tuple)

        print(f"\nDepth {current_depth}.{branch_idx} - Current state: {game.state}")
        print(f"Current loss: {game.total_loss}")
        print(f"Current moves: {game.moves}")

        # 1. Try all possible group actions first
        print("===Considering group actions====")
        state = game.state
        group_moves = find_possible_groups(state)
        print(f"\tFound {len(group_moves)} possible group moves")
        for group_move in group_moves:
            print(f"\t\tGroup move: {group_move}")

        # game_freeze = deepcopy(game)
        group_sets = self.find_compatible_groups(group_moves)
        print(f"\tFound {len(group_sets)} possible group sets")
        for group_set in group_sets:
            print(f"\t\tGroup set: {group_set}")

        if len(group_sets) > 0:
            print("===Applying group actions====")

            for i, group_set in enumerate(group_sets):
                game_freeze = deepcopy(game)
                print(f"\t\tApplying group set: {group_set}")
                for group_move in group_set:
                    game_freeze.step(group_move)
                    print(f"\t\t\tApplied group move: {group_move}")
                    print(f"\t\t\tNew state: {game_freeze.state}")

                # Recursively solve the game
                solution = self.solve_dfs(
                    game_freeze,
                    current_depth + 1,
                    i,
                    max_depth,
                    lookahead,
                    visited_states,
                    desired_loss,
                )
                if solution:
                    return solution

        print("===Considering clamp actions====")

        clamp_moves = find_possible_clamps(state, game.unlocked_clamps)
        clamp_sets = self.find_compatible_clamps(clamp_moves)
        print(f"\tFound {len(clamp_moves)} possible clamp moves")
        if len(clamp_sets) > 0 and len(clamp_sets[0]) > 0:
            print("===Applying clamp actions====")
            for i, clamp_set in enumerate(clamp_sets):
                print(f"\t\tClamp set: {clamp_set}")
                game_freeze = deepcopy(game)
                for clamp_move in clamp_set:
                    print(f"\t\t\tApplying clamp move: {clamp_move}")
                    game_freeze.step(clamp_move)
                    print(f"\t\t\tNew state: {game_freeze.state}")

                    # Recursively solve the game
                solution = self.solve_dfs(
                    game_freeze,
                    current_depth + 1,
                    i,
                    max_depth,
                    lookahead,
                    visited_states,
                    desired_loss,
                )
                if solution:
                    return solution

        print("===Considering move actions====")
        moves = find_possible_moves(state)
        move_sets = group_moves_by_position(moves)
        print(f"\tFound {len(move_sets)} possible move moves")
        # if len(move_sets) > 0:
        #     print("===Applying move actions====")
        #     for i, move_set in enumerate(move_sets):
        #         print(f"\t\tMove set: {move_set}")
        #         game_freeze = deepcopy(game)
        #         for move in move_set:
        #           print(f"\t\t\tApplying move: {move} \n\t\t\t to game: {game_freeze.state}")
        #           game_freeze.step(move)
        #           print(f"\t\t\tNew state: {game_freeze.state}")

        #         solution = self.solve_dfs(game_freeze, current_depth+1, i, max_depth, 2)
        #         if solution:
        #             return solution
        print("Starting with state: ", game.state)
        for move in moves:
            print(f"===Applying move: {move}====")
            game_freeze = deepcopy(game)
            game_freeze.step(move)
            solution = self.solve_dfs(
                game_freeze,
                current_depth + 1,
                0,
                max_depth,
                2,
                visited_states,
                desired_loss,
            )
            if solution:
                return solution


def change_initial_state(delay: float, new_state: List[int]):
    def _change():
        CompressionGame.set_global_initial_state(new_state)
        print(f"\nState changed after {delay}s to: {new_state}")

    return _change


def run_solver(
    initial_states_and_times: List[Tuple[List[int], float]],
    hole_idx: int,
    max_calls: int = 500,
    desired_loss=0,
):
    """
    Run solver with scheduled state changes.

    Args:
        initial_states_and_times: List of (state_array, change_time) tuples
        hole_idx: Index of the hole in the initial state
        max_calls: Maximum number of solver calls allowed
    """
    # Sort by time to ensure changes happen in order
    state_changes = sorted(initial_states_and_times, key=lambda x: x[1])

    # Initialize with first state
    initial_state = state_changes[0][0]
    game = CompressionGame(initial_state, hole_idx)

    # Set up state change timers
    timers = []
    for state, delay in state_changes[1:]:  # Skip first state as it's the initial one
        timer = threading.Timer(delay, change_initial_state(delay, state))
        timers.append(timer)

    # Create and configure solver
    solver = DFSSolver(
        game.state, hole_idx, preserve_moves_on_change=True, max_calls=max_calls
    )

    # Start all timers
    for timer in timers:
        timer.start()

    # Start solving
    solution = solver.solve_dfs(
        game,
        0,
        0,
        max_depth=20,
        lookahead=3,
        visited_states=set(),
        desired_loss=desired_loss,
    )

    print("\n=== Final Results ===")
    print("Visited states: ", solver.visited_states)
    print("Final moves: ", solution.moves if solution else [])
    print("Total calls: ", solver.total_calls)
    print(f"Solution: {solution}")
    if solution:
        print("Layers:", solution.layers)
        print_all_layers(solution.layers[1:], hole_idx)

    return solver, solution


if __name__ == "__main__":
    # Example usage with state changes
    if len(sys.argv) > 1:
        test_case = sys.argv[1]
    else:
        print("No test_case provided")
    try:
        if test_case == "1-easy":
            state_changes = [
                ([0, 1, 1, 0, 1, 1, 0, 0], 0),  # Initial state
            ]
            hole_idx = 3
            desired_loss = 0
        elif test_case == "1-medium":
            state_changes = [
                ([1, 1, 1, 0, 1, 1, 0, 1], 0),  # Initial state
            ]
            hole_idx = 3
            desired_loss = 0
        elif test_case == "1-hard":
            state_changes = [
                (2 * [0, 1, 1, 0, 1, 1, 0], 0),  # Initial state
            ]
            hole_idx = 3
            desired_loss = 0
        elif test_case == "1-unsolvable":
            state_changes = [
                (
                    [0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1],
                    0,
                ),  # Initial state. Note changingjust one digit here will make this state easy. which one will it be?
            ]
            hole_idx = 3
            desired_loss = 2  # this will not solve within 500 state calls and is an example of a state with likely no desired_loss=0 solution.
        elif test_case == "3-easy":
            state_changes = [
                ([1, 1, 1, 0, 1, 1, 0, 1], 0),  # Initial state
                ([1, 1, 1, 0, 1, 1, 1, 0], 0.8),  # First change after 0.8 seconds
                ([1, 1, 1, 0, 1, 1, 1, 1], 2.5),  # Second change after 2.5 seconds
            ]

            hole_idx = 3
            desired_loss = 0
        else:
            print(
                f"could not find test case of name {test_case}. Run `cat dfs_solver.py` to see available test cases or add your own."
            )
            raise ValueError(
                f"could not find test case of name {test_case}. Run `cat dfs_solver.py` to see available test cases or add your own."
            )

        solver, solution = run_solver(
            initial_states_and_times=state_changes,
            hole_idx=hole_idx,
            max_calls=500,
            desired_loss=desired_loss,
        )
        # plot_solver_losses(solver, first_state=state_changes[0][0])
        from plotter import plot_solver_losses_ascii

        plot_solver_losses_ascii(
            solver, first_state=state_changes[0][0], width=250, height=35
        )
    except Exception as e:
        raise Exception(str(e))
