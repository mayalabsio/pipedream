from typing import List, Set, Optional, Union, Tuple
from game import GroupAction, ClampAction, MoveAction, Group, Clamp, CompressionGame, print_state
from solver import GameSolver, GameState
from copy import deepcopy
import heapq

class DFSSolver(GameSolver):
    def __init__(self, initial_state: List[int], hole_idx: Optional[int] = None):
        super().__init__(initial_state, hole_idx)
        self.best_solution = None
        self.best_loss = float('inf')
        self.visited_states = set()
        
    def find_compatible_groups(self, actions: List[GroupAction]) -> List[Set[GroupAction]]:
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
        
    def evaluate_state(self, state: GameState, depth: int, max_depth: int) -> float:
        """Evaluate a state by running DFS for N steps and returning best achievable loss"""
        if depth >= max_depth:
            return self.get_loss(state.state)
            
        best_loss = float('inf')
        
        # Try groups using group sets
        groups = self.find_possible_groups(state)
        group_sets = self.find_compatible_groups(groups)
        #log group sets
        print(f"Group sets at depth {depth}: {group_sets}")
        for group_set in group_sets:
            try:
                new_state = deepcopy(state)
                for group in group_set:
                    new_state = self.apply_action(new_state, group)
                loss = self.evaluate_state(new_state, depth + 1, max_depth)
                best_loss = min(best_loss, loss)
            except ValueError:
                continue
                
        # Try clamps
        clamps = self.find_possible_clamps(state)
        for clamp in clamps:
            try:
                new_state = self.apply_action(deepcopy(state), clamp)
                loss = self.evaluate_state(new_state, depth + 1, max_depth)
                best_loss = min(best_loss, loss)
            except ValueError:
                continue
                
        # Try moves
        moves = self.find_possible_moves(state)
        for move in moves:
            try:
                new_state = self.apply_action(deepcopy(state), move)
                loss = self.evaluate_state(new_state, depth + 1, max_depth)
                best_loss = min(best_loss, loss)
            except ValueError:
                continue
                
        return best_loss if best_loss != float('inf') else self.get_loss(state.state)
        
    def solve_dfs(self, state: GameState, depth: int = 0, max_depth: int = 20, lookahead: int = 3) -> Optional[GameState]:
        """Main DFS solver with N-step lookahead for action selection"""
        # Check if state already visited
        state_hash = hash(state)
        if state_hash in self.visited_states:
            return None
        self.visited_states.add(state_hash)
        print(f"===============Depth: {depth}===================")
        current_loss = self.get_loss(state.state)
        
        # Update best solution if we found a better one
        if current_loss < self.best_loss:
            self.best_loss = current_loss
            self.best_solution = state
            print(f"\nNew best solution found with loss {current_loss}:")
            print_state(state.state, current_loss, hole_idx=self.hole_idx)
            
        # Base cases
        if current_loss == 0:  # Perfect solution
            return state
        if depth >= max_depth:  # Max depth reached
            return None
            
        # 1. Try group actions first
        possible_groups = self.find_possible_groups(state)
        #log possible groups
        print(f"Possible groups at depth {depth}: {possible_groups}")
        group_sets = self.find_compatible_groups(possible_groups)
        #log group sets
        print(f"Group sets at depth {depth}: {group_sets}")
        
        # Evaluate each group set with lookahead
        group_evaluations = []
        for group_set in group_sets:
            temp_state = deepcopy(state)
            try:
                for group_action in group_set:
                    temp_state = self.apply_action(temp_state, group_action)
                    #log temp state
                    print(f"Temp state after applying group action {group_action}: {temp_state.state}")
                eval_score = self.evaluate_state(temp_state, depth+1, lookahead)
                #log eval score
                print(f"Eval score for group set {group_set}: {eval_score}")
                group_evaluations.append((eval_score, group_set))
            except ValueError:
                continue
                
        # Try group sets in order of their evaluation
        for eval_score, group_set in sorted(group_evaluations, key=lambda x: x[0]):
            new_state = deepcopy(state)
            try:
                for group in group_set:
                    new_state = self.apply_action(new_state, group)
                if solution := self.solve_dfs(new_state, depth + 1, max_depth, lookahead):
                    return solution
            except ValueError:
                continue

        # exit if depth is > 2
        if depth > 2:
            return None
                
        # 2. Try clamp actions
        possible_clamps = self.find_possible_clamps(state)
        #log possible clamps
        print(f"Possible clamps at depth {depth}: {possible_clamps}")
        clamp_evaluations = []
        
        for clamp in possible_clamps:
            temp_state = deepcopy(state)
            try:
                temp_state = self.apply_action(temp_state, clamp)
                # log temp state
                print(f"Temp state after applying clamp action {clamp}: {temp_state.state}")
                eval_score = self.evaluate_state(temp_state, 0, lookahead)

                clamp_evaluations.append((eval_score, clamp))
                # log eval score
                print(f"Eval score for clamp {clamp}: {eval_score}")
            except ValueError:
                continue
                
        # # Try clamps in order of their evaluation
        # for eval_score, clamp in sorted(clamp_evaluations, key=lambda x: x[0]):
        #     try:
        #         new_state = self.apply_action(deepcopy(state), clamp)
        #         if solution := self.solve_dfs(new_state, depth + 1, max_depth, lookahead):
        #             return solution
        #     except ValueError:
        #         continue
                
        # # 3. Try move actions
        # possible_moves = self.find_possible_moves(state)
        # move_evaluations = []
        
        # for move in possible_moves:
        #     temp_state = deepcopy(state)
        #     try:
        #         temp_state = self.apply_action(temp_state, move)
        #         eval_score = self.evaluate_state(temp_state, 0, lookahead)
        #         move_evaluations.append((eval_score, move))
        #     except ValueError:
        #         continue
                
        # Try moves in order of their evaluation
        # for eval_score, move in sorted(move_evaluations, key=lambda x: x[0]):
        #     try:
        #         new_state = self.apply_action(deepcopy(state), move)
        #         if solution := self.solve_dfs(new_state, depth + 1, max_depth, lookahead):
        #             return solution
        #     except ValueError:
        #         continue
                
        return None

def solve_game(initial_state: List[int], hole_idx: Optional[int] = None, max_depth: int = 20, lookahead: int = 3) -> Tuple[List[Union[GroupAction, ClampAction, MoveAction]], int]:
    """Helper function to solve a game and return the solution moves and final loss"""
    solver = DFSSolver(initial_state, hole_idx)
    initial_game_state = GameState(
        state=initial_state.copy(),
        unlocked_clamps=set(),
        groups_seen={},
        total_loss=0,
        moves=[],
        hole_idx=hole_idx
    )
    
    solution = solver.solve_dfs(initial_game_state, max_depth=max_depth, lookahead=lookahead)
    return solution.moves if solution else [], solver.best_loss

if __name__ == "__main__":
    # Test case
    initial_state = [1, 1, 1, 0, 1, 1, 0, 1]
    hole_idx = 8
    
    print("Initial state:", initial_state)
    print("Hole index:", hole_idx)
    
    best_moves, best_loss = solve_game(initial_state, hole_idx)
    
    if best_moves:
        print("\nBest solution found with loss:", best_loss)
        print("\nMoves to take:")
        for i, move in enumerate(best_moves, 1):
            print(f"{i}. {move}")
            
        # Simulate the solution
        print("\nSimulating solution:")
        game = CompressionGame(initial_state, hole_idx)
        game.reset()
        
        for move in best_moves:
            state, reward, done, info = game.step(move)
            print(f"\nAfter {move.__class__.__name__}:")
            print_state(state, info['loss'], hole_idx=hole_idx)
    else:
        print("\nNo solution found") 