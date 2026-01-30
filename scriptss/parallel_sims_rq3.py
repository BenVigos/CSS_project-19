"""
Parallel parameter sweep for the INHOMOGENEOUS forest-fire model.
Adapated from parallel_sims.py to support oak_ratio and p_burn_oak.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import csv
import os
from pathlib import Path
from datetime import datetime
import json
import sys

# minimal imports; import run_simulation inside worker to avoid pickling issues

def worker(outdir, params):
    """Run one INHOMOGENEOUS simulation for a given parameter set.
    """
    # Ensure the project root is on sys.path so child processes can import src
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

   
    from simulations.inhomogeneous import simulate_inhomogeneous_record
    import numpy as _np

    # Standaard parameters ophalen
    L = int(params.get('L', 64))
    p = float(params.get('p', 0.01))
    f = float(params.get('f', 0.0005))
    steps = int(params.get('steps', 500))
    param_id = params.get('param_id', '')
    run_id = params.get('run_id', '')
    
    
    oak_ratio = float(params.get('oak_ratio', 0.0))
    p_burn_oak = float(params.get('p_burn_oak', 0.3))

    
    fires, grid, records = simulate_inhomogeneous_record(
        L=L, 
        p=p, 
        f=f, 
        steps=steps, 
        oak_ratio=oak_ratio,       # New
        p_burn_oak=p_burn_oak      # Nnew
    )

    # Basic summary
    summary = {
        'L': L,
        'p': p,
        'f': f,
        'steps': steps,
        'oak_ratio': oak_ratio,       
        'p_burn_oak': p_burn_oak,     
        'param_id': param_id,
        'run_id': run_id,
        'num_fires': len(fires),
        'mean_size': float(_np.mean(fires)) if fires else 0.0,
        'max_size': int(_np.max(fires)) if fires else 0,
        'remaining_trees': int(_np.sum(grid > 0)), # Let op: >0 want 1=Den en 2=Eik
    }

    # Save per-step records to CSV
    timestamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
    # Bestandsnaam iets aangepast zodat je ziet dat het oak_ratio bevat
    perstep_fname = outdir / f"perstep_param{param_id}_oak{oak_ratio}_id{run_id}_{timestamp}.csv"
    
    try:
        with open(perstep_fname, 'w', newline='') as fh:
            writer = csv.writer(fh)
            # header
            writer.writerow(['step', 'fire_size', 'cluster distr', 'mean tree density'])
            for rec in records:
                writer.writerow([
                    rec['step'],
                    json.dumps(rec['fires']),
                    json.dumps(rec['cluster_sizes']),
                    rec['mean_density_before'],
                ])
        summary['perstep_file'] = str(perstep_fname)
    except Exception as e:
        summary['perstep_file'] = None
        summary['perstep_save_error'] = str(e)

    # Also save aggregated raw fire sizes
    raw_fname = outdir / f"fires_param{param_id}_oak{oak_ratio}_id{run_id}_{timestamp}.csv"
    try:
        with open(raw_fname, 'w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(['fire_size'])
            for s in fires:
                writer.writerow([int(s)])
        summary['raw_file'] = str(raw_fname)
    except Exception as e:
        summary['raw_file'] = None
        summary['save_error'] = str(e)

    return summary

def worker2(outdir, params):
    
    # Pad fix
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # --- HIER IS HET VERSCHIL: Importeer de SPATIAL simulatie ---
    import numpy as _np
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
    fires, grid, records, _ = simulate_spatial_record(
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

# De main functie is handig als je het script los wilt draaien, 
# maar voor jouw notebook gebruik je alleen de 'worker' hierboven.
def main():
    print("Dit script is bedoeld om vanuit een Notebook aangeroepen te worden via de 'worker' functie.")

if __name__ == '__main__':
    main()