"""
Universe Cache - System name ↔ ID mapping with bundled data and ESI fallback.

Provides fast lookups for EVE system names and IDs.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from argus_overview.esi.client import ESIClient


class UniverseCache:
    """
    Cache for EVE universe data (system name ↔ ID mapping).

    Loads bundled system data on init, falls back to ESI for unknown systems.
    """

    def __init__(self, esi_client: Optional[ESIClient] = None):
        """
        Initialize universe cache.

        Args:
            esi_client: Optional ESI client for fallback lookups
        """
        self.logger = logging.getLogger(__name__)
        self.esi_client = esi_client

        # Name -> ID mapping (lowercase names for case-insensitive lookup)
        self._name_to_id: Dict[str, int] = {}

        # ID -> Name mapping
        self._id_to_name: Dict[int, str] = {}

        # Load bundled data
        self._load_bundled_systems()

    def _load_bundled_systems(self):
        """Load bundled system data from JSON file."""
        data_file = Path(__file__).parent.parent / "data" / "systems.json"

        if not data_file.exists():
            self.logger.warning(f"Systems data file not found: {data_file}")
            return

        try:
            with open(data_file) as f:
                data = json.load(f)

            # Build mappings
            for name, system_id in data.items():
                self._name_to_id[name.lower()] = system_id
                self._id_to_name[system_id] = name

            self.logger.info(f"Loaded {len(self._name_to_id)} systems from cache")

        except Exception as e:
            self.logger.error(f"Failed to load systems data: {e}")

    def get_system_id(self, name: str) -> Optional[int]:
        """
        Get system ID by name.

        Args:
            name: System name (case-insensitive)

        Returns:
            System ID, or None if not found
        """
        name_lower = name.lower()

        # Check cache first
        if name_lower in self._name_to_id:
            return self._name_to_id[name_lower]

        # Fallback to ESI
        if self.esi_client:
            system_id = self._lookup_system_esi(name)
            if system_id:
                # Cache the result
                self._name_to_id[name_lower] = system_id
                self._id_to_name[system_id] = name
                return system_id

        self.logger.debug(f"System not found: {name}")
        return None

    def get_system_name(self, system_id: int) -> Optional[str]:
        """
        Get system name by ID.

        Args:
            system_id: System ID

        Returns:
            System name, or None if not found
        """
        return self._id_to_name.get(system_id)

    def _lookup_system_esi(self, name: str) -> Optional[int]:
        """
        Look up system ID via ESI.

        Args:
            name: System name

        Returns:
            System ID, or None
        """
        if not self.esi_client:
            return None

        try:
            result = self.esi_client.post(
                "/universe/ids/",
                json_data=[name],
            )

            if result and "systems" in result and result["systems"]:
                system = result["systems"][0]
                return system.get("id")

        except Exception as e:
            self.logger.warning(f"ESI system lookup failed: {e}")

        return None

    def add_system(self, name: str, system_id: int):
        """
        Add a system to the cache.

        Args:
            name: System name
            system_id: System ID
        """
        self._name_to_id[name.lower()] = system_id
        self._id_to_name[system_id] = name

    def contains(self, name: str) -> bool:
        """
        Check if system is in cache.

        Args:
            name: System name

        Returns:
            True if system is cached
        """
        return name.lower() in self._name_to_id

    def __len__(self) -> int:
        """Get number of cached systems."""
        return len(self._name_to_id)
