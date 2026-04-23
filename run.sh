#!/bin/bash
# Argus Overview v2.4 Launcher
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Use venv python directly if available, otherwise system python.
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

if [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="venv/bin/python3"
elif [ -f ".venv/bin/python3" ]; then
    PYTHON_CMD=".venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

# Fail fast on unsupported runtimes before Qt initializes.
if ! "$PYTHON_CMD" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PY_VER="$("$PYTHON_CMD" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")' 2>/dev/null || echo "unknown")"
    echo "Argus Overview requires Python 3.10+ (detected ${PY_VER} from ${PYTHON_CMD})." >&2
    echo "Recreate your environment with Python 3.10+ and reinstall dependencies." >&2
    exit 1
fi

exec "$PYTHON_CMD" src/main.py "$@"
