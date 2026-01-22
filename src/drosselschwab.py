import numpy as np

def burn_step(grid, x, y, L, connectivity=4):
    """
    Burn the entire connected cluster of trees containing (x, y) using an
    iterative flood-fill (stack). Trees are represented by 1 and emptied to 0.

    Parameters
    - grid: 2D numpy array of ints (0 = empty, 1 = tree)
    - x, y: starting coordinates (integers)
    - L: grid linear size (for bounds checking)
    - connectivity: 4 or 8 (4 = von Neumann, 8 = Moore neighborhood)

    Returns the number of trees burned (cluster size). If (x,y) is not a tree
    the function returns 0.
    """
    # If the starting site is not a tree, nothing to burn
    if grid[x, y] != 1:
        return 0

    # Choose neighbor offsets based on requested connectivity
    if connectivity == 8:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    else:
        # default: 4-neighbor (von Neumann)
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    burned_size = 0
    stack = [(x, y)]

    # Iterative flood-fill: pop positions from stack, inspect neighbors
    while stack:
        cx, cy = stack.pop()
        # If this site is not a tree (might have been cleared by earlier pop), skip
        if grid[cx, cy] != 1:
            continue
        # Burn this tree (set to empty)
        grid[cx, cy] = 0
        burned_size += 1

        # Check neighbors
        for dx, dy in neighbors:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < L and 0 <= ny < L and grid[nx, ny] == 1:
                # Mark for burning by pushing onto stack. We don't mark it here to 0
                # to avoid double-counting until popped (but an early mark is fine too).
                stack.append((nx, ny))

    return burned_size

def step(grid, fire_sizes, L, p, f):
    """
    Run a single step of the simulation.

    Parameters
    - grid: 2D numpy array of ints (0 = empty, 1 = tree)
    - fire_sizes: list of fire sizes (appended to in place: one per lightning fire, the cluster size)
    - L: grid linear size (for bounds checking)
    - p: probability of a tree growing
    - f: probability of a tree being struck by lightning
    Returns the number of trees burned (cluster size). If (x,y) is not a tree
    """
    # 1. Growth Phase: Empty sites become trees with probability p 
    empty_mask = (grid == 0)
    growth_roll = np.random.random(np.count_nonzero(empty_mask))
    # build an explicit numpy int8 array from the boolean mask to avoid analyzer warnings
    grid[empty_mask] = np.array(growth_roll < p, dtype=np.int8)

    # 2. Lightning Phase: Trees are struck with probability f [cite: 49]
    tree_indices = np.argwhere(grid == 1)
    if len(tree_indices) > 0:
        lightning_roll = np.random.random(len(tree_indices))
        strikes = tree_indices[lightning_roll < f]

        # 3. Burning Phase: Burn the whole connected cluster 
        for start_pos in strikes:
            # Re-check if site is still a tree (might have burned in this step)
            if grid[start_pos[0], start_pos[1]] == 1:
                size = burn_step(grid, start_pos[0], start_pos[1], L)
                fire_sizes.append(size)