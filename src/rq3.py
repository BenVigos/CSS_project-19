import numpy as np 

EMPTY = 0
PINE = 1
OAK = 2
FIRE = 3


def burn_step_inhomogeneous(grid, x, y, L, p_burn_oak=0.3, connectivity=4, advanced_state=False):
    if grid[x, y] == EMPTY:
        return 0

    if connectivity == 8:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    else:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    burned_size = 0
    stack = [(x, y)]

    while stack:
        cx, cy = stack.pop()

        if grid[cx, cy] == EMPTY or grid[cx, cy] == FIRE:
            continue

        grid[cx, cy] = FIRE if advanced_state else EMPTY
        burned_size += 1

        for dx, dy in neighbors:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < L and 0 <= ny < L:
                cell_value = grid[nx, ny]

                if cell_value == EMPTY:
                    continue

                will_burn = False
                if cell_value == PINE:
                    will_burn = True
                elif cell_value == OAK:
                    if np.random.rand() < p_burn_oak:
                        will_burn = True
                
                if will_burn:
                    stack.append((nx, ny))
        
    return burned_size

def step_inhomogeneous(grid, fire_sizes, L, p, f, oak_ratio=0.3, p_burn_oak=0.3, advanced_state=False):
    grid[grid == FIRE] = EMPTY

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

    tree_indices = np.argwhere(grid > EMPTY)
    if len(tree_indices) > 0:
        lightning_roll = np.random.random(len(tree_indices))
        strikes = tree_indices[lightning_roll < f]
        for start_pos in strikes:
            if grid[start_pos[0], start_pos[1]] != EMPTY:
                burned_size = burn_step_inhomogeneous(
                    grid, start_pos[0], start_pos[1], L,
                    p_burn_oak=p_burn_oak, advanced_state=advanced_state
                )
                fire_sizes.append(burned_size)