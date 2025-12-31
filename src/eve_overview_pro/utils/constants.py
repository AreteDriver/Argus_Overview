"""Centralized constants for Argus Overview."""

import os
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
CONFIG_DIR = Path(os.environ.get("ARGUS_CONFIG_DIR", _DEFAULT_CONFIG_DIR)).expanduser()

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Config file paths
SETTINGS_FILE = CONFIG_DIR / "settings.json"
CHARACTERS_FILE = CONFIG_DIR / "characters.json"
TEAMS_FILE = CONFIG_DIR / "teams.json"
LOG_FILE = CONFIG_DIR / "argus-overview.log"
