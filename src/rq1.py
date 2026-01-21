import numpy as np

def burn_cluster(grid, x, y, L):
    """
    Uses a stack-based flood fill to burn the connected tree cluster.
    Trees (1) become empty sites (0).
    """
    stack = [(x, y)]
    grid[x, y] = 0
    burned_size = 1
    
    while len(stack) > 0:
        cx, cy = stack.pop()
        # Check 4-nearest neighbors (nearest-neighbor coupling)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < L and 0 <= ny < L:
                if grid[nx, ny] == 1:
                    grid[nx, ny] = 0
                    burned_size += 1
                    stack.append((nx, ny))
    return burned_size

def run_simulation(L=128, p=0.01, f=0.0001, steps=1000):
    # grid: 0 = empty, 1 = tree [cite: 47]
    grid = np.zeros((L, L), dtype=np.int8)
    fire_sizes = []

    for _ in range(steps):
        # 1. Growth Phase: Empty sites become trees with probability p 
        empty_mask = (grid == 0)
        growth_roll = np.random.random(np.count_nonzero(empty_mask))
        grid[empty_mask] = (growth_roll < p).astype(np.int8)

        # 2. Lightning Phase: Trees are struck with probability f [cite: 49]
        tree_indices = np.argwhere(grid == 1)
        if len(tree_indices) > 0:
            lightning_roll = np.random.random(len(tree_indices))
            strikes = tree_indices[lightning_roll < f]

            # 3. Burning Phase: Burn the whole connected cluster 
            for start_pos in strikes:
                # Re-check if site is still a tree (might have burned in this step)
                if grid[start_pos[0], start_pos[1]] == 1:
                    size = burn_cluster(grid, start_pos[0], start_pos[1], L)
                    fire_sizes.append(size)

    return fire_sizes, grid