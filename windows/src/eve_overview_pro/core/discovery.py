"""
Auto-Discovery - Background process to detect new EVE windows
v2.2 Feature: Automatic detection of new EVE clients
Windows Edition - Uses Win32 API
"""
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, Set, Tuple

from PySide6.QtCore import QObject, QTimer, Signal

try:
    import win32con
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


@dataclass
class DiscoveredCharacter:
    """Information about a discovered character"""
    name: str
    window_id: str
    window_title: str
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)


class AutoDiscovery(QObject):
    """
    Background service to automatically detect new EVE windows.

    Features:
    - Scans for EVE windows every N seconds (configurable)
    - Detects new characters that weren't seen before
    - Emits signals when new characters are found
    - Tracks known characters with timestamps
    - Supports catchall group for auto-assignment
    """

    # Signals
    new_character_found = Signal(str, str, str)  # char_name, window_id, window_title
    character_gone = Signal(str, str)  # char_name, window_id
    scan_completed = Signal(int)  # total_windows_found

    # EVE window detection patterns
    EVE_TITLE_PATTERNS = [
        r'^EVE - (.+)$',           # Standard: "EVE - Character Name"
        r'^EVE Online - (.+)$',    # Alternative: "EVE Online - Character Name"
    ]

    # EVE executable names for window class detection
    EVE_CLASS_NAMES = [
        'triuiScreen',  # EVE main window class
    ]

    def __init__(self, interval_seconds: int = 5, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.interval = interval_seconds * 1000  # Convert to milliseconds
        self.enabled = True

        # State
        self.known_characters: Dict[str, DiscoveredCharacter] = {}
        self.active_window_ids: Set[str] = set()

        # Callbacks
        self._on_new_callback: Optional[Callable] = None

        # Timer for background scanning
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self._scan_cycle)

        if not HAS_WIN32:
            self.logger.warning("win32gui not available - auto-discovery disabled")
            self.enabled = False

        self.logger.info(f"AutoDiscovery initialized with {interval_seconds}s interval")

    def start(self):
        """Start the auto-discovery background process"""
        if not self.enabled:
            self.logger.info("AutoDiscovery is disabled")
            return

        # Do an initial scan immediately
        self._scan_cycle()

        # Start timer for subsequent scans
        self.scan_timer.start(self.interval)
        self.logger.info("AutoDiscovery started")

    def stop(self):
        """Stop the auto-discovery process"""
        self.scan_timer.stop()
        self.logger.info("AutoDiscovery stopped")

    def set_interval(self, seconds: int):
        """
        Set the scan interval

        Args:
            seconds: Interval in seconds (1-60)
        """
        self.interval = max(1, min(60, seconds)) * 1000
        if self.scan_timer.isActive():
            self.scan_timer.setInterval(self.interval)
        self.logger.info(f"Scan interval set to {seconds} seconds")

    def set_enabled(self, enabled: bool):
        """
        Enable or disable auto-discovery

        Args:
            enabled: True to enable
        """
        self.enabled = enabled and HAS_WIN32
        if not self.enabled and self.scan_timer.isActive():
            self.stop()
        elif self.enabled and not self.scan_timer.isActive():
            self.start()

    def set_on_new_callback(self, callback: Callable):
        """
        Set callback for when new characters are found

        Args:
            callback: Function(char_name, window_id, window_title)
        """
        self._on_new_callback = callback

    def _scan_cycle(self):
        """Perform one scan cycle"""
        try:
            windows = self._get_eve_windows()
            current_ids = set()

            for window_id, window_title in windows:
                current_ids.add(window_id)

                # Extract character name
                char_name = self._extract_character_name(window_title)
                if not char_name:
                    continue

                # Check if this is a new character
                is_new = window_id not in self.active_window_ids

                if is_new:
                    # New character found
                    self.logger.info(f"New EVE character detected: {char_name} ({window_id})")

                    # Add to known characters
                    self.known_characters[window_id] = DiscoveredCharacter(
                        name=char_name,
                        window_id=window_id,
                        window_title=window_title
                    )

                    # Emit signal
                    self.new_character_found.emit(char_name, window_id, window_title)

                    # Call callback if set
                    if self._on_new_callback:
                        try:
                            self._on_new_callback(char_name, window_id, window_title)
                        except Exception as e:
                            self.logger.error(f"Callback error: {e}")

                elif window_id in self.known_characters:
                    # Update last seen
                    self.known_characters[window_id].last_seen = datetime.now()

            # Check for characters that went away
            gone_ids = self.active_window_ids - current_ids
            for window_id in gone_ids:
                if window_id in self.known_characters:
                    char = self.known_characters[window_id]
                    self.logger.info(f"EVE character gone: {char.name} ({window_id})")
                    self.character_gone.emit(char.name, window_id)

            # Update active window set
            self.active_window_ids = current_ids

            # Emit scan completed
            self.scan_completed.emit(len(windows))

        except Exception as e:
            self.logger.error(f"Scan cycle error: {e}")

    def _get_eve_windows(self) -> List[Tuple[str, str]]:
        """
        Get all EVE Online windows using Win32 API

        Returns:
            List of (window_id, window_title) tuples
        """
        eve_windows = []

        if not HAS_WIN32:
            return eve_windows

        def enum_callback(hwnd, results):
            """Callback for EnumWindows"""
            if not win32gui.IsWindowVisible(hwnd):
                return True

            try:
                title = win32gui.GetWindowText(hwnd)
                if title and self._is_eve_window(title):
                    window_id = hex(hwnd)
                    results.append((window_id, title))
            except Exception:
                pass

            return True

        try:
            win32gui.EnumWindows(enum_callback, eve_windows)
        except Exception as e:
            self.logger.error(f"Failed to enumerate windows: {e}")

        return eve_windows

    def _is_eve_window(self, title: str) -> bool:
        """
        Check if a window title belongs to EVE Online

        Args:
            title: Window title

        Returns:
            True if it's an EVE window
        """
        # Check title patterns
        for pattern in self.EVE_TITLE_PATTERNS:
            if re.match(pattern, title):
                return True

        return False

    def _extract_character_name(self, title: str) -> Optional[str]:
        """
        Extract character name from window title

        Args:
            title: Window title

        Returns:
            Character name or None
        """
        for pattern in self.EVE_TITLE_PATTERNS:
            match = re.match(pattern, title)
            if match:
                return match.group(1).strip()

        return None

    def get_known_characters(self) -> List[DiscoveredCharacter]:
        """
        Get list of all known characters

        Returns:
            List of DiscoveredCharacter
        """
        return list(self.known_characters.values())

    def get_active_characters(self) -> List[DiscoveredCharacter]:
        """
        Get list of currently active characters

        Returns:
            List of active DiscoveredCharacter
        """
        return [
            char for wid, char in self.known_characters.items()
            if wid in self.active_window_ids
        ]

    def force_scan(self) -> int:
        """
        Force an immediate scan

        Returns:
            Number of EVE windows found
        """
        self._scan_cycle()
        return len(self.active_window_ids)

    def clear_history(self):
        """Clear the known characters history"""
        self.known_characters.clear()
        self.active_window_ids.clear()
        self.logger.info("Character history cleared")

    def to_dict(self) -> Dict:
        """
        Serialize known characters to dict for config storage

        Returns:
            Dict with character data
        """
        return {
            "known_characters": [
                {
                    "name": char.name,
                    "window_id": char.window_id,
                    "first_seen": char.first_seen.isoformat(),
                    "last_seen": char.last_seen.isoformat()
                }
                for char in self.known_characters.values()
            ]
        }

    def from_dict(self, data: Dict):
        """
        Load known characters from dict

        Args:
            data: Dict with character data
        """
        if "known_characters" in data:
            for char_data in data["known_characters"]:
                try:
                    char = DiscoveredCharacter(
                        name=char_data["name"],
                        window_id=char_data["window_id"],
                        window_title=f"EVE - {char_data['name']}",
                        first_seen=datetime.fromisoformat(char_data.get("first_seen", datetime.now().isoformat())),
                        last_seen=datetime.fromisoformat(char_data.get("last_seen", datetime.now().isoformat()))
                    )
                    self.known_characters[char.window_id] = char
                except Exception as e:
                    self.logger.error(f"Failed to load character: {e}")


def scan_eve_windows() -> List[Tuple[str, str, str]]:
    """
    One-shot scan for all EVE windows.
    Convenience function for one-click import.

    Returns:
        List of (window_id, window_title, character_name) tuples
    """
    logger = logging.getLogger(__name__)
    results = []

    if not HAS_WIN32:
        logger.warning("win32gui not available for window scanning")
        return results

    def enum_callback(hwnd, results_list):
        """Callback for EnumWindows"""
        if not win32gui.IsWindowVisible(hwnd):
            return True

        try:
            title = win32gui.GetWindowText(hwnd)
            if title:
                for pattern in AutoDiscovery.EVE_TITLE_PATTERNS:
                    match = re.match(pattern, title)
                    if match:
                        char_name = match.group(1).strip()
                        window_id = hex(hwnd)
                        results_list.append((window_id, title, char_name))
                        break
        except Exception:
            pass

        return True

    try:
        win32gui.EnumWindows(enum_callback, results)
    except Exception as e:
        logger.error(f"scan_eve_windows failed: {e}")

    return results
