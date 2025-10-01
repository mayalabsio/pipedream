def find_all_patterns(arr):
    n = len(arr)
    all_patterns = []
    
    def find_patterns_with_length(length):
        patterns = []
        for i in range(n - length + 1):
            pattern = arr[i:i + length]
            # Find all occurrences
            occurrences = []
            j = i + length
            while j <= n - length:
                if arr[j:j + length] == pattern:
                    occurrences.append((i, j))
                j += 1
            if occurrences:
                patterns.append((pattern, occurrences))
        return patterns
    
    # Find all patterns of each length
    for length in range(2, 5):
        patterns = find_patterns_with_length(length)
        for pattern, occurrences in patterns:
            # Create a new array with the pattern grouped
            for start, next_pos in occurrences:
                new_arr = arr.copy()
                # Replace both occurrences with the pattern as a list
                result = (
                    new_arr[:start] + 
                    [list(pattern)] + 
                    new_arr[start + length:next_pos] + 
                    [list(pattern)] + 
                    new_arr[next_pos + length:]
                )
                all_patterns.append(result)
    
    # Remove duplicates
    seen = set()
    unique_patterns = []
    for pattern in all_patterns:
        pattern_tuple = tuple(tuple(x) if isinstance(x, list) else x for x in pattern)
        if pattern_tuple not in seen:
            seen.add(pattern_tuple)
            unique_patterns.append(pattern)
    
    return unique_patterns

# Test
arr = [1, 1, 1, 0, 0, 1, 1, 0, 1]
results = find_all_patterns(arr)
for result in results:
    print(result)