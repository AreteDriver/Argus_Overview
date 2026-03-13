"""EVE Online system name database.

Loads system names from a bundled JSON file derived from the EVE Static Data
Export (SDE). Falls back to a hardcoded set of common systems if the data
file is missing.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Minimal fallback set used when the JSON file is unavailable
_FALLBACK_SYSTEMS: set[str] = {
    "jita",
    "amarr",
    "dodixie",
    "rens",
    "hek",
    "hed-gp",
    "1dq1-a",
    "r1o-gn",
    "b-r5rb",
    "m-oee8",
    "y-2anf",
    "ge-8jv",
    "f-eup9",
    "4-hwwf",
    "t-m0fa",
    "amamake",
    "tama",
    "rancer",
    "old man star",
    "asakai",
    "rakapas",
    "thera",
    "poitot",
}


def get_default_data_path() -> Path:
    """Return the path to the bundled systems.json file."""
    return Path(__file__).parent / "data" / "systems.json"


def load_systems(data_path: Path | None = None) -> set[str]:
    """Load system names from a JSON file.

    Args:
        data_path: Path to a JSON file containing an array of system name
            strings.  Defaults to the bundled ``data/systems.json``.

    Returns:
        Set of system names in **lowercase** for case-insensitive matching.
    """
    path = data_path or get_default_data_path()

    try:
        raw = path.read_text(encoding="utf-8")
        names: list[str] = json.loads(raw)
        if not isinstance(names, list):
            raise TypeError(f"Expected JSON array, got {type(names).__name__}")
        systems = {name.lower() for name in names if isinstance(name, str)}
        logger.info("Loaded %d system names from %s", len(systems), path)
        return systems
    except FileNotFoundError:
        logger.warning("System data file not found at %s — using fallback set", path)
        return set(_FALLBACK_SYSTEMS)
    except (json.JSONDecodeError, TypeError, OSError) as exc:
        logger.warning(
            "Failed to load system data from %s (%s) — using fallback set",
            path,
            exc,
        )
        return set(_FALLBACK_SYSTEMS)
