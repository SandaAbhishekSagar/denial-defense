#!/bin/bash
# Denial Defense demo launcher
# Starts the Flask web UI on http://localhost:5000

set -e

# Check API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable not set"
    echo "Set it in .env or export it:"
    echo "  export OPENAI_API_KEY='your-key-here'"
    exit 1
fi

if [ -z "$WANDB_API_KEY" ]; then
    echo "ERROR: WANDB_API_KEY environment variable not set"
    echo "Set it in .env or export it:"
    echo "  export WANDB_API_KEY='your-key-here'"
    exit 1
fi

echo "=========================================="
echo "Denial Defense - Multi-Agent Demo"
echo "=========================================="
echo "Starting web UI on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Run Flask app
python3 web/app.py
