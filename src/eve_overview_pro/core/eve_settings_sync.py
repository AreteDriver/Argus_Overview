"""
EVE Settings Synchronization
Copies EVE Online client settings between characters
Scans local EVE installation for ALL character data (even logged off)
"""
import logging
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class EVECharacterSettings:
    """EVE character settings location"""
    character_name: str
    character_id: str
    settings_dir: Path
    core_char_file: Path
    core_user_file: Optional[Path] = None
    user_id: Optional[str] = None
    has_settings: bool = False
    last_login: Optional[datetime] = None


@dataclass
class EVECharacterInfo:
    """Basic character info extracted from EVE files"""
    character_id: str
    character_name: str
    user_id: Optional[str] = None
    settings_path: Optional[Path] = None
    last_seen: Optional[datetime] = None
    has_settings: bool = False


class EVESettingsSync:
    """Manages EVE Online settings synchronization and character discovery"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Steam/Proton paths (most common on Linux)
        steam_base = Path.home() / '.steam' / 'debian-installation' / 'steamapps' / 'compatdata'
        steam_alt = Path.home() / '.local' / 'share' / 'Steam' / 'steamapps' / 'compatdata'

        # EVE Online Steam App ID is 8500
        eve_steam_paths = [
            steam_base / '8500' / 'pfx' / 'drive_c' / 'users' / 'steamuser' /
            'AppData' / 'Local' / 'CCP' / 'EVE',
            steam_alt / '8500' / 'pfx' / 'drive_c' / 'users' / 'steamuser' /
            'AppData' / 'Local' / 'CCP' / 'EVE',
        ]

        # Steam game logs paths
        self.eve_logs_paths = [
            steam_base / '8500' / 'pfx' / 'drive_c' / 'users' / 'steamuser' /
            'Documents' / 'EVE' / 'logs' / 'Gamelogs',
            steam_alt / '8500' / 'pfx' / 'drive_c' / 'users' / 'steamuser' /
            'Documents' / 'EVE' / 'logs' / 'Gamelogs',
        ]

        # Common EVE installation paths (Wine, CrossOver, native)
        legacy_paths = [
            Path.home() / '.eve' / 'wineenv' / 'drive_c' / 'users' / 'crossover' /
            'Local Settings' / 'Application Data' / 'CCP' / 'EVE',

            Path.home() / '.wine' / 'drive_c' / 'users' / Path.home().name /
            'Local Settings' / 'Application Data' / 'CCP' / 'EVE',

            Path.home() / '.wine' / 'drive_c' / 'users' / Path.home().name /
            'AppData' / 'Local' / 'CCP' / 'EVE',

            Path.home() / 'EVE' / 'settings',
            Path.home() / '.local' / 'share' / 'CCP' / 'EVE',
        ]

        self.eve_paths = eve_steam_paths + legacy_paths

        self.custom_paths: List[Path] = []
        self.character_settings: Dict[str, EVECharacterSettings] = {}
        self.character_id_to_name: Dict[str, str] = {}  # Cache of ID -> name mappings
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

            for log_file in logs_dir.glob("*.txt"):
                # Extract character ID from filename like 20251208_053612_94468033.txt
                match = re.search(r'_(\d{7,})\.txt$', log_file.name)
                if match:
                    char_id = match.group(1)
                    if char_id in self.character_id_to_name:
                        continue  # Already have this one

                    # Read first few lines to find Listener name
                    try:
                        with open(log_file, encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f):
                                if i > 10:  # Only check first 10 lines
                                    break
                                if 'Listener:' in line:
                                    char_name = line.split('Listener:')[1].strip()
                                    self.character_id_to_name[char_id] = char_name
                                    break
                    except Exception as e:
                        self.logger.debug(f"Error reading log {log_file}: {e}")

        self.logger.info(f"Loaded {len(self.character_id_to_name)} character names from logs")

    def get_character_name(self, char_id: str) -> str:
        """Get character name from ID, returns ID if not found"""
        return self.character_id_to_name.get(char_id, f"Character_{char_id}")

    def get_all_known_characters(self) -> List[EVECharacterInfo]:
        """Get all known characters from EVE installation (even logged off ones)

        This scans the EVE settings directory for core_char_*.dat files
        and cross-references with game logs to get character names.

        Returns:
            List of EVECharacterInfo for all found characters
        """
        characters = []
        all_paths = self.eve_paths + self.custom_paths

        for base_path in all_paths:
            if not base_path.exists():
                continue

            self.logger.info(f"Scanning for characters at: {base_path}")

            # Look for tranquility (main server) settings
            for server_dir in base_path.iterdir():
                if not server_dir.is_dir():
                    continue

                # Look for settings_Default or similar
                for settings_dir in server_dir.iterdir():
                    if not settings_dir.is_dir():
                        continue
                    if not settings_dir.name.startswith('settings'):
                        continue

                    # Scan for core_char_*.dat files
                    for char_file in settings_dir.glob("core_char_*.dat"):
                        # Extract character ID from filename
                        match = re.search(r'core_char_(\d+)\.dat$', char_file.name)
                        if not match:
                            continue

                        char_id = match.group(1)
                        char_name = self.get_character_name(char_id)

                        # Get file modification time as last seen
                        try:
                            mtime = char_file.stat().st_mtime
                            last_seen = datetime.fromtimestamp(mtime)
                        except OSError:
                            last_seen = None

                        char_info = EVECharacterInfo(
                            character_id=char_id,
                            character_name=char_name,
                            settings_path=settings_dir,
                            last_seen=last_seen,
                            has_settings=True
                        )
                        characters.append(char_info)

                        self.logger.debug(f"Found character: {char_name} (ID: {char_id})")

        self.logger.info(f"Found {len(characters)} characters in EVE settings")
        return characters

    def scan_for_characters(self) -> List[EVECharacterSettings]:
        """Scan for EVE character settings

        Scans settings directories for core_char_*.dat files and returns
        one EVECharacterSettings per character found.

        Returns:
            List of found character settings
        """
        found_characters = []
        all_paths = self.eve_paths + self.custom_paths

        for base_path in all_paths:
            if not base_path.exists():
                continue

            self.logger.info(f"Scanning EVE path: {base_path}")

            try:
                for server_dir in base_path.iterdir():
                    if not server_dir.is_dir():
                        continue

                    for settings_dir in server_dir.iterdir():
                        if not settings_dir.is_dir():
                            continue
                        if not settings_dir.name.startswith('settings'):
                            continue

                        # Scan for core_char_*.dat files inside settings directory
                        for char_file in settings_dir.glob('core_char_*.dat'):
                            char_settings = self._parse_char_file(char_file, settings_dir)
                            if char_settings:
                                found_characters.append(char_settings)
                                self.character_settings[char_settings.character_name] = char_settings

            except Exception as e:
                self.logger.error(f"Error scanning {base_path}: {e}")

        self.logger.info(f"Found {len(found_characters)} character settings")
        return found_characters

    def _parse_char_file(self, char_file: Path, settings_dir: Path) -> Optional[EVECharacterSettings]:
        """Parse a core_char_*.dat file to extract character settings

        Args:
            char_file: Path to core_char_*.dat file
            settings_dir: Parent settings directory

        Returns:
            EVECharacterSettings if valid, None otherwise
        """
        try:
            # Extract character ID from filename (core_char_12345678.dat)
            match = re.search(r'core_char_(\d+)\.dat$', char_file.name)
            if not match:
                return None

            char_id = match.group(1)
            char_name = self.get_character_name(char_id)

            # Find corresponding user file if exists
            user_files = list(settings_dir.glob('core_user_*.dat'))
            core_user_file = user_files[0] if user_files else None

            char_settings = EVECharacterSettings(
                character_name=char_name,
                character_id=char_id,
                settings_dir=settings_dir,
                core_char_file=char_file,
                core_user_file=core_user_file,
                has_settings=True
            )

            return char_settings

        except Exception as e:
            self.logger.error(f"Error parsing char file {char_file}: {e}")
            return None

    def sync_settings(self, source_char: str, target_chars: List[str],
                     backup: bool = True) -> Dict[str, bool]:
        """Synchronize settings from source to target characters

        Args:
            source_char: Source character name
            target_chars: List of target character names
            backup: Create backups before overwriting

        Returns:
            Dict mapping target character names to success status
        """
        results = {}

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

            except Exception as e:
                self.logger.error(f"Error syncing to '{target_char}': {e}")
                results[target_char] = False

        return results

    def _backup_settings(self, char_settings: EVECharacterSettings):
        """Create backup of character settings

        Args:
            char_settings: Character settings to backup
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = char_settings.settings_dir.parent / f"backup_{char_settings.character_name}_{timestamp}"

        try:
            shutil.copytree(char_settings.settings_dir, backup_dir)
            self.logger.info(f"Created backup: {backup_dir}")
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            raise

    def _copy_settings(self, source: EVECharacterSettings,
                      target: EVECharacterSettings) -> bool:
        """Copy settings files from source to target

        Args:
            source: Source character settings
            target: Target character settings

        Returns:
            True if successful
        """
        try:
            source_dir = source.settings_dir
            target_dir = target.settings_dir

            # Files to copy
            files_to_copy = [
                'core_char_*.dat',
                'core_user_*.dat',
                'prefs.ini',
                'overview.yaml',
                'shortcuts.yaml',
                'wnd_*.dat',  # Window layouts
                'chat_*.txt',  # Chat settings
            ]

            copied_count = 0

            for pattern in files_to_copy:
                for source_file in source_dir.glob(pattern):
                    target_file = target_dir / source_file.name

                    try:
                        shutil.copy2(source_file, target_file)
                        copied_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to copy {source_file.name}: {e}")

            self.logger.info(f"Copied {copied_count} settings files")
            return copied_count > 0

        except Exception as e:
            self.logger.error(f"Settings copy error: {e}")
            return False

    def get_settings_summary(self, char_name: str) -> Optional[Dict]:
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
        settings_files = list(char_settings.settings_dir.glob('*.dat'))
        settings_files += list(char_settings.settings_dir.glob('*.ini'))
        settings_files += list(char_settings.settings_dir.glob('*.yaml'))

        return {
            'character': char_name,
            'settings_dir': str(char_settings.settings_dir),
            'has_settings': char_settings.has_settings,
            'total_files': len(settings_files),
            'last_modified': max(
                (f.stat().st_mtime for f in settings_files),
                default=0
            ) if settings_files else 0
        }

    def list_available_characters(self) -> List[str]:
        """Get list of characters with available settings

        Returns:
            List of character names
        """
        return [name for name, settings in self.character_settings.items()
                if settings.has_settings]
