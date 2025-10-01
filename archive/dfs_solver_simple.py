import sys
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

sys.setrecursionlimit(10_000)


MAX_DEPTH = 10


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
    if (
        len(groups) == 2
        and groups[0][1].contents == groups[1][1].contents
        and all(not isinstance(c, int) and not isinstance(c, Clamp) for c in state)
    ):
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
    def __init__(self, initial_state: List[int], hole_idx: Optional[int] = None):
        super().__init__(initial_state, hole_idx)
        self.best_solution = None
        self.best_loss = float("inf")
        self.visited_states = set()

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
        # if state.total_loss == 0:
        #     return state
        # if depth > MAX_DEPTH:
        #     return None

        if game.get_loss() == desired_loss:
            print("Found solution:", game.state)
            return game

        state_tuple = tuple(game.state)
        if state_tuple in visited_states:
            print(f"State {state_tuple} already visited")
            return None

        visited_states.add(state_tuple)

        # if current_depth > 8:
        #     return None

        print(f"===============Depth: {current_depth}.{branch_idx}===================")
        print(f"Current state: {game.state}")
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


def solve_game(
    initial_state: List[int],
    hole_idx: Optional[int] = None,
    max_depth: int = 20,
    lookahead: int = 3,
) -> Tuple[List[Union[GroupAction, ClampAction, MoveAction]], int]:
    """Helper function to solve a game and return the solution moves and final loss"""
    solver = DFSSolver(initial_state, hole_idx)
    initial_game_state = GameState(
        state=initial_state.copy(),
        unlocked_clamps=set(),
        groups_seen={},
        total_loss=0,
        moves=[],
        hole_idx=hole_idx,
    )

    solution = solver.solve_dfs(
        initial_game_state, 0, max_depth=max_depth, lookahead=lookahead
    )
    return solution.moves if solution else [], solver.best_loss


if __name__ == "__main__":
    # Test case
    initial_state = [1, 0, 1, 1, 0, 1, 0, 1, 1]
    # initial_state = [1, 1, 1, 0, 0, 1, 1, 0,0, 0, 1,1,0,1,0,1,1,0,1,1, 0,1,1,1,0]
    # # initial_state = [Group((1, 1)), Group((1, 1)), 1, 0, Group((1, 1)), Group((1, 1)), 0, 1]
    # hole_idx = 10
    # desired_loss = 4

    # initial_state = [1,1,0,0,0,1,1,0,0,0,1,1,1,0,0,1,1,1]
    hole_idx = 3
    desired_loss = 1

    print("Initial state:", initial_state)
    print("Hole index:", hole_idx)

    game = CompressionGame(initial_state, hole_idx)

    print("===Applying group action====")
    # final_state = [Group((1, 1)), Group((1, 1)), 1, 0, Group((1, 1)), Group((1, 1)), 0, 1]
    # state = game.step(GroupAction(0, 2))
    # state = game.step(GroupAction(4, 2))
    # state = game.step(ClampAction(0, 2))
    # state = game.step(ClampAction(4, 2))

    solver = DFSSolver(game.state, hole_idx)

    solution = solver.solve_dfs(
        game,
        0,
        0,
        max_depth=20,
        lookahead=3,
        visited_states=set(),
        desired_loss=desired_loss,
    )
    print("Visited states: ", solver.visited_states)
    print(f"Solution: {solution}")
    print("Layers:", solution.layers)
    print_all_layers(solution.layers[1:], hole_idx)
