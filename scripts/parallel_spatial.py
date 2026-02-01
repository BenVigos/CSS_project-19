import sys
import os
from pathlib import Path
import csv
import json
import numpy as _np

def worker2(outdir, params):
    # Pad fix
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    
    from simulations.spatial import simulate_spatial_record

    # Parameters uitlezen
    L = int(params.get('L', 256))
    p = float(params.get('p', 0.01))
    f = float(params.get('f', 0.0001))
    steps = int(params.get('steps', 5000))
    oak_ratio = float(params.get('oak_ratio', 0.3))
    p_burn_oak = float(params.get('p_burn_oak', 0.3))
    
    param_id = params.get('param_id', '')
    run_id = params.get('run_id', '')

    # Simulatie draaien
    fires, grid, records = simulate_spatial_record(
        L=L, p=p, f=f, steps=steps, 
        oak_ratio=oak_ratio, 
        p_burn_oak=p_burn_oak
    )

    # Resultaten opslaan (Summary)
    summary = {
        'L': L, 'p': p, 'f': f, 'steps': steps,
        'oak_ratio': oak_ratio,
        'p_burn_oak': p_burn_oak,
        'param_id': param_id,
        'run_id': run_id,
        'num_fires': len(fires),
        'mean_size': float(_np.mean(fires)) if fires else 0.0,
        'max_size': int(_np.max(fires)) if fires else 0,
    }

    # Ruwe brand data opslaan (Nodig voor je plots!)
    raw_fname = outdir / f"fires_spatial_p{param_id}_r{run_id}.csv"
    with open(raw_fname, 'w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['fire_size'])
        for s in fires:
            writer.writerow([int(s)])
    
    summary['raw_file'] = str(raw_fname)
    return summary