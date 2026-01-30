"""
Route Service - Jump distance calculation using ESI route API.

Provides jump distance calculation between EVE systems with caching.
"""

import logging
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal

from argus_overview.esi.client import ESIClient
from argus_overview.esi.universe_cache import UniverseCache


class RouteService(QObject):
    """
    Service for calculating jump distances between EVE systems.

    Uses ESI /route/ endpoint with LRU caching.
    """

    # Signals
    route_calculated = Signal(str, str, int)  # origin, dest, jumps
    route_failed = Signal(str, str, str)  # origin, dest, error message

    # Route flags
    FLAG_SHORTEST = "shortest"
    FLAG_SECURE = "secure"
    FLAG_INSECURE = "insecure"

    def __init__(
        self,
        esi_client: Optional[ESIClient] = None,
        universe_cache: Optional[UniverseCache] = None,
        parent: Optional[QObject] = None,
    ):
        """
        Initialize route service.

        Args:
            esi_client: ESI client (created if not provided)
            universe_cache: Universe cache (created if not provided)
            parent: Parent QObject
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Initialize dependencies
        self.esi_client = esi_client or ESIClient(parent=self)
        self.universe_cache = universe_cache or UniverseCache(self.esi_client)

        # Route cache with TTL (5 minutes)
        self._route_cache: dict = {}
        self._cache_ttl = 300  # seconds

        # Default route flag
        self._route_flag = self.FLAG_SHORTEST

    def set_route_flag(self, flag: str):
        """
        Set route calculation flag.

        Args:
            flag: Route flag (shortest, secure, insecure)
        """
        if flag in (self.FLAG_SHORTEST, self.FLAG_SECURE, self.FLAG_INSECURE):
            self._route_flag = flag
            # Clear cache when flag changes
            self._route_cache.clear()
        else:
            self.logger.warning(f"Invalid route flag: {flag}")

    def calculate_jumps(
        self,
        origin: str,
        destination: str,
        flag: Optional[str] = None,
    ) -> Optional[int]:
        """
        Calculate jump distance between two systems.

        Args:
            origin: Origin system name
            destination: Destination system name
            flag: Route flag (default: current setting)

        Returns:
            Number of jumps, or None if route not found
        """
        if not origin or not destination:
            return None

        # Normalize names
        origin = origin.strip()
        destination = destination.strip()

        if origin.lower() == destination.lower():
            return 0

        # Check cache
        cache_key = self._cache_key(origin, destination, flag)
        cached = self._get_cached_route(cache_key)
        if cached is not None:
            return cached

        # Get system IDs
        origin_id = self.universe_cache.get_system_id(origin)
        destination_id = self.universe_cache.get_system_id(destination)

        if not origin_id:
            self.logger.debug(f"Origin system not found: {origin}")
            self.route_failed.emit(origin, destination, f"Unknown system: {origin}")
            return None

        if not destination_id:
            self.logger.debug(f"Destination system not found: {destination}")
            self.route_failed.emit(origin, destination, f"Unknown system: {destination}")
            return None

        # Calculate route via ESI
        route_flag = flag or self._route_flag
        jumps = self._calculate_route_esi(origin_id, destination_id, route_flag)

        if jumps is not None:
            # Cache result
            self._cache_route(cache_key, jumps)
            self.route_calculated.emit(origin, destination, jumps)
            self.logger.debug(f"Route: {origin} -> {destination} = {jumps} jumps")

        return jumps

    def _calculate_route_esi(
        self,
        origin_id: int,
        destination_id: int,
        flag: str,
    ) -> Optional[int]:
        """
        Calculate route via ESI API.

        Args:
            origin_id: Origin system ID
            destination_id: Destination system ID
            flag: Route flag

        Returns:
            Number of jumps, or None on error
        """
        endpoint = f"/route/{origin_id}/{destination_id}/"

        try:
            result = self.esi_client.get(
                endpoint,
                params={"flag": flag},
            )

            if result is None:
                return None

            if isinstance(result, list):
                # Route is list of system IDs
                # Jumps = len(route) - 1 (route includes origin)
                return max(0, len(result) - 1)

            return None

        except Exception as e:
            self.logger.warning(f"ESI route calculation failed: {e}")
            self.route_failed.emit(str(origin_id), str(destination_id), str(e))
            return None

    def _cache_key(self, origin: str, destination: str, flag: Optional[str]) -> str:
        """Generate cache key for route."""
        route_flag = flag or self._route_flag
        return f"{origin.lower()}:{destination.lower()}:{route_flag}"

    def _get_cached_route(self, cache_key: str) -> Optional[int]:
        """Get cached route if not expired."""
        if cache_key in self._route_cache:
            timestamp, jumps = self._route_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return jumps
            # Expired, remove
            del self._route_cache[cache_key]
        return None

    def _cache_route(self, cache_key: str, jumps: int):
        """Cache route result."""
        self._route_cache[cache_key] = (time.time(), jumps)

        # Limit cache size (LRU-ish)
        if len(self._route_cache) > 1000:
            # Remove oldest entries
            sorted_keys = sorted(
                self._route_cache.keys(),
                key=lambda k: self._route_cache[k][0],
            )
            for key in sorted_keys[:100]:
                del self._route_cache[key]

    def clear_cache(self):
        """Clear route cache."""
        self._route_cache.clear()

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self._route_cache),
            "systems_loaded": len(self.universe_cache),
        }

    def close(self):
        """Cleanup resources."""
        self.esi_client.close()
