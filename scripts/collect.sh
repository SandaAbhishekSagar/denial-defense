#!/bin/bash
# Denial Defense data collection runner script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==========================="
echo "Denial Defense Data Collection"
echo "==========================="
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv "$PROJECT_ROOT/venv"
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r "$PROJECT_ROOT/requirements.txt"
echo "✓ Dependencies installed"
echo ""

# Run collection script with all phases
echo "Starting data collection..."
echo ""
python "$SCRIPT_DIR/collect_supplemental_data.py" --all --root "$PROJECT_ROOT"

echo ""
echo "==========================="
echo "Collection complete!"
echo "Check logs/collection.log for details"
echo "==========================="
