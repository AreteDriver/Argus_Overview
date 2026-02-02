"""Platform abstraction layer for cross-platform window management.

This module provides platform-independent interfaces for:
- Window management (move, resize, activate, minimize)
- Window capture (screenshot generation)
- Screen geometry queries
- EVE Online path resolution
- Hotkey normalization

Usage:
    from argus_overview.platform import (
        get_window_manager,
        get_window_capture,
        get_screen_manager,
        get_eve_path_resolver,
        get_hotkey_helper,
        get_platform_name,
    )

    # Get platform-appropriate implementations
    window_mgr = get_window_manager()
    windows = window_mgr.get_eve_windows()
"""

import sys
from typing import TYPE_CHECKING

from .base import (
    EVEPathResolver,
    HotkeyHelper,
    ScreenGeometry,
    ScreenManager,
    WindowCapture,
    WindowInfo,
    WindowManager,
)

if TYPE_CHECKING:
    pass

__all__ = [
    # Base classes
    "WindowManager",
    "WindowCapture",
    "ScreenManager",
    "EVEPathResolver",
    "HotkeyHelper",
    "ScreenGeometry",
    "WindowInfo",
    # Factory functions
    "get_window_manager",
    "get_window_capture",
    "get_screen_manager",
    "get_eve_path_resolver",
    "get_hotkey_helper",
    "get_platform_name",
    "is_windows",
    "is_linux",
]


def get_platform_name() -> str:
    """Get the current platform name.

    Returns:
        'windows', 'linux', or 'unknown'
    """
    if sys.platform == "win32":
        return "windows"
    elif sys.platform in ("linux", "linux2"):
        return "linux"
    elif sys.platform == "darwin":
        return "macos"
    return "unknown"


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


def is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform in ("linux", "linux2")


def get_window_manager() -> WindowManager:
    """Create a platform-appropriate WindowManager instance.

    Returns:
        WindowManager implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    platform = get_platform_name()
    if platform == "windows":
        from .windows import WindowManagerWindows

        return WindowManagerWindows()
    elif platform == "linux":
        from .linux import WindowManagerLinux

        return WindowManagerLinux()
    raise RuntimeError(f"Unsupported platform: {platform}")


def get_window_capture(max_workers: int = 4) -> WindowCapture:
    """Create a platform-appropriate WindowCapture instance.

    Args:
        max_workers: Number of capture worker threads

    Returns:
        WindowCapture implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    platform = get_platform_name()
    if platform == "windows":
        from .windows import WindowCaptureWindows

        return WindowCaptureWindows(max_workers=max_workers)
    elif platform == "linux":
        from .linux import WindowCaptureLinux

        return WindowCaptureLinux(max_workers=max_workers)
    raise RuntimeError(f"Unsupported platform: {platform}")


def get_screen_manager() -> ScreenManager:
    """Create a platform-appropriate ScreenManager instance.

    Returns:
        ScreenManager implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    platform = get_platform_name()
    if platform == "windows":
        from .windows import ScreenManagerWindows

        return ScreenManagerWindows()
    elif platform == "linux":
        from .linux import ScreenManagerLinux

        return ScreenManagerLinux()
    raise RuntimeError(f"Unsupported platform: {platform}")


def get_eve_path_resolver() -> EVEPathResolver:
    """Create a platform-appropriate EVEPathResolver instance.

    Returns:
        EVEPathResolver implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    platform = get_platform_name()
    if platform == "windows":
        from .windows import EVEPathResolverWindows

        return EVEPathResolverWindows()
    elif platform == "linux":
        from .linux import EVEPathResolverLinux

        return EVEPathResolverLinux()
    raise RuntimeError(f"Unsupported platform: {platform}")


def get_hotkey_helper() -> HotkeyHelper:
    """Create a platform-appropriate HotkeyHelper instance.

    Returns:
        HotkeyHelper implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    platform = get_platform_name()
    if platform == "windows":
        from .windows import HotkeyHelperWindows

        return HotkeyHelperWindows()
    elif platform == "linux":
        from .linux import HotkeyHelperLinux

        return HotkeyHelperLinux()
    raise RuntimeError(f"Unsupported platform: {platform}")
