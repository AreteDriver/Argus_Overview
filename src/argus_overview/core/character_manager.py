"""
Character and Team Management System
Handles EVE character database, account grouping, and activity-based teams
"""

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def sanitize_character_name(name: str) -> str:
    """Sanitize a character name to prevent path traversal and injection.

    Removes path separators, null bytes, and other dangerous characters.
    Returns a safe name or raises ValueError if result is empty.
    """
    # Remove path separators and null bytes
    sanitized = re.sub(r"[/\\:\x00]", "", name)
    # Remove leading/trailing dots and spaces (prevents .. traversal)
    sanitized = sanitized.strip(". ")
    # Limit length
    sanitized = sanitized[:100]

    if not sanitized:
        raise ValueError(f"Invalid character name: '{name}' produces empty name after sanitization")

    return sanitized


@dataclass
class Character:
    """EVE Online character"""

    name: str
    account: str = ""  # Account name (each account has 3 chars)
    role: str = "DPS"  # Miner, Scout, DPS, Logi, Hauler, etc.
    notes: str = ""
    is_main: bool = False
    window_id: Optional[str] = None  # Assigned when logged in
    last_seen: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Character":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Team:
    """Activity-based team of characters"""

    name: str
    description: str = ""
    characters: List[str] = field(default_factory=list)  # Character names
    layout_name: str = "Default"  # Associated layout preset
    color: str = "#4287f5"  # Team color for UI
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Team":
        """Create from dictionary"""
        return cls(**data)


class CharacterManager:
    """Manages character database and teams"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)

        if config_dir is None:
            config_dir = Path.home() / ".config" / "argus-overview"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.characters_file = self.config_dir / "characters.json"
        self.teams_file = self.config_dir / "teams.json"

        self.characters: Dict[str, Character] = {}
        self.teams: Dict[str, Team] = {}

        self._load_data()

    @staticmethod
    def _validate_character_data(data) -> bool:
        """Validate character dict has required fields with correct types."""
        if not isinstance(data, dict):
            return False
        if "name" not in data or not isinstance(data["name"], str) or not data["name"]:
            return False
        type_checks = {
            "account": str,
            "role": str,
            "notes": str,
            "is_main": bool,
        }
        for key, expected_type in type_checks.items():
            if key in data and data[key] is not None:
                if not isinstance(data[key], expected_type):
                    return False
        return True

    @staticmethod
    def _validate_team_data(data) -> bool:
        """Validate team dict has required fields with correct types."""
        if not isinstance(data, dict):
            return False
        if "name" not in data or not isinstance(data["name"], str) or not data["name"]:
            return False
        type_checks = {
            "description": str,
            "layout_name": str,
            "color": str,
        }
        for key, expected_type in type_checks.items():
            if key in data and data[key] is not None:
                if not isinstance(data[key], expected_type):
                    return False
        if "characters" in data and not isinstance(data.get("characters"), list):
            return False
        return True

    def _load_data(self):
        """Load characters and teams from disk"""
        # Load characters
        if self.characters_file.exists():
            try:
                with open(self.characters_file) as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        self.logger.warning("Characters file is not a JSON object, using defaults")
                    else:
                        for name, char_data in data.items():
                            if self._validate_character_data(char_data):
                                self.characters[name] = Character.from_dict(char_data)
                            else:
                                self.logger.warning(
                                    f"Skipping invalid character entry '{name}': "
                                    "missing or malformed fields"
                                )
                self.logger.info(f"Loaded {len(self.characters)} characters")
            except Exception as e:
                self.logger.error(f"Failed to load characters: {e}")

        # Load teams
        if self.teams_file.exists():
            try:
                with open(self.teams_file) as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        self.logger.warning("Teams file is not a JSON object, using defaults")
                    else:
                        for name, team_data in data.items():
                            if self._validate_team_data(team_data):
                                self.teams[name] = Team.from_dict(team_data)
                            else:
                                self.logger.warning(
                                    f"Skipping invalid team entry '{name}': "
                                    "missing or malformed fields"
                                )
                self.logger.info(f"Loaded {len(self.teams)} teams")
            except Exception as e:
                self.logger.error(f"Failed to load teams: {e}")

    def save_data(self) -> bool:
        """Save characters and teams to disk"""
        try:
            # Save characters
            with open(self.characters_file, "w") as f:
                data = {name: char.to_dict() for name, char in self.characters.items()}
                json.dump(data, f, indent=2)

            # Save teams
            with open(self.teams_file, "w") as f:
                data = {name: team.to_dict() for name, team in self.teams.items()}
                json.dump(data, f, indent=2)

            self.logger.info("Saved character and team data")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            return False

    # Character Management
    def add_character(self, character: Character) -> bool:
        """Add a character to the database"""
        try:
            sanitized = sanitize_character_name(character.name)
        except ValueError:
            self.logger.error(f"Rejected invalid character name: '{character.name}'")
            return False

        character.name = sanitized

        if character.name in self.characters:
            self.logger.warning(f"Character '{character.name}' already exists")
            return False

        self.characters[character.name] = character
        self.save_data()
        self.logger.info(f"Added character '{character.name}'")
        return True

    def remove_character(self, char_name: str) -> bool:
        """Remove a character"""
        if char_name not in self.characters:
            return False

        # Remove from all teams
        for team in self.teams.values():
            if char_name in team.characters:
                team.characters.remove(char_name)

        del self.characters[char_name]
        self.save_data()
        self.logger.info(f"Removed character '{char_name}'")
        return True

    def update_character(self, char_name: str, **kwargs) -> bool:
        """Update character properties"""
        if char_name not in self.characters:
            return False

        char = self.characters[char_name]
        for key, value in kwargs.items():
            if hasattr(char, key):
                setattr(char, key, value)

        self.save_data()
        return True

    def get_character(self, char_name: str) -> Optional[Character]:
        """Get character by name"""
        return self.characters.get(char_name)

    def get_all_characters(self) -> List[Character]:
        """Get all characters"""
        return list(self.characters.values())

    def get_characters_by_account(self, account: str) -> List[Character]:
        """Get all characters in an account"""
        return [char for char in self.characters.values() if char.account == account]

    def get_accounts(self) -> List[str]:
        """Get all account names"""
        accounts = set()
        for char in self.characters.values():
            if char.account:
                accounts.add(char.account)
        return sorted(accounts)

    # Team Management
    def create_team(self, team: Team) -> bool:
        """Create a new team"""
        if team.name in self.teams:
            self.logger.warning(f"Team '{team.name}' already exists")
            return False

        self.teams[team.name] = team
        self.save_data()
        self.logger.info(f"Created team '{team.name}'")
        return True

    def delete_team(self, team_name: str) -> bool:
        """Delete a team"""
        if team_name not in self.teams:
            return False

        del self.teams[team_name]
        self.save_data()
        self.logger.info(f"Deleted team '{team_name}'")
        return True

    def update_team(self, team_name: str, **kwargs) -> bool:
        """Update team properties"""
        if team_name not in self.teams:
            return False

        team = self.teams[team_name]
        for key, value in kwargs.items():
            if hasattr(team, key):
                setattr(team, key, value)

        self.save_data()
        return True

    def add_character_to_team(self, team_name: str, char_name: str) -> bool:
        """Add character to a team"""
        if team_name not in self.teams or char_name not in self.characters:
            return False

        team = self.teams[team_name]
        if char_name not in team.characters:
            team.characters.append(char_name)
            self.save_data()
            return True
        return False

    def remove_character_from_team(self, team_name: str, char_name: str) -> bool:
        """Remove character from a team"""
        if team_name not in self.teams:
            return False

        team = self.teams[team_name]
        if char_name in team.characters:
            team.characters.remove(char_name)
            self.save_data()
            return True
        return False

    def get_team(self, team_name: str) -> Optional[Team]:
        """Get team by name"""
        return self.teams.get(team_name)

    def get_all_teams(self) -> List[Team]:
        """Get all teams"""
        return list(self.teams.values())

    def get_teams_for_character(self, char_name: str) -> List[Team]:
        """Get all teams containing a character"""
        return [team for team in self.teams.values() if char_name in team.characters]

    # Window Assignment
    def assign_window(self, char_name: str, window_id: str) -> bool:
        """Assign a window ID to a character"""
        if char_name not in self.characters:
            return False

        self.characters[char_name].window_id = window_id
        self.characters[char_name].last_seen = datetime.now().isoformat()
        self.save_data()
        return True

    def unassign_window(self, char_name: str) -> bool:
        """Unassign window from character"""
        if char_name not in self.characters:
            return False

        self.characters[char_name].window_id = None
        self.save_data()
        return True

    def get_character_by_window(self, window_id: str) -> Optional[Character]:
        """Find character by window ID"""
        for char in self.characters.values():
            if char.window_id == window_id:
                return char
        return None

    def get_active_characters(self) -> List[Character]:
        """Get characters currently logged in (with window IDs)"""
        return [char for char in self.characters.values() if char.window_id]

    # Import from EVE files
    def import_from_eve_sync(self, eve_characters: List) -> int:
        """Import characters discovered from EVE installation files

        Args:
            eve_characters: List of EVECharacterInfo objects from EVESettingsSync

        Returns:
            Number of new characters imported
        """
        imported = 0
        required_attrs = ("character_name", "character_id", "last_seen")

        for eve_char in eve_characters:
            # Validate required attributes exist
            missing = [attr for attr in required_attrs if not hasattr(eve_char, attr)]
            if missing:
                self.logger.warning(
                    f"Skipping malformed EVE character: missing attributes {missing}"
                )
                continue

            try:
                char_name = sanitize_character_name(eve_char.character_name)
            except (ValueError, TypeError):
                self.logger.warning(
                    f"Skipping EVE character with invalid name: {eve_char.character_name!r}"
                )
                continue

            # Validate character_id is present
            if eve_char.character_id is None:
                self.logger.warning(f"Skipping EVE character '{char_name}': missing character_id")
                continue

            # Skip if already exists
            if char_name in self.characters:
                # Update last_seen if we have new data
                try:
                    if eve_char.last_seen:
                        self.characters[char_name].last_seen = eve_char.last_seen.isoformat()
                except AttributeError:
                    self.logger.warning(f"Invalid last_seen for existing character '{char_name}'")
                continue

            # Build last_seen safely
            last_seen_str = None
            if eve_char.last_seen is not None:
                try:
                    last_seen_str = eve_char.last_seen.isoformat()
                except AttributeError:
                    self.logger.warning(f"Invalid last_seen for '{char_name}', ignoring timestamp")

            # Create new character entry
            character = Character(
                name=char_name,
                account="",  # Unknown from files
                role="DPS",  # Default role
                notes=f"Imported from EVE. ID: {eve_char.character_id}",
                is_main=False,
                window_id=None,
                last_seen=last_seen_str,
            )

            self.characters[char_name] = character
            imported += 1
            self.logger.info(f"Imported character from EVE: {char_name}")

        if imported > 0:
            self.save_data()
            self.logger.info(f"Imported {imported} new characters from EVE files")

        return imported

    # Auto-detection
    def auto_assign_windows(self, windows: List[tuple]) -> Dict[str, str]:
        """Auto-assign windows to characters based on window titles

        Args:
            windows: List of (window_id, window_title) tuples

        Returns:
            Dict mapping character names to window IDs
        """
        assignments = {}

        for window_id, window_title in windows:
            # Try to extract character name from EVE window title
            # Format: "EVE - CharacterName" or just "CharacterName"
            char_name = window_title.replace("EVE -", "").strip()
            if not char_name:
                continue

            # Check if this character exists
            if char_name in self.characters:
                self.assign_window(char_name, window_id)
                assignments[char_name] = window_id
                self.logger.info(f"Auto-assigned window {window_id} to {char_name}")

        return assignments
