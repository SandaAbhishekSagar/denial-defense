import io
import sys
import pandas as pd
import json
from pathlib import Path

# Fix Windows Unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("SANITY CHECK - Denial Defense Project")
print("=" * 60)

# Check eval set
try:
    df = pd.read_parquet('data/processed/eval_set_imr.parquet')
    print(f'✓ Eval set: {df.shape[0]} cases, {df.shape[1]} columns')
    print(f'  - Medical Necessity: {(df["Type"] == "Medical Necessity").sum()}')
    print(f'  - Experimental/Investigational: {(df["Type"] == "Experimental/Investigational").sum()}')
    print(f'  - Urgent Care: {(df["Type"] == "Urgent Care").sum()}')
except Exception as e:
    print(f'✗ Eval set: {e}')

# Check demo cases
demo_cases = list(Path('data/demo').glob('*.json'))
print(f'\n✓ Demo cases: {len(demo_cases)} found')
for case_path in sorted(demo_cases):
    try:
        case = json.load(open(case_path))
        print(f'  - {case.get("display_name", case_path.name)}')
    except Exception as e:
        print(f'  - {case_path.name}: Error loading - {e}')

# Check playbook
playbook_path = Path('data/processed/denial_playbook.json')
if playbook_path.exists():
    try:
        playbook = json.load(open(playbook_path))
        print(f'\n✓ Playbook: {len(playbook)} entries')
    except Exception as e:
        print(f'\n✗ Playbook: {e}')
else:
    print(f'\n✗ Playbook: File not found at {playbook_path}')

# Check agents module (will be built Sunday)
agents_dir = Path('agents')
if agents_dir.exists() and list(agents_dir.glob('*.py')):
    py_files = list(agents_dir.glob('*.py'))
    print(f'\n✓ Agents: {len(py_files)} Python files')
    for f in py_files:
        print(f'  - {f.name}')
else:
    print(f'\n⚠ Agents: Not yet implemented (expected - will be built Sunday)')

print("\n" + "=" * 60)
print("Sanity check complete!")
print("=" * 60)

