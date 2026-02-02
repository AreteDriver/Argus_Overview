"""Abstract base classes for platform-specific functionality.

This module defines the interfaces that platform implementations must provide.
Each abstract class represents a category of platform-specific operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image


@dataclass
class ScreenGeometry:
    """Screen/monitor geometry information."""

    x: int
    y: int
    width: int
    height: int
    is_primary: bool = False


@dataclass
class WindowInfo:
    """Information about a window."""

    window_id: str
    title: str
    class_name: str = ""


class WindowManager(ABC):
    """Abstract interface for window management operations.

    Implementations handle platform-specific window enumeration, positioning,
    and state changes (activate, minimize, restore).
    """

    @abstractmethod
    def get_window_list(self) -> List[Tuple[str, str]]:
        """Get list of all visible windows.

        Returns:
            List of (window_id, window_title) tuples
        """

    @abstractmethod
    def get_eve_windows(self) -> List[Tuple[str, str]]:
        """Get list of EVE Online windows.

        Returns:
            List of (window_id, window_title) tuples for EVE windows
        """

    @abstractmethod
    def move_window(
        self, window_id: str, x: int, y: int, w: int, h: int, timeout: float = 2.0
    ) -> bool:
        """Move and resize a window.

        Args:
            window_id: Platform-specific window identifier
            x: Target X position
            y: Target Y position
            w: Target width
            h: Target height
            timeout: Operation timeout in seconds

        Returns:
            True if successful
        """

    @abstractmethod
    def activate_window(self, window_id: str, timeout: float = 2.0) -> bool:
        """Activate (focus/bring to front) a window.

        Args:
            window_id: Platform-specific window identifier
            timeout: Operation timeout in seconds

        Returns:
            True if successful
        """

    @abstractmethod
    def minimize_window(self, window_id: str) -> bool:
        """Minimize a window.

        Args:
            window_id: Platform-specific window identifier

        Returns:
            True if successful
        """

    @abstractmethod
    def restore_window(self, window_id: str) -> bool:
        """Restore a minimized window.

        Args:
            window_id: Platform-specific window identifier

        Returns:
            True if successful
        """

    @abstractmethod
    def get_focused_window(self) -> Optional[str]:
        """Get the currently focused window ID.

        Returns:
            Window ID string or None if unable to determine
        """

    @abstractmethod
    def is_valid_window_id(self, window_id: str) -> bool:
        """Validate that a string is a valid window ID for this platform.

        Args:
            window_id: The window ID to validate

        Returns:
            True if valid format for this platform
        """

    @abstractmethod
    def get_window_title(self, window_id: str) -> str:
        """Get the title of a window.

        Args:
            window_id: Platform-specific window identifier

        Returns:
            Window title string
        """


class WindowCapture(ABC):
    """Abstract interface for window capture operations.

    Implementations handle platform-specific screen capture using
    appropriate APIs (ImageMagick/X11 on Linux, GDI on Windows).
    """

    @abstractmethod
    def start(self):
        """Start capture worker threads."""

    @abstractmethod
    def stop(self):
        """Stop capture worker threads."""

    @property
    @abstractmethod
    def running(self) -> bool:
        """Check if capture workers are running."""

    @abstractmethod
    def capture_window_async(self, window_id: str, scale: float = 1.0) -> str:
        """Request async window capture.

        Args:
            window_id: Platform-specific window identifier
            scale: Scale factor (0.0-1.0)

        Returns:
            Request ID (UUID) to retrieve result later, empty string if invalid
        """

    @abstractmethod
    def get_result(
        self, timeout: float = 0.1
    ) -> Optional[Tuple[str, str, Image.Image]]:
        """Get capture result if available.

        Args:
            timeout: Timeout in seconds

        Returns:
            Tuple of (request_id, window_id, image) or None
        """

    @abstractmethod
    def capture_window_sync(
        self, window_id: str, scale: float = 1.0
    ) -> Optional[Image.Image]:
        """Synchronous window capture.

        Args:
            window_id: Platform-specific window identifier
            scale: Scale factor (0.0-1.0)

        Returns:
            PIL Image or None if capture failed
        """


class ScreenManager(ABC):
    """Abstract interface for screen/display information.

    Implementations query display geometry using platform-appropriate
    methods (xrandr on Linux, EnumDisplayMonitors on Windows).
    """

    @abstractmethod
    def get_screen_geometry(self, monitor: int = 0) -> ScreenGeometry:
        """Get geometry for a specific monitor.

        Args:
            monitor: Monitor index (0-based)

        Returns:
            ScreenGeometry for requested monitor, or default on failure
        """

    @abstractmethod
    def get_all_monitors(self) -> List[ScreenGeometry]:
        """Get geometry for all connected monitors.

        Returns:
            List of ScreenGeometry for all monitors
        """


class EVEPathResolver(ABC):
    """Abstract interface for EVE Online path resolution.

    Implementations locate EVE settings and log directories using
    platform-specific paths (Proton/Wine on Linux, LOCALAPPDATA on Windows).
    """

    @abstractmethod
    def get_eve_settings_paths(self) -> List[Path]:
        """Get list of candidate EVE settings paths.

        Returns:
            List of paths that may contain EVE settings
        """

    @abstractmethod
    def get_eve_logs_paths(self) -> List[Path]:
        """Get list of candidate EVE game logs paths.

        Returns:
            List of paths that may contain EVE game logs
        """

    @abstractmethod
    def get_config_directory(self) -> Path:
        """Get application config directory.

        Returns:
            Path to store application configuration
        """


class HotkeyHelper(ABC):
    """Abstract interface for hotkey format handling.

    Implementations normalize hotkey strings to pynput-compatible format.
    Linux requires additional format fixes that Windows doesn't need.
    """

    @abstractmethod
    def normalize_combo(self, key_combo: str) -> str:
        """Normalize a hotkey combo string for pynput.

        Args:
            key_combo: Raw hotkey combo string (e.g., "<ctrl>+<v>")

        Returns:
            Normalized string compatible with pynput
        """

    @abstractmethod
    def is_single_key(self, key_combo: str) -> bool:
        """Check if a key combo is a single key (no modifiers).

        Args:
            key_combo: Hotkey combo string

        Returns:
            True if single key, False if combo with modifiers
        """
