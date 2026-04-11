"""Window management utilities with validation and retry logic.

v3.0: Cross-platform support via platform abstraction layer.
This module now serves as a compatibility layer, delegating to platform implementations.
"""

import logging

from argus_overview.platform import get_window_manager, is_linux

logger = logging.getLogger(__name__)

# Re-export run_x11_subprocess for code that still needs it directly
if is_linux():
    from argus_overview.platform.linux import run_x11_subprocess
else:
    # Provide a stub for Windows - should not be called
    def run_x11_subprocess(*args, **kwargs):  # type: ignore[misc]
        raise RuntimeError("run_x11_subprocess is only available on Linux")


# Module-level window manager instance (lazy initialization)
_window_mgr = None


def _get_window_mgr():
    global _window_mgr
    if _window_mgr is None:
        _window_mgr = get_window_manager()
    return _window_mgr


def is_valid_window_id(window_id: str) -> bool:
    """Validate that a string is a valid window ID for the current platform.

    Args:
        window_id: The window ID to validate

    Returns:
        True if valid window ID format for current platform
    """
    return _get_window_mgr().is_valid_window_id(window_id)


def move_window(window_id: str, x: int, y: int, w: int, h: int, timeout: float = 2.0) -> bool:
    """Move and resize a window safely with validation and retry.

    Args:
        window_id: Platform-specific window ID
        x: Target X position
        y: Target Y position
        w: Target width
        h: Target height
        timeout: Operation timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    return _get_window_mgr().move_window(window_id, x, y, w, h, timeout)


def activate_window(window_id: str, timeout: float = 2.0) -> bool:
    """Activate (focus) a window safely with validation and retry.

    Args:
        window_id: Platform-specific window ID
        timeout: Operation timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    return _get_window_mgr().activate_window(window_id, timeout)


def get_focused_window() -> str | None:
    """Get the currently focused window ID.

    Returns:
        Window ID string or None if unable to determine
    """
    return _get_window_mgr().get_focused_window()
