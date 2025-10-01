def plot_solver_losses_ascii(solver, first_state=None, width=80, height=20):
    """
    ASCII text-only version of plot_solver_losses() that displays loss progression
    in the terminal without matplotlib dependencies.
    
    Args:
        solver: The solver object with loss_history
        first_state: Optional first state to include
        width: Width of the ASCII plot in characters
        height: Height of the ASCII plot in characters
    """
    print("Plotting solver losses (ASCII)")
    print(f"Total loss history entries: {len(solver.loss_history)}")
    
    # Modified to handle both regular losses and state change markers
    regular_losses = []
    state_changes = []
    states = [first_state] if first_state else [solver.original_initial_state]
    
    for i, loss_entry in enumerate(solver.loss_history):
        if isinstance(loss_entry, tuple):
            if len(loss_entry) == 2:
                # Regular loss entry (total_loss, current_loss)
                total_loss, current_loss = loss_entry
                regular_losses.append((i, total_loss, current_loss))
            elif len(loss_entry) == 4:
                # State change marker (call_number, total_loss, current_loss, state)
                call_number = loss_entry[0]
                state_changes.append(call_number)
                current_state = loss_entry[3]
                states.append(current_state)

    print(f"State changes detected at: {state_changes}")
    print(f"States: {states}")
    
    if not regular_losses:
        print("No regular loss data to plot")
        return
    
    calls, total_losses, current_losses = zip(*regular_losses)
    
    # Prepare data for plotting
    max_call = max(calls)
    min_call = min(calls)
    max_loss = min(10, max(current_losses))  # Cap at 10 like original
    min_loss = 0
    
    # Create the ASCII plot
    print(f"\nLoss Progression During Solving")
    print(f"Number of Solver Calls: {min_call} to {max_call}")
    print(f"Loss Range: {min_loss:.1f} to {max_loss:.1f}")
    print("=" * width)
    
    # Create plot grid
    plot_grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Scale functions
    def scale_x(call_num):
        if max_call == min_call:
            return width // 2
        return int((call_num - min_call) / (max_call - min_call) * (width - 1))
    
    def scale_y(loss_val):
        if max_loss == min_loss:
            return height // 2
        return int((height - 1) - (loss_val - min_loss) / (max_loss - min_loss) * (height - 1))
    
    # Plot data points with colors for different states
    change_points = [0] + state_changes + [max(calls) + 1]
    
    # ANSI color codes for different states
    colors = [
        '\033[91m',  # Red
        '\033[92m',  # Green  
        '\033[93m',  # Yellow
        '\033[94m',  # Blue
        '\033[95m',  # Magenta
        '\033[96m',  # Cyan
        '\033[97m',  # White
        '\033[90m',  # Gray
    ]
    reset_color = '\033[0m'
    
    # First pass: plot all data points
    plot_points = []
    for i, (call, _, current_loss) in enumerate(regular_losses):
        # Determine which state segment this point belongs to
        state_idx = 0
        for j in range(len(change_points) - 1):
            if change_points[j] <= call < change_points[j + 1]:
                state_idx = j
                break
        
        x = scale_x(call)
        y = scale_y(current_loss)
        
        if 0 <= x < width and 0 <= y < height:
            color = colors[state_idx % len(colors)]
            colored_char = f"{color}_{reset_color}"
            plot_grid[y][x] = colored_char
            plot_points.append((x, y, state_idx))
    
    # Second pass: connect consecutive points with lines
    for i in range(len(plot_points) - 1):
        x1, y1, state1 = plot_points[i]
        x2, y2, state2 = plot_points[i + 1]
        
        # Only connect points from the same state
        if state1 == state2:
            color = colors[state1 % len(colors)]
            
            # Draw line from (x1, y1) to (x2, y2)
            # Handle both horizontal and vertical segments
            
            if x1 == x2:
                # Vertical line only
                min_y, max_y = min(y1, y2), max(y1, y2)
                for y in range(min_y + 1, max_y):
                    if 0 <= y < height and plot_grid[y][x1] == ' ':
                        plot_grid[y][x1] = f"{color}|{reset_color}"
            else:
                # Draw horizontal and vertical segments to connect points
                # Use a simple line drawing algorithm
                
                dx = x2 - x1
                dy = y2 - y1
                steps = max(abs(dx), abs(dy))
                
                if steps > 0:
                    x_inc = dx / steps
                    y_inc = dy / steps
                    
                    for step in range(1, steps):
                        x = int(x1 + step * x_inc)
                        y = int(y1 + step * y_inc)
                        
                        if 0 <= x < width and 0 <= y < height and plot_grid[y][x] == ' ':
                            # Use vertical bar for mostly vertical segments, underscore for horizontal
                            if abs(y_inc) > abs(x_inc):
                                plot_grid[y][x] = f"{color}|{reset_color}"
                            else:
                                plot_grid[y][x] = f"{color}_{reset_color}"
    
    # Mark state changes with vertical lines
    for call_num in state_changes:
        x = scale_x(call_num)
        if 0 <= x < width:
            for y in range(height):
                if plot_grid[y][x] == ' ':
                    plot_grid[y][x] = '|'
    
    # Print Y-axis labels and plot
    for i, row in enumerate(plot_grid):
        loss_val = min_loss + (max_loss - min_loss) * (height - 1 - i) / (height - 1)
        print(f"{loss_val:4.1f} |{''.join(row)}")
    
    # Print X-axis
    print("     " + "-" * width)
    
    # Print X-axis labels evenly distributed across width
    # Calculate how many labels we can fit (assuming ~4 chars per label)
    label_width = 4
    num_labels = min(10, width // label_width)  # Cap at 10 labels max
    
    x_axis_line = [' '] * width
    for i in range(num_labels):
        pos = int(i * (width - 1) / max(1, num_labels - 1))
        call_val = min_call + (max_call - min_call) * pos / (width - 1)
        label = f"{int(call_val)}"
        
        # Place label at position, ensuring it fits within width
        start_pos = max(0, min(pos - len(label)//2, width - len(label)))
        for j, char in enumerate(label):
            if start_pos + j < width:
                x_axis_line[start_pos + j] = char
    
    print("     " + "".join(x_axis_line))
    print(f"     {'Number of Solver Calls':^{width}}")
    
    # Print legend
    print("\nLegend:")
    for i, state in enumerate(states[:len(colors)]):
        color = colors[i % len(colors)]
        colored_underscore = f"{color}_{reset_color}"
        state_str = str(state) if state is not None else "Unknown"
        print(f"  {colored_underscore} = State {i+1}: {state_str}")
    
    print("  | = State Change / Continuity Line")
    
    # Print summary statistics
    print(f"\nSummary:")
    print(f"  Total solver calls: {len(regular_losses)}")
    print(f"  Final loss: {current_losses[-1]:.2f}")
    print(f"  Best loss: {min(current_losses):.2f}")
    print(f"  State changes: {len(state_changes)}")


if __name__ == "__main__":
    # Example usage - this would normally be called with a real solver object
    print("ASCII plot function ready for use.")
    print("Usage: plot_solver_losses_ascii(solver, first_state=None, width=80, height=20)")