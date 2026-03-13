"""
Unit tests for the intel systems module.

Tests cover:
- Loading systems from a valid JSON file
- Fallback when JSON file is missing
- Fallback when JSON file is corrupt
- get_default_data_path returns expected location
"""

import json
from pathlib import Path

from argus_overview.intel.systems import (
    _FALLBACK_SYSTEMS,
    get_default_data_path,
    load_systems,
)


class TestGetDefaultDataPath:
    """Tests for get_default_data_path."""

    def test_returns_path_object(self):
        """Should return a Path instance."""
        result = get_default_data_path()
        assert isinstance(result, Path)

    def test_points_to_data_dir(self):
        """Should point to intel/data/systems.json."""
        result = get_default_data_path()
        assert result.name == "systems.json"
        assert result.parent.name == "data"

    def test_bundled_file_exists(self):
        """The bundled systems.json should actually exist."""
        assert get_default_data_path().exists()


class TestLoadSystemsValidJSON:
    """Tests for load_systems with valid JSON input."""

    def test_load_from_default_path(self):
        """Should load systems from the bundled JSON file."""
        systems = load_systems()
        assert isinstance(systems, set)
        assert len(systems) > 50
        assert "jita" in systems
        assert "amarr" in systems

    def test_load_from_custom_path(self, tmp_path):
        """Should load systems from a custom JSON file."""
        data = ["Alpha", "Beta", "Gamma-1"]
        json_file = tmp_path / "custom.json"
        json_file.write_text(json.dumps(data))

        systems = load_systems(data_path=json_file)
        assert systems == {"alpha", "beta", "gamma-1"}

    def test_all_names_lowercased(self):
        """Every system name should be lowercased."""
        systems = load_systems()
        for name in systems:
            assert name == name.lower(), f"{name!r} is not lowercase"

    def test_contains_trade_hubs(self):
        """Should contain major trade hub systems."""
        systems = load_systems()
        for hub in ("jita", "amarr", "dodixie", "rens", "hek"):
            assert hub in systems, f"Missing trade hub: {hub}"

    def test_contains_nullsec_systems(self):
        """Should contain famous null-sec systems."""
        systems = load_systems()
        for sys_name in ("hed-gp", "1dq1-a", "b-r5rb"):
            assert sys_name in systems, f"Missing null-sec system: {sys_name}"

    def test_contains_multi_word_systems(self):
        """Should contain multi-word system names."""
        systems = load_systems()
        assert "old man star" in systems


class TestLoadSystemsMissingFile:
    """Tests for load_systems when the JSON file is missing."""

    def test_fallback_on_missing_file(self, tmp_path):
        """Should return fallback set when file does not exist."""
        missing = tmp_path / "nonexistent.json"
        systems = load_systems(data_path=missing)
        assert systems == _FALLBACK_SYSTEMS

    def test_fallback_has_core_systems(self, tmp_path):
        """Fallback set should include essential systems."""
        missing = tmp_path / "nonexistent.json"
        systems = load_systems(data_path=missing)
        assert "jita" in systems
        assert "amarr" in systems
        assert "hed-gp" in systems


class TestLoadSystemsCorruptJSON:
    """Tests for load_systems when the JSON file is corrupt."""

    def test_fallback_on_invalid_json(self, tmp_path):
        """Should return fallback set for malformed JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json!!!")

        systems = load_systems(data_path=bad_file)
        assert systems == _FALLBACK_SYSTEMS

    def test_fallback_on_wrong_type(self, tmp_path):
        """Should return fallback set when JSON is not an array."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text('{"systems": ["Jita"]}')

        systems = load_systems(data_path=bad_file)
        assert systems == _FALLBACK_SYSTEMS

    def test_filters_non_string_entries(self, tmp_path):
        """Should skip non-string entries in the array."""
        data_file = tmp_path / "mixed.json"
        data_file.write_text(json.dumps(["Jita", 42, None, "Amarr"]))

        systems = load_systems(data_path=data_file)
        assert systems == {"jita", "amarr"}


class TestFallbackSetIntegrity:
    """Tests that the fallback set is sane."""

    def test_fallback_not_empty(self):
        """Fallback set should not be empty."""
        assert len(_FALLBACK_SYSTEMS) > 10

    def test_fallback_all_lowercase(self):
        """All fallback entries should be lowercase."""
        for name in _FALLBACK_SYSTEMS:
            assert name == name.lower()

    def test_load_returns_copy(self, tmp_path):
        """Returned set should be a copy, not the original."""
        missing = tmp_path / "nonexistent.json"
        s1 = load_systems(data_path=missing)
        s1.add("mutated")
        s2 = load_systems(data_path=missing)
        assert "mutated" not in s2
