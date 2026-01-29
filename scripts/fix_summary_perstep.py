import csv
from pathlib import Path
import re
import sys

# Usage: python scripts/fix_summary_perstep.py <experiment_dir>

def find_perstep_map(exp_dir: Path):
    # pattern: perstep_param{param}_..._id{run}_timestamp.csv
    pattern = re.compile(r'perstep_param(?P<param>\d+)_.*_id(?P<run>\d+)_')
    mapping = {}
    for p in exp_dir.glob('perstep_*.csv'):
        m = pattern.search(p.name)
        if not m:
            continue
        pid = int(m.group('param'))
        rid = int(m.group('run'))
        mapping.setdefault((pid, rid), str(p))
    return mapping


def fix_summary(exp_dir: Path):
    summaries = sorted(exp_dir.glob('summary_*.csv'))
    if not summaries:
        print('No summary CSV found in', exp_dir)
        return
    summary_file = summaries[-1]
    print('Fixing summary file:', summary_file)

    perstep_map = find_perstep_map(exp_dir)
    print('Found perstep files for keys:', list(perstep_map.keys()))

    rows = []
    with open(summary_file, newline='') as fh:
        reader = csv.DictReader(fh)
        keys = reader.fieldnames
        for row in reader:
            try:
                pid = int(row.get('param_id') or -1)
                rid = int(row.get('run_id') or -1)
            except Exception:
                pid = -1; rid = -1
            key = (pid, rid)
            if not row.get('perstep_file') and key in perstep_map:
                row['perstep_file'] = perstep_map[key]
            rows.append(row)

    # write out backup and updated file
    backup = summary_file.with_suffix('.bak.csv')
    summary_file.rename(backup)
    with open(summary_file, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print('Updated summary written to', summary_file, '(backup:', backup, ')')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/fix_summary_perstep.py <experiment_dir>')
        sys.exit(1)
    exp_dir = Path(sys.argv[1])
    fix_summary(exp_dir)
