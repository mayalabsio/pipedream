from copy import deepcopy

class ToyGame:
    _global_state = None  # Class variable shared by all instances
    
    def __init__(self, local_state):
        self.local_state = local_state  # Instance variable
    
    @classmethod
    def set_global_state(cls, state):
        cls._global_state = state
        
    def get_states(self):
        return f"Global: {self._global_state}, Local: {self.local_state}"

def main():
    # Create original game
    game = ToyGame("A")
    ToyGame.set_global_state("Original")
    
    print("Original game:", game.get_states())
    
    # Make some copies
    games = [deepcopy(game) for _ in range(3)]
    print("\nAfter making copies:")
    for i, g in enumerate(games):
        print(f"Copy {i}:", g.get_states())
    
    # Change global state
    print("\nChanging global state...")
    ToyGame.set_global_state("Changed!")
    
    # Show that all copies see the change
    print("\nAll games after global change:")
    print("Original:", game.get_states())
    for i, g in enumerate(games):
        print(f"Copy {i}:", g.get_states())
    
    # Show that local states remain independent
    print("\nChanging local state of one copy...")
    games[0].local_state = "Modified"
    
    print("\nFinal states:")
    print("Original:", game.get_states())
    for i, g in enumerate(games):
        print(f"Copy {i}:", g.get_states())

if __name__ == "__main__":
    main() 