"""
Unit tests for JSON schema validation on config file loading.

Tests cover malformed config handling for:
- CharacterManager: characters.json, teams.json
- LayoutManager: layout preset .json files

Verifies that invalid configs fall back to defaults with warnings logged,
rather than crashing with KeyError/TypeError.
"""

import json
import tempfile
from pathlib import Path

from argus_overview.core.character_manager import CharacterManager
from argus_overview.core.layout_manager import LayoutManager


class TestCharacterManagerValidation:
    """Tests for CharacterManager config validation"""

    def test_characters_file_is_array_not_dict(self):
        """Array instead of object falls back to empty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "characters.json").write_text(json.dumps(["a", "b"]))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 0

    def test_teams_file_is_array_not_dict(self):
        """Array instead of object falls back to empty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "teams.json").write_text(json.dumps(["a", "b"]))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.teams) == 0

    def test_characters_file_is_string(self):
        """String JSON value falls back to empty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "characters.json").write_text(json.dumps("just a string"))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 0

    def test_character_entry_missing_name(self):
        """Character entry without 'name' is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            data = {"Pilot1": {"role": "DPS", "account": ""}}
            (config_dir / "characters.json").write_text(json.dumps(data))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 0

    def test_character_entry_name_empty_string(self):
        """Character entry with empty name string is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            data = {"Pilot1": {"name": "", "role": "DPS"}}
            (config_dir / "characters.json").write_text(json.dumps(data))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 0

    def test_character_entry_name_is_int(self):
        """Character entry with non-string name is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            data = {"Pilot1": {"name": 12345, "role": "DPS"}}
            (config_dir / "characters.json").write_text(json.dumps(data))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 0

    def test_character_entry_is_not_dict(self):
        """Character entry that is a string instead of dict is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            data = {"Pilot1": "not a dict"}
            (config_dir / "characters.json").write_text(json.dumps(data))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 0

    def test_character_entry_wrong_type_is_main(self):
        """Character with is_main as string instead of bool is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            data = {
                "Pilot1": {
                    "name": "Pilot1",
                    "account": "",
                    "role": "DPS",
                    "notes": "",
                    "is_main": "yes",
                    "window_id": None,
                    "last_seen": None,
                }
            }
            (config_dir / "characters.json").write_text(json.dumps(data))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 0

    def test_valid_entries_loaded_invalid_skipped(self):
        """Mix of valid and invalid entries: valid loaded, invalid skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            data = {
                "Good": {
                    "name": "Good",
                    "account": "",
                    "role": "DPS",
                    "notes": "",
                    "is_main": False,
                    "window_id": None,
                    "last_seen": None,
                },
                "Bad": "not a dict",
            }
            (config_dir / "characters.json").write_text(json.dumps(data))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.characters) == 1
            assert "Good" in manager.characters

    def test_team_entry_missing_name(self):
        """Team entry without 'name' is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            data = {"Team1": {"description": "no name field", "characters": []}}
            (config_dir / "teams.json").write_text(json.dumps(data))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.teams) == 0

    def test_team_entry_characters_not_list(self):
        """Team entry with characters as string is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            data = {
                "Team1": {
                    "name": "Team1",
                    "description": "",
                    "characters": "not a list",
                    "layout_name": "Default",
                    "color": "#fff",
                    "created_at": "2025-01-01",
                }
            }
            (config_dir / "teams.json").write_text(json.dumps(data))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.teams) == 0

    def test_team_entry_is_not_dict(self):
        """Team entry that is an int is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            data = {"Team1": 42}
            (config_dir / "teams.json").write_text(json.dumps(data))
            manager = CharacterManager(config_dir=config_dir)
            assert len(manager.teams) == 0


class TestLayoutManagerValidation:
    """Tests for LayoutManager config validation"""

    def test_preset_file_is_array(self):
        """Array instead of object is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)
            (layouts_dir / "bad.json").write_text(json.dumps([1, 2, 3]))
            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 0

    def test_preset_missing_name(self):
        """Preset without name field is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)
            data = {"description": "no name", "windows": [], "refresh_rate": 30}
            (layouts_dir / "bad.json").write_text(json.dumps(data))
            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 0

    def test_preset_name_empty(self):
        """Preset with empty name is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)
            data = {"name": "", "windows": [], "refresh_rate": 30}
            (layouts_dir / "bad.json").write_text(json.dumps(data))
            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 0

    def test_preset_windows_not_list(self):
        """Preset with windows as string is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)
            data = {"name": "Bad", "windows": "not a list", "refresh_rate": 30}
            (layouts_dir / "bad.json").write_text(json.dumps(data))
            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 0

    def test_preset_window_entry_missing_fields(self):
        """Preset with window missing required fields is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)
            data = {
                "name": "Bad",
                "windows": [{"window_id": "0x1"}],  # missing x, y, width, height
                "refresh_rate": 30,
            }
            (layouts_dir / "bad.json").write_text(json.dumps(data))
            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 0

    def test_preset_window_entry_not_dict(self):
        """Preset with window entry as string is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)
            data = {"name": "Bad", "windows": ["not a dict"], "refresh_rate": 30}
            (layouts_dir / "bad.json").write_text(json.dumps(data))
            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 0

    def test_preset_refresh_rate_wrong_type(self):
        """Preset with refresh_rate as string is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)
            data = {"name": "Bad", "windows": [], "refresh_rate": "fast"}
            (layouts_dir / "bad.json").write_text(json.dumps(data))
            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 0

    def test_valid_preset_still_loads(self):
        """Valid preset file still loads correctly after adding validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)
            data = {
                "name": "Good",
                "description": "Valid preset",
                "windows": [
                    {
                        "window_id": "0x1",
                        "x": 0,
                        "y": 0,
                        "width": 400,
                        "height": 300,
                        "monitor": 0,
                        "opacity": 1.0,
                        "zoom": 0.3,
                        "always_on_top": True,
                    }
                ],
                "refresh_rate": 30,
                "grid_pattern": "custom",
                "created_at": "2025-01-01",
                "modified_at": "2025-01-01",
            }
            (layouts_dir / "Good.json").write_text(json.dumps(data))
            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 1
            assert "Good" in manager.presets

    def test_mix_valid_and_invalid_presets(self):
        """Valid presets load, invalid ones are skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)

            good = {
                "name": "Good",
                "description": "",
                "windows": [],
                "refresh_rate": 30,
                "grid_pattern": "custom",
                "created_at": "2025-01-01",
                "modified_at": "2025-01-01",
            }
            (layouts_dir / "Good.json").write_text(json.dumps(good))

            bad = {"no_name": True}
            (layouts_dir / "Bad.json").write_text(json.dumps(bad))

            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 1
            assert "Good" in manager.presets


class TestValidationStaticMethods:
    """Direct tests for validation static methods"""

    def test_validate_character_data_valid(self):
        data = {
            "name": "Pilot",
            "account": "Acc",
            "role": "DPS",
            "notes": "",
            "is_main": False,
            "window_id": None,
            "last_seen": None,
        }
        assert CharacterManager._validate_character_data(data) is True

    def test_validate_character_data_none(self):
        assert CharacterManager._validate_character_data(None) is False

    def test_validate_character_data_name_none(self):
        assert CharacterManager._validate_character_data({"name": None}) is False

    def test_validate_team_data_valid(self):
        data = {
            "name": "Team",
            "description": "",
            "characters": [],
            "layout_name": "Default",
            "color": "#fff",
            "created_at": "2025-01-01",
        }
        assert CharacterManager._validate_team_data(data) is True

    def test_validate_team_data_none(self):
        assert CharacterManager._validate_team_data(None) is False

    def test_validate_preset_data_valid(self):
        data = {"name": "Test", "windows": [], "refresh_rate": 30}
        assert LayoutManager._validate_preset_data(data) is True

    def test_validate_preset_data_none(self):
        assert LayoutManager._validate_preset_data(None) is False
