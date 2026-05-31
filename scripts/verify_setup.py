"""
Quick verification script - checks structure without calling APIs.
Run this before adding API keys to verify everything imports correctly.
"""

import sys
import io
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix Unicode output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("DENIAL DEFENSE - PRE-FLIGHT CHECK")
print("=" * 80)
print()

errors = []
warnings = []

# Check 1: File structure
print("✓ Checking file structure...")
required_files = [
    "agents/__init__.py",
    "agents/prompts.py",
    "agents/baseline.py",
    "agents/harness.py",
    "agents/playbook.py",
    "web/app.py",
    "web/templates/index.html",
    "eval/__init__.py",
    "eval/compare_eval.py",
    "data/demo/case_01_oscar_cromolyn.json",
    "data/demo/case_02_spinal_cord_stimulator.json",
    "data/demo/case_03_mhpaea_parity.json",
    "data/processed/denial_playbook.json",
    "data/processed/eval_set_imr.parquet",
    ".env.example",
    "requirements.txt",
]

for f in required_files:
    if not Path(f).exists():
        errors.append(f"Missing file: {f}")
    else:
        print(f"  ✓ {f}")

print()

# Check 2: Python imports
print("✓ Checking Python imports...")
try:
    import openai
    print("  ✓ openai")
except ImportError as e:
    errors.append(f"Missing package: openai ({e})")

try:
    import langgraph
    print("  ✓ langgraph")
except ImportError as e:
    errors.append(f"Missing package: langgraph ({e})")

try:
    import weave
    print("  ✓ weave")
except ImportError as e:
    errors.append(f"Missing package: weave ({e})")

try:
    import flask
    print("  ✓ flask")
except ImportError as e:
    errors.append(f"Missing package: flask ({e})")

try:
    import pandas
    print("  ✓ pandas")
except ImportError as e:
    errors.append(f"Missing package: pandas ({e})")

print()

# Check 3: Agent modules import correctly
print("✓ Checking agent modules...")
try:
    from agents import prompts
    print("  ✓ agents.prompts")
    
    # Verify prompts exist
    assert hasattr(prompts, 'MEDICAL_NECESSITY_SYSTEM')
    assert hasattr(prompts, 'POLICY_CITATION_SYSTEM')
    assert hasattr(prompts, 'PRECEDENT_SYSTEM')
    assert hasattr(prompts, 'INSURER_DEFENSE_SYSTEM')
    assert hasattr(prompts, 'SUPERVISOR_SYNTHESIS_SYSTEM')
    assert hasattr(prompts, 'BASELINE_SYSTEM')
    print("    ✓ All 6 prompts defined")
    
except Exception as e:
    errors.append(f"agents.prompts import failed: {e}")

try:
    from agents import playbook
    print("  ✓ agents.playbook")
    assert hasattr(playbook, 'Playbook')
    print("    ✓ Playbook class exists")
except Exception as e:
    errors.append(f"agents.playbook import failed: {e}")

# Note: We can't import baseline or harness without API keys
# since they initialize OpenAI client at module level
print("  ⚠ Skipping baseline/harness import (requires API keys)")
warnings.append("baseline.py and harness.py require OPENAI_API_KEY to import")

print()

# Check 4: Demo cases load
print("✓ Checking demo cases...")
import json
for case_id in ["case_01_oscar_cromolyn", "case_02_spinal_cord_stimulator", "case_03_mhpaea_parity"]:
    try:
        case_path = Path(f"data/demo/{case_id}.json")
        case_data = json.load(open(case_path))
        assert "display_name" in case_data
        assert "denial_letter" in case_data
        assert "patient_context" in case_data
        print(f"  ✓ {case_id}: {case_data['display_name']}")
    except Exception as e:
        errors.append(f"Case {case_id} invalid: {e}")

print()

# Check 5: Environment setup
print("✓ Checking environment setup...")
import os
if os.path.exists(".env"):
    print("  ✓ .env file exists")
    # Don't read it, just check it exists
else:
    warnings.append(".env file not found - copy .env.example and add your API keys")
    print("  ⚠ .env file not found")

if not os.getenv("OPENAI_API_KEY"):
    warnings.append("OPENAI_API_KEY not set")
    print("  ⚠ OPENAI_API_KEY not set")
else:
    print("  ✓ OPENAI_API_KEY set")

if not os.getenv("WANDB_API_KEY"):
    warnings.append("WANDB_API_KEY not set")
    print("  ⚠ WANDB_API_KEY not set")
else:
    print("  ✓ WANDB_API_KEY set")

print()
print("=" * 80)

if errors:
    print("❌ ERRORS FOUND:")
    for err in errors:
        print(f"  - {err}")
    print()
    sys.exit(1)

if warnings:
    print("⚠ WARNINGS:")
    for warn in warnings:
        print(f"  - {warn}")
    print()

print("✅ PRE-FLIGHT CHECK PASSED")
print()
print("Next steps:")
print("  1. Copy .env.example to .env")
print("  2. Add your OPENAI_API_KEY and WANDB_API_KEY to .env")
print("  3. Run: python agents/baseline.py")
print("  4. Run: python agents/harness.py")
print("  5. Run: python web/app.py")
print()
print("=" * 80)
