"""
EVE Settings Synchronization
Copies EVE Online client settings between characters
Scans local EVE installation for ALL character data (even logged off)

v3.0: Cross-platform support via platform abstraction layer.
"""

import logging
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from argus_overview.platform import get_eve_path_resolver


@dataclass
class EVECharacterSettings:
    """EVE character settings location"""

    character_name: str
    character_id: str
    settings_dir: Path
    core_char_file: Path
    core_user_file: Path | None = None
    user_id: str | None = None
    has_settings: bool = False
    last_login: datetime | None = None


@dataclass
class EVECharacterInfo:
    """Basic character info extracted from EVE files"""

    character_id: str
    character_name: str
    user_id: str | None = None
    settings_path: Path | None = None
    last_seen: datetime | None = None
    has_settings: bool = False


class EVESettingsSync:
    """Manages EVE Online settings synchronization and character discovery"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Use platform abstraction for path resolution
        path_resolver = get_eve_path_resolver()

        # Get platform-specific EVE paths
        self.eve_paths = path_resolver.get_eve_settings_paths()
        self.eve_logs_paths = path_resolver.get_eve_logs_paths()

        self.custom_paths: list[Path] = []
        self.character_settings: dict[str, EVECharacterSettings] = {}
        self.character_id_to_name: dict[str, str] = {}  # Cache of ID -> name mappings
        self._load_character_names_from_logs()

    def add_custom_path(self, path: Path):
        """Add custom EVE settings path"""
        if path.exists() and path.is_dir():
            self.custom_paths.append(path)
            self.logger.info(f"Added custom EVE path: {path}")

    def _load_character_names_from_logs(self):
        """Load character ID -> name mappings from game logs"""
        for logs_dir in self.eve_logs_paths:
            if not logs_dir.exists():
                continue

            self.logger.info(f"Scanning logs at: {logs_dir}")
            self._process_log_files(logs_dir)

        self.logger.info(f"Loaded {len(self.character_id_to_name)} character names from logs")

    def _process_log_files(self, logs_dir: Path):
        """Process all log files in directory to extract character names."""
        for log_file in logs_dir.glob("*.txt"):
            # Extract character ID from filename like 20251208_053612_94468033.txt
            match = re.search(r"_(\d{7,})\.txt$", log_file.name)
            if not match:
                continue
            char_id = match.group(1)
            if char_id in self.character_id_to_name:
                continue  # Already have this one

            char_name = self._parse_log_for_char_name(log_file)
            if char_name:
                self.character_id_to_name[char_id] = char_name

    def get_character_name(self, char_id: str) -> str:
        """Get character name from ID, returns ID if not found"""
        return self.character_id_to_name.get(char_id, f"Character_{char_id}")

    def _is_path_accessible(self, path: Path) -> bool:
        """Check if a path exists and is readable.

        Args:
            path: Path to check

        Returns:
            True if path exists and is accessible
        """
        try:
            return path.exists() and path.is_dir() and any(path.iterdir())
        except (OSError, PermissionError) as e:
            self.logger.debug(f"Path not accessible {path}: {e}")
            return False

    def _iter_settings_dirs(self):
        """Yield all valid EVE settings directories.

        Iterates through EVE paths, server directories, and settings directories.
        Yields (settings_dir, base_path) tuples.
        """
        all_paths = self.eve_paths + self.custom_paths
        for base_path in all_paths:
            if not self._is_path_accessible(base_path):
                continue
            try:
                for server_dir in base_path.iterdir():
                    if not server_dir.is_dir():
                        continue
                    for settings_dir in server_dir.iterdir():
                        if settings_dir.is_dir() and settings_dir.name.startswith("settings"):
                            yield settings_dir, base_path
            except OSError as e:
                self.logger.debug(f"Error iterating {base_path}: {e}")

    def _parse_log_for_char_name(self, log_file: Path) -> str | None:
        """Parse a log file to extract the character name from Listener line."""
        try:
            with open(log_file, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f):
                    if i > 10:  # Only check first 10 lines
                        break
                    if "Listener:" in line:
                        char_name = line.split("Listener:")[1].strip()
                        return char_name if char_name else None
        except OSError as e:
            self.logger.debug(f"Error reading log {log_file}: {e}")
        return None

    def _create_char_info(self, char_file: Path, settings_dir: Path) -> EVECharacterInfo | None:
        """Create EVECharacterInfo from a core_char_*.dat file."""
        match = re.search(r"core_char_(\d+)\.dat$", char_file.name)
        if not match:
            return None

        char_id = match.group(1)
        char_name = self.get_character_name(char_id)

        try:
            mtime = char_file.stat().st_mtime
            last_seen = datetime.fromtimestamp(mtime)
        except OSError:
            last_seen = None

        return EVECharacterInfo(
            character_id=char_id,
            character_name=char_name,
            settings_path=settings_dir,
            last_seen=last_seen,
            has_settings=True,
        )

    def get_all_known_characters(self) -> list[EVECharacterInfo]:
        """Get all known characters from EVE installation (even logged off ones)

        This scans the EVE settings directory for core_char_*.dat files
        and cross-references with game logs to get character names.

        Returns:
            List of EVECharacterInfo for all found characters
        """
        characters = []
        logged_paths = set()

        for settings_dir, base_path in self._iter_settings_dirs():
            if base_path not in logged_paths:
                self.logger.info(f"Scanning for characters at: {base_path}")
                logged_paths.add(base_path)

            for char_file in settings_dir.glob("core_char_*.dat"):
                char_info = self._create_char_info(char_file, settings_dir)
                if char_info:
                    characters.append(char_info)
                    self.logger.debug(
                        f"Found character: {char_info.character_name} (ID: {char_info.character_id})"
                    )

        self.logger.info(f"Found {len(characters)} characters in EVE settings")
        return characters

    def scan_for_characters(self) -> list[EVECharacterSettings]:
        """Scan for EVE character settings

        Scans settings directories for core_char_*.dat files and returns
        one EVECharacterSettings per character found.

        Returns:
            List of found character settings
        """
        found_characters = []
        logged_paths = set()

        for settings_dir, base_path in self._iter_settings_dirs():
            if base_path not in logged_paths:
                self.logger.info(f"Scanning EVE path: {base_path}")
                logged_paths.add(base_path)

            for char_file in settings_dir.glob("core_char_*.dat"):
                char_settings = self._parse_char_file(char_file, settings_dir)
                if char_settings:
                    found_characters.append(char_settings)
                    self.character_settings[char_settings.character_name] = char_settings

        self.logger.info(f"Found {len(found_characters)} character settings")
        return found_characters

    def _parse_char_file(
        self, char_file: Path, settings_dir: Path
    ) -> EVECharacterSettings | None:
        """Parse a core_char_*.dat file to extract character settings

        Args:
            char_file: Path to core_char_*.dat file
            settings_dir: Parent settings directory

        Returns:
            EVECharacterSettings if valid, None otherwise
        """
        try:
            # Extract character ID from filename (core_char_12345678.dat)
            match = re.search(r"core_char_(\d+)\.dat$", char_file.name)
            if not match:
                return None

            char_id = match.group(1)
            char_name = self.get_character_name(char_id)

            # Find corresponding user file if exists
            user_files = list(settings_dir.glob("core_user_*.dat"))
            core_user_file = user_files[0] if user_files else None

            char_settings = EVECharacterSettings(
                character_name=char_name,
                character_id=char_id,
                settings_dir=settings_dir,
                core_char_file=char_file,
                core_user_file=core_user_file,
                has_settings=True,
            )

            return char_settings

        except (OSError, ValueError) as e:
            self.logger.error(f"Error parsing char file {char_file}: {e}")
            return None

    def sync_settings(
        self, source_char: str, target_chars: list[str], backup: bool = True
    ) -> dict[str, bool]:
        """Synchronize settings from source to target characters

        Args:
            source_char: Source character name
            target_chars: List of target character names
            backup: Create backups before overwriting

        Returns:
            Dict mapping target character names to success status
        """
        results: dict[str, bool] = {}

        if source_char not in self.character_settings:
            self.logger.error(f"Source character '{source_char}' not found")
            return results

        source = self.character_settings[source_char]

        if not source.has_settings:
            self.logger.error(f"Source character '{source_char}' has no settings")
            return results

        for target_char in target_chars:
            if target_char not in self.character_settings:
                self.logger.warning(f"Target character '{target_char}' not found")
                results[target_char] = False
                continue

            target = self.character_settings[target_char]

            try:
                # Create backup if requested
                if backup:
                    self._backup_settings(target)

                # Copy settings files
                success = self._copy_settings(source, target)
                results[target_char] = success

                if success:
                    self.logger.info(f"Synced settings to '{target_char}'")
                else:
                    self.logger.error(f"Failed to sync settings to '{target_char}'")

            except OSError as e:
                self.logger.error(f"Error syncing to '{target_char}': {e}")
                results[target_char] = False

        return results

    def _backup_settings(self, char_settings: EVECharacterSettings):
        """Create backup of character's settings file

        Args:
            char_settings: Character settings to backup
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Backup the specific character's .dat file, not the whole directory
        source_file = char_settings.core_char_file
        backup_file = source_file.parent / f"{source_file.stem}_backup_{timestamp}.dat"

        try:
            shutil.copy2(source_file, backup_file)
            self.logger.info(f"Created backup: {backup_file}")
        except OSError as e:
            self.logger.error(f"Backup failed: {e}")
            raise

    def _copy_settings(self, source: EVECharacterSettings, target: EVECharacterSettings) -> bool:
        """Copy settings from source character to target character

        Since all characters share the same settings directory, this copies
        the CONTENT of source's core_char_<id>.dat to target's core_char_<id>.dat

        Args:
            source: Source character settings
            target: Target character settings

        Returns:
            True if successful
        """
        try:
            # Copy content of source's .dat file to target's .dat file
            # This preserves window layouts, keybinds, overview settings, etc.
            source_file = source.core_char_file
            target_file = target.core_char_file

            if not source_file.exists():
                self.logger.error(f"Source file not found: {source_file}")
                return False

            # Read source content and write to target
            # This copies all settings (overview, keybinds, window layouts)
            shutil.copy2(source_file, target_file)
            self.logger.info(f"Copied {source_file.name} -> {target_file.name}")

            return True

        except OSError as e:
            self.logger.error(f"Settings copy error: {e}")
            return False

    def get_settings_summary(self, char_name: str) -> dict | None:
        """Get summary of character's settings

        Args:
            char_name: Character name

        Returns:
            Dict with settings info, or None if not found
        """
        if char_name not in self.character_settings:
            return None

        char_settings = self.character_settings[char_name]

        # Count settings files
        settings_files = list(char_settings.settings_dir.glob("*.dat"))
        settings_files += list(char_settings.settings_dir.glob("*.ini"))
        settings_files += list(char_settings.settings_dir.glob("*.yaml"))

        return {
            "character": char_name,
            "settings_dir": str(char_settings.settings_dir),
            "has_settings": char_settings.has_settings,
            "total_files": len(settings_files),
            "last_modified": max((f.stat().st_mtime for f in settings_files), default=0)
            if settings_files
            else 0,
        }

    def list_available_characters(self) -> list[str]:
        """Get list of characters with available settings

        Returns:
            List of character names
        """
        return [name for name, settings in self.character_settings.items() if settings.has_settings]
