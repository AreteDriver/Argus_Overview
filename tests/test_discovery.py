"""
Unit tests for the Discovery module.

Tests cover:
- DiscoveredCharacter dataclass
- AutoDiscovery initialization
- EVE window pattern matching
- Character name extraction
- Scan cycle behavior
- Known/active character tracking
- Serialization
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

from eve_overview_pro.core.discovery import (
    DiscoveredCharacter,
    AutoDiscovery,
    scan_eve_windows,
)


class TestDiscoveredCharacter:
    """Tests for DiscoveredCharacter dataclass"""

    def test_create_character(self):
        """DiscoveredCharacter can be created"""
        char = DiscoveredCharacter(
            name="TestPilot",
            window_id="0x123",
            window_title="EVE - TestPilot"
        )

        assert char.name == "TestPilot"
        assert char.window_id == "0x123"
        assert char.window_title == "EVE - TestPilot"

    def test_default_timestamps(self):
        """Timestamps default to now"""
        before = datetime.now()
        char = DiscoveredCharacter(
            name="Test",
            window_id="0x1",
            window_title="EVE - Test"
        )
        after = datetime.now()

        assert before <= char.first_seen <= after
        assert before <= char.last_seen <= after

    def test_custom_timestamps(self):
        """Can set custom timestamps"""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        char = DiscoveredCharacter(
            name="Test",
            window_id="0x1",
            window_title="EVE - Test",
            first_seen=custom_time,
            last_seen=custom_time
        )

        assert char.first_seen == custom_time
        assert char.last_seen == custom_time


class TestAutoDiscoveryInit:
    """Tests for AutoDiscovery initialization"""

    def test_default_interval(self):
        """Default interval is 5 seconds"""
        discovery = AutoDiscovery()
        assert discovery.interval == 5000  # milliseconds

    def test_custom_interval(self):
        """Can set custom interval"""
        discovery = AutoDiscovery(interval_seconds=10)
        assert discovery.interval == 10000

    def test_initial_state(self):
        """Starts with correct initial state"""
        discovery = AutoDiscovery()

        assert discovery.enabled is True
        assert discovery.known_characters == {}
        assert discovery.active_window_ids == set()
        assert discovery._on_new_callback is None


class TestSetInterval:
    """Tests for set_interval method"""

    def test_set_interval(self):
        """Can set interval"""
        discovery = AutoDiscovery()
        discovery.set_interval(15)
        assert discovery.interval == 15000

    def test_interval_min_clamp(self):
        """Interval clamped to minimum 1"""
        discovery = AutoDiscovery()
        discovery.set_interval(0)
        assert discovery.interval == 1000

    def test_interval_max_clamp(self):
        """Interval clamped to maximum 60"""
        discovery = AutoDiscovery()
        discovery.set_interval(100)
        assert discovery.interval == 60000


class TestEVEWindowPatterns:
    """Tests for EVE window title pattern matching"""

    @pytest.fixture
    def discovery(self):
        """Create a fresh discovery instance"""
        return AutoDiscovery()

    def test_is_eve_window_standard(self, discovery):
        """Matches standard EVE title"""
        assert discovery._is_eve_window("EVE - TestPilot") is True

    def test_is_eve_window_online(self, discovery):
        """Matches EVE Online title"""
        assert discovery._is_eve_window("EVE Online - TestPilot") is True

    def test_is_eve_window_not_eve(self, discovery):
        """Rejects non-EVE windows"""
        assert discovery._is_eve_window("Firefox") is False
        assert discovery._is_eve_window("Chrome - Google") is False
        assert discovery._is_eve_window("Terminal") is False

    def test_is_eve_window_partial(self, discovery):
        """Rejects partial matches"""
        assert discovery._is_eve_window("EVETHING") is False
        assert discovery._is_eve_window("MyEVE - Test") is False


class TestCharacterNameExtraction:
    """Tests for character name extraction"""

    @pytest.fixture
    def discovery(self):
        """Create a fresh discovery instance"""
        return AutoDiscovery()

    def test_extract_standard(self, discovery):
        """Extracts from standard format"""
        name = discovery._extract_character_name("EVE - Test Pilot")
        assert name == "Test Pilot"

    def test_extract_online(self, discovery):
        """Extracts from EVE Online format"""
        name = discovery._extract_character_name("EVE Online - Another Pilot")
        assert name == "Another Pilot"

    def test_extract_strips_whitespace(self, discovery):
        """Strips extra whitespace"""
        name = discovery._extract_character_name("EVE -  Spaced Name  ")
        assert name == "Spaced Name"

    def test_extract_no_match(self, discovery):
        """Returns None for non-EVE windows"""
        name = discovery._extract_character_name("Firefox")
        assert name is None

    def test_extract_special_characters(self, discovery):
        """Handles special characters in names"""
        name = discovery._extract_character_name("EVE - Drunk'n Sailor")
        assert name == "Drunk'n Sailor"


class TestCallbackRegistration:
    """Tests for callback registration"""

    def test_set_callback(self):
        """Can set callback"""
        discovery = AutoDiscovery()
        callback = MagicMock()

        discovery.set_on_new_callback(callback)

        assert discovery._on_new_callback == callback


class TestKnownCharacters:
    """Tests for known character management"""

    @pytest.fixture
    def discovery(self):
        """Create discovery with some characters"""
        d = AutoDiscovery()
        d.known_characters["0x1"] = DiscoveredCharacter(
            name="Pilot1", window_id="0x1", window_title="EVE - Pilot1"
        )
        d.known_characters["0x2"] = DiscoveredCharacter(
            name="Pilot2", window_id="0x2", window_title="EVE - Pilot2"
        )
        d.active_window_ids = {"0x1"}  # Only one active
        return d

    def test_get_known_characters(self, discovery):
        """Returns all known characters"""
        known = discovery.get_known_characters()
        assert len(known) == 2

    def test_get_active_characters(self, discovery):
        """Returns only active characters"""
        active = discovery.get_active_characters()
        assert len(active) == 1
        assert active[0].name == "Pilot1"

    def test_clear_history(self, discovery):
        """Clears all character data"""
        discovery.clear_history()

        assert len(discovery.known_characters) == 0
        assert len(discovery.active_window_ids) == 0


class TestSerialization:
    """Tests for to_dict/from_dict"""

    @pytest.fixture
    def discovery(self):
        """Create discovery with characters"""
        d = AutoDiscovery()
        d.known_characters["0x1"] = DiscoveredCharacter(
            name="Pilot1",
            window_id="0x1",
            window_title="EVE - Pilot1",
            first_seen=datetime(2025, 1, 1, 10, 0, 0),
            last_seen=datetime(2025, 1, 1, 12, 0, 0)
        )
        return d

    def test_to_dict(self, discovery):
        """Serializes to dict"""
        data = discovery.to_dict()

        assert "known_characters" in data
        assert len(data["known_characters"]) == 1
        assert data["known_characters"][0]["name"] == "Pilot1"
        assert data["known_characters"][0]["window_id"] == "0x1"

    def test_from_dict(self):
        """Loads from dict"""
        discovery = AutoDiscovery()
        data = {
            "known_characters": [
                {
                    "name": "LoadedPilot",
                    "window_id": "0x999",
                    "first_seen": "2025-01-01T10:00:00",
                    "last_seen": "2025-01-01T12:00:00"
                }
            ]
        }

        discovery.from_dict(data)

        assert "0x999" in discovery.known_characters
        assert discovery.known_characters["0x999"].name == "LoadedPilot"

    def test_from_dict_invalid_data(self):
        """Handles invalid data gracefully"""
        discovery = AutoDiscovery()
        data = {
            "known_characters": [
                {"invalid": "data"}  # Missing required fields
            ]
        }

        # Should not raise
        discovery.from_dict(data)
        assert len(discovery.known_characters) == 0


class TestScanCycle:
    """Tests for scan cycle behavior"""

    @pytest.fixture
    def discovery(self):
        """Create a fresh discovery instance"""
        return AutoDiscovery()

    def test_scan_empty_result(self, discovery):
        """Handles empty scan result"""
        with patch.object(discovery, '_get_eve_windows', return_value=[]):
            discovery._scan_cycle()
            assert len(discovery.active_window_ids) == 0

    def test_scan_detects_new_character(self, discovery):
        """Detects new character"""
        callback = MagicMock()
        discovery.set_on_new_callback(callback)

        with patch.object(discovery, '_get_eve_windows',
                         return_value=[("0x123", "EVE - NewPilot")]):
            discovery._scan_cycle()

            assert "0x123" in discovery.known_characters
            assert discovery.known_characters["0x123"].name == "NewPilot"
            callback.assert_called_once_with("NewPilot", "0x123", "EVE - NewPilot")

    def test_scan_updates_last_seen(self, discovery):
        """Updates last_seen for existing characters"""
        # Add existing character
        old_time = datetime(2025, 1, 1, 10, 0, 0)
        discovery.known_characters["0x1"] = DiscoveredCharacter(
            name="Existing",
            window_id="0x1",
            window_title="EVE - Existing",
            last_seen=old_time
        )
        discovery.active_window_ids.add("0x1")

        with patch.object(discovery, '_get_eve_windows',
                         return_value=[("0x1", "EVE - Existing")]):
            discovery._scan_cycle()

            # last_seen should be updated
            assert discovery.known_characters["0x1"].last_seen > old_time

    def test_scan_callback_error_handled(self, discovery):
        """Handles callback errors gracefully"""
        callback = MagicMock(side_effect=Exception("Test error"))
        discovery.set_on_new_callback(callback)

        with patch.object(discovery, '_get_eve_windows',
                         return_value=[("0x1", "EVE - Test")]):
            # Should not raise
            discovery._scan_cycle()
            assert "0x1" in discovery.known_characters


class TestSetEnabled:
    """Tests for enabling/disabling discovery"""

    def test_disable_stops_timer(self):
        """Disabling stops the scan timer"""
        discovery = AutoDiscovery()

        with patch.object(discovery.scan_timer, 'isActive', return_value=True):
            with patch.object(discovery, 'stop') as mock_stop:
                discovery.set_enabled(False)
                mock_stop.assert_called_once()

    def test_enable_when_disabled_starts(self):
        """Enabling when disabled starts discovery"""
        discovery = AutoDiscovery()
        discovery.enabled = False

        with patch.object(discovery.scan_timer, 'isActive', return_value=False):
            with patch.object(discovery, 'start') as mock_start:
                discovery.set_enabled(True)
                mock_start.assert_called_once()


class TestScanEveWindowsFunction:
    """Tests for standalone scan_eve_windows function"""

    def test_returns_list(self):
        """Returns list of tuples"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="0x123  0 host EVE - Pilot1\n0x456  0 host EVE - Pilot2\n"
            )

            result = scan_eve_windows()

            assert len(result) == 2
            assert result[0] == ("0x123", "EVE - Pilot1", "Pilot1")
            assert result[1] == ("0x456", "EVE - Pilot2", "Pilot2")

    def test_handles_empty_output(self):
        """Handles empty wmctrl output"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            result = scan_eve_windows()
            assert result == []

    def test_handles_subprocess_error(self):
        """Handles subprocess failure"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("wmctrl failed")

            result = scan_eve_windows()
            assert result == []

    def test_filters_non_eve_windows(self):
        """Only returns EVE windows"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="0x1  0 host Firefox\n0x2  0 host EVE - Test\n0x3  0 host Terminal\n"
            )

            result = scan_eve_windows()
            assert len(result) == 1
            assert result[0][2] == "Test"
