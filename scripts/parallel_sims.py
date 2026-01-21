"""Parallel parameter sweep for the forest-fire model.

Each parameter set runs a separate process which calls `run_simulation` from src.rq1
and returns summary statistics and optionally saves the raw fire-size list.

Usage (example):
    python scripts/parallel_sims.py

This will run a small demo sweep. To customize, edit the PARAMS list or add CLI
argument parsing.
"""
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import csv
import os
from pathlib import Path
from datetime import datetime

# minimal imports; import run_simulation inside worker to avoid pickling issues

OUTDIR = Path("results")
OUTDIR.mkdir(exist_ok=True)


def worker(params):
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
    from src.rq1 import run_simulation
    import numpy as _np

    L = int(params.get('L', 64))
    p = float(params.get('p', 0.01))
    f = float(params.get('f', 0.0005))
    steps = int(params.get('steps', 500))
    run_id = params.get('run_id', '')

    fires, grid = run_simulation(L=L, p=p, f=f, steps=steps)

    # Basic summary
    summary = {
        'L': L,
        'p': p,
        'f': f,
        'steps': steps,
        'run_id': run_id,
        'num_fires': len(fires),
        'mean_size': float(_np.mean(fires)) if fires else 0.0,
        'max_size': int(_np.max(fires)) if fires else 0,
        'remaining_trees': int(_np.sum(grid == 1)),
    }

    # Save raw fire sizes for this run to a csv file
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    fname = OUTDIR / f"fires_L{L}_p{p}_f{f}_steps{steps}_id{run_id}_{timestamp}.csv"
    try:
        with open(fname, 'w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(['fire_size'])
            for s in fires:
                writer.writerow([int(s)])
        summary['raw_file'] = str(fname)
    except Exception as e:
        summary['raw_file'] = None
        summary['save_error'] = str(e)

    return summary


def main():
    # Example parameter sweep: small demo grid. Replace with your actual sweep.
    param_list = []
    run_idx = 0
    L = 100
    steps = 1000

    # vary p and f in a few combinations (one simulation per tuple)
    p_values = [0.005, 0.01]
    f_values = [0.0001, 0.0005, 0.001]

    for p in p_values:
        for f in f_values:
            run_idx += 1
            param_list.append({'L': L, 'p': p, 'f': f, 'steps': steps, 'run_id': run_idx})

    # Allow overriding number of workers via environment variable (or use CPU count)
    max_workers = int(os.environ.get('MAX_WORKERS', multiprocessing.cpu_count()))
    print(f"Running {len(param_list)} simulations with up to {max_workers} workers...")

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(worker, params): params for params in param_list}
        for fut in as_completed(futures):
            params = futures[fut]
            try:
                res = fut.result()
                print(f"Done: p={res['p']}, f={res['f']}, fires={res['num_fires']}, mean={res['mean_size']:.2f}, max={res['max_size']}")
                results.append(res)
            except Exception as e:
                print(f"Error for params {params}: {e}")

    # Write a summary CSV
    summary_file = OUTDIR / f"summary_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
    keys = ['L', 'p', 'f', 'steps', 'run_id', 'num_fires', 'mean_size', 'max_size', 'remaining_trees', 'raw_file']
    with open(summary_file, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, keys)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, '') for k in keys})

    print(f"Summary written to {summary_file}")


if __name__ == '__main__':
    main()
