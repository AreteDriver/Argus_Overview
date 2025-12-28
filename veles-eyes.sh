#!/bin/bash
# EVE Veles Eyes Launcher Script

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment and run
cd "$SCRIPT_DIR"
source .venv/bin/activate

# Add src to PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

python3 src/main.py "$@"
