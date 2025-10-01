from typing import List, Set, Optional, Union, Tuple
from game import GroupAction, ClampAction, MoveAction, Group, Clamp, CompressionGame, print_state
from copy import deepcopy

def detect_state_changes(old_state: List[Union[int, Group, Clamp]], 
                        new_state: List[Union[int, Group, Clamp]]) -> Tuple[List[int], List[int]]:
    """
    Detects changes between two states and returns indices of changes.
    
    Args:
        old_state: Previous state
        new_state: New state after chaotic change
        
    Returns:
        Tuple of (changed_indices, unchanged_indices)
    """
    changed_indices = []
    unchanged_indices = []
    
    # Handle states of different lengths
    min_len = min(len(old_state), len(new_state))
    
    for i in range(min_len):
        if old_state[i] != new_state[i]:
            changed_indices.append(i)
        else:
            unchanged_indices.append(i)
            
    # If new state is longer, all additional indices are changes
    if len(new_state) > min_len:
        changed_indices.extend(range(min_len, len(new_state)))
        
    return changed_indices, unchanged_indices

def identify_valid_layers(game: CompressionGame, 
                         changed_indices: List[int]) -> List[int]:
    """
    Identifies which layers in the game history are still valid after state changes.
    
    Args:
        game: CompressionGame instance
        changed_indices: Indices that changed in the initial state
        
    Returns:
        List of layer indices that are still valid
    """
    valid_layers = []
    
    # First layer is always the initial state, which has changed
    for i in range(1, len(game.layers)):
        # Check if this layer's move only affected unchanged positions
        affected_positions = set()
        
        # Get the move that created this layer
        move = game.moves[i-1]
        
        if isinstance(move, GroupAction):
            affected_positions.update(range(move.position, move.position + move.size))
        elif isinstance(move, ClampAction):
            affected_positions.update(range(move.position, move.position + move.size))
        elif isinstance(move, MoveAction):
            affected_positions.add(move.position)
            affected_positions.add(move.position + move.direction)
            
        # If move didn't affect any changed positions, layer is valid
        if not any(pos in changed_indices for pos in affected_positions):
            valid_layers.append(i)
            
    return valid_layers

def identify_new_opportunities(old_state: List[Union[int, Group, Clamp]],
                             new_state: List[Union[int, Group, Clamp]],
                             changed_indices: List[int]) -> List[Union[GroupAction, ClampAction]]:
    """
    Identifies new grouping/clamping opportunities created by state changes.
    
    Args:
        old_state: Previous state
        new_state: Current state after changes
        changed_indices: Indices that changed
        
    Returns:
        List of possible new actions
    """
    new_opportunities = []
    
    # Look for new grouping opportunities around changed indices
    for idx in changed_indices:
        # Look for groups starting at this position
        for size in range(2, 5):  # Check groups of size 2-4
            if idx + size > len(new_state):
                break
                
            elements = new_state[idx:idx + size]
            if all(isinstance(e, int) and e != 0 for e in elements):
                # Check if this was not possible in old state
                old_elements = old_state[idx:idx + size] if idx + size <= len(old_state) else None
                if not old_elements or not all(isinstance(e, int) and e != 0 for e in old_elements):
                    new_opportunities.append(GroupAction(idx, size))
        
        # Look for groups ending at this position
        for size in range(2, 5):
            start = idx - size + 1
            if start < 0:
                continue
                
            elements = new_state[start:idx + 1]
            if all(isinstance(e, int) and e != 0 for e in elements):
                # Check if this was not possible in old state
                old_elements = old_state[start:idx + 1] if start >= 0 and idx < len(old_state) else None
                if not old_elements or not all(isinstance(e, int) and e != 0 for e in old_elements):
                    new_opportunities.append(GroupAction(start, size))
    
    return new_opportunities

def adapt_game_layers(game: CompressionGame, 
                     new_initial_state: List[Union[int, Group, Clamp]], 
                     valid_layers: List[int],
                     new_opportunities: List[Union[GroupAction, ClampAction]] = None) -> CompressionGame:
    """
    Creates a new game instance with adapted layers based on valid moves.
    
    Args:
        game: Original CompressionGame instance
        new_initial_state: New chaotic initial state
        valid_layers: Indices of layers that are still valid
        new_opportunities: List of new possible actions to try
        
    Returns:
        New CompressionGame instance with adapted layers
    """
    new_game = CompressionGame(new_initial_state, game.hole_idx)
    
    # Apply only the moves that created valid layers
    for layer_idx in valid_layers:
        move = game.moves[layer_idx-1]  # -1 because moves list is 0-indexed
        try:
            new_game.step(move)
        except ValueError:
            # If move is no longer valid, stop here
            break
    
    # Try applying new opportunities
    if new_opportunities:
        for move in new_opportunities:
            try:
                new_game.step(move)
            except ValueError:
                continue
                
    return new_game

def test_move_validity(move: Union[GroupAction, ClampAction, MoveAction], 
                      state: List[Union[int, Group, Clamp]]) -> bool:
    """
    Tests if a move is still valid in the new state.
    
    Args:
        move: Move to test
        state: Current state to test move against
        
    Returns:
        Boolean indicating if move is still valid
    """
    if isinstance(move, GroupAction):
        if move.position + move.size > len(state):
            return False
        elements = state[move.position:move.position + move.size]
        return all(e != 0 for e in elements)
        
    elif isinstance(move, ClampAction):
        if move.position + move.size > len(state):
            return False
        elements = state[move.position:move.position + move.size]
        if not all(isinstance(e, Group) for e in elements):
            return False
        return all(e == elements[0] for e in elements)
        
    elif isinstance(move, MoveAction):
        if not (0 <= move.position < len(state)):
            return False
        if not isinstance(state[move.position], Clamp):
            return False
        new_pos = move.position + move.direction
        if not (0 <= new_pos < len(state)):
            return False
        return state[new_pos] == 0
        
    return False

def test_cascade_functions():
    """Test the cascade handling functions"""
    # Test case 1: Simple state change
    print("=== Test Case 1: Simple State Change ===")
    initial_state = [1, 1, 0, 0, 1, 1, 0, 0, 0]
    new_state = [1, 1, 0, 0, 1, 1, 0, 1, 1]
    
    game = CompressionGame(initial_state, hole_idx=3)
    
    # Make some moves
    game.step(GroupAction(0, 2))  # Group first two 1s
    game.step(GroupAction(4, 2))  # Group second pair of 1s
    
    # Detect changes
    changed_indices, unchanged_indices = detect_state_changes(initial_state, new_state)
    print(f"Changed indices: {changed_indices}")
    print(f"Unchanged indices: {unchanged_indices}")
    
    # Find valid layers
    valid_layers = identify_valid_layers(game, changed_indices)
    print(f"Valid layers: {valid_layers}")
    
    # Find new opportunities
    new_opportunities = identify_new_opportunities(initial_state, new_state, changed_indices)
    print(f"New opportunities: {new_opportunities}")
    
    # Adapt game
    new_game = adapt_game_layers(game, new_state, valid_layers, new_opportunities)
    print(f"Original game final state: {game.state}")
    print(f"Adapted game final state: {new_game.state}")
    
    # Test case 2: Test move validity
    print("\n=== Test Case 2: Move Validity ===")
    move1 = GroupAction(0, 2)
    move2 = GroupAction(7, 2)  # Should be valid in new state but not old state
    
    print(f"Move {move1} valid in old state: {test_move_validity(move1, initial_state)}")
    print(f"Move {move1} valid in new state: {test_move_validity(move1, new_state)}")
    print(f"Move {move2} valid in old state: {test_move_validity(move2, initial_state)}")
    print(f"Move {move2} valid in new state: {test_move_validity(move2, new_state)}")
    
    # Test case 3: Complex state change with new opportunities
    # print("\n=== Test Case 3: Complex State Change ===")
    # initial_state = [1, 1, 0, 0, 1, 1, 0, 0, 0]
    # new_state = [1, 1, 0, 0, 1, 1, 1, 1, 1]  # Added three 1s
    
    # game = CompressionGame(initial_state, hole_idx=3)
    # game.step(GroupAction(0, 2))
    # game.step(GroupAction(4, 2))
    
    # changed_indices, _ = detect_state_changes(initial_state, new_state)
    # valid_layers = identify_valid_layers(game, changed_indices)
    # new_opportunities = identify_new_opportunities(initial_state, new_state, changed_indices)
    
    # print(f"Changed indices: {changed_indices}")
    # print(f"Valid layers: {valid_layers}")
    # print(f"New opportunities: {new_opportunities}")
    
    # new_game = adapt_game_layers(game, new_state, valid_layers, new_opportunities)
    # print(f"Original game final state: {game.state}")
    # print(f"Adapted game final state: {new_game.state}")

if __name__ == "__main__":
    test_cascade_functions() 