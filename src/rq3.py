import numpy as np
from scipy.ndimage import label

#Variable definitions
EMPTY = 0
PINE = 1
OAK = 2
FIRE = 3

def burn_step_inhomogeneous(grid, x, y, L, p_burn_oak=0.3, connectivity=4, advanced_state=False):
    """
    Berekent de brandgrootte met een STACK (Iteratief).
    Dit is veiliger dan recursie voor grote grids (voorkomt RecursionError).
    """
    # Check startconditie
    if x < 0 or x >= L or y < 0 or y >= L:
        return 0
    if grid[x, y] == EMPTY or grid[x, y] == FIRE:
        return 0

    if connectivity == 8:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    else:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    burned_size = 0
    stack = [(x, y)]

    while stack:
        cx, cy = stack.pop()

        # Check of we deze cel nog moeten verwerken
        val = grid[cx, cy]
        if val == EMPTY or val == FIRE:
            continue
        
        # Check Oak weerstand
        if val == OAK:
            if np.random.rand() > p_burn_oak:
                continue # Eik weigert te branden

        # Steek aan
        grid[cx, cy] = FIRE if advanced_state else EMPTY
        burned_size += 1

        # Voeg buren toe aan stack
        for dx, dy in neighbors:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < L and 0 <= ny < L:
                cell_value = grid[nx, ny]
                
                # Voeg alleen toe als het brandbaar is (PINE of OAK)
                if cell_value == PINE or cell_value == OAK:
                    stack.append((nx, ny))
        
    return burned_size

def step_inhomogeneous(grid, fire_sizes, L, p, f, oak_ratio=0.3, p_burn_oak=0.3, advanced_state=False):
    """
    Standaard Random Model (Hagelslag).
    """
    grid[grid == FIRE] = EMPTY

    empty_mask = (grid == EMPTY)
    num_empty = np.count_nonzero(empty_mask)

    # 1. Groei
    if num_empty > 0:
        growth_roll = np.random.random(num_empty)
        new_tree_indices = np.where(growth_roll < p)[0]
        new_values = np.full(len(new_tree_indices), PINE, dtype=np.int8)
        type_roll = np.random.random(len(new_tree_indices))
        new_values[type_roll < oak_ratio] = OAK
        flat_indices = np.flatnonzero(empty_mask)
        grid.ravel()[flat_indices[new_tree_indices]] = new_values

    # 2. Bliksem
    tree_indices = np.argwhere(grid > EMPTY)
    if len(tree_indices) > 0:
        lightning_roll = np.random.random(len(tree_indices))
        strikes = tree_indices[lightning_roll < f]
        for start_pos in strikes:
            if grid[start_pos[0], start_pos[1]] != EMPTY:
                # FIX: Zet NIET eerst op FIRE, laat de functie dat doen!
                burned_size = burn_step_inhomogeneous(
                    grid, start_pos[0], start_pos[1], L,
                    p_burn_oak=p_burn_oak, advanced_state=advanced_state
                )
                fire_sizes.append(burned_size)

def step_inhomogeneous_spatial(grid, fire_sizes, L, p, f, oak_mask, p_burn_oak=0.3, advanced_state=False):
    """
    Slime Mold Model (Spatial).
    """
    grid[grid == FIRE] = EMPTY

    # 1. Groei
    empty_mask = (grid == EMPTY)
    num_empty = np.count_nonzero(empty_mask)

    if num_empty > 0:
        growth_roll = np.random.random(num_empty)
        new_tree_indices_flat = np.where(growth_roll < p)[0]
        flat_indices_all = np.flatnonzero(empty_mask)
        grow_indices_flat = flat_indices_all[new_tree_indices_flat]
        grow_x, grow_y = np.unravel_index(grow_indices_flat, (L, L))
        is_oak = oak_mask[grow_x, grow_y]
        grid[grow_x, grow_y] = np.where(is_oak, OAK, PINE)

    # 2. Bliksem
    tree_indices = np.argwhere(grid > EMPTY)
    if len(tree_indices) > 0:
        lightning_roll = np.random.random(len(tree_indices))
        strikes = tree_indices[lightning_roll < f]
        
        for start_pos in strikes:
            if grid[start_pos[0], start_pos[1]] != EMPTY:
                # FIX: Zet NIET eerst op FIRE, laat de functie dat doen!
                burned_size = burn_step_inhomogeneous(
                    grid, start_pos[0], start_pos[1], L,
                    p_burn_oak=p_burn_oak, advanced_state=advanced_state
                )
                fire_sizes.append(burned_size)

def _compute_cluster_sizes(grid):
    """Helper voor statistieken."""
    tree_mask = grid != 0
    structure = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    labeled_array, num_features = label(tree_mask, structure=structure)
    if num_features == 0:
        return np.array([])
    return np.bincount(labeled_array.ravel())[1:]