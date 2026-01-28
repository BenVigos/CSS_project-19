import numpy as np 

EMPTY = 0
PINE = 1
OAK = 2

def burn_step_inhomogeneous(grid, x, y, L, p_burn_oak=0.3, connectivity=4):

    if grid[x,y] == EMPTY:
        return 0
    
    if connectivity == 8:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    else:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    
    burned_size = 0
    stack = [(x, y)]


    while stack:
        cx, cy = stack.pop()

        if grid[cx, cy] == EMPTY:
            continue

      
        grid[cx, cy] = EMPTY
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

def step_inhomogeneous(grid, fire_sizes, L, p, f, oak_ratio=0.3, p_burn_oak=0.3):

    empty_mask = (grid == EMPTY)
    num_empty = np.count_nonzero(empty_mask)

    if num_empty > 0:
        # Stap A: Bepaal WELKE cellen een boom worden
        growth_roll = np.random.random(num_empty)
        new_tree_indices = np.where(growth_roll < p)[0] # Indices binnen de empty_mask selectie
        
        # Stap B: Bepaal welk TYPE boom het wordt voor de nieuwe bomen
        # We maken eerst alles PINE (1)
        new_values = np.full(len(new_tree_indices), PINE, dtype=np.int8)
        
        # Nu gooien we voor deze nieuwe bomen nog een keer om te kijken of het OAK (2) wordt
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
                    burned_size = burn_step_inhomogeneous(grid, start_pos[0], start_pos[1], L, p_burn_oak)
                    fire_sizes.append(burned_size)
                