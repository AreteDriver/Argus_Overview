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


_singleton_cache: dict[str, object] = {}


def _clear_singleton_cache() -> None:
    """Clear singleton cache (for testing)."""
    _singleton_cache.clear()


def _is_pure_wayland() -> bool:
    """Check if running in pure Wayland (no XWayland).

    Returns:
        True if pure Wayland session where X11 tools won't work.
    """
    if sys.platform not in ("linux", "linux2"):
        return False
    try:
        from ..utils.display_server import DisplayServer, detect_display_server

        info = detect_display_server()
        return info.server == DisplayServer.WAYLAND
    except ImportError:
        return False


def get_window_manager() -> WindowManager:
    """Get the platform-appropriate WindowManager singleton.

    Returns:
        WindowManager implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    key = "window_manager"
    if key not in _singleton_cache:
        platform = get_platform_name()
        if platform == "windows":
            from .windows import WindowManagerWindows

            _singleton_cache[key] = WindowManagerWindows()
        elif platform == "linux" and _is_pure_wayland():
            from .wayland import WindowManagerWayland

            _singleton_cache[key] = WindowManagerWayland()
        elif platform == "linux":
            from .linux import WindowManagerLinux

            _singleton_cache[key] = WindowManagerLinux()
        else:
            raise RuntimeError(f"Unsupported platform: {platform}")
    return _singleton_cache[key]  # type: ignore[return-value]


def get_window_capture(max_workers: int = 4) -> WindowCapture:
    """Get the platform-appropriate WindowCapture singleton.

    Args:
        max_workers: Number of capture worker threads (only used on first call)

    Returns:
        WindowCapture implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    key = "window_capture"
    if key not in _singleton_cache:
        platform = get_platform_name()
        if platform == "windows":
            from .windows import WindowCaptureWindows

            _singleton_cache[key] = WindowCaptureWindows(max_workers=max_workers)
        elif platform == "linux" and _is_pure_wayland():
            from .wayland import WindowCaptureWayland

            _singleton_cache[key] = WindowCaptureWayland(max_workers=max_workers)
        elif platform == "linux":
            from .linux import WindowCaptureLinux

            _singleton_cache[key] = WindowCaptureLinux(max_workers=max_workers)
        else:
            raise RuntimeError(f"Unsupported platform: {platform}")
    return _singleton_cache[key]  # type: ignore[return-value]


def get_screen_manager() -> ScreenManager:
    """Get the platform-appropriate ScreenManager singleton.

    Returns:
        ScreenManager implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    key = "screen_manager"
    if key not in _singleton_cache:
        platform = get_platform_name()
        if platform == "windows":
            from .windows import ScreenManagerWindows

            _singleton_cache[key] = ScreenManagerWindows()
        elif platform == "linux" and _is_pure_wayland():
            from .wayland import ScreenManagerWayland

            _singleton_cache[key] = ScreenManagerWayland()
        elif platform == "linux":
            from .linux import ScreenManagerLinux

            _singleton_cache[key] = ScreenManagerLinux()
        else:
            raise RuntimeError(f"Unsupported platform: {platform}")
    return _singleton_cache[key]  # type: ignore[return-value]


def get_eve_path_resolver() -> EVEPathResolver:
    """Get the platform-appropriate EVEPathResolver singleton.

    Returns:
        EVEPathResolver implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    key = "eve_path_resolver"
    if key not in _singleton_cache:
        platform = get_platform_name()
        if platform == "windows":
            from .windows import EVEPathResolverWindows

            _singleton_cache[key] = EVEPathResolverWindows()
        elif platform == "linux" and _is_pure_wayland():
            from .wayland import EVEPathResolverWayland

            _singleton_cache[key] = EVEPathResolverWayland()
        elif platform == "linux":
            from .linux import EVEPathResolverLinux

            _singleton_cache[key] = EVEPathResolverLinux()
        else:
            raise RuntimeError(f"Unsupported platform: {platform}")
    return _singleton_cache[key]  # type: ignore[return-value]


def get_hotkey_helper() -> HotkeyHelper:
    """Get the platform-appropriate HotkeyHelper singleton.

    Returns:
        HotkeyHelper implementation for current platform

    Raises:
        RuntimeError: If platform is not supported
    """
    key = "hotkey_helper"
    if key not in _singleton_cache:
        platform = get_platform_name()
        if platform == "windows":
            from .windows import HotkeyHelperWindows

            _singleton_cache[key] = HotkeyHelperWindows()
        elif platform == "linux" and _is_pure_wayland():
            from .wayland import HotkeyHelperWayland

            _singleton_cache[key] = HotkeyHelperWayland()
        elif platform == "linux":
            from .linux import HotkeyHelperLinux

            _singleton_cache[key] = HotkeyHelperLinux()
        else:
            raise RuntimeError(f"Unsupported platform: {platform}")
    return _singleton_cache[key]  # type: ignore[return-value]
