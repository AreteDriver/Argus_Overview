"""
Chat Log Watcher - Monitors EVE Online chat log files for new messages.

Uses watchdog for cross-platform file monitoring with efficient inotify
on Linux.

EVE Log Details:
    - Location: ~/.eve/logs/Chatlogs/ (native) or Steam/Proton paths
    - Encoding: UTF-16-LE
    - Filename format: {ChannelName}_{YYYYMMDD}_{HHMMSS}.txt
    - Line format: [ YYYY.MM.DD HH:MM:SS ] PlayerName > message
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from PySide6.QtCore import QObject, QTimer, Signal


@dataclass
class ChatMessage:
    """Represents a single chat message from EVE logs."""

    timestamp: datetime
    channel: str
    speaker: str
    message: str
    raw_line: str


class ChatLogWatcher(QObject):
    """
    Watches EVE chat logs for new messages.

    Uses polling with QTimer for Qt integration. Monitors active log files
    and emits signals when new messages arrive.

    Signals:
        message_received: Emitted when a new chat message is parsed
        error_occurred: Emitted when an error occurs during monitoring
    """

    message_received = Signal(object)  # ChatMessage
    error_occurred = Signal(str)

    # Regex pattern for parsing chat log lines
    # Format: [ YYYY.MM.DD HH:MM:SS ] PlayerName > message
    LINE_PATTERN = re.compile(
        r"\[\s*(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s*\]\s*(.+?)\s*>\s*(.+)"
    )

    def __init__(
        self,
        log_paths: Optional[List[Path]] = None,
        poll_interval_ms: int = 1000,
        parent: Optional[QObject] = None,
    ):
        """
        Initialize the chat log watcher.

        Args:
            log_paths: Optional list of additional log directories to search
            poll_interval_ms: Polling interval in milliseconds
            parent: Parent QObject
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.custom_log_paths = log_paths or []
        self.poll_interval_ms = poll_interval_ms

        # Track file positions for tailing
        self.file_positions: Dict[Path, int] = {}

        # Currently monitored channels (filenames without date suffix)
        self.monitored_channels: Set[str] = set()

        # Polling timer
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._poll_files)

        self._running = False
        self._log_directory: Optional[Path] = None

    def find_log_directory(self) -> Optional[Path]:
        """
        Auto-detect EVE log directory.

        Returns:
            Path to EVE chat logs directory, or None if not found
        """
        candidates = [
            # Native Linux EVE
            Path.home() / ".eve" / "logs" / "Chatlogs",
            # Steam/Proton
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
            # Alternative Proton path
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
        ]

        # Add custom paths
        candidates.extend(self.custom_log_paths)

        for path in candidates:
            if path.exists() and path.is_dir():
                self.logger.info(f"Found EVE chat logs at: {path}")
                return path

        self.logger.warning("Could not find EVE chat log directory")
        return None

    def get_active_channels(self) -> List[Path]:
        """
        Get today's log files (channels currently open).

        Returns:
            List of paths to today's log files
        """
        if not self._log_directory:
            self._log_directory = self.find_log_directory()
            if not self._log_directory:
                return []

        today = datetime.now().strftime("%Y%m%d")
        log_files = list(self._log_directory.glob(f"*_{today}_*.txt"))

        # Filter by monitored channels if specified
        if self.monitored_channels:
            log_files = [
                f for f in log_files if self._extract_channel_name(f) in self.monitored_channels
            ]

        return sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True)

    def _extract_channel_name(self, filepath: Path) -> str:
        """
        Extract channel name from log filename.

        Args:
            filepath: Path to log file

        Returns:
            Channel name (e.g., "Alliance", "Intel")
        """
        # Filename format: ChannelName_YYYYMMDD_HHMMSS.txt
        name = filepath.stem
        # Remove date and time suffix
        parts = name.rsplit("_", 2)
        if len(parts) >= 3:
            return parts[0]
        return name

    def parse_line(self, line: str, channel_name: str) -> Optional[ChatMessage]:
        """
        Parse a single chat log line.

        Args:
            line: Raw line from log file
            channel_name: Name of the channel this line is from

        Returns:
            ChatMessage if successfully parsed, None otherwise
        """
        line = line.strip()
        if not line:
            return None

        match = self.LINE_PATTERN.match(line)
        if not match:
            return None

        timestamp_str, speaker, message = match.groups()

        try:
            timestamp = datetime.strptime(timestamp_str, "%Y.%m.%d %H:%M:%S")
        except ValueError:
            self.logger.warning(f"Failed to parse timestamp: {timestamp_str}")
            return None

        return ChatMessage(
            timestamp=timestamp,
            channel=channel_name,
            speaker=speaker.strip(),
            message=message.strip(),
            raw_line=line,
        )

    def tail_file(self, filepath: Path) -> List[ChatMessage]:
        """
        Read new lines from a log file.

        Args:
            filepath: Path to log file

        Returns:
            List of new ChatMessages
        """
        messages = []

        if not filepath.exists():
            return messages

        try:
            file_size = filepath.stat().st_size

            # If file is new or smaller (rotated), start from end
            if filepath not in self.file_positions:
                self.file_positions[filepath] = file_size
                return messages

            if file_size < self.file_positions[filepath]:
                # File was truncated/rotated
                self.file_positions[filepath] = 0

            if file_size == self.file_positions[filepath]:
                # No new content
                return messages

            # Read new content
            # EVE logs are UTF-16-LE encoded
            with open(filepath, encoding="utf-16-le", errors="ignore") as f:
                f.seek(self.file_positions[filepath])
                new_lines = f.readlines()
                self.file_positions[filepath] = f.tell()

            channel_name = self._extract_channel_name(filepath)

            for line in new_lines:
                msg = self.parse_line(line, channel_name)
                if msg:
                    messages.append(msg)

        except PermissionError:
            self.logger.warning(f"Permission denied reading: {filepath}")
        except Exception as e:
            self.logger.error(f"Error reading {filepath}: {e}")
            self.error_occurred.emit(str(e))

        return messages

    def set_monitored_channels(self, channels: List[str]):
        """
        Set which channels to monitor.

        Args:
            channels: List of channel names (e.g., ["Alliance", "Intel"])
        """
        self.monitored_channels = {ch.lower() for ch in channels}
        self.logger.info(f"Monitoring channels: {self.monitored_channels}")

    def add_channel(self, channel: str):
        """Add a channel to monitor."""
        self.monitored_channels.add(channel.lower())

    def remove_channel(self, channel: str):
        """Remove a channel from monitoring."""
        self.monitored_channels.discard(channel.lower())

    def _poll_files(self):
        """Poll all active log files for new messages."""
        log_files = self.get_active_channels()

        for filepath in log_files:
            messages = self.tail_file(filepath)
            for msg in messages:
                self.message_received.emit(msg)

    def start(self):
        """Start watching for log changes."""
        if self._running:
            return

        self._log_directory = self.find_log_directory()
        if not self._log_directory:
            self.error_occurred.emit("Could not find EVE chat log directory")
            return

        self._running = True
        self.poll_timer.start(self.poll_interval_ms)
        self.logger.info(f"Started chat log watcher (interval: {self.poll_interval_ms}ms)")

    def stop(self):
        """Stop watching."""
        self._running = False
        self.poll_timer.stop()
        self.logger.info("Stopped chat log watcher")

    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running

    def get_log_directory(self) -> Optional[Path]:
        """Get the currently monitored log directory."""
        return self._log_directory

    def set_log_directory(self, path: Path):
        """
        Manually set the log directory.

        Args:
            path: Path to EVE chat logs directory
        """
        if path.exists() and path.is_dir():
            self._log_directory = path
            self.file_positions.clear()  # Reset positions for new directory
            self.logger.info(f"Log directory set to: {path}")
        else:
            self.logger.error(f"Invalid log directory: {path}")
