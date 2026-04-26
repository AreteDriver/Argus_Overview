"""
Character Location Tracker — per-character current-system tracking from EVE logs.

EVE Online writes a separate Local channel chat log per character session.
Each Local log file has:

    1. A header block declaring the listener (the character) and channel:

         ---------------------------------------------------------------
           Channel ID:    Local
           Channel Name:  Local
           Listener:      MyCharName
           Session Started: 2024.01.15 14:30:00
         ---------------------------------------------------------------

    2. Lines of the form
         [ 2024.01.15 14:30:05 ] EVE System > Channel changed to Local : Jita
       whenever the character jumps into a new system.

This tracker polls today's Local_*.txt files, parses the listener header
once per file, then tails each file for "Channel changed to Local" lines
and maintains a {character_name -> current_system} map. It emits
character_system_changed when a character's system updates.

Files are UTF-16-LE (matches ChatLogWatcher).

PR4 of the intel-aware UI uplift. Pairs with the chip strip + preview
borders so threat fan-out and chip system labels can become per-character.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

# Header line: "  Listener:      MyCharName"
# Whitespace before label, around colon, and before/after name is variable.
_LISTENER_RE = re.compile(r"^\s*Listener:\s*(?P<name>.+?)\s*$")

# Channel-changed line as it appears inside a Local log:
#   [ 2024.01.15 14:30:05 ] EVE System > Channel changed to Local : Jita
_CHANNEL_CHANGED_RE = re.compile(
    r"\[\s*\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}\s*\]"
    r"\s*EVE\s+System\s*>\s*Channel changed to Local\s*:\s*(?P<system>.+?)\s*$"
)

# Local logs are written one-per-character. Filename pattern:
#   Local_YYYYMMDD_HHMMSS_<charid>.txt   (current EVE clients, charid optional)
_LOCAL_FILE_GLOB = "Local_*.txt"

# How many bytes from the start of the file to scan for the Listener header.
# The header is small (~300 bytes incl. UTF-16 BOM); 4KB is generous.
_HEADER_SCAN_BYTES = 4096


def find_eve_chat_log_directory() -> Path | None:
    """Locate the EVE Online chat log directory.

    Mirrors ChatLogWatcher.find_log_directory but lives here so the tracker
    can be used without instantiating a watcher.
    """
    candidates = [
        Path.home() / ".eve" / "logs" / "Chatlogs",
        Path.home()
        / ".local"
        / "share"
        / "Steam"
        / "steamapps"
        / "compatdata"
        / "8500"
        / "pfx"
        / "drive_c"
        / "users"
        / "steamuser"
        / "Documents"
        / "EVE"
        / "logs"
        / "Chatlogs",
        Path.home()
        / ".steam"
        / "steam"
        / "steamapps"
        / "compatdata"
        / "8500"
        / "pfx"
        / "drive_c"
        / "users"
        / "steamuser"
        / "Documents"
        / "EVE"
        / "logs"
        / "Chatlogs",
        Path.home() / "Documents" / "EVE" / "logs" / "Chatlogs",
    ]
    for path in candidates:
        if path.exists() and path.is_dir():
            return path
    return None


@dataclass
class _FileState:
    """Tail-cursor state for one Local log file."""

    listener: str | None
    position: int  # next read offset


class CharacterLocationTracker(QObject):
    """Per-character current-system tracker.

    Polls Local_*.txt files in the EVE chat log directory, parses the
    Listener header once per file, then tails each file for
    "Channel changed to Local : <System>" lines.

    Signals:
        character_system_changed(str, str): (character_name, system)
            Emitted when a character moves to a new system. Also fires
            once per character on initial detection.
    """

    character_system_changed = Signal(str, str)  # char_name, system

    def __init__(
        self,
        log_directory: Path | None = None,
        poll_interval_ms: int = 2000,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._explicit_log_dir = log_directory
        self._log_directory: Path | None = log_directory
        self.poll_interval_ms = max(250, int(poll_interval_ms))

        # Per-file cursor state, keyed by absolute path.
        self._file_state: dict[Path, _FileState] = {}
        # Authoritative location map: character_name -> current_system
        self._locations: dict[str, str] = {}

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll)
        self._running = False

    # ---- Public API --------------------------------------------------------
    def get_system(self, character_name: str) -> str | None:
        """Return the last known system for character_name, or None."""
        return self._locations.get(character_name)

    def get_all_locations(self) -> dict[str, str]:
        """Snapshot of all known {character_name: system} pairs."""
        return dict(self._locations)

    def start(self) -> None:
        """Begin polling for Local log changes."""
        if self._running:
            return
        if self._log_directory is None:
            self._log_directory = find_eve_chat_log_directory()
        if self._log_directory is None:
            self.logger.warning(
                "CharacterLocationTracker: no EVE chat log directory found; tracker will idle."
            )
            return
        self._running = True
        self._poll_timer.start(self.poll_interval_ms)
        # Run once immediately so chips populate without a 2s wait
        self._poll()

    def stop(self) -> None:
        """Stop polling. Safe to call multiple times."""
        if not self._running:
            return
        self._running = False
        self._poll_timer.stop()

    def is_running(self) -> bool:
        return self._running

    # ---- Internals ---------------------------------------------------------
    def _poll(self) -> None:
        """Scan today's Local log files and emit any new system changes."""
        if self._log_directory is None or not self._log_directory.exists():
            return
        try:
            files = list(self._log_directory.glob(_LOCAL_FILE_GLOB))
        except OSError as e:
            self.logger.warning(f"Failed to list log directory: {e}")
            return

        for path in files:
            try:
                self._process_file(path)
            except (OSError, UnicodeDecodeError) as e:
                self.logger.debug(f"Skipping {path.name}: {e}")
                continue

    def _process_file(self, path: Path) -> None:
        """Read header (once) and tail the file for new channel-changed events."""
        state = self._file_state.get(path)
        if state is None:
            listener = self._read_listener(path)
            # Start at end-of-file so we don't replay history on first open.
            try:
                position = path.stat().st_size
            except OSError:
                return
            state = _FileState(listener=listener, position=position)
            self._file_state[path] = state
            # Optional: also seed initial system from header-adjacent lines?
            # Skipped — we wait for the first explicit "Channel changed" line
            # so we never claim a stale system.

        if state.listener is None:
            return  # Cannot map systems to a character without a listener.

        try:
            file_size = path.stat().st_size
        except OSError:
            return

        if file_size < state.position:
            # File rotated/truncated.
            state.position = 0

        if file_size == state.position:
            return  # No new content.

        try:
            with open(path, "rb") as fb:
                fb.seek(state.position)
                raw = fb.read()
                state.position = fb.tell()
        except OSError as e:
            self.logger.debug(f"Read failed for {path.name}: {e}")
            return

        try:
            text = raw.decode("utf-16-le", errors="ignore")
        except UnicodeDecodeError:
            return

        for line in text.splitlines():
            match = _CHANNEL_CHANGED_RE.search(line)
            if not match:
                continue
            system = match.group("system").strip()
            self._update_location(state.listener, system)

    def _read_listener(self, path: Path) -> str | None:
        """Parse the Listener: header from the start of a Local log file."""
        try:
            with open(path, "rb") as fb:
                raw = fb.read(_HEADER_SCAN_BYTES)
        except OSError:
            return None
        if not raw:
            return None
        try:
            text = raw.decode("utf-16-le", errors="ignore")
        except UnicodeDecodeError:
            return None
        for line in text.splitlines():
            m = _LISTENER_RE.match(line)
            if m:
                listener = m.group("name").strip()
                if listener:
                    return listener
        return None

    def _update_location(self, character_name: str, system: str) -> None:
        prev = self._locations.get(character_name)
        if prev == system:
            return
        self._locations[character_name] = system
        self.logger.info(
            f"CharacterLocationTracker: {character_name} -> {system} (was {prev or 'unknown'})"
        )
        self.character_system_changed.emit(character_name, system)
