import unittest
from game import CompressionGame, GroupAction, ClampAction, MoveAction, Group, Clamp
from typing import List, Set, Optional, Union, Tuple
from copy import deepcopy

def track_state_changes(initial_state: List[Union[int, Group, Clamp]], 
                       current_state: List[Union[int, Group, Clamp]]) -> List[Tuple[int, Union[int, Group, Clamp]]]:
    """
    Track changes between initial and current state.
    Returns list of (position, value) tuples where state differs.
    """
    changes = []
    for i, (init, curr) in enumerate(zip(initial_state, current_state)):
        if init != curr:
            changes.append((i, curr))
    return changes

def is_move_reversible(move: Union[GroupAction, ClampAction, MoveAction], 
                      initial_state: List[Union[int, Group, Clamp]],
                      current_state: List[Union[int, Group, Clamp]]) -> bool:
    """
    Determine if a move is reversible when initial state changes.
    GroupActions and ClampActions are irreversible if they involve positions that changed.
    MoveActions are always reversible.
    """
    if isinstance(move, MoveAction):
        return True
    
    # For GroupAction and ClampAction, check if any involved positions changed
    start_pos = move.position
    end_pos = move.position + move.size
    
    for i in range(start_pos, end_pos):
        if i < len(initial_state) and i < len(current_state):
            if initial_state[i] != current_state[i]:
                return False
    return True

def adapt_current_state(current_state: List[Union[int, Group, Clamp]], 
                       new_initial_state: List[Union[int, Group, Clamp]], 
                       moves: List[Union[GroupAction, ClampAction, MoveAction]]) -> Tuple[List[Union[int, Group, Clamp]], List[Union[GroupAction, ClampAction, MoveAction]]]:
    """
    Adapt current state when initial state changes.
    Returns (adapted_state, valid_moves).
    """
    # Start with new initial state
    adapted_state = new_initial_state.copy()
    valid_moves = []
    
    # Reapply only reversible moves
    for move in moves:
        if is_move_reversible(move, new_initial_state, current_state):
            valid_moves.append(move)
            # Apply move to adapted state
            game = CompressionGame(adapted_state, None)  # hole_idx not needed for this
            game.state = adapted_state  # Set state directly to avoid reset
            try:
                game.step(move)
                adapted_state = game.state
            except ValueError:
                # If move is no longer valid, don't include it
                valid_moves.pop()
                
    return adapted_state, valid_moves

class TestChaoticSolver(unittest.TestCase):
    def test_track_state_changes(self):
        initial_state = [1, 1, 0, 1, 0]
        current_state = [Group((1, 1)), Group((1, 1)), 0, 1, 0]
        changes = track_state_changes(initial_state, current_state)
        self.assertEqual(len(changes), 2)  # First two positions changed to groups
        self.assertEqual(changes[0][0], 0)  # First change at position 0
        self.assertEqual(changes[1][0], 1)  # Second change at position 1
        
    def test_is_move_reversible(self):
        initial_state = [1, 1, 0, 1, 0]
        current_state = [Group((1, 1)), Group((1, 1)), 0, 1, 0]
        
        # Test MoveAction is always reversible
        move_action = MoveAction(2, 1)
        self.assertTrue(is_move_reversible(move_action, initial_state, current_state))
        
        # Test GroupAction involving changed positions is not reversible
        group_action = GroupAction(0, 2)
        self.assertFalse(is_move_reversible(group_action, initial_state, current_state))
        
        # Test GroupAction on unchanged positions is reversible
        group_action = GroupAction(3, 2)
        self.assertTrue(is_move_reversible(group_action, initial_state, current_state))
        
    def test_adapt_current_state(self):
        # Initial setup with a state that allows two identical groups
        initial_state = [1, 1, 0, 1, 1, 1, 0]  # Changed to allow two groups of (1,1)
        
        # Create game and apply first group to register it
        game = CompressionGame(initial_state, None)
        
        # Create two identical groups to unlock clamping
        game.step(GroupAction(0, 2))  # First group at 0,1
        game.step(GroupAction(3, 2))  # Second group at 3,4
        
        # Now we can clamp and move
        moves = [
            GroupAction(0, 2),
            GroupAction(3, 2),
            ClampAction(0, 2),
            ClampAction(3, 2),
            MoveAction(0, 1)
        ]
        
        # Reset game and apply all moves
        game = CompressionGame(initial_state, None)
        for move in moves:
            game.step(move)
        current_state = game.state
        
        # New initial state (shifted right by 1)
        new_initial_state = [1, 1, 0, 1, 1, 0, 1]
        
        # Adapt state
        adapted_state, valid_moves = adapt_current_state(current_state, new_initial_state, moves)
        
        # Only MoveAction should be valid after shift
        self.assertEqual(len(valid_moves), 1)
        self.assertTrue(isinstance(valid_moves[0], MoveAction))
        
    def test_adapt_current_state_with_clamps(self):
        # Test with a sequence involving clamps
        initial_state = [1, 1, 0, 1, 1]
        moves = [
            GroupAction(0, 2),
            GroupAction(3, 2),
            ClampAction(0, 2)
        ]
        
        # Apply moves to get current state
        game = CompressionGame(initial_state, None)
        for move in moves:
            game.step(move)
        current_state = game.state
        
        # New initial state (shifted)
        new_initial_state = [1, 0, 1, 1, 1]
        
        # Adapt state
        adapted_state, valid_moves = adapt_current_state(current_state, new_initial_state, moves)
        
        # Verify no group/clamp actions on shifted positions are included
        for move in valid_moves:
            if isinstance(move, (GroupAction, ClampAction)):
                self.assertTrue(is_move_reversible(move, new_initial_state, current_state))

if __name__ == '__main__':
    unittest.main() 