import numpy as np

from src.drosselschwab import step, burn_step


def _compute_cluster_sizes(grid, connectivity=4):
    """Compute sizes of connected tree clusters (value==1) in grid without modifying it.
    Uses iterative flood-fill (stack/DFS) and returns a list of cluster sizes.
    """
    Lx, Ly = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    clusters = []

    if np.count_nonzero(grid == 1) == 0:
        return clusters

    # neighbor offsets
    if connectivity == 8:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    else:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    for i in range(Lx):
        for j in range(Ly):
            if grid[i, j] == 1 and not visited[i, j]:
                # start new cluster
                size = 0
                stack = [(i, j)]
                visited[i, j] = True
                while stack:
                    cx, cy = stack.pop()
                    size += 1
                    for dx, dy in neighbors:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < Lx and 0 <= ny < Ly and not visited[nx, ny] and grid[nx, ny] == 1:
                            visited[nx, ny] = True
                            stack.append((nx, ny))
                clusters.append(size)

    return clusters


def simulate_drosselschwab_record(L=10, p=0.05, f=0.001, steps=500, connectivity=4, suppress=0):
    """Run simulation and return aggregated fires + final grid + per-step records.

    Returns (fire_sizes, grid, records) where records is a list of dicts per step:
    {'step': i, 'fires': [s1,s2,...], 'cluster_sizes': [c1,c2,...], 'mean_density_before': d}
    """
    grid = np.zeros((L, L), dtype=np.int8)
    fire_sizes = []
    records = []

    for i in range(steps):
        # Growth phase occurs inside step(); but we need mean density BEFORE burning which is after growth
        # To capture that, we replicate the growth portion here and then perform lightning/burning similar to step()
        # 1. Growth Phase: Empty sites become trees with probability p
        empty_mask = (grid == 0)
        growth_roll = np.random.random(np.count_nonzero(empty_mask))
        grid[empty_mask] = np.array(growth_roll < p, dtype=np.int8)

        # mean tree density before lightning/burning
        mean_density_before = float(np.mean(grid == 1))

        # 2. Lightning Phase: Trees are struck with probability f
        tree_indices = np.argwhere(grid == 1)
        step_fires = []
        if len(tree_indices) > 0:
            lightning_roll = np.random.random(len(tree_indices))
            strikes = tree_indices[lightning_roll < f]

            # 3. Burning Phase: Burn the whole connected cluster
            for start_pos in strikes:
                if grid[start_pos[0], start_pos[1]] == 1:
                    # cast to plain int to avoid numpy scalar serialization issues
                    size = int(burn_step(grid, start_pos[0], start_pos[1], L, connectivity=connectivity, suppress=suppress))
                    step_fires.append(size)
                    fire_sizes.append(size)

        # After burning, compute cluster sizes of remaining trees
        cluster_sizes = _compute_cluster_sizes(grid, connectivity=connectivity)

        # ensure cluster sizes are plain ints for JSON/CSV serialization
        cluster_sizes = [int(c) for c in cluster_sizes]

        records.append({
            'step': int(i),
            'fires': list(step_fires),
            'cluster_sizes': list(cluster_sizes),
            'mean_density_before': mean_density_before,
        })

    return fire_sizes, grid, records


# keep existing API for backwards compatibility

def simulate_drosselschwab(L=10, p=0.05, f=0.001, steps=500):
    grid = np.zeros((L, L), dtype=np.int8)
    fire_sizes = []

    for _ in range(steps):
        step(grid, fire_sizes, L, p, f)

    return fire_sizes, grid


def simulate_drosselschwab_steps(
    L=10, p=0.05, f=0.001, steps=500, suppress=0, advanced_state=False,
    initial_grid=None, initial_fire_sizes=None, start_step=0,
):
    """Yield (grid, fire_sizes, step_index) after each simulation step for live UI updates.

    fire_sizes is a single list for the whole run; step() appends to it in place
    on each lightning strike (one entry per fire = cluster size). It therefore
    grows across steps. Each yield returns a snapshot list(fire_sizes).

    If initial_grid and initial_fire_sizes are provided, continue from that state
    for steps start_step+1 .. steps (start_step is the step index already reached).
    """
    if initial_grid is not None and initial_fire_sizes is not None:
        grid = np.array(initial_grid, dtype=np.int8, copy=True)
        fire_sizes = list(initial_fire_sizes)
        step_range = range(start_step, steps)
    else:
        grid = np.zeros((L, L), dtype=np.int8)
        fire_sizes = []
        step_range = range(steps)

    for i in step_range:
        step(grid, fire_sizes, L, p, f, suppress=suppress, advanced_state=advanced_state)
        yield np.copy(grid), list(fire_sizes), i + 1
