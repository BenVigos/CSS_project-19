from pathlib import Path
import importlib.util
import sys

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Load scripts/parallel_sims.py as a module without requiring package imports
ps_path = project_root / 'scripts' / 'parallel_sims.py'
spec = importlib.util.spec_from_file_location('parallel_sims_module', str(ps_path))
ps_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ps_mod)
worker = ps_mod.worker

outdir = Path('data/test_worker_suppress')
# remove existing dir if present (best-effort)
if outdir.exists():
    import shutil
    shutil.rmtree(outdir)
outdir.mkdir(parents=True, exist_ok=True)

params = {'L': 64, 'p': 0.01, 'f': 0.001, 'steps': 20, 'param_id': 42, 'run_id': 7, 'suppress': 10}
print('Calling worker with params:', params)
res = worker(outdir, params)
print('Worker returned summary:')
print(res)

# list files created
files = sorted(outdir.iterdir())
print('\nFiles created in outdir:')
for f in files:
    print('-', f.name)

# find perstep and raw files
perstep = next((f for f in files if f.name.startswith('perstep_')), None)
raw = next((f for f in files if f.name.startswith('fires_')), None)
debug = next((f for f in files if f.name.startswith('debug_')), None)

if perstep:
    print('\nPer-step CSV content:')
    print(perstep.read_text())
else:
    print('\nNo perstep file found')

if raw:
    print('\nRaw fires CSV content (first 30 lines):')
    print('\n'.join(raw.read_text().splitlines()[:30]))
else:
    print('\nNo raw file found')

if debug:
    print('\nDebug JSON:')
    print(debug.read_text())
else:
    print('\nNo debug file found')
