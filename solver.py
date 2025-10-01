from dataclasses import dataclass
from typing import List, Tuple, Set, Optional, Dict, Union
from game import Group, Clamp, GroupAction, ClampAction, MoveAction, Action, CompressionGame
import copy
from collections import deque
import heapq

@dataclass
class GameState:
    """Represents a state in the game"""
    state: List[Union[int, 'Group', 'Clamp']]  # Current board state
    unlocked_clamps: Set[tuple]  # Available clamp patterns
    groups_seen: Dict[tuple, int]  # Track group frequencies
    total_loss: int  # Cumulative loss
    moves: List[Union[GroupAction, ClampAction, MoveAction]]  # History of moves
    hole_idx: int  # Position of the hole
    
    def __hash__(self):
        # Convert state to tuple of strings
        state_tuple = tuple(str(x) for x in self.state)
        # Convert unlocked clamps to tuple of strings and sort
        clamps_tuple = tuple(sorted(str(x) for x in self.unlocked_clamps))
        return hash((state_tuple, clamps_tuple))
    
    def __eq__(self, other):
        if not isinstance(other, GameState):
            return False
        return (self.state == other.state and 
                self.unlocked_clamps == other.unlocked_clamps)
    
    def __lt__(self, other):
        """Define ordering to break ties in priority queue"""
        return self.total_loss < other.total_loss

class GameSolver:
    def __init__(self, initial_state: List[int], hole_idx: int):
        self.initial_state = initial_state
        self.hole_idx = hole_idx
        
    def get_loss(self, state: List[any]) -> int:
        """Calculate current loss (non-zero elements excluding hole)"""
        return sum(1 for i, x in enumerate(state) if x != 0 and i != self.hole_idx)
    
    def find_possible_groups_old(self, state: GameState) -> List[GroupAction]:
        """Find all possible group actions in current state"""
        actions = []
        i = 0
        print("State: ", state.state)
        while i < len(state.state):
            # Look for consecutive identical elements
            if i < len(state.state) - 1 and state.state[i] == state.state[i+1]:
                j = i + 1
                while j < len(state.state) and state.state[j] == state.state[i]:
                    j += 1
                if j - i >= 2:  # Need at least 2 elements to form a group
                    actions.append(GroupAction(i, j - i))
                i = j  # Jump to end of group
            else:
                i += 1  # Move to next element
        return actions
    
    def find_possible_groups(self, state: GameState, allow_zero: bool = False) -> List[GroupAction]:
        """Find group actions based on repeating patterns (2-4 elements)
        
        Args:
            allow_zero: If True, allows patterns containing 0 (hole) 
        """
        actions = []
        state_arr = state.state
        n = len(state_arr)

        non_zero_elements = [(i, e) for i, e in enumerate(state_arr) if e != 0]
        if (len(non_zero_elements) == 2 and 
            abs(non_zero_elements[0][0] - non_zero_elements[1][0]) == 1 and  # Adjacent positions
            isinstance(non_zero_elements[0][1], Clamp) and 
            isinstance(non_zero_elements[1][1], Clamp) and 
            non_zero_elements[0][1].contents == non_zero_elements[1][1].contents):
            return [GroupAction(non_zero_elements[0][0], 2)]
        
        # Check all possible group lengths from 2 to 4
        for length in range(2, 5):
            # Check all possible starting positions
            for i in range(n - length + 1):
                # Extract current potential group
                pattern = []
                valid = True
                current_section = state_arr[i:i+length]

                for e in state_arr[i:i+length]:
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
                    for e in state_arr[j:j+length]:
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
    
    def find_possible_clamps(self, state: GameState) -> List[ClampAction]:
        """Find all possible clamp actions in current state"""
        actions = []
        current_loss = self.get_loss(state.state)
        print("Unlocked clamps: ", state.unlocked_clamps)
        
        # Get all groups in the state
        groups = [(i, g) for i, g in enumerate(state.state) if isinstance(g, Group)]
        
        # If only 2 groups remain, allow clamping them regardless of unlocked patterns
        if len(groups) == 2 and groups[0][1].contents == groups[1][1].contents:
            # Add clamp action starting at the first group's position
            return [ClampAction(groups[0][0], 2)]
        
        # Otherwise, proceed with normal unlocked clamp checking
        for contents in state.unlocked_clamps:
            size = len(contents) if isinstance(contents, tuple) else 1
            for i in range(len(state.state) - size + 1):
                elements = state.state[i:i + size]
                if all(isinstance(e, Group) for e in elements):
                    if all(e.contents == contents for e in elements):
                        actions.append(ClampAction(i, size))
        return actions
    
    def find_possible_moves(self, state: GameState) -> List[MoveAction]:
        """Find all possible move actions in current state"""
        actions = []
        for i in range(len(state.state)):
            if isinstance(state.state[i], Clamp):
                if i > 0 and state.state[i-1] == 0:
                    actions.append(MoveAction(i, -1))
                if i < len(state.state)-1 and state.state[i+1] == 0:
                    actions.append(MoveAction(i, 1))
        return actions
    
    def apply_action(self, state: GameState, action: Action) -> GameState:
        """Apply action to state and return new state"""
        new_state = GameState(
            state=state.state.copy(),
            unlocked_clamps=state.unlocked_clamps.copy(),
            groups_seen=state.groups_seen.copy(),
            total_loss=state.total_loss + self.get_loss(state.state),
            moves=state.moves + [action],
            hole_idx=state.hole_idx
        )
        
        if isinstance(action, GroupAction):
            # Get contents of the group, using underlying values for existing groups/clamps
            elements = tuple(
                x.contents if isinstance(x, (Group, Clamp)) else x 
                for x in new_state.state[action.position:action.position + action.size]
            )
            group = Group(elements)
            for i in range(action.position, action.position + action.size):
                new_state.state[i] = group
            
            # Update groups seen with the primitive values
            new_state.groups_seen[elements] = new_state.groups_seen.get(elements, 0) + 1
            if new_state.groups_seen[elements] >= 2:
                new_state.unlocked_clamps.add(elements)
                
        elif isinstance(action, ClampAction):
            # Get group contents
            group = new_state.state[action.position]
            clamp = Clamp(group.contents)
            
            # Apply clamp
            new_state.state[action.position] = clamp
            for i in range(action.position + 1, action.position + action.size):
                new_state.state[i] = 0
                
        elif isinstance(action, MoveAction):
            # Move clamp
            curr_pos = action.position
            new_pos = curr_pos + action.direction
            new_state.state[new_pos] = new_state.state[curr_pos]
            new_state.state[curr_pos] = 0
            
        return new_state
    
    def calculate_move_priority(self, state: GameState, action: Action) -> float:
        """Calculate priority score for a move (lower is better)"""
        if isinstance(action, GroupAction):
            return 1  # Highest priority
        elif isinstance(action, ClampAction):
            return 2  # Second priority
        else:  # MoveAction
            # Priority based on distance to hole
            pos = action.position
            new_pos = pos + action.direction
            old_dist = abs(pos - state.hole_idx)
            new_dist = abs(new_pos - state.hole_idx)
            return 3 + (new_dist / len(state.state))  # Lower priority, but prefer moves toward hole
    
    def solve(self, max_moves: int = 1000) -> Optional[GameState]:
        """Find solution using priority-based search"""
        initial = GameState(
            state=self.initial_state.copy(),
            unlocked_clamps=set(),
            groups_seen={},
            total_loss=0,
            moves=[],
            hole_idx=self.hole_idx
        )
        
        # Priority queue of (priority, state)
        queue = [(0, initial)]
        seen = {hash(initial)}
        best_solution = None
        actions_explored = 0
        
        print("\n=== Solver Start ===")
        print(f"Initial state: {initial.state}")
        print(f"Initial loss: {self.get_loss(initial.state)}")
        
        while queue and moves_explored < max_moves:
            priority, current = heapq.heappop(queue)
            moves_explored += 1
            
            # Check if we've reached a solution
            current_loss = self.get_loss(current.state)
            print(f"Current loss: {current_loss}")
            
            if current_loss == 0:
                print("!!! Found potential solution !!!")
                if best_solution is None or current.total_loss < best_solution.total_loss:
                    best_solution = current
                    print("New best solution updated")
                continue
            
            # Generate and evaluate all possible moves
            groups = self.find_possible_groups(current)
            clamps = self.find_possible_clamps(current)
            moves = self.find_possible_moves(current)
            all_actions = groups + clamps + moves
            
            print(f"Found {len(all_actions)} actions:")
            print(f" - Groups: {len(groups)}")
            print(f" - Clamps: {len(clamps)}")
            print(f" - Moves: {len(moves)}")
            
            for action in all_actions:
                try:
                    new_state = self.apply_action(current, action)
                    state_hash = hash(new_state)
                    
                    print(f"\nProcessing {action.__class__.__name__}:")
                    print(f" - Action details: {action}")
                    print(f" - New state hash: {state_hash}")
                    print(f" - New state: {[str(x) for x in new_state.state]}")
                    print(f" - New loss: {self.get_loss(new_state.state)}")
                    
                    if state_hash not in seen:
                        seen.add(state_hash)
                        new_priority = self.calculate_move_priority(current, action)
                        heapq.heappush(queue, (new_priority, new_state))
                        print(f" - Added to queue with priority {new_priority:.2f}")
                    else:
                        print(" - State already seen, skipping")
                    
                except ValueError as e:
                    print(f" - Invalid action: {str(e)}")
                    continue
        
        print("\n=== Solver Finished ===")
        print(f"Total moves explored: {moves_explored}")
        print(f"Best solution loss: {best_solution.total_loss if best_solution else 'None'}")
        return best_solution

    def print_solution(self, solution: GameState):
        """Print the solution path with state after each move"""
        if not solution:
            print("No solution found!")
            return
        
        print(f"\nSolution found with total loss {solution.total_loss}:")
        print("\nInitial state:")
        print([str(x) for x in self.initial_state])
        print(f"Initial loss: {self.get_loss(self.initial_state)}")
        
        current_state = GameState(
            state=self.initial_state.copy(),
            unlocked_clamps=set(),
            groups_seen={},
            total_loss=0,
            moves=[],
            hole_idx=self.hole_idx
        )
        
        for i, move in enumerate(solution.moves, 1):
            try:
                current_state = self.apply_action(current_state, move)
                print(f"\nStep {i}: {move.__class__.__name__}")
                print(f"Position: {move.position}, " + 
                      (f"Size: {move.size}" if hasattr(move, 'size') else f"Direction: {move.direction}"))
                print([str(x) for x in current_state.state])
                print(f"Loss: {self.get_loss(current_state.state)}")
                print(f"Unlocked clamps: {current_state.unlocked_clamps}")
            except ValueError as e:
                print(f"Error applying move: {e}")
                break 

def solve_game(initial_state: List[int], hole_idx: Optional[int] = None) -> GameState:
    """Main entry point for the solver"""
    game = CompressionGame(initial_state, hole_idx)
    best_solution = GameState(game.get_state(), float('inf'), [])
    
    def try_all_moves(game: CompressionGame, current_moves: List[Union[GroupAction, ClampAction, MoveAction]]) -> None:
        """Recursive function to try all possible moves"""
        nonlocal best_solution
        
        # Get current state info
        current_state = game.get_state()
        current_loss = game.get_loss()
        
        # If we found a better solution, update it
        if current_loss < best_solution.total_loss:
            best_solution = GameState(
                state=current_state,
                total_loss=current_loss,
                moves=current_moves.copy()
            )
            print(f"Found better solution with loss {current_loss}")
        
        # Base case: if we can't reduce further or we're already worse than best
        if current_loss == 0 or current_loss >= best_solution.total_loss:
            return
            
        # Try moves in specified order: groups -> clamps -> moves
        
        # 1. Try all possible group actions first
        valid_actions = game.get_valid_actions()
        group_actions = [a for a in valid_actions if isinstance(a, GroupAction)]
        
        for action in group_actions:
            # Create new game state for this branch
            new_game = CompressionGame(initial_state, hole_idx)
            # Replay moves up to this point
            for move in current_moves:
                new_game.step(move)
            # Try this new move
            try:
                new_game.step(action)
                new_moves = current_moves + [action]
                try_all_moves(new_game, new_moves)
            except ValueError:
                continue
        
        # 2. Try all possible clamp actions
        clamp_actions = [a for a in valid_actions if isinstance(a, ClampAction)]
        
        for action in clamp_actions:
            new_game = CompressionGame(initial_state, hole_idx)
            for move in current_moves:
                new_game.step(move)
            try:
                new_game.step(action)
                new_moves = current_moves + [action]
                try_all_moves(new_game, new_moves)
            except ValueError:
                continue
                
        # 3. Try all possible move actions
        move_actions = [a for a in valid_actions if isinstance(a, MoveAction)]
        
        for action in move_actions:
            new_game = CompressionGame(initial_state, hole_idx)
            for move in current_moves:
                new_game.step(move)
            try:
                new_game.step(action)
                new_moves = current_moves + [action]
                try_all_moves(new_game, new_moves)
            except ValueError:
                continue
    
    # Start the recursive search
    try_all_moves(game, [])
    return best_solution

if __name__ == "__main__":
    # Example usage
    initial_state = [1, 1, 1, 0, 0, 1, 1, 0, 1]
    hole_idx = 3
    
    print(f"Solving game with initial state: {initial_state}")
    print(f"Hole position: {hole_idx}")
    
    solution = solve_game(initial_state, hole_idx)
    
    print("\nBest solution found:")
    print(f"Final loss: {solution.total_loss}")
    print("Moves to take:")
    for i, move in enumerate(solution.moves, 1):
        print(f"{i}. {move}")

