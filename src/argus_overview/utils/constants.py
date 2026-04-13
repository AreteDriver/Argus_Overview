"""Centralized constants for Argus Overview."""

import os
import tempfile
from pathlib import Path

# Subprocess timeout values (seconds)
TIMEOUT_SHORT = 1  # Quick operations (getwindowfocus)
TIMEOUT_MEDIUM = 2  # Window move/resize operations
TIMEOUT_LONG = 5  # Slower operations (wmctrl -l)

# Window capture settings
DEFAULT_CAPTURE_WORKERS = 4
DEFAULT_REFRESH_RATE = 30  # FPS

# Configuration paths
_DEFAULT_CONFIG_DIR = Path.home() / ".config" / "argus-overview"
_REQUESTED_CONFIG_DIR = Path(os.environ.get("ARGUS_CONFIG_DIR", _DEFAULT_CONFIG_DIR)).expanduser()


def _resolve_config_dir() -> Path:
    """Return a writable config directory, falling back when home is unavailable."""
    try:
        _REQUESTED_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return _REQUESTED_CONFIG_DIR
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "argus-overview"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


CONFIG_DIR = _resolve_config_dir()

# Config file paths
SETTINGS_FILE = CONFIG_DIR / "settings.json"
CHARACTERS_FILE = CONFIG_DIR / "characters.json"
TEAMS_FILE = CONFIG_DIR / "teams.json"
LOG_FILE = CONFIG_DIR / "argus-overview.log"
