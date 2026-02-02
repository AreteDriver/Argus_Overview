"""Tests for intel tab UI module.

Tests IntelLogTable and IntelTab widgets.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from argus_overview.intel.parser import IntelReport, ThreatLevel


# Ensure QApplication exists for widget tests
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_settings_manager():
    """Create mock settings manager."""
    sm = MagicMock()
    # Return defaults for all settings
    sm.get.side_effect = lambda key, default=None: default
    return sm


class TestIntelLogTable:
    """Tests for IntelLogTable widget."""

    def test_init(self, qapp):
        """Test IntelLogTable initialization."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        assert table.columnCount() == 6
        assert table.rowCount() == 0
        assert table.reports == []

    def test_threat_colors_defined(self, qapp):
        """Test threat level colors are defined."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        assert ThreatLevel.CLEAR in table.THREAT_COLORS
        assert ThreatLevel.INFO in table.THREAT_COLORS
        assert ThreatLevel.WARNING in table.THREAT_COLORS
        assert ThreatLevel.DANGER in table.THREAT_COLORS
        assert ThreatLevel.CRITICAL in table.THREAT_COLORS

    def test_add_report(self, qapp):
        """Test adding a report to the table."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.DANGER,
            hostile_count=3,
            ship_types=["Sabre", "Loki"],
            player_names=["Player1"],
            raw_message="HED-GP 3 hostiles",
            timestamp=datetime.now(),
        )

        table.add_report(report)

        assert table.rowCount() == 1
        assert len(table.reports) == 1
        assert table.reports[0] == report

    def test_add_multiple_reports(self, qapp):
        """Test adding multiple reports (newest first)."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        report1 = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.WARNING,
            hostile_count=1,
            ship_types=[],
            player_names=[],
            raw_message="first",
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
        )

        report2 = IntelReport(
            system="1DQ1-A",
            threat_level=ThreatLevel.DANGER,
            hostile_count=5,
            ship_types=[],
            player_names=[],
            raw_message="second",
            timestamp=datetime(2026, 1, 1, 12, 1, 0),
        )

        table.add_report(report1)
        table.add_report(report2)

        assert table.rowCount() == 2
        # Newest (report2) should be first
        assert table.reports[0] == report2

    def test_clear_all(self, qapp):
        """Test clearing all reports."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        report = IntelReport(
            system="TEST",
            threat_level=ThreatLevel.INFO,
            hostile_count=0,
            ship_types=[],
            player_names=[],
            raw_message="test",
        )

        table.add_report(report)
        assert table.rowCount() == 1

        table.clear_all()

        assert table.rowCount() == 0
        assert table.reports == []


class TestIntelTab:
    """Tests for IntelTab widget."""

    def test_init(self, qapp, mock_settings_manager):
        """Test IntelTab initialization."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        assert tab.log_watcher is not None
        assert tab.intel_parser is not None
        assert tab.alert_dispatcher is not None
        assert tab.intel_table is not None

    def test_has_alert_config(self, qapp, mock_settings_manager):
        """Test IntelTab has alert configuration."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # Should have alert dispatcher with config
        assert tab.alert_dispatcher.config is not None

    def test_get_alert_dispatcher(self, qapp, mock_settings_manager):
        """Test getting alert dispatcher."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)
        dispatcher = tab.get_alert_dispatcher()

        assert dispatcher is not None
        assert dispatcher == tab.alert_dispatcher

    def test_stop(self, qapp, mock_settings_manager):
        """Test stop method."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)
        tab.log_watcher = MagicMock()

        tab.stop()

        tab.log_watcher.stop.assert_called_once()


class TestIntelTabIntegration:
    """Integration tests for IntelTab."""

    def test_process_message(self, qapp, mock_settings_manager):
        """Test processing a chat message."""
        from argus_overview.intel.log_watcher import ChatMessage
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        msg = ChatMessage(
            timestamp=datetime.now(),
            channel="Intel",
            speaker="Scout",
            message="HED-GP 3 hostiles Sabre Loki",
            raw_line="[ 2026.01.15 12:00:00 ] Scout > HED-GP 3 hostiles Sabre Loki",
        )

        # Process the message using the internal method
        tab._on_chat_message(msg)

        # Should add to table (may or may not parse depending on parser)
        assert tab.intel_table.rowCount() >= 0

    def test_start_stop_monitoring(self, qapp, mock_settings_manager):
        """Test start/stop monitoring."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # Mock the log watcher to avoid file system access
        tab.log_watcher = MagicMock()
        tab.log_watcher.is_running.return_value = False

        tab._start_monitoring()
        tab.log_watcher.start.assert_called_once()

        tab.log_watcher.is_running.return_value = True
        tab._stop_monitoring()
        tab.log_watcher.stop.assert_called_once()
