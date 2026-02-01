import numpy as np
from scipy.ndimage import gaussian_filter

def generate_slime_mold_mask(L, ratio, steps=300):
    """
    Generates a binary mask (L x L) based on a Slime Mold simulation.
    - True (1) = Position for an Oak (the veins of the slime mold)
    - False (0) = Position for a Pine
    
    The function ensures that EXACTLY 'ratio' percent of the board is True.
    """
    # Settings for Physarum (The Intelligent Settings)
    num_agents = int(L * L * 0.15) # Iets meer agents voor betere verbindingen
    
    # Sensor instellingen (Dit bepaalt de 'intelligentie')
    sensor_angle = np.pi / 2   # 45 graden kijkhoek
    sensor_dist = 9.0          # Hoe ver kijken ze vooruit?
    turn_angle = np.pi / 2     # Hoe scherp kunnen ze draaien?
    
    # 1. Initialization
    agents_x = np.random.rand(num_agents) * L
    agents_y = np.random.rand(num_agents) * L
    agents_angle = np.random.rand(num_agents) * 2 * np.pi
    trail_map = np.zeros((L, L))
    
    # 2. Simulation Loop
    for _ in range(steps):
        # A. Movement
        agents_x += np.cos(agents_angle)
        agents_y += np.sin(agents_angle)
        
        # Wrap around (torus world)
        agents_x %= L
        agents_y %= L
        
        # B. Deposit (Leave trail)
        ix = agents_x.astype(int)
        iy = agents_y.astype(int)
        np.add.at(trail_map, (ix, iy), 1.0)
        
        # C. Diffuse & Decay (Scherpere settings voor aders)
        # sigma: 0.8 -> 0.6 (Minder blur)
        # decay: 0.95 -> 0.92 (Oude paden verdwijnen sneller)
        trail_map = gaussian_filter(trail_map, sigma=0.5) * 0.90
        
        # D. Sense & Rotate (The Advanced Logic)
        
        # 1. Bereken posities van de 3 sensoren (Links, Midden, Rechts)
        angle_L = agents_angle - sensor_angle
        angle_C = agents_angle
        angle_R = agents_angle + sensor_angle
        
        # Coördinaten berekenen + Wrap around (% L)
        # We moeten dit omzetten naar integers om in de map te kijken
        xL = (agents_x + np.cos(angle_L) * sensor_dist) % L
        yL = (agents_y + np.sin(angle_L) * sensor_dist) % L
        
        xC = (agents_x + np.cos(angle_C) * sensor_dist) % L
        yC = (agents_y + np.sin(angle_C) * sensor_dist) % L
        
        xR = (agents_x + np.cos(angle_R) * sensor_dist) % L
        yR = (agents_y + np.sin(angle_R) * sensor_dist) % L
        
        # 2. Ruiken: Wat is de waarde op die plekken?
        val_L = trail_map[xL.astype(int), yL.astype(int)]
        val_C = trail_map[xC.astype(int), yC.astype(int)]
        val_R = trail_map[xR.astype(int), yR.astype(int)]
        
        # 3. Sturen (Vectorized logic)
        
        # Conditie: Links is het sterkst -> Draai Links
        mask_left = (val_L > val_C) & (val_L > val_R)
        agents_angle[mask_left] -= turn_angle
        
        # Conditie: Rechts is het sterkst -> Draai Rechts
        mask_right = (val_R > val_C) & (val_R > val_L)
        agents_angle[mask_right] += turn_angle
        
        # Als Midden het sterkst is, doen we niks (rechtdoor).
        
        # Altijd een heel klein beetje willekeur toevoegen zodat ze niet vastlopen
        agents_angle += (np.random.rand(num_agents) - 0.5) * 0.5

    # 3. Thresholding
    flattened = trail_map.flatten()
    threshold_value = np.percentile(flattened, 100 - (ratio * 100))
    
    # Return binary mask (zoals je simulatie verwacht)
    oak_mask = trail_map > threshold_value
    
    return oak_mask