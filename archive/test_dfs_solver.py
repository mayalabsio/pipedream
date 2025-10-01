import unittest
from dfs_solver_v2 import DFSSolver, CompressionGame
from game import print_all_layers

class TestDFSSolver(unittest.TestCase):
    def test_solver_case_1(self):
        """Test case with initial hole at position 4"""
        initial_state = [0, 1, 1, 1, 0, 1, 1, 0, 1]
        hole_idx = 4
        desired_loss = 0
        
        game = CompressionGame(initial_state, hole_idx)
        solver = DFSSolver(initial_state, hole_idx)
        solution = solver.solve_dfs(game, 0, 0, max_depth=20, lookahead=3, visited_states=set(), desired_loss=desired_loss)
        
        # Check if solution was found
        self.assertIsNotNone(solution, "No solution found for test case 1")
        if solution:
            self.assertEqual(solution.get_loss(), desired_loss, 
                           f"Solution found but loss {solution.get_loss()} != desired loss {desired_loss}")
            print("\nTest Case 1 Solution:")
            print("Final state:", solution.state)
            print("Moves:", solution.moves)
            if hasattr(solution, 'layers'):
                print_all_layers(solution.layers[1:], hole_idx)

    def test_solver_case_2(self):
        """Test case with initial hole at position 3"""
        initial_state = [1, 1, 0, 1, 0, 1, 1, 0, 1]
        hole_idx = 3
        desired_loss = 0
        
        game = CompressionGame(initial_state, hole_idx)
        solver = DFSSolver(initial_state, hole_idx)
        solution = solver.solve_dfs(game, 0, 0, max_depth=20, lookahead=3, visited_states=set(), desired_loss=desired_loss)
        
        # Check if solution was found
        self.assertIsNotNone(solution, "No solution found for test case 2")
        if solution:
            self.assertEqual(solution.get_loss(), desired_loss, 
                           f"Solution found but loss {solution.get_loss()} != desired loss {desired_loss}")
            print("\nTest Case 2 Solution:")
            print("Final state:", solution.state)
            print("Moves:", solution.moves)
            if hasattr(solution, 'layers'):
                print_all_layers(solution.layers[1:], hole_idx)

    def test_solver_case_3(self):
        """Test case with multiple holes"""
        initial_state = [1, 1, 0, 0, 0, 1, 1, 0, 0]
        hole_idx = 3
        desired_loss = 0
        
        game = CompressionGame(initial_state, hole_idx)
        solver = DFSSolver(initial_state, hole_idx)
        solution = solver.solve_dfs(game, 0, 0, max_depth=20, lookahead=3, visited_states=set(), desired_loss=desired_loss)
        
        # Check if solution was found
        self.assertIsNotNone(solution, "No solution found for test case 3")
        if solution:
            self.assertEqual(solution.get_loss(), desired_loss, 
                           f"Solution found but loss {solution.get_loss()} != desired loss {desired_loss}")
            print("\nTest Case 3 Solution:")
            print("Final state:", solution.state)
            print("Moves:", solution.moves)
            if hasattr(solution, 'layers'):
                print_all_layers(solution.layers[1:], hole_idx)

    def test_solver_case_4(self):
        """Test case with longer sequence and desired loss of 2"""
        initial_state = [1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1]
        hole_idx = 3
        desired_loss = 2
        
        game = CompressionGame(initial_state, hole_idx)
        solver = DFSSolver(initial_state, hole_idx)
        solution = solver.solve_dfs(game, 0, 0, max_depth=20, lookahead=3, visited_states=set(), desired_loss=desired_loss)
        
        # Check if solution was found
        self.assertIsNotNone(solution, "No solution found for test case 4")
        if solution:
            self.assertEqual(solution.get_loss(), desired_loss, 
                           f"Solution found but loss {solution.get_loss()} != desired loss {desired_loss}")
            print("\nTest Case 4 Solution:")
            print("Final state:", solution.state)
            print("Moves:", solution.moves)
            if hasattr(solution, 'layers'):
                print_all_layers(solution.layers[1:], hole_idx)

    def test_solver_case_5(self):
        """Test case with multiple holes and longer sequence"""
        initial_state = [1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0]
        hole_idx = 5
        desired_loss = 2
        
        game = CompressionGame(initial_state, hole_idx)
        solver = DFSSolver(initial_state, hole_idx)
        solution = solver.solve_dfs(game, 0, 0, max_depth=20, lookahead=3, visited_states=set(), desired_loss=desired_loss)
        
        # Check if solution was found
        self.assertIsNotNone(solution, "No solution found for test case 5")
        if solution:
            self.assertEqual(solution.get_loss(), desired_loss, 
                           f"Solution found but loss {solution.get_loss()} != desired loss {desired_loss}")
            print("\nTest Case 5 Solution:")
            print("Final state:", solution.state)
            print("Moves:", solution.moves)
            if hasattr(solution, 'layers'):
                print_all_layers(solution.layers[1:], hole_idx)

    def test_solver_case_6(self):
        """Test case with long sequence and multiple holes"""
        initial_state = [1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0]
        hole_idx = 10
        desired_loss = 4
        
        game = CompressionGame(initial_state, hole_idx)
        solver = DFSSolver(initial_state, hole_idx)
        solution = solver.solve_dfs(game, 0, 0, max_depth=20, lookahead=3, visited_states=set(), desired_loss=desired_loss)
        
        # Check if solution was found
        self.assertIsNotNone(solution, "No solution found for test case 6")
        if solution:
            self.assertEqual(solution.get_loss(), desired_loss, 
                           f"Solution found but loss {solution.get_loss()} != desired loss {desired_loss}")
            print("\nTest Case 6 Solution:")
            print("Final state:", solution.state)
            print("Moves:", solution.moves)
            if hasattr(solution, 'layers'):
                print_all_layers(solution.layers[1:], hole_idx)

if __name__ == '__main__':
    unittest.main() 