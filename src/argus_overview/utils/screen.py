"""Screen geometry utilities - shared across UI components.

v3.0: Cross-platform support via platform abstraction layer.
"""

import logging

from argus_overview.platform import get_screen_manager
from argus_overview.platform.base import ScreenGeometry

logger = logging.getLogger(__name__)

# Re-export ScreenGeometry for backward compatibility
__all__ = ["ScreenGeometry", "get_screen_geometry", "get_all_monitors"]


def get_screen_geometry(monitor: int = 0) -> ScreenGeometry:
    """Get screen geometry for a specific monitor.

    Uses platform-specific methods (xrandr on Linux, EnumDisplayMonitors on Windows).

    Args:
        monitor: Monitor index (0-based)

    Returns:
        ScreenGeometry for requested monitor, or default 1920x1080 on failure
    """
    screen_mgr = get_screen_manager()
    return screen_mgr.get_screen_geometry(monitor)


def get_all_monitors() -> list[ScreenGeometry]:
    """Get geometry for all connected monitors.

    Uses platform-specific methods (xrandr on Linux, EnumDisplayMonitors on Windows).

    Returns:
        List of ScreenGeometry for all monitors, or single default on failure
    """
    screen_mgr = get_screen_manager()
    return screen_mgr.get_all_monitors()
