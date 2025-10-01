from dataclasses import dataclass
from typing import List, Tuple, Optional, Set, Union
from abc import ABC, abstractmethod
import random
import os
import sys
import ast
from datetime import datetime

@dataclass
class Group:
    """Represents a group of elements and their contents"""
    contents: tuple  # The actual elements in the group
    
    def __repr__(self):
        return f"g{self.contents}"
    
    def __eq__(self, other):
        if not isinstance(other, Group):
            return False
        return self.contents == other.contents

    def __hash__(self) -> int:
        return hash(self.contents)

@dataclass
class Clamp:
    """Represents a clamp and its contents"""
    contents: tuple  # The original elements that were clamped
    
    def __repr__(self):
        return f"c{self.contents}"
    
    def __eq__(self, other):
        if not isinstance(other, Clamp):
            return False
        return self.contents == other.contents

    def __hash__(self) -> int:
        return hash(self.contents)

class Action(ABC):
    @abstractmethod
    def validate(self, state: List[Union[int, Group, Clamp]]) -> bool:
        """Validate if action is legal in given state"""
        pass

@dataclass
class GroupAction(Action):
    position: int    # Starting position
    size: int       # Size of group to create
    
    def __hash__(self) -> int:
        """Make GroupAction hashable so it can be used in sets"""
        return hash((self.position, self.size))
    
    def conflicts_with(self, other: 'GroupAction') -> bool:
        """Check if this group action overlaps with another group action"""
        if not isinstance(other, GroupAction):
            return False
            
        # Calculate ranges [start, end] for both actions
        self_start = self.position
        self_end = self.position + self.size - 1
        other_start = other.position
        other_end = other.position + other.size - 1
        
        # Check if ranges overlap
        return max(self_start, other_start) <= min(self_end, other_end)
    
    def validate(self, state: List[Union[int, Group, Clamp]]) -> bool:
        if self.position + self.size > len(state):
            return False
        
        elements = state[self.position:self.position + self.size]
        if all(e != 0 for e in elements):
            return True
        return False

@dataclass
class ClampAction(Action):
    position: int    # Starting position
    size: int       # Size of group to create
    
    def __hash__(self) -> int:
        return hash((self.position, self.size))

    def conflicts_with(self, other: 'ClampAction') -> bool:
        if not isinstance(other, ClampAction):
            return False
            
        self_start = self.position
        self_end = self.position + self.size - 1
        other_start = other.position
        other_end = other.position + other.size - 1

        return max(self_start, other_start) <= min(self_end, other_end)

    def validate(self, state: List[Union[int, Group, Clamp]], unlocked_clamps: Set[tuple], current_loss: int = None) -> bool:
        if self.position + self.size > len(state):
            return False
        
        # Get the contents of the group we're trying to clamp
        elements = state[self.position:self.position + self.size]
        if not all(isinstance(e, Group) and e == elements[0] for e in elements):
            return False
        
        # If only 2 elements remain, allow clamping any group
        if current_loss <= 2:
            return True
            
        # Check if this group pattern is unlocked
        group_contents = elements[0].contents
        return group_contents in unlocked_clamps

@dataclass
class MoveAction(Action):
    position: int    # Current position of clamp
    direction: int   # -1 for left, 1 for right
    
    def __hash__(self) -> int:
        """Make MoveAction hashable so it can be used in sets"""
        return hash((self.position, self.direction))
    
    def __eq__(self, other):
        """Define equality for MoveAction"""
        if not isinstance(other, MoveAction):
            return False
        return self.position == other.position and self.direction == other.direction
    
    def validate(self, state: List[Union[int, Group, Clamp]]) -> bool:
        if not (0 <= self.position < len(state)):
            return False
            
        # Check if there's a clamp at position
        if not isinstance(state[self.position], Clamp):
            return False
            
        # Check if we can move in desired direction
        new_pos = self.position + self.direction
        if not (0 <= new_pos < len(state)):
            return False
            
        return state[new_pos] == 0

class CompressionGame:
    _global_initial_state = None  # Class variable shared by all instances
    
    @classmethod
    def set_global_initial_state(cls, state):
        cls._global_initial_state = state.copy() if state else None
        
    @classmethod
    def get_global_initial_state(cls):
        return cls._global_initial_state.copy() if cls._global_initial_state is not None else None
    
    def __init__(self, initial_state: List[int], hole_idx: Optional[int] = None):
        if CompressionGame._global_initial_state is None:
            CompressionGame.set_global_initial_state(initial_state)
        self.initial_state = initial_state.copy()
        self.state = initial_state.copy()
        self.hole_idx = hole_idx
        self.unlocked_clamps: Set[tuple] = set()  # Tracks available clamp patterns
        self.groups_seen: dict = {}  # Tracks {contents: count} of groups seen
        self.total_loss = 0  # Track cumulative loss
        self.layers = [initial_state.copy()]  # Track state history when clamps are added
        self.moves = []  # Track all moves made
        
    def get_state(self) -> List[Union[int, Group, Clamp]]:
        return self.state.copy()
    
    def get_loss(self) -> int:
        """Calculate current loss (number of non-zero elements, excluding hole position)"""
        return sum(1 for i, x in enumerate(self.state) if x != 0 and i != self.hole_idx)
    
    def _update_clamp_availability(self):
        """Update which clamp patterns are available based on groups seen"""
        for contents, count in self.groups_seen.items():
            if count >= 2 and contents not in self.unlocked_clamps:
                self.unlocked_clamps.add(contents)

    def get_valid_actions(self) -> List[Action]:
        valid_actions = []
        
        # Check for possible groups
        for start in range(len(self.state)):
            # Skip if current element is already a Group or Clamp or zero
            if self.state[start] == 0:
                continue
                
            # Look for groups of size 2 or more
            for size in range(2, len(self.state) - start + 1):
                end = start + size
                if end > len(self.state):
                    break
                    
                elements = self.state[start:end]
                # Check if all elements are the same non-zero integers and not special types
                if all(e != 0 for e in elements):
                    valid_actions.append(GroupAction(start, size))
        
        # Check for possible clamps
        for contents in self.unlocked_clamps:
            size = len(contents)
            for i in range(len(self.state) - size + 1):
                # Check if there's a matching group
                elements = self.state[i:i + size]
                if all(isinstance(e, Group) for e in elements):
                    if all(e.contents == contents for e in elements):
                        valid_actions.append(ClampAction(i, size))
        
        # Check for possible moves
        for i in range(len(self.state)):
            if isinstance(self.state[i], Clamp):
                if i > 0 and self.state[i-1] == 0:
                    valid_actions.append(MoveAction(i, -1))
                if i < len(self.state)-1 and self.state[i+1] == 0:
                    valid_actions.append(MoveAction(i, 1))
        
        return valid_actions

    def step(self, action: Action) -> Tuple[List[Union[int, Group, Clamp]], int, bool, dict]:
        """Apply action and return (new_state, reward, done, info)"""
        if isinstance(action, GroupAction):
            if not action.validate(self.state):
                raise ValueError("Invalid group action")
            self.moves.append(action)
            
            # Get contents of the group
            elements = tuple(self.state[action.position:action.position + action.size])
            group = Group(elements)
            for i in range(action.position, action.position + action.size):
                self.state[i] = group
            
            # Update groups seen
            self.groups_seen[elements] = self.groups_seen.get(elements, 0) + 1
            self._update_clamp_availability()
            
            # Add new layer with loss after group is created
            current_loss = self.get_loss()
            self.layers.append((self.state.copy(), current_loss))
            
        elif isinstance(action, ClampAction):
            if not action.validate(self.state, self.unlocked_clamps, self.get_loss()):
                raise ValueError(f"Invalid clamp action: {action} {self.state} {self.unlocked_clamps}")
            
            self.moves.append(action)
            # Get group contents
            group = self.state[action.position]
            clamp = Clamp(group.contents)
            
            # Apply clamp
            self.state[action.position] = clamp
            for i in range(action.position + 1, action.position + action.size):
                self.state[i] = 0
            
            # Store new layer with loss after clamp is applied
            current_loss = self.get_loss()
            self.layers.append((self.state.copy(), current_loss))
                
        elif isinstance(action, MoveAction):
            if not action.validate(self.state):
                raise ValueError("Invalid move action")
            
            self.moves.append(action)    
            # Move clamp
            curr_pos = action.position
            new_pos = curr_pos + action.direction
            self.state[new_pos] = self.state[curr_pos]
            self.state[curr_pos] = 0
            
            # Add new layer with loss after move
            current_loss = self.get_loss()
            self.layers.append((self.state.copy(), current_loss))
            
        new_loss = self.get_loss()
        done = new_loss == 0  # Game ends when we can't reduce further
        
        reward = -new_loss  # Negative because we want to minimize loss
        
        info = {
            'loss': new_loss,
            'unlocked_clamps': self.unlocked_clamps
        }
        
        return self.get_state(), reward, done, info

    def reset(self) -> List[Union[int, Group, Clamp]]:
        """Reset environment to initial state"""
        self.state = [1 if x == 1 else 0 for x in self.state]
        self.unlocked_clamps = set()
        self.groups_seen = {}
        initial_loss = self.get_loss()
        self.layers = [(self.state.copy(), initial_loss)]
        self.moves = []
        return self.get_state()

    def dump_game_info(self, game_dir: str):
        """Save all game information to the specified directory"""
        os.makedirs(game_dir, exist_ok=True)
        
        # Save initial state and configuration
        with open(os.path.join(game_dir, 'init.txt'), 'w') as f:
            f.write(f"initial_state={self.layers[0][0]}\n")
            f.write(f"hole_idx={self.hole_idx}\n")
        
        # Save moves
        with open(os.path.join(game_dir, 'moves.txt'), 'w') as f:
            for move in self.moves:
                if isinstance(move, GroupAction):
                    f.write("0\n")  # move_id for GroupAction
                    f.write(f"{move.position}\n")
                    f.write(f"{move.size}\n")
                elif isinstance(move, ClampAction):
                    f.write("1\n")  # move_id for ClampAction
                    f.write(f"{move.position}\n")
                    f.write(f"{move.size}\n")
                elif isinstance(move, MoveAction):
                    f.write("2\n")  # move_id for MoveAction
                    f.write(f"{move.position}\n")
                    f.write(f"{move.direction}\n")
        print(f"Game information saved to {game_dir}")

def print_state(state: List[Union[int, Group, Clamp]], loss: int, layer_num: int = None, hole_idx: Optional[int] = None):
    """Pretty print the state in an ASCII grid with variable width cells"""
    state_str = [str(x) for x in state]
    if not state_str:
        print(f"[] loss={loss}m/s")
        return
    
    # Use uniform width for all cells based on the widest content
    cell_width = max(max(len(str(i)) for i in range(len(state_str))),
                    max(len(s) for s in state_str))
    widths = [cell_width] * len(state_str)
    
    # Create grid components
    horizontal_border = "+" + "+".join(["-" * (w + 2) for w in widths]) + "+"
    middle_row = "|" + "|".join([f" {s:^{w}} " for s, w in zip(state_str, widths)]) + "|"
    index_row = "|" + "|".join([f" {i:^{w}} " for i, w in enumerate(widths)]) + "|"
    
    # Create hole indicator row if hole_idx is provided
    if hole_idx is not None:
        hole_row = "|" + "|".join([f" {'H' if i == hole_idx else ' ':^{w}} " for i, w in enumerate(widths)]) + "|"
    
    # Print the grid
    print(horizontal_border)
    print(index_row)
    print(horizontal_border)
    print(middle_row)
    print(horizontal_border)
    if hole_idx is not None:
        print(hole_row)
        print(horizontal_border)
    if layer_num is not None:
        print(f"Layer {layer_num} | loss={loss}m/s")
    else:
        print(f"loss={loss}m/s")

def print_all_layers(layers: List[Tuple[List[Union[int, Group, Clamp]], int]], hole_idx: Optional[int] = None):
    """Pretty print all layers of the game state in an ASCII grid"""
    # Use uniform width for all cells based on the widest content across all layers
    cell_width = max(
        max(len(str(i)) for i in range(len(layers[0][0]))),
        max(len(str(x)) for layer, _ in layers for x in layer)
    )
    max_widths = [cell_width] * len(layers[0][0])
    
    # Print header row with position indices
    header = "+" + "+".join(["-" * (w + 2) for w in max_widths]) + "+"
    print(header)
    index_row = "|" + "|".join([f" {i:^{w}} " for i, w in enumerate(max_widths)]) + "|"
    print(index_row)
    print(header)
    
    # Print each layer as a row
    for i, (layer_state, loss) in enumerate(layers):
        row = "|" + "|".join([f" {str(x):^{w}} " for x, w in zip(layer_state, max_widths)]) + f"| L{i} (loss={loss})"
        print(row)
        print(header)
    
    # Add hole indicator row if hole_idx provided
    if hole_idx is not None:
        hole_row = "|" + "|".join([f" {'H' if i == hole_idx else ' ':^{w}} " for i, w in enumerate(max_widths)]) + "| Hole"
        print(hole_row)
        print(header)

def replay_game(replay_dir: str):
    """Replay a previously played game from saved files"""
    # Read initial state
    with open(os.path.join(replay_dir, 'init.txt')) as f:
        for line in f:
            if line.startswith('initial_state='):
                initial_state = ast.literal_eval(line.split('=')[1].strip())
            elif line.startswith('hole_idx='):
                hole_idx = ast.literal_eval(line.split('=')[1].strip())

    print(f"Replaying game from {replay_dir}")
    print(f"Initial state: {initial_state}")
    print(f"Hole position: {hole_idx}")
    
    game = CompressionGame(initial_state, hole_idx)
    state = game.reset()
    
    # Read and replay moves
    with open(os.path.join(replay_dir, 'moves.txt')) as f:
        moves = []
        while True:
            move_type = f.readline().strip()
            if not move_type:
                break
                
            if move_type == '0':  # GroupAction
                pos = int(f.readline())
                size = int(f.readline())
                moves.append(GroupAction(pos, size))
            elif move_type == '1':  # ClampAction
                pos = int(f.readline())
                size = int(f.readline())
                moves.append(ClampAction(pos, size))
            elif move_type == '2':  # MoveAction
                pos = int(f.readline())
                direction = int(f.readline())
                moves.append(MoveAction(pos, direction))
    
    # Replay moves with delay
    for i, move in enumerate(moves):
        print(f"\n=== Move {i+1} ===")
        print(f"Executing: {move}")
        state, reward, done, info = game.step(move)
        print_state(state, info['loss'], hole_idx=hole_idx)
        input("Press Enter for next move...")
    
    print("\nReplay complete! Final state:")
    print_state(state, game.get_loss(), hole_idx=hole_idx)
    print("\nFinal layer hierarchy:")
    print_all_layers(game.layers, hole_idx)

def play_interactive(init_state: List[int]=[1, 1, 1, 0, 0, 1, 1, 0, 1], hole_idx: Optional[int] = None):
    print("Welcome to the Compression Game!")
    if hole_idx is not None:
        print(f"Hole is at position {hole_idx}")
    game = CompressionGame(init_state, hole_idx)
    state = game.reset()
    done = False
    steps = 0
    unlocked_clamps = set()
    while not done:
        print(f"================== Step {steps} ==================")
        print(f"Unlocked clamps: {unlocked_clamps}")
        print_state(state, game.get_loss(), hole_idx=hole_idx)
        print("You can perform these actions:")
        print("0: Group elements - e.g. GroupAction(position=0, size=2)")
        print("1: Clamp group - e.g. ClampAction(position=0, size=2)")
        print("2: Move clamp - e.g. MoveAction(position=5, direction=1)")
        print("3: Show all layers")
        print("4: Dump moves to moves.txt")
        print("q: Quit game")
        
        # Get action from user
        action_index = ""
        while not action_index:
            action_index = input("Choose action (0-4, q to quit): ").strip()
        
        # Handle quit
        if action_index.lower() == 'q':
            print("\nQuitting game...")
            # Save game state before quitting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            game_dir = os.path.join("gameplays", f"game_{timestamp}")
            print(f"Saving game information to: {game_dir}")
            game.dump_game_info(game_dir)
            break
            
        # Create action based on user input
        if action_index == '0':
            pos = int(input("Group position: "))
            size = int(input("Group size: "))
            action = GroupAction(pos, size)
        elif action_index == '1':
            pos = int(input("Clamp position: "))
            size = int(input("Clamp size: "))
            action = ClampAction(pos, size)
        elif action_index == '2':
            pos = int(input("Clamp position: "))
            direction = int(input("Direction (-1=left, 1=right): "))
            action = MoveAction(pos, direction)
        elif action_index == '4':
            game.dump_moves()
            continue
        elif action_index == '3':
            print("\n=== Showing all layers ===")
            print_all_layers(game.layers, hole_idx)
            continue
        else:
            print("Invalid choice!")
            continue
        try:
            state, reward, done, info = game.step(action)
            game.total_loss += info['loss']
            print(f"Current loss: {info['loss']} | Total loss so far: {game.total_loss}")
            unlocked_clamps = info['unlocked_clamps']
            steps += 1
        except ValueError as e:
            print(f"Invalid move: {e}")

    print("\nFinal state achieved!")
    print_state(state, info['loss'])
    print(f"\nFinal total loss: {game.total_loss}")
    print("\nFinal layer hierarchy:")
    print_all_layers(game.layers, hole_idx)
    # Create timestamped game directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    game_dir = os.path.join("gameplays", f"game_{timestamp}")
    print(f"\nSaving game information to: {game_dir}")
    game.dump_game_info(game_dir)

def generate_random_state(length: int = 9, num_zeros: int = 3) -> List[int]:
    """Generate a random initial state with specified number of zeros"""
    if num_zeros > length:
        raise ValueError("Number of zeros cannot exceed length")
    
    # Create list with required number of 1s and 0s
    state = [1] * (length - num_zeros) + [0] * num_zeros
    # Shuffle the list
    random.shuffle(state)
    return state

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Compression Game')
    parser.add_argument('--replay', type=str, help='Replay directory path')
    parser.add_argument('--state', type=str, help='Initial state as comma-separated values (e.g. "1,1,1,0,0,1,1,0,1")')
    parser.add_argument('--hole', type=int, help='Hole position index')
    
    args = parser.parse_args()

    if args.replay:
        replay_game(args.replay)
    else:
        if args.state:
            # Parse state string into list of integers
            initial_state = [int(x) for x in args.state.split(',')]
            hole_idx = args.hole
        else:
            # Generate random state if none provided
            length = 9
            num_zeros = 3
            initial_state = generate_random_state(length, num_zeros)
            hole_idx = random.randint(0, length-1) if args.hole is None else args.hole

        print(f"Initial state: {initial_state}")
        print(f"Hole position: {hole_idx}")

        play_interactive(initial_state, hole_idx)
