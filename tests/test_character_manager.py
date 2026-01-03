"""
Unit tests for the CharacterManager module.

Tests cover:
- Character dataclass serialization
- Team dataclass serialization
- CharacterManager CRUD operations
- Team management
- Character-team relationships
- Window assignment
"""
import json
import tempfile
from pathlib import Path

import pytest

from eve_overview_pro.core.character_manager import (
    Character,
    CharacterManager,
    Team,
)


class TestCharacterDataclass:
    """Tests for Character dataclass"""

    def test_create_minimal_character(self):
        """Character can be created with just a name"""
        char = Character(name="TestPilot")
        assert char.name == "TestPilot"
        assert char.account == ""
        assert char.role == "DPS"
        assert char.is_main is False
        assert char.window_id is None

    def test_create_full_character(self):
        """Character can be created with all fields"""
        char = Character(
            name="MainPilot",
            account="Account1",
            role="Logi",
            notes="Main healer",
            is_main=True,
            window_id="0x12345",
            last_seen="2025-01-01T00:00:00"
        )
        assert char.name == "MainPilot"
        assert char.account == "Account1"
        assert char.role == "Logi"
        assert char.notes == "Main healer"
        assert char.is_main is True
        assert char.window_id == "0x12345"

    def test_to_dict(self):
        """Character can be serialized to dict"""
        char = Character(name="TestPilot", role="Scout")
        data = char.to_dict()
        assert isinstance(data, dict)
        assert data["name"] == "TestPilot"
        assert data["role"] == "Scout"

    def test_from_dict(self):
        """Character can be deserialized from dict"""
        data = {
            "name": "TestPilot",
            "account": "Acc1",
            "role": "Miner",
            "notes": "",
            "is_main": False,
            "window_id": None,
            "last_seen": None
        }
        char = Character.from_dict(data)
        assert char.name == "TestPilot"
        assert char.account == "Acc1"
        assert char.role == "Miner"

    def test_roundtrip_serialization(self):
        """Character survives to_dict -> from_dict roundtrip"""
        original = Character(
            name="RoundTrip",
            account="TestAcc",
            role="Hauler",
            notes="Test notes",
            is_main=True,
            window_id="0xABCDE",
            last_seen="2025-12-28T12:00:00"
        )
        data = original.to_dict()
        restored = Character.from_dict(data)
        assert restored.name == original.name
        assert restored.account == original.account
        assert restored.role == original.role
        assert restored.notes == original.notes
        assert restored.is_main == original.is_main
        assert restored.window_id == original.window_id


class TestTeamDataclass:
    """Tests for Team dataclass"""

    def test_create_minimal_team(self):
        """Team can be created with just a name"""
        team = Team(name="Mining Fleet")
        assert team.name == "Mining Fleet"
        assert team.description == ""
        assert team.characters == []
        assert team.layout_name == "Default"

    def test_create_full_team(self):
        """Team can be created with all fields"""
        team = Team(
            name="PvP Squad",
            description="Small gang roam",
            characters=["Pilot1", "Pilot2"],
            layout_name="Combat",
            color="#ff0000"
        )
        assert team.name == "PvP Squad"
        assert team.description == "Small gang roam"
        assert len(team.characters) == 2
        assert team.layout_name == "Combat"
        assert team.color == "#ff0000"

    def test_to_dict(self):
        """Team can be serialized to dict"""
        team = Team(name="Test Team", characters=["A", "B"])
        data = team.to_dict()
        assert isinstance(data, dict)
        assert data["name"] == "Test Team"
        assert data["characters"] == ["A", "B"]

    def test_from_dict(self):
        """Team can be deserialized from dict"""
        data = {
            "name": "Loaded Team",
            "description": "From file",
            "characters": ["Char1"],
            "layout_name": "Grid",
            "color": "#00ff00",
            "created_at": "2025-01-01T00:00:00"
        }
        team = Team.from_dict(data)
        assert team.name == "Loaded Team"
        assert team.characters == ["Char1"]

    def test_roundtrip_serialization(self):
        """Team survives to_dict -> from_dict roundtrip"""
        original = Team(
            name="RoundTrip Team",
            description="Test",
            characters=["A", "B", "C"],
            layout_name="Cascade",
            color="#123456"
        )
        data = original.to_dict()
        restored = Team.from_dict(data)
        assert restored.name == original.name
        assert restored.characters == original.characters


class TestCharacterManagerInit:
    """Tests for CharacterManager initialization"""

    def test_creates_config_dir(self):
        """Manager creates config directory if missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "new_config"
            assert not config_dir.exists()
            CharacterManager(config_dir=config_dir)
            assert config_dir.exists()

    def test_loads_empty_state(self):
        """Manager starts with empty state if no files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CharacterManager(config_dir=Path(tmpdir))
            assert len(manager.characters) == 0
            assert len(manager.teams) == 0

    def test_loads_existing_data(self):
        """Manager loads existing character/team files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create character file
            chars_file = config_dir / "characters.json"
            chars_file.write_text(json.dumps({
                "Pilot1": {"name": "Pilot1", "account": "", "role": "DPS",
                          "notes": "", "is_main": False, "window_id": None,
                          "last_seen": None}
            }))

            # Create team file
            teams_file = config_dir / "teams.json"
            teams_file.write_text(json.dumps({
                "Team1": {"name": "Team1", "description": "", "characters": [],
                         "layout_name": "Default", "color": "#4287f5",
                         "created_at": "2025-01-01"}
            }))

            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 1
            assert "Pilot1" in manager.characters
            assert len(manager.teams) == 1
            assert "Team1" in manager.teams


class TestCharacterCRUD:
    """Tests for character CRUD operations"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield CharacterManager(config_dir=Path(tmpdir))

    def test_add_character(self, manager):
        """Can add a character"""
        char = Character(name="NewPilot")
        result = manager.add_character(char)
        assert result is True
        assert "NewPilot" in manager.characters

    def test_add_duplicate_character_fails(self, manager):
        """Adding duplicate character returns False"""
        char = Character(name="Duplicate")
        manager.add_character(char)
        result = manager.add_character(Character(name="Duplicate"))
        assert result is False

    def test_remove_character(self, manager):
        """Can remove a character"""
        manager.add_character(Character(name="ToRemove"))
        result = manager.remove_character("ToRemove")
        assert result is True
        assert "ToRemove" not in manager.characters

    def test_remove_nonexistent_character(self, manager):
        """Removing nonexistent character returns False"""
        result = manager.remove_character("DoesNotExist")
        assert result is False

    def test_update_character(self, manager):
        """Can update character properties"""
        manager.add_character(Character(name="ToUpdate", role="DPS"))
        result = manager.update_character("ToUpdate", role="Logi", notes="Updated")
        assert result is True
        char = manager.get_character("ToUpdate")
        assert char.role == "Logi"
        assert char.notes == "Updated"

    def test_update_nonexistent_character(self, manager):
        """Updating nonexistent character returns False"""
        result = manager.update_character("DoesNotExist", role="Scout")
        assert result is False

    def test_get_character(self, manager):
        """Can get character by name"""
        manager.add_character(Character(name="GetMe"))
        char = manager.get_character("GetMe")
        assert char is not None
        assert char.name == "GetMe"

    def test_get_nonexistent_character(self, manager):
        """Getting nonexistent character returns None"""
        char = manager.get_character("DoesNotExist")
        assert char is None

    def test_get_all_characters(self, manager):
        """Can get all characters"""
        manager.add_character(Character(name="A"))
        manager.add_character(Character(name="B"))
        manager.add_character(Character(name="C"))
        all_chars = manager.get_all_characters()
        assert len(all_chars) == 3

    def test_get_characters_by_account(self, manager):
        """Can filter characters by account"""
        manager.add_character(Character(name="A", account="Acc1"))
        manager.add_character(Character(name="B", account="Acc1"))
        manager.add_character(Character(name="C", account="Acc2"))
        acc1_chars = manager.get_characters_by_account("Acc1")
        assert len(acc1_chars) == 2

    def test_get_accounts(self, manager):
        """Can get list of accounts"""
        manager.add_character(Character(name="A", account="Alpha"))
        manager.add_character(Character(name="B", account="Beta"))
        manager.add_character(Character(name="C", account="Alpha"))
        accounts = manager.get_accounts()
        assert len(accounts) == 2
        assert "Alpha" in accounts
        assert "Beta" in accounts


class TestTeamCRUD:
    """Tests for team CRUD operations"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield CharacterManager(config_dir=Path(tmpdir))

    def test_create_team(self, manager):
        """Can create a team"""
        team = Team(name="NewTeam")
        result = manager.create_team(team)
        assert result is True
        assert "NewTeam" in manager.teams

    def test_create_duplicate_team_fails(self, manager):
        """Creating duplicate team returns False"""
        manager.create_team(Team(name="Duplicate"))
        result = manager.create_team(Team(name="Duplicate"))
        assert result is False

    def test_delete_team(self, manager):
        """Can delete a team"""
        manager.create_team(Team(name="ToDelete"))
        result = manager.delete_team("ToDelete")
        assert result is True
        assert "ToDelete" not in manager.teams

    def test_delete_nonexistent_team(self, manager):
        """Deleting nonexistent team returns False"""
        result = manager.delete_team("DoesNotExist")
        assert result is False

    def test_update_team(self, manager):
        """Can update team properties"""
        manager.create_team(Team(name="ToUpdate"))
        result = manager.update_team("ToUpdate", description="Updated desc")
        assert result is True
        team = manager.get_team("ToUpdate")
        assert team.description == "Updated desc"

    def test_get_team(self, manager):
        """Can get team by name"""
        manager.create_team(Team(name="GetMe"))
        team = manager.get_team("GetMe")
        assert team is not None
        assert team.name == "GetMe"

    def test_get_all_teams(self, manager):
        """Can get all teams"""
        manager.create_team(Team(name="A"))
        manager.create_team(Team(name="B"))
        all_teams = manager.get_all_teams()
        assert len(all_teams) == 2


class TestCharacterTeamRelationships:
    """Tests for character-team relationships"""

    @pytest.fixture
    def manager(self):
        """Create manager with characters and teams"""
        with tempfile.TemporaryDirectory() as tmpdir:
            m = CharacterManager(config_dir=Path(tmpdir))
            m.add_character(Character(name="Pilot1"))
            m.add_character(Character(name="Pilot2"))
            m.add_character(Character(name="Pilot3"))
            m.create_team(Team(name="Team1"))
            m.create_team(Team(name="Team2"))
            yield m

    def test_add_character_to_team(self, manager):
        """Can add character to team"""
        result = manager.add_character_to_team("Team1", "Pilot1")
        assert result is True
        team = manager.get_team("Team1")
        assert "Pilot1" in team.characters

    def test_add_nonexistent_character_to_team(self, manager):
        """Adding nonexistent character to team fails"""
        result = manager.add_character_to_team("Team1", "FakePilot")
        assert result is False

    def test_add_character_to_nonexistent_team(self, manager):
        """Adding character to nonexistent team fails"""
        result = manager.add_character_to_team("FakeTeam", "Pilot1")
        assert result is False

    def test_add_duplicate_character_to_team(self, manager):
        """Adding same character twice returns False"""
        manager.add_character_to_team("Team1", "Pilot1")
        result = manager.add_character_to_team("Team1", "Pilot1")
        assert result is False

    def test_remove_character_from_team(self, manager):
        """Can remove character from team"""
        manager.add_character_to_team("Team1", "Pilot1")
        result = manager.remove_character_from_team("Team1", "Pilot1")
        assert result is True
        team = manager.get_team("Team1")
        assert "Pilot1" not in team.characters

    def test_remove_character_not_in_team(self, manager):
        """Removing character not in team returns False"""
        result = manager.remove_character_from_team("Team1", "Pilot1")
        assert result is False

    def test_get_teams_for_character(self, manager):
        """Can get all teams containing a character"""
        manager.add_character_to_team("Team1", "Pilot1")
        manager.add_character_to_team("Team2", "Pilot1")
        teams = manager.get_teams_for_character("Pilot1")
        assert len(teams) == 2

    def test_removing_character_removes_from_teams(self, manager):
        """Removing character also removes from all teams"""
        manager.add_character_to_team("Team1", "Pilot1")
        manager.add_character_to_team("Team2", "Pilot1")
        manager.remove_character("Pilot1")
        team1 = manager.get_team("Team1")
        team2 = manager.get_team("Team2")
        assert "Pilot1" not in team1.characters
        assert "Pilot1" not in team2.characters


class TestWindowAssignment:
    """Tests for window assignment functionality"""

    @pytest.fixture
    def manager(self):
        """Create manager with characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            m = CharacterManager(config_dir=Path(tmpdir))
            m.add_character(Character(name="Pilot1"))
            m.add_character(Character(name="Pilot2"))
            yield m

    def test_assign_window(self, manager):
        """Can assign window to character"""
        result = manager.assign_window("Pilot1", "0x12345")
        assert result is True
        char = manager.get_character("Pilot1")
        assert char.window_id == "0x12345"
        assert char.last_seen is not None

    def test_assign_window_nonexistent_character(self, manager):
        """Assigning window to nonexistent character fails"""
        result = manager.assign_window("FakePilot", "0x12345")
        assert result is False

    def test_unassign_window(self, manager):
        """Can unassign window from character"""
        manager.assign_window("Pilot1", "0x12345")
        result = manager.unassign_window("Pilot1")
        assert result is True
        char = manager.get_character("Pilot1")
        assert char.window_id is None

    def test_get_character_by_window(self, manager):
        """Can find character by window ID"""
        manager.assign_window("Pilot1", "0x12345")
        char = manager.get_character_by_window("0x12345")
        assert char is not None
        assert char.name == "Pilot1"

    def test_get_character_by_unknown_window(self, manager):
        """Unknown window ID returns None"""
        char = manager.get_character_by_window("0xUNKNOWN")
        assert char is None

    def test_get_active_characters(self, manager):
        """Can get list of characters with windows"""
        manager.assign_window("Pilot1", "0x11111")
        # Pilot2 has no window
        active = manager.get_active_characters()
        assert len(active) == 1
        assert active[0].name == "Pilot1"


class TestAutoAssignWindows:
    """Tests for auto-assign window functionality"""

    @pytest.fixture
    def manager(self):
        """Create manager with characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            m = CharacterManager(config_dir=Path(tmpdir))
            m.add_character(Character(name="MainPilot"))
            m.add_character(Character(name="AltScout"))
            yield m

    def test_auto_assign_eve_format(self, manager):
        """Auto-assigns windows with EVE title format"""
        windows = [
            ("0x111", "EVE - MainPilot"),
            ("0x222", "EVE - AltScout"),
        ]
        assignments = manager.auto_assign_windows(windows)
        assert len(assignments) == 2
        assert assignments["MainPilot"] == "0x111"
        assert assignments["AltScout"] == "0x222"

    def test_auto_assign_unknown_character(self, manager):
        """Unknown characters are not assigned"""
        windows = [
            ("0x111", "EVE - UnknownPilot"),
        ]
        assignments = manager.auto_assign_windows(windows)
        assert len(assignments) == 0

    def test_auto_assign_mixed(self, manager):
        """Only known characters are assigned"""
        windows = [
            ("0x111", "EVE - MainPilot"),
            ("0x222", "EVE - UnknownAlt"),
        ]
        assignments = manager.auto_assign_windows(windows)
        assert len(assignments) == 1
        assert "MainPilot" in assignments


class TestExceptionHandling:
    """Tests for exception handling in load/save operations"""

    def test_handles_corrupted_characters_file(self):
        """Handles corrupted characters.json gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            chars_file = config_dir / "characters.json"
            chars_file.write_text("not valid json {{{")

            # Should not raise, just log error and start empty
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 0

    def test_handles_corrupted_teams_file(self):
        """Handles corrupted teams.json gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            teams_file = config_dir / "teams.json"
            teams_file.write_text("invalid json content")

            # Should not raise, just log error and start empty
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.teams) == 0

    def test_save_data_handles_write_error(self):
        """save_data returns False when write fails"""
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CharacterManager(config_dir=Path(tmpdir))

            # Mock open to raise an exception
            with patch("builtins.open", side_effect=PermissionError("No write access")):
                result = manager.save_data()
                assert result is False

    def test_uses_default_config_dir_when_none(self):
        """Uses home config dir when config_dir is None"""
        from unittest.mock import patch, MagicMock

        mock_home = Path("/fake/home")
        mock_path = mock_home / '.config' / 'eve-overview-pro'

        with patch.object(Path, 'home', return_value=mock_home):
            with patch.object(Path, 'mkdir'):
                with patch.object(Path, 'exists', return_value=False):
                    manager = CharacterManager(config_dir=None)
                    assert manager.config_dir == mock_path


class TestMissingEdgeCases:
    """Tests for edge cases not covered elsewhere"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield CharacterManager(config_dir=Path(tmpdir))

    def test_update_nonexistent_team(self, manager):
        """Updating nonexistent team returns False"""
        result = manager.update_team("NonexistentTeam", description="New desc")
        assert result is False

    def test_remove_character_from_nonexistent_team(self, manager):
        """Removing character from nonexistent team returns False"""
        manager.add_character(Character(name="Pilot1"))
        result = manager.remove_character_from_team("NonexistentTeam", "Pilot1")
        assert result is False

    def test_unassign_window_nonexistent_character(self, manager):
        """Unassigning window from nonexistent character returns False"""
        result = manager.unassign_window("NonexistentPilot")
        assert result is False


class TestImportFromEveSync:
    """Tests for import_from_eve_sync functionality"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield CharacterManager(config_dir=Path(tmpdir))

    def test_imports_new_characters(self, manager):
        """Imports new characters from EVE sync data"""
        from unittest.mock import MagicMock
        from datetime import datetime

        eve_char = MagicMock()
        eve_char.character_name = "NewEVEPilot"
        eve_char.character_id = 12345678
        eve_char.last_seen = datetime(2025, 1, 1, 12, 0, 0)

        imported = manager.import_from_eve_sync([eve_char])

        assert imported == 1
        assert "NewEVEPilot" in manager.characters
        char = manager.characters["NewEVEPilot"]
        assert "12345678" in char.notes
        assert char.last_seen is not None

    def test_skips_existing_characters(self, manager):
        """Skips characters that already exist"""
        from unittest.mock import MagicMock

        # Add existing character
        manager.add_character(Character(name="ExistingPilot"))

        eve_char = MagicMock()
        eve_char.character_name = "ExistingPilot"
        eve_char.character_id = 99999999
        eve_char.last_seen = None

        imported = manager.import_from_eve_sync([eve_char])

        assert imported == 0
        # Should still have only 1 character
        assert len(manager.characters) == 1

    def test_updates_last_seen_for_existing(self, manager):
        """Updates last_seen for existing characters"""
        from unittest.mock import MagicMock
        from datetime import datetime

        # Add existing character without last_seen
        manager.add_character(Character(name="ExistingPilot", last_seen=None))

        eve_char = MagicMock()
        eve_char.character_name = "ExistingPilot"
        eve_char.character_id = 99999999
        eve_char.last_seen = datetime(2025, 6, 15, 10, 30, 0)

        manager.import_from_eve_sync([eve_char])

        char = manager.characters["ExistingPilot"]
        assert char.last_seen == "2025-06-15T10:30:00"

    def test_handles_none_last_seen(self, manager):
        """Handles characters with no last_seen timestamp"""
        from unittest.mock import MagicMock

        eve_char = MagicMock()
        eve_char.character_name = "NoLastSeenPilot"
        eve_char.character_id = 11111111
        eve_char.last_seen = None

        imported = manager.import_from_eve_sync([eve_char])

        assert imported == 1
        char = manager.characters["NoLastSeenPilot"]
        assert char.last_seen is None

    def test_imports_multiple_characters(self, manager):
        """Imports multiple characters at once"""
        from unittest.mock import MagicMock
        from datetime import datetime

        eve_chars = []
        for i in range(3):
            eve_char = MagicMock()
            eve_char.character_name = f"Pilot{i}"
            eve_char.character_id = 10000000 + i
            eve_char.last_seen = datetime(2025, 1, i + 1)
            eve_chars.append(eve_char)

        imported = manager.import_from_eve_sync(eve_chars)

        assert imported == 3
        assert len(manager.characters) == 3

    def test_saves_after_import(self, manager):
        """Saves data after importing characters"""
        from unittest.mock import MagicMock, patch
        from datetime import datetime

        eve_char = MagicMock()
        eve_char.character_name = "SavedPilot"
        eve_char.character_id = 12345678
        eve_char.last_seen = datetime(2025, 1, 1)

        with patch.object(manager, 'save_data') as mock_save:
            manager.import_from_eve_sync([eve_char])
            mock_save.assert_called_once()

    def test_no_save_when_nothing_imported(self, manager):
        """Does not save when no new characters imported"""
        from unittest.mock import MagicMock, patch

        # Add existing character first
        manager.add_character(Character(name="ExistingPilot"))

        eve_char = MagicMock()
        eve_char.character_name = "ExistingPilot"
        eve_char.character_id = 99999999
        eve_char.last_seen = None

        with patch.object(manager, 'save_data') as mock_save:
            mock_save.reset_mock()  # Reset from add_character call
            manager.import_from_eve_sync([eve_char])
            mock_save.assert_not_called()


class TestDataPersistence:
    """Tests for data persistence"""

    def test_save_and_reload(self):
        """Data persists across manager instances"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create and populate manager
            m1 = CharacterManager(config_dir=config_dir)
            m1.add_character(Character(name="Persistent", role="Tank"))
            m1.create_team(Team(name="SavedTeam", characters=["Persistent"]))

            # Create new manager with same config dir
            m2 = CharacterManager(config_dir=config_dir)
            assert "Persistent" in m2.characters
            assert m2.characters["Persistent"].role == "Tank"
            assert "SavedTeam" in m2.teams
            assert "Persistent" in m2.teams["SavedTeam"].characters
