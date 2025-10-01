from typing import List, Union, Tuple, Optional, Set
from game import CompressionGame, GroupAction, ClampAction, MoveAction, Group, Clamp, print_state
import copy
import argparse

class GameSolver:
    def __init__(self, initial_state: List[int], hole_idx: Optional[int] = None):
        self.game = CompressionGame(initial_state, hole_idx)
        self.best_solution = None
        self.best_loss = float('inf')
        self.best_moves = []
        
    def solve(self) -> List[Union[GroupAction, ClampAction, MoveAction]]:
        """Main entry point to find the optimal solution"""
        state = self.game.reset()
        self._solve_recursive(state, [], 0)
        return self.best_moves
        
    def _solve_recursive(self, state: List[Union[int, Group, Clamp]], 
                        moves: List[Union[GroupAction, ClampAction, MoveAction]], 
                        total_loss: int):
        """Recursive helper to explore all possible moves"""
        # Base case: if we've found a better solution, update it
        current_loss = self.game.get_loss()
        if current_loss < self.best_loss:
            self.best_loss = current_loss
            self.best_moves = moves.copy()
            
        # If we've reached a state with no valid moves, return
        if current_loss == 0:
            return
            
        # Try all possible group actions first
        valid_actions = self.game.get_valid_actions()
        group_actions = [a for a in valid_actions if isinstance(a, GroupAction)]
        
        for action in group_actions:
            # Make a copy of the game state
            game_copy = copy.deepcopy(self.game)
            try:
                new_state, reward, done, info = game_copy.step(action)
                self.game = game_copy
                self._solve_recursive(new_state, moves + [action], total_loss + info['loss'])
            except ValueError:
                continue
                
        # Then try all possible clamp actions
        clamp_actions = [a for a in valid_actions if isinstance(a, ClampAction)]
        
        for action in clamp_actions:
            game_copy = copy.deepcopy(self.game)
            try:
                new_state, reward, done, info = game_copy.step(action)
                self.game = game_copy
                self._solve_recursive(new_state, moves + [action], total_loss + info['loss'])
            except ValueError:
                continue
                
        # Finally try all possible move actions
        move_actions = [a for a in valid_actions if isinstance(a, MoveAction)]
        
        for action in move_actions:
            game_copy = copy.deepcopy(self.game)
            try:
                new_state, reward, done, info = game_copy.step(action)
                self.game = game_copy
                self._solve_recursive(new_state, moves + [action], total_loss + info['loss'])
            except ValueError:
                continue

def solve_game(initial_state: List[int], hole_idx: Optional[int] = None) -> Tuple[List[Union[GroupAction, ClampAction, MoveAction]], int]:
    """Helper function to solve a game and return the solution moves and final loss"""
    solver = GameSolver(initial_state, hole_idx)
    best_moves = solver.solve()
    return best_moves, solver.best_loss

def dfs_solver(game, depth, max_depth, cumulative_cost, visited=None):
    """
    Recursively search for an action sequence to minimize cumulative loss.
    The order of actions is: GroupAction, then ClampAction, then MoveAction.
    Returns a tuple (best_plan, best_total_cost) where best_plan is a list of actions and best_total_cost is the cumulative cost.
    """
    # Initialize visited set if None
    if visited is None:
        visited = set()
        
    # Create a hashable representation of the current state
    current_state = tuple(game.state)
    if current_state in visited:
        return ([], float('inf'))  # Return infinite cost for visited states
        
    # Add current state to visited set
    visited.add(current_state)
    
    # Terminal condition: if the game is solved, return the cumulative cost
    print("Depth: ", depth)
    if game.get_loss() == 0:
        return ([], cumulative_cost)
    
    actions = game.get_valid_actions()
    print("Possible actions: ", actions)
    # If at max depth or no further actions, return current cumulative cost as terminal value
    if depth == max_depth or not actions:
        return ([], cumulative_cost)
    
    # Order actions: groups first, then clamps, then moves
    group_actions = [a for a in actions if isinstance(a, GroupAction)]
    clamp_actions = [a for a in actions if isinstance(a, ClampAction)]
    move_actions  = [a for a in actions if isinstance(a, MoveAction)]
    ordered_actions = group_actions + clamp_actions + move_actions

    best_plan = []
    best_total_cost = float('inf')

    for action in ordered_actions:
        # Clone the game state to simulate the action
        cloned_game = copy.deepcopy(game)
        try:
            state, reward, done, info = cloned_game.step(action)
        except Exception as err:
            # Skip invalid actions
            continue
        immediate_cost = info.get('loss', 0)
        new_cumulative_cost = cumulative_cost + immediate_cost
        
        # Pass visited set to recursive call
        subplan, subcost = dfs_solver(cloned_game, depth + 1, max_depth, new_cumulative_cost, visited.copy())
        total_cost = subcost
        
        if total_cost < best_total_cost:
            best_total_cost = total_cost
            best_plan = [action] + subplan

    return (best_plan, best_total_cost)


def solve_brute_force(initial_state, hole_idx=None, max_depth=3):
    """
    Create a CompressionGame with the given initial state and hole index,
    then solve using brute-force DFS up to max_depth moves.
    Returns the best plan (sequence of actions) and the cumulative cost.
    """
    game = CompressionGame(initial_state, hole_idx)
    game.reset()
    best_plan, best_cost = dfs_solver(game, 0, max_depth, 0)
    return best_plan, best_cost


def simulate_plan(game, plan):
    """
    Execute a given plan (list of actions) on the game and print the state and cumulative cost after each move.
    """
    cumulative_cost = 0
    for i, action in enumerate(plan):
        state, reward, done, info = game.step(action)
        immediate_cost = info.get('loss', 0)
        cumulative_cost += immediate_cost
        print(f"\nAfter move {i+1}: {action}")
        print_state(state, info.get('loss'), hole_idx=game.hole_idx)
        print(f"Cumulative cost: {cumulative_cost}")
        if done:
            print("Game finished!")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brute Force Solver for Compression Game")
    parser.add_argument("--state", type=str, help="Initial state as comma separated values, e.g. '1,1,1,0,0,1,1,0,1'")
    parser.add_argument("--hole", type=int, help="Hole index (optional)")
    parser.add_argument("--depth", type=int, default=12, help="Max lookahead depth for solving")
    
    args = parser.parse_args()

    # Parse initial state
    if args.state:
        initial_state = [int(x.strip()) for x in args.state.split(",")]
    else:
        # Default initial state if none provided
        initial_state = [1, 1, 1, 0, 1, 1, 0, 1]

    if args.hole:
        hole_idx = args.hole
    else:
        hole_idx = 3

    print("Initial state:", initial_state)
    print("Hole index:", hole_idx)
    print("Max lookahead depth:", args.depth)

    best_plan, best_cost = solve_brute_force(initial_state, hole_idx, max_depth=args.depth)

    if best_plan:
        print("\nBest plan found with cumulative cost:", best_cost)
        for i, action in enumerate(best_plan):
            print(f"Move {i+1}: {action}")
        
        print("\nSimulating best plan:")
        game = CompressionGame(initial_state, hole_idx)
        game.reset()
        simulate_plan(game, best_plan)
    else:
        print("No valid moves found or game already solved.") 