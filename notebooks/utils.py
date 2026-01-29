"""Utility functions for Drossel-Schwab model experiment notebooks."""

import csv
import json
import re
from datetime import datetime
from pathlib import Path

import data
import results


# =============================================================================
# Experiment Directory Management
# =============================================================================

def create_experiment_dir(experiment_name: str) -> Path:
    """Create data/{experiment_name}/experiment_{idx}/, auto-incrementing idx."""
    base_dir = data.path(experiment_name)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    idx = 1
    while (base_dir / f"experiment_{idx}").exists():
        idx += 1
    
    outdir = base_dir / f"experiment_{idx}"
    outdir.mkdir(parents=True, exist_ok=False)
    print(f"Created experiment directory: {outdir}")
    return outdir


def get_latest_experiment_dir(experiment_name: str) -> Path:
    """Find the latest experiment directory under data/{experiment_name}/."""
    base_dir = data.path(experiment_name)
    if not base_dir.exists():
        raise FileNotFoundError(f"Base directory not found: {base_dir}")
    
    exp_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith('experiment_')]
    if not exp_dirs:
        raise FileNotFoundError(f"No experiment directories found under {base_dir}")
    
    return max(exp_dirs, key=lambda d: int(d.name.split('_')[-1])).resolve()


# =============================================================================
# Simulation Execution
# =============================================================================

def run_parallel_simulations(param_list: list, outdir: Path) -> list:
    """Run simulations in parallel. Returns list of result dicts."""
    import os
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from scripts.parallel_sims import worker
    
    max_workers = int(os.environ.get('MAX_WORKERS', multiprocessing.cpu_count()))
    print(f"Running {len(param_list)} simulations with up to {max_workers} workers...")
    
    sim_results = []
    with ProcessPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(worker, outdir, params): params for params in param_list}
        for fut in as_completed(futures):
            params = futures[fut]
            try:
                res = fut.result()
                print(f"Done: L={res['L']}, p={res['p']}, f={res['f']}, suppress={res['suppress']},"
                      f"fires={res['num_fires']}, mean={res['mean_size']:.2f}, max={res['max_size']}")
                sim_results.append(res)
            except Exception as e:
                print(f"Error for params {params}: {e}")
    
    return sim_results


def save_summary(sim_results: list, outdir: Path) -> Path:
    """Save summary CSV with all simulation results."""
    summary_file = outdir / f"summary_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}.csv"
    keys = ['L', 'p', 'f', 'steps', 'suppress', 'param_id', 'run_id', 'num_fires',
            'mean_size', 'max_size', 'remaining_trees', 'raw_file', 'perstep_file']
    
    with open(summary_file, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, keys)
        writer.writeheader()
        for r in sim_results:
            writer.writerow({k: r.get(k, '') for k in keys})
    
    print(f"Summary written to {summary_file}")
    return summary_file


# =============================================================================
# Data Loading
# =============================================================================

def load_experiment_data(exp_dir: Path) -> dict:
    """Load all per-step files from experiment directory.
    
    Returns dict: param_id -> list of {run_id, fires_all, clusters_all, density_series}
    """
    perstep_files = sorted(exp_dir.glob('perstep_param*_*.csv'))
    print(f"Found {len(perstep_files)} per-step files in {exp_dir}")
    
    pattern = re.compile(r'perstep_param(?P<param>\d+)_.*_id(?P<run>\d+)_')
    runs_by_param = {}
    
    for fp in perstep_files:
        m = pattern.search(fp.name)
        if not m:
            continue
        
        pid, rid = int(m.group('param')), int(m.group('run'))
        
        # Load and aggregate data
        fires_all, clusters_all, density_series = [], [], []
        with open(fp, newline='') as fh:
            reader = csv.reader(fh)
            next(reader, None)  # skip header
            for row in reader:
                if not row:
                    continue
                fires_all.extend(json.loads(row[1]) if row[1] else [])
                clusters_all.extend(json.loads(row[2]) if row[2] else [])
                density_series.append(float(row[3]) if row[3] else None)
        
        runs_by_param.setdefault(pid, []).append({
            'run_id': rid,
            'fires_all': fires_all,
            'clusters_all': clusters_all,
            'density_series': density_series
        })
    
    print(f"Loaded runs for param_ids: {sorted(runs_by_param.keys())}")
    return runs_by_param


def load_summary_map(exp_dir: Path) -> dict:
    """Load param_id -> {L, p, f} mapping from summary file."""
    summary_map = {}
    summaries = list(exp_dir.glob('summary_*.csv'))
    if not summaries:
        return summary_map
    
    latest = max(summaries, key=lambda p: p.stat().st_mtime)
    with open(latest, newline='') as fh:
        for row in csv.DictReader(fh):
            try:
                pid = int(row.get('param_id', ''))
                summary_map[pid] = {'L': row.get('L', ''), 'p': row.get('p', ''), 'f': row.get('f', '')}
            except (ValueError, TypeError):
                continue
    return summary_map


# =============================================================================
# Plotting Functions
# =============================================================================

def _make_label(pid: int, summary_map: dict = None) -> str:
    """Generate label for a parameter id."""
    if summary_map and pid in summary_map:
        sm = summary_map[pid]
        return f"L={sm['L']}, p={sm['p']}, f={sm['f']}"
    return f'param {pid}'


def plot_size_distribution(runs_by_param: dict, data_key: str = 'fires_all',
                           summary_map: dict = None, title: str = "Size Distribution",
                           xlabel: str = "Size", save_path: Path = None):
    """Plot log-log size distribution. data_key is 'fires_all' or 'clusters_all'."""
    import numpy as np
    import matplotlib.pyplot as plt
    
    # Collect all data for global bins
    all_data = []
    for runs in runs_by_param.values():
        for r in runs:
            all_data.extend(r[data_key])
    
    if not all_data:
        print(f"No {data_key} recorded")
        return
    
    all_data = np.array(all_data)
    bins = np.logspace(np.log10(max(1, all_data.min())), np.log10(all_data.max()), num=25)
    
    plt.figure(figsize=(10, 6))
    for pid in sorted(runs_by_param.keys()):
        agg = np.concatenate([np.array(r[data_key]) for r in runs_by_param[pid] if r[data_key]])
        if agg.size == 0:
            continue
        
        hist, edges = np.histogram(agg, bins=bins, density=True)
        centers = np.sqrt(edges[:-1] * edges[1:])
        mask = hist > 0
        plt.loglog(centers[mask], hist[mask], 'o-', label=_make_label(pid, summary_map))
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel('Probability density')
    plt.legend(fontsize='small')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved plot to {save_path}")
    plt.show()


def plot_fire_size_distribution(runs_by_param: dict, summary_map: dict = None,
                                 title: str = "Fire Size Distribution", save_path: Path = None):
    """Plot fire size distribution (log-log)."""
    plot_size_distribution(runs_by_param, 'fires_all', summary_map, title, 'Fire size', save_path)


def plot_cluster_size_distribution(runs_by_param: dict, summary_map: dict = None,
                                    title: str = "Cluster Size Distribution", save_path: Path = None):
    """Plot cluster size distribution (log-log)."""
    plot_size_distribution(runs_by_param, 'clusters_all', summary_map, title, 'Cluster size', save_path)


def plot_density_timeseries(runs_by_param: dict, summary_map: dict = None,
                            title: str = "Tree Density Over Time", save_path: Path = None):
    """Plot mean tree density over time, averaged across runs per parameter."""
    import numpy as np
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(10, 5))
    
    maxlen_global = 0
    param_series = {}
    
    for pid in sorted(runs_by_param.keys()):
        densities = [np.array(r['density_series'], dtype=float) 
                     for r in runs_by_param[pid] if r['density_series']]
        if not densities:
            continue
        
        maxlen = max(arr.size for arr in densities)
        maxlen_global = max(maxlen_global, maxlen)
        stacked = np.vstack([np.pad(arr, (0, maxlen - arr.size), constant_values=np.nan) 
                             for arr in densities])
        param_series[pid] = np.nanmean(stacked, axis=0)
    
    for pid, series in param_series.items():
        s = np.pad(series, (0, maxlen_global - series.size), constant_values=np.nan)
        plt.plot(np.arange(maxlen_global), s, label=_make_label(pid, summary_map))
    
    plt.xlabel('Step')
    plt.ylabel('Mean tree density')
    plt.title(title)
    plt.legend(fontsize='small', loc='best')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved plot to {save_path}")
    plt.show()
