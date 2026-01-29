import numpy as np
from src.rq3 import burn_step_inhomogeneous, step_inhomogeneous 



def _compute_cluster_sizes(grid, connectivity=4):
    Lx, Ly = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    clusters = []

    if np.count_nonzero(grid > 0) == 0: # Let op: > 0 want 1=Den, 2=Eik
        return clusters

    # neighbor offsets
    if connectivity == 8:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    else:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    for i in range(Lx):
        for j in range(Ly):
            # We kijken of er een boom staat (grid > 0)
            if grid[i, j] > 0 and not visited[i, j]:
                size = 0
                stack = [(i, j)]
                visited[i, j] = True
                while stack:
                    cx, cy = stack.pop()
                    size += 1
                    for dx, dy in neighbors:
                        nx, ny = cx + dx, cy + dy
                        # Check of buurman ook een boom is (> 0)
                        if 0 <= nx < Lx and 0 <= ny < Ly and not visited[nx, ny] and grid[nx, ny] > 0:
                            visited[nx, ny] = True
                            stack.append((nx, ny))
                clusters.append(size)
    return clusters


def simulate_inhomogeneous_record(L=128, p=0.01, f=0.0001, steps=1000, oak_ratio=0.3, p_burn_oak=0.3):
    """
    Run inhomogeneous forest fire simulation and return aggregated fires + final grid + per-step records.
    """
    
    # Constants
    EMPTY = 0
    PINE = 1
    OAK = 2

    grid = np.zeros((L, L), dtype=np.int8)
    fire_sizes = [] # Total overview of all fires
    records = []    # Per-step records

    for i in range(steps):
        
        empty_mask = (grid == EMPTY)
        num_empty = np.count_nonzero(empty_mask)
        
        if num_empty > 0:
            growth_roll = np.random.random(num_empty)
            new_tree_indices = np.where(growth_roll < p)[0]
            
                
            new_values = np.full(len(new_tree_indices), PINE, dtype=np.int8)
            type_roll = np.random.random(len(new_tree_indices))
            new_values[type_roll < oak_ratio] = OAK
            
                
            flat_indices = np.flatnonzero(empty_mask)
            grid.ravel()[flat_indices[new_tree_indices]] = new_values

        
        mean_density_before = float(np.mean(grid > 0))

       
        tree_indices = np.argwhere(grid > 0) # Alles wat boom is
        step_fires = []
        
        if len(tree_indices) > 0:
            lightning_roll = np.random.random(len(tree_indices))
            strikes = tree_indices[lightning_roll < f]

            
            for start_pos in strikes:
                if grid[start_pos[0], start_pos[1]] > 0:
                    # Gebruik jouw NIEUWE inhomogene burn functie
                    size = burn_step_inhomogeneous(
                        grid, 
                        start_pos[0], start_pos[1], 
                        L, 
                        p_burn_oak=p_burn_oak
                    )
                    step_fires.append(size)
                    fire_sizes.append(size)

        
        current_clusters = _compute_cluster_sizes(grid)

        
        records.append({
            'step': i,
            'fires': list(step_fires),
            'cluster_sizes': list(current_clusters),
            'mean_density_before': mean_density_before,
            'oak_ratio': oak_ratio 
        })

    return fire_sizes, grid, records


def simulate_inhomogeneous_steps(
    L=128,
    p=0.01,
    f=0.0001,
    steps=1000,
    oak_ratio=0.3,
    p_burn_oak=0.3,
    advanced_state=False,
    initial_grid=None,
    initial_fire_sizes=None,
    start_step=0,
):
    """Yield (grid, fire_sizes, step_index) after each simulation step for live UI updates."""
    if initial_grid is not None and initial_fire_sizes is not None:
        grid = np.array(initial_grid, dtype=np.int8, copy=True)
        fire_sizes = list(initial_fire_sizes)
        step_range = range(start_step, steps)
    else:
        grid = np.zeros((L, L), dtype=np.int8)
        fire_sizes = []
        step_range = range(steps)

    for i in step_range:
        step_inhomogeneous(
            grid, fire_sizes, L, p, f,
            oak_ratio=oak_ratio, p_burn_oak=p_burn_oak, advanced_state=advanced_state,
        )
        yield np.copy(grid), list(fire_sizes), i + 1
