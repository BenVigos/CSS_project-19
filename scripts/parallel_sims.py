"""Parallel parameter sweep for the forest-fire model.

Each parameter set runs a separate process which calls `run_simulation` from src.rq1
and returns summary statistics and optionally saves the raw fire-size list.

Usage (example):
    python scripts/parallel_sims.py

This will run a small demo sweep. To customize, edit the PARAMS list or add CLI
argument parsing.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import csv
import os
from pathlib import Path
from datetime import datetime

# minimal imports; import run_simulation inside worker to avoid pickling issues

def worker(outdir, params):
    """Run one simulation for a given parameter set.

    params: dict-like with keys 'L','p','f','steps','run_id'
    Returns a result dict with summary stats. Also writes the raw fires to a file.
    """
    # Ensure the project root is on sys.path so child processes can import src
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Import inside worker to ensure child processes can import the module
    from simulations.drosselschwab import simulate_drosselschwab_record
    import numpy as _np

    L = int(params.get('L', 64))
    p = float(params.get('p', 0.01))
    f = float(params.get('f', 0.0005))
    steps = int(params.get('steps', 500))
    param_id = params.get('param_id', '')
    run_id = params.get('run_id', '')
    connectivity = params.get('connectivity', 4)

    # Run the record-enabled simulation
    fires, grid, records = simulate_drosselschwab_record(L=L, p=p, f=f, steps=steps, connectivity=connectivity)

    # Basic summary
    summary = {
        'L': L,
        'p': p,
        'f': f,
        'steps': steps,
        'param_id': param_id,
        'run_id': run_id,
        'num_fires': len(fires),
        'mean_size': float(_np.mean(fires)) if fires else 0.0,
        'max_size': int(_np.max(fires)) if fires else 0,
        'remaining_trees': int(_np.sum(grid == 1)),
    }

    # Save per-step records to CSV (requested format)
    import json
    timestamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
    perstep_fname = outdir / f"perstep_param{param_id}_L{L}_p{p}_f{f}_steps{steps}_id{run_id}_{timestamp}.csv"
    try:
        with open(perstep_fname, 'w', newline='') as fh:
            writer = csv.writer(fh)
            # header must exactly match the requested format
            writer.writerow(['step', 'fire_size', 'cluster distr', 'mean tree density'])
            for rec in records:
                # serialize lists as JSON strings for safety and easy parsing
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

    # Also save aggregated raw fire sizes (legacy behavior)
    raw_fname = outdir / f"fires_param{param_id}_L{L}_p{p}_f{f}_steps{steps}_id{run_id}_{timestamp}.csv"
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


def main():
    parser = argparse.ArgumentParser(
        description="Parallel parameter sweep for forest-fire model.")

    parser.add_argument("--L", type=int, default=256,
                        help="Linear system size")
    parser.add_argument("--steps", type=int, default=10000,
                        help="Number of simulation steps")

    parser.add_argument("--p", type=float, nargs="+", default=[0.01],
                        help="List of tree growth probabilities")
    parser.add_argument("--f", type=float, nargs="+", default=[0.001],
                        help="List of lightning probabilities")
    parser.add_argument("--replicates", type=int, default=100,
                        help="Number of runs per (p,f) parameter set")
    parser.add_argument("--processes", type=int, default=None,
                        help="Number of parallel processes (default: cpu count)")
    parser.add_argument(
    "--name",
    type=str,
    default=None,
    help="Name of the experiment"
    )

    args = parser.parse_args()

    # Create experiments root under project/data/f_over_p and pick the next available experiment index
    project_root = Path(__file__).resolve().parent.parent
    base_dir = (project_root / "data" / args.name)
    base_dir.mkdir(parents=True, exist_ok=True)

    # Find lowest available experiment index starting from 1
    idx = 1
    while (base_dir / f"experiment_{idx}").exists():
        idx += 1
    outdir = base_dir / f"experiment_{idx}"
    outdir.mkdir(parents=True, exist_ok=False)
    print(f"Saving results to experiment directory: {outdir}")

    # Example parameter sweep: small demo grid. Replace with your actual sweep.
    L = args.L
    steps = args.steps
    p_values = args.p
    f_values = args.f
    replicates = args.replicates

    param_list = []
    run_idx = 0
    param_idx = 0

    for p in p_values:
        for f in f_values:
            param_idx += 1
            run_idx += 1
            param_list.append({
                    "param_id": param_idx,
                    "run_id": run_idx,
                    "L": L,
                    "p": p,
                    "f": f,
                    "steps": steps,
                })

    # Allow overriding number of workers via environment variable (or use CPU count)
    max_workers = int(os.environ.get('MAX_WORKERS', multiprocessing.cpu_count()))
    print(f"Running {len(param_list)} simulations with up to {max_workers} workers...")

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as exe:
        # worker now expects (outdir, params) as its arguments
        futures = {exe.submit(worker, outdir, params): params for params in param_list}
        for fut in as_completed(futures):
            params = futures[fut]
            try:
                res = fut.result()
                print(f"Done: p={res['p']}, f={res['f']}, fires={res['num_fires']}, mean={res['mean_size']:.2f}, max={res['max_size']}")
                results.append(res)
            except Exception as e:
                print(f"Error for params {params}: {e}")

    # Write a summary CSV
    summary_file = outdir / f"summary_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}.csv"
    keys = ['L', 'p', 'f', 'steps', 'param_id', 'run_id', 'num_fires', 'mean_size', 'max_size', 'remaining_trees', 'raw_file', 'perstep_file']
    with open(summary_file, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, keys)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, '') for k in keys})

    print(f"Summary written to {summary_file}")


if __name__ == '__main__':
    main()
