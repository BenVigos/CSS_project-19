import json
import csv
import re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Determine project root reliably (parent of this scripts folder)
project_root = Path(__file__).resolve().parent.parent
base_dir = (project_root / "data" / "f_over_p").resolve()
if not base_dir.exists():
    raise FileNotFoundError(f"Base data directory not found: {base_dir}")
exp_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith('experiment_')]
if not exp_dirs:
    raise FileNotFoundError(f"No experiment directories found under {base_dir}")

def _exp_index(d):
    try:
        return int(d.name.split('_')[-1])
    except Exception:
        return -1

exp_dirs_sorted = sorted(exp_dirs, key=_exp_index)
EXP_DIR = exp_dirs_sorted[-1].resolve()
print('Experiment dir:', EXP_DIR)

# find perstep files created by the worker
perstep_files = sorted(EXP_DIR.glob('perstep_param*_*.csv'))
print(f'Found {len(perstep_files)} per-step files')

pattern = re.compile(r'perstep_param(?P<param>\d+)_.*_id(?P<run>\d+)_')


def load_perstep_file(fp):
    records = []
    with open(fp, newline='') as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            return records
        for row in reader:
            if not row:
                continue
            step = int(row[0])
            fires = json.loads(row[1]) if row[1] else []
            clusters = json.loads(row[2]) if row[2] else []
            density = float(row[3]) if row[3] != '' else None
            records.append({'step': step, 'fires': fires, 'clusters': clusters, 'density': density})
    return records

runs_by_param = {}
for fp in perstep_files:
    m = pattern.search(fp.name)
    if not m:
        print('Skipping unknown file pattern:', fp.name)
        continue
    pid = int(m.group('param'))
    rid = int(m.group('run'))
    recs = load_perstep_file(fp)
    fires_all = []
    clusters_all = []
    density_series = []
    for r in recs:
        fires_all.extend(r['fires'])
        clusters_all.extend(r['clusters'])
        density_series.append(r['density'])
    runs_by_param.setdefault(pid, []).append({'run_id': rid, 'file': fp, 'records': recs, 'fires_all': fires_all, 'clusters_all': clusters_all, 'density_series': density_series})

print('Loaded runs for param_ids:', sorted(runs_by_param.keys()))

# create plots dir
plots_dir = EXP_DIR / 'plots'
plots_dir.mkdir(parents=True, exist_ok=True)

# Fire-size distributions per param_id per run
for pid in sorted(runs_by_param.keys()):
    runs = runs_by_param[pid]
    all_fs = np.concatenate([np.array(r['fires_all']) for r in runs if len(r['fires_all']) > 0]) if any(len(r['fires_all'])>0 for r in runs) else np.array([])
    if all_fs.size == 0:
        print(f'param {pid}: no fires')
        continue
    min_s = max(1, int(all_fs.min()))
    max_s = int(all_fs.max())
    bins = np.logspace(np.log10(min_s), np.log10(max_s), num=20)
    plt.figure(figsize=(7,4))
    for r in runs:
        fs = np.array(r['fires_all'])
        if fs.size == 0:
            continue
        hist, edges = np.histogram(fs, bins=bins, density=True)
        centers = np.sqrt(edges[:-1] * edges[1:])
        mask = hist > 0
        plt.loglog(centers[mask], hist[mask], marker='o', linestyle='-', label=f"run {r['run_id']}")
    plt.title(f'Fire-size distributions for param_id {pid}')
    plt.xlabel('Fire size')
    plt.ylabel('Probability density')
    plt.legend()
    plt.tight_layout()
    outp = plots_dir / f'fire_dist_param{pid}.png'
    plt.savefig(outp)
    plt.close()
    print('Saved', outp)

# aggregated by param_id
all_fires_global = np.concatenate([np.concatenate([np.array(r['fires_all']) for r in runs_by_param[pid] if len(r['fires_all'])>0]) for pid in runs_by_param.keys() if any(len(r['fires_all'])>0 for r in runs_by_param[pid])]) if any(any(len(r['fires_all'])>0 for r in runs_by_param[pid]) for pid in runs_by_param.keys()) else np.array([])
if all_fires_global.size > 0:
    min_s = max(1, int(all_fires_global.min()))
    max_s = int(all_fires_global.max())
    bins = np.logspace(np.log10(min_s), np.log10(max_s), num=25)
    plt.figure(figsize=(8,5))
    for pid in sorted(runs_by_param.keys()):
        runs = runs_by_param[pid]
        agg = np.concatenate([np.array(r['fires_all']) for r in runs if len(r['fires_all']) > 0]) if any(len(r['fires_all'])>0 for r in runs) else np.array([])
        if agg.size == 0:
            continue
        hist, edges = np.histogram(agg, bins=bins, density=True)
        centers = np.sqrt(edges[:-1] * edges[1:])
        mask = hist > 0
        plt.loglog(centers[mask], hist[mask], marker='o', linestyle='-', label=f'param {pid}')
    plt.title('Fire-size distributions aggregated by param_id')
    plt.xlabel('Fire size')
    plt.ylabel('Probability density')
    plt.legend()
    plt.tight_layout()
    outp = plots_dir / 'fire_dist_by_param.png'
    plt.savefig(outp)
    plt.close()
    print('Saved', outp)

# Cluster-size distributions per param
all_clusters_global = np.concatenate([np.concatenate([np.array(r['clusters_all']) for r in runs_by_param[pid] if len(r['clusters_all'])>0]) for pid in runs_by_param.keys() if any(len(r['clusters_all'])>0 for r in runs_by_param[pid])]) if any(any(len(r['clusters_all'])>0 for r in runs_by_param[pid]) for pid in runs_by_param.keys()) else np.array([])
if all_clusters_global.size > 0:
    min_c = max(1, int(all_clusters_global.min()))
    max_c = int(all_clusters_global.max())
    bins = np.logspace(np.log10(min_c), np.log10(max_c), num=25)
    plt.figure(figsize=(8,5))
    for pid in sorted(runs_by_param.keys()):
        runs = runs_by_param[pid]
        agg = np.concatenate([np.array(r['clusters_all']) for r in runs if len(r['clusters_all']) > 0]) if any(len(r['clusters_all'])>0 for r in runs) else np.array([])
        if agg.size == 0:
            continue
        hist, edges = np.histogram(agg, bins=bins, density=True)
        centers = np.sqrt(edges[:-1] * edges[1:])
        mask = hist > 0
        plt.loglog(centers[mask], hist[mask], marker='o', linestyle='-', label=f'param {pid}')
    plt.title('Cluster-size distributions aggregated by param_id')
    plt.xlabel('Cluster size')
    plt.ylabel('Probability density')
    plt.legend()
    plt.tight_layout()
    outp = plots_dir / 'cluster_dist_by_param.png'
    plt.savefig(outp)
    plt.close()
    print('Saved', outp)

# Mean density time series per param
for pid in sorted(runs_by_param.keys()):
    runs = runs_by_param[pid]
    densities = [np.array(r['density_series'], dtype=float) for r in runs if len(r['density_series'])>0]
    if not densities:
        print(f'param {pid}: no density series available')
        continue
    maxlen = max(arr.size for arr in densities)
    stacked = np.vstack([np.pad(arr, (0, maxlen - arr.size), constant_values=np.nan) for arr in densities])
    mean_series = np.nanmean(stacked, axis=0)
    std_series = np.nanstd(stacked, axis=0)
    x = np.arange(mean_series.size)
    plt.figure(figsize=(8,4))
    for i, arr in enumerate(stacked):
        plt.plot(np.arange(arr.size), arr, alpha=0.3, label=f'run {runs[i]["run_id"]}')
    plt.plot(x, mean_series, color='k', linewidth=2, label='mean')
    plt.fill_between(x, mean_series - std_series, mean_series + std_series, color='k', alpha=0.2, label='std')
    plt.title(f'Mean tree density over time (param {pid})')
    plt.xlabel('Step')
    plt.ylabel('Mean tree density')
    plt.legend()
    plt.tight_layout()
    outp = plots_dir / f'density_param{pid}.png'
    plt.savefig(outp)
    plt.close()
    print('Saved', outp)

print('Analysis complete')
