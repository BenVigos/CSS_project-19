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

def step_inhomogeneous_spatial(grid, fire_sizes, L, p, f, oak_mask, p_burn_oak=0.3):
    """
    Stap functie die een 'oak_mask' (bodemkaart) gebruikt i.p.v. random ratio.
    """
    # Constanten
    EMPTY = 0
    PINE = 1
    OAK = 2
    
    # 1. Growth Phase
    empty_mask = (grid == EMPTY)
    num_empty = np.count_nonzero(empty_mask)
    
    if num_empty > 0:
        # Bepaal welke cellen een boom worden (tijd)
        growth_roll = np.random.random(num_empty)
        new_tree_indices_local = np.where(growth_roll < p)[0]
        
        # Vertaal naar grid coördinaten
        flat_indices = np.flatnonzero(empty_mask)
        target_indices = flat_indices[new_tree_indices_local]
        
        # --- HIER IS DE MAGIE ---
        # We kijken op de oak_mask wat voor grond hier ligt.
        # oak_mask is True (Eik) of False (Den).
        
        # Haal de bodem-waardes op voor de nieuwe bomen
        # We moeten de oak_mask ook even plat maken om te kunnen indexeren
        soil_values = oak_mask.ravel()[target_indices] 
        
        # Maak lijst met nieuwe boomsoorten
        new_trees = np.full(len(target_indices), PINE, dtype=np.int8)
        new_trees[soil_values] = OAK # Als bodem True is, wordt het Oak
        
        # Plaats in grid
        grid.ravel()[target_indices] = new_trees

    # 2. Lightning & 3. Burning (Precies hetzelfde als normaal)
    tree_indices = np.argwhere(grid > EMPTY)
    
    if len(tree_indices) > 0:
        lightning_roll = np.random.random(len(tree_indices))
        strikes = tree_indices[lightning_roll < f]

        for start_pos in strikes:
            if grid[start_pos[0], start_pos[1]] > EMPTY:
                size = burn_step_inhomogeneous(
                    grid, start_pos[0], start_pos[1], L, p_burn_oak=p_burn_oak
                )
                fire_sizes.append(size)



def _compute_cluster_sizes(grid, connectivity=4):
    """
    Hulpfunctie: Berekent de grootte van alle clusters (bomen) in het grid.
    Nodig voor de statistieken in de output.
    """
    Lx, Ly = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    clusters = []

    # Optimalisatie: Als er geen bomen zijn, stop direct
    # Let op: grid > 0 omdat we 1 (Den) en 2 (Eik) hebben
    if np.count_nonzero(grid > 0) == 0:
        return clusters

    # Buren offsets
    if connectivity == 8:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    else:
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    # Loop door het rooster
    for i in range(Lx):
        for j in range(Ly):
            # Als er een boom staat (>0) en we zijn er nog niet geweest
            if grid[i, j] > 0 and not visited[i, j]:
                size = 0
                stack = [(i, j)]
                visited[i, j] = True
                
                # Flood fill algoritme (Stack based)
                while stack:
                    cx, cy = stack.pop()
                    size += 1
                    for dx, dy in neighbors:
                        nx, ny = cx + dx, cy + dy
                        # Check buren: binnen rooster, nog niet bezocht, en is een boom (>0)
                        if 0 <= nx < Lx and 0 <= ny < Ly and not visited[nx, ny] and grid[nx, ny] > 0:
                            visited[nx, ny] = True
                            stack.append((nx, ny))
                clusters.append(size)

    return clusters