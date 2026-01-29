import numpy as np
import random as rnd

def burn_step(grid, x, y, L, connectivity=4, suppress=0, advanced_state=False):
    """
    Burn the entire connected cluster of trees containing (x, y) using an
    iterative flood-fill (stack). Trees are represented by 1 and emptied to 0.

    Parameters
    - grid: 2D numpy array of ints (0 = empty, 1 = tree, 2 = fire, 3 = suppressed)
    - x, y: starting coordinates (integers)
    - L: grid linear size (for bounds checking)
    - connectivity: 4 or 8 (4 = von Neumann, 8 = Moore neighborhood)
    - suppress: number of trees to replant after burning
    - advanced_state: if True, use state 2 for fire and state 3 for suppressed trees
                      if False, fire cells are set to 2 but suppressed go to 1 (default)

    Returns the number of trees burned (cluster size). If (x,y) is not a tree
    the function returns 0.
    """

    burnt_trees = set()

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

    burnt_trees.add((x, y))

    # Iterative flood-fill: pop positions from stack, inspect neighbors
    while stack:
        cx, cy = stack.pop()
        # If this site is not a tree (might have been cleared by earlier pop), skip
        if grid[cx, cy] != 1:
            continue
        # Burn this tree (set to fire state, cleared next step)
        grid[cx, cy] = 2
        burned_size += 1

        # Check neighbors
        for dx, dy in neighbors:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < L and 0 <= ny < L and grid[nx, ny] == 1:
                # Mark for burning by pushing onto stack. We don't mark it here to 0
                # to avoid double-counting until popped (but an early mark is fine too).
                stack.append((nx, ny))
                burnt_trees.add((nx, ny))

    # Suppression: replant some trees
    num_replace = np.min([burned_size, suppress])
    trees_to_replace = rnd.sample(list(burnt_trees), num_replace)

    # Use state 3 (suppressed) if advanced_state, otherwise state 1 (tree)
    replant_state = 3 if advanced_state else 1
    for coords in trees_to_replace:
        grid[coords[0], coords[1]] = replant_state

    return burned_size - num_replace

def step(grid, fire_sizes, L, p, f, suppress=0, advanced_state=False):
    """
    Run a single step of the simulation.

    Parameters
    - grid: 2D numpy array of ints (0 = empty, 1 = tree, 2 = fire, 3 = suppressed)
    - fire_sizes: list of fire sizes (appended to in place: one per lightning fire, the cluster size)
    - L: grid linear size (for bounds checking)
    - p: probability of a tree growing
    - f: probability of a tree being struck by lightning
    - suppress: number of trees to replant after burning (suppression)
    - advanced_state: if True, preserve fire (2) and suppressed (3) states for visualization
                      if False (default), only states 0 and 1 are used between steps
    """
    # 0. Clear previous fires (fire → empty) and suppressed → tree
    grid[grid == 2] = 0
    grid[grid == 3] = 1

    # 1. Growth Phase: Empty sites become trees with probability p 
    empty_mask = (grid == 0)
    growth_roll = np.random.random(np.count_nonzero(empty_mask))
    # build an explicit numpy int8 array from the boolean mask to avoid analyzer warnings
    grid[empty_mask] = np.array(growth_roll < p, dtype=np.int8)

    # 2. Lightning Phase: Trees are struck with probability f
    tree_indices = np.argwhere(grid == 1)
    if len(tree_indices) > 0:
        lightning_roll = np.random.random(len(tree_indices))
        strikes = tree_indices[lightning_roll < f]

        # 3. Burning Phase: Burn the whole connected cluster 
        for start_pos in strikes:
            # Re-check if site is still a tree (might have burned in this step)
            if grid[start_pos[0], start_pos[1]] == 1:
                size = burn_step(grid, start_pos[0], start_pos[1], L, suppress=suppress, advanced_state=advanced_state)
                fire_sizes.append(size)