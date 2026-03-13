"""EVE Online jump distance calculator.

Uses system adjacency data to compute shortest jump distances via BFS.
Data derived from EVE Static Data Export (SDE) mapSolarSystemJumps table.
"""

import json
import logging
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)


def get_default_data_path() -> Path:
    """Return the path to the bundled jumps.json file."""
    return Path(__file__).parent / "data" / "jumps.json"


class JumpCalculator:
    """Calculate shortest jump distances between EVE systems via BFS.

    Loads adjacency data from a JSON file mapping system names (lowercase)
    to lists of adjacent system names. All lookups are case-insensitive.
    """

    def __init__(self, data_path: Path | None = None):
        """Initialize the jump calculator.

        Args:
            data_path: Path to a JSON file containing adjacency data.
                Defaults to the bundled ``data/jumps.json``.
        """
        path = data_path or get_default_data_path()
        self._graph: dict[str, list[str]] = {}
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise TypeError(f"Expected JSON object, got {type(data).__name__}")
            self._graph = {
                k.lower(): [v.lower() for v in vals]
                for k, vals in data.items()
                if isinstance(vals, list)
            }
            logger.info(
                "Loaded adjacency data for %d systems from %s",
                len(self._graph),
                path,
            )
        except FileNotFoundError:
            logger.warning(
                "Jump data file not found at %s — calculator will return None for all queries",
                path,
            )
        except (json.JSONDecodeError, TypeError, OSError) as exc:
            logger.warning(
                "Failed to load jump data from %s (%s) — calculator will"
                " return None for all queries",
                path,
                exc,
            )

    @property
    def system_count(self) -> int:
        """Number of systems in the adjacency graph."""
        return len(self._graph)

    def distance(self, from_system: str, to_system: str) -> int | None:
        """Compute the shortest jump distance between two systems.

        Args:
            from_system: Origin system name (case-insensitive).
            to_system: Destination system name (case-insensitive).

        Returns:
            Number of jumps, or None if either system is unknown or no
            path exists.
        """
        start = from_system.lower()
        end = to_system.lower()

        if start not in self._graph or end not in self._graph:
            return None
        if start == end:
            return 0

        visited: set[str] = {start}
        queue: deque[tuple[str, int]] = deque([(start, 0)])

        while queue:
            current, dist = queue.popleft()
            for neighbor in self._graph.get(current, []):
                if neighbor == end:
                    return dist + 1
                if neighbor not in visited and neighbor in self._graph:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))

        return None

    def systems_within(self, system: str, max_jumps: int) -> dict[str, int]:
        """Find all systems within a given jump range.

        Args:
            system: Origin system name (case-insensitive).
            max_jumps: Maximum number of jumps to search.

        Returns:
            Dict mapping system name (lowercase) to jump distance.
            Empty dict if system is unknown.
        """
        start = system.lower()
        if start not in self._graph:
            return {}

        result: dict[str, int] = {start: 0}
        queue: deque[tuple[str, int]] = deque([(start, 0)])

        while queue:
            current, dist = queue.popleft()
            if dist >= max_jumps:
                continue
            for neighbor in self._graph.get(current, []):
                if neighbor not in result:
                    result[neighbor] = dist + 1
                    if neighbor in self._graph:
                        queue.append((neighbor, dist + 1))

        return result

    def path(self, from_system: str, to_system: str) -> list[str] | None:
        """Find the shortest path between two systems.

        Args:
            from_system: Origin system name (case-insensitive).
            to_system: Destination system name (case-insensitive).

        Returns:
            List of system names forming the shortest path (inclusive of
            start and end), or None if no path exists.
        """
        start = from_system.lower()
        end = to_system.lower()

        if start not in self._graph or end not in self._graph:
            return None
        if start == end:
            return [start]

        visited: set[str] = {start}
        # Each entry: (current_system, path_so_far)
        queue: deque[tuple[str, list[str]]] = deque([(start, [start])])

        while queue:
            current, current_path = queue.popleft()
            for neighbor in self._graph.get(current, []):
                if neighbor == end:
                    return current_path + [neighbor]
                if neighbor not in visited and neighbor in self._graph:
                    visited.add(neighbor)
                    queue.append((neighbor, current_path + [neighbor]))

        return None
