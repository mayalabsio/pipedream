from solver import GameSolver

def main():
    # Example cases from the logs
    cases = [
        # {
        #     'name': 'Hole at 7',
        #     'initial_state': [1, 1, 1, 0, 0, 1, 1, 0, 1],
        #     'hole_idx': 7
        # },
        # {
        #     'name': 'Hole at 4',
        #     'initial_state': [1, 1, 1, 0, 0, 1, 1, 0, 1],
        #     'hole_idx': 4
        # },
        {
            'name': 'Simple case',
            'initial_state': [1, 1, 0, 1, 1],
            'hole_idx': 2
        }
    ]
    
    for case in cases:
        print(f"\n=== Solving {case['name']} ===")
        solver = GameSolver(case['initial_state'], case['hole_idx'])
        solution = solver.solve()
        solver.print_solution(solution)

if __name__ == '__main__':
    main() 