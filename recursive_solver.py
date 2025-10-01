from typing import Optional, Set, List
from game import GroupAction, MoveAction, print_state
from solver import GameState, GameSolver
from collections import defaultdict
from itertools import product
from copy import deepcopy

class RecursiveSolver(GameSolver):
    def find_compatible_groups(self, actions: List[GroupAction]) -> List[Set[GroupAction]]:
        """
        Takes a list of GroupAction objects and returns a list of sets, where each set
        contains GroupAction objects that don't conflict with each other.
        
        Args:
            actions: List of GroupAction objects to analyze
            
        Returns:
            List of sets, where each set contains compatible GroupAction objects
        """
        result = []
        
        # For each action, find all compatible actions
        for base_action in actions:
            compatible = {base_action}  # Start with the base action
            
            # Add only actions that don't conflict with ANY action already in the set
            for other_action in actions:
                if other_action == base_action:
                    continue
                    
                # Check if other_action conflicts with any action in our compatible set
                conflicts = False
                for existing_action in compatible:
                    if existing_action.conflicts_with(other_action):
                        conflicts = True
                        break
                        
                if not conflicts:
                    compatible.add(other_action)
                    
            result.append(compatible)
        
        # Remove duplicate sets
        unique_result = []
        for group in result:
            if group not in unique_result:
                unique_result.append(group)
            
        return unique_result

    def recursive_solver(self, state: GameState, depth: int = 0) -> Optional[GameState]:
        """Recursively search for solution using group->clamp->move priority"""
        # if visited is None:
        #     visited = set()
        
        # state_hash = hash(state)
        # if state_hash in visited:
        #     return None
        # visited.add(state_hash)
        print(f"================Depth {depth}=====================")
        if self.get_loss(state.state) == 0:
            return state  # Found solution
        # print total loss
        print_state(state.state, self.get_loss(state.state), hole_idx=state.hole_idx)
        print(f"Total loss till now: {state.total_loss} at depth {depth}")
        # Try group actions first
        possible_groups = self.find_possible_groups(state)
        print(f"Found {len(possible_groups)} possible group actions at depth {depth}")
        
        # Find all non-conflicting action sets
        action_sets = self.find_compatible_groups(possible_groups)
        print(f"Found {len(action_sets)} non-conflicting action sets at depth {depth}")
        print(action_sets)
        current_state = state
        if depth > 8:
            exit()
        for i, action_set in enumerate(action_sets):
            # Apply all actions in the set (non-conflicting so order doesn't matter)
            new_state = current_state
            for action in action_set:
                print(f"Applying group action: pos={action.position}, size={action.size}")
                new_state = self.apply_action(new_state, action)
            
            print(f"State after group set {i}: {[str(x) for x in new_state.state]}")
            solution_state = self.recursive_solver(new_state, depth + 1)
            print(f"Solution state: {[str(x) for x in solution_state.state]}")
            if solution := self.recursive_solver(new_state, depth + 1):
                return solution
        # cancel if depth > 10

        
        # Then clamp actions
        possible_clamps = self.find_possible_clamps(state)
        print(f"Found {len(possible_clamps)} possible clamp actions at depth {depth}")
        new_state = state
        if len(possible_clamps) > 0:    
            for i, action in enumerate(possible_clamps):
                new_state = self.apply_action(new_state, action)
                print(f"State after clamp action {i}: {[str(x) for x in new_state.state]}")
        
            if solution := self.recursive_solver(new_state, depth + 1):
                return solution
        
        # Finally move actions
        possible_moves = self.find_possible_moves(state)
        move_impacts = []
        for move in possible_moves:
            temp_state = self.apply_action(deepcopy(state), move)
            impact =self.get_loss(state.state) - self.get_loss(temp_state.state) 
            move_impacts.append((move, impact))
        
        # Sort by impact (highest first)
        print("Move impacts: ", move_impacts)
        possible_moves = [move for move, impact in sorted(move_impacts, key=lambda x: x[1], reverse=True)]
        possible_move_sets = self.group_moves_by_position(possible_moves)
        print("Possible move sets: ", possible_move_sets)
        print(f"Found {len(possible_move_sets)} possible move sets at depth {depth}")
        for move_set in possible_move_sets:
            print(move_set)
            for move in move_set:
                new_state = self.apply_action(new_state, move)
                print(f"State after move action: {[str(x) for x in new_state.state]}")

            if solution := self.recursive_solver(new_state, depth + 1):
                return solution
        
        return None

    def group_moves_by_position(self, moves: List[MoveAction]) -> List[Set[MoveAction]]:
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

if __name__ == "__main__":
    # Test case setup
    # {
    #         'name': 'Simple case',
    #         'initial_state': [1, 1, 0, 1, 1],
    #         'hole_idx': 2
    #     }
    # initial_state = [1, 1, 0, 1, 1]
    # hole_idx = 2
    initial_state = [1, 1, 1, 0, 0, 1, 1, 0, 1]
    hole_idx = 4
    solver = RecursiveSolver(initial_state, hole_idx)
    
    initial_game_state = GameState(
        state=initial_state,
        unlocked_clamps=set(),
        groups_seen={},
        total_loss=0,
        moves=[],
        hole_idx=hole_idx
    )
    
    print("\n=== Starting Recursive Solver ===")
    solution = solver.recursive_solver(initial_game_state)
    
    if solution:
        print("\n=== Solution Found ===")
        solver.print_solution(solution)
    else:
        print("\nNo solution found")