import numpy as np
from src.slimemold import generate_slime_mold_mask
from src.rq3 import step_inhomogeneous_spatial, _compute_cluster_sizes # hergebruik de cluster size functie

def simulate_spatial_record(L=256, p=0.01, f=0.0001, steps=5000, oak_ratio=0.3, p_burn_oak=0.3):
    

    oak_mask = generate_slime_mold_mask(L, oak_ratio)
    
    # B. Start Simulation
    grid = np.zeros((L, L), dtype=np.int8)
    fire_sizes = []
    records = []

    for i in range(steps):
        
        step_inhomogeneous_spatial(grid, fire_sizes, L, p, f, oak_mask, p_burn_oak)
        

        mean_density = float(np.mean(grid > 0))
        # Clusters berekenen (optioneel, kan traag zijn)
        # current_clusters = _compute_cluster_sizes(grid) 
        
        records.append({
            'step': i,
            'fires': list(fire_sizes[-1:]) if fire_sizes else [], 
            
        })
    
    return fire_sizes, grid, records, oak_mask