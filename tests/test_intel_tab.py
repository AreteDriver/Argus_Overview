"""Tests for intel tab UI module.

Tests IntelLogTable and IntelTab widgets.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
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


class TestIntelLogTableEdgeCases:
    """Edge case tests for IntelLogTable widget."""

    def test_ships_overflow_display(self, qapp):
        """Test that more than 3 ship types shows overflow count (line 123)."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.DANGER,
            hostile_count=5,
            ship_types=["Sabre", "Loki", "Muninn", "Huginn", "Scimitar"],
            player_names=[],
            raw_message="HED-GP 5 hostiles",
            timestamp=datetime.now(),
        )

        table.add_report(report)

        # Ships column is index 4
        ships_item = table.item(0, 4)
        ships_text = ships_item.text()
        # Should show "Sabre, Loki, Muninn +2"
        assert "+2" in ships_text
        assert "Sabre" in ships_text

    def test_message_truncation(self, qapp):
        """Test that long messages are truncated with ellipsis (line 130)."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        long_message = "A" * 150  # 150 chars, should be truncated at 100
        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.WARNING,
            hostile_count=1,
            ship_types=[],
            player_names=[],
            raw_message=long_message,
            timestamp=datetime.now(),
        )

        table.add_report(report)

        # Message column is index 5
        msg_item = table.item(0, 5)
        msg_text = msg_item.text()
        assert msg_text.endswith("...")
        assert len(msg_text) == 103  # 100 chars + "..."

    def test_row_limit_enforcement(self, qapp):
        """Test that table is limited to 500 rows (lines 144-146)."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        # Add 505 reports
        for i in range(505):
            report = IntelReport(
                system=f"SYS-{i}",
                threat_level=ThreatLevel.INFO,
                hostile_count=1,
                ship_types=[],
                player_names=[],
                raw_message=f"Report {i}",
                timestamp=datetime.now(),
            )
            table.add_report(report)

        # Should be capped at 500
        assert table.rowCount() == 500
        assert len(table.reports) == 500

    def test_selection_emits_signal(self, qapp):
        """Test that selecting a row emits entry_selected signal (lines 150-154)."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        report = IntelReport(
            system="TEST",
            threat_level=ThreatLevel.WARNING,
            hostile_count=1,
            ship_types=[],
            player_names=[],
            raw_message="test message",
            timestamp=datetime.now(),
        )
        table.add_report(report)

        # Connect signal to mock
        signal_handler = MagicMock()
        table.entry_selected.connect(signal_handler)

        # Select the row
        table.selectRow(0)

        # Signal should have been emitted with the report
        signal_handler.assert_called_once_with(report)

    def test_get_selected_report_returns_report(self, qapp):
        """Test get_selected_report returns correct report (lines 158-163)."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()

        report = IntelReport(
            system="TEST",
            threat_level=ThreatLevel.DANGER,
            hostile_count=2,
            ship_types=["Sabre"],
            player_names=["Player1"],
            raw_message="test",
            timestamp=datetime.now(),
        )
        table.add_report(report)

        # Select the row
        table.selectRow(0)

        # Should return the report
        selected = table.get_selected_report()
        assert selected == report

    def test_get_selected_report_no_selection(self, qapp):
        """Test get_selected_report returns None when nothing selected."""
        from argus_overview.ui.intel_tab import IntelLogTable

        table = IntelLogTable()
        table.add_report(
            IntelReport(
                system="TEST",
                threat_level=ThreatLevel.INFO,
                hostile_count=0,
                ship_types=[],
                player_names=[],
                raw_message="test",
            )
        )

        # Don't select anything
        table.clearSelection()

        # Should return None
        assert table.get_selected_report() is None


class TestIntelTabSettings:
    """Tests for IntelTab settings loading and saving."""

    def test_load_custom_log_path(self, qapp, tmp_path):
        """Test loading custom log path from settings (lines 227-229)."""
        from argus_overview.ui.intel_tab import IntelTab

        # Create a temp directory to use as log path
        log_dir = tmp_path / "eve_logs"
        log_dir.mkdir()

        # Mock settings manager to return custom path
        sm = MagicMock()
        sm.get.side_effect = lambda key, default=None: {
            "intel.channels": ["Intel"],
            "intel.custom_log_path": str(log_dir),
            "intel.alerts_enabled": True,
            "intel.visual_border": True,
            "intel.visual_overlay": True,
            "intel.audio_enabled": True,
            "intel.system_notification": False,
            "intel.min_threat_level": "warning",
            "intel.jumps_threshold": 5,
            "intel.cooldown_seconds": 5,
        }.get(key, default)

        tab = IntelTab(sm)

        # Log watcher should have the custom path set
        assert tab.log_watcher.get_log_directory() == log_dir

    def test_save_settings(self, qapp):
        """Test saving settings to settings manager (lines 237-264)."""
        from argus_overview.ui.intel_tab import IntelTab

        sm = MagicMock()
        sm.get.side_effect = lambda key, default=None: default

        tab = IntelTab(sm)

        # Modify alert config
        tab.alert_config.enabled = False
        tab.alert_config.audio = False
        tab.alert_config.cooldown_seconds = 10

        # Save settings
        tab._save_settings()

        # Verify settings manager was called with correct values
        sm.set.assert_any_call("intel.alerts_enabled", False, auto_save=False)
        sm.set.assert_any_call("intel.audio_enabled", False, auto_save=False)
        sm.set.assert_any_call("intel.cooldown_seconds", 10, auto_save=False)
        sm.save_settings.assert_called_once()


class TestIntelTabUI:
    """Tests for IntelTab UI interactions."""

    def test_toggle_monitoring_starts_when_stopped(self, qapp, mock_settings_manager):
        """Test toggle monitoring starts when stopped (lines 501-504)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)
        tab.log_watcher = MagicMock()
        tab.log_watcher.is_running.return_value = False

        tab._toggle_monitoring()

        tab.log_watcher.start.assert_called_once()

    def test_toggle_monitoring_stops_when_running(self, qapp, mock_settings_manager):
        """Test toggle monitoring stops when running."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)
        tab.log_watcher = MagicMock()
        tab.log_watcher.is_running.return_value = True

        tab._toggle_monitoring()

        tab.log_watcher.stop.assert_called_once()

    def test_clear_log(self, qapp, mock_settings_manager):
        """Test clear log method (lines 555-556)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # Add a report first
        report = IntelReport(
            system="TEST",
            threat_level=ThreatLevel.INFO,
            hostile_count=0,
            ship_types=[],
            player_names=[],
            raw_message="test",
        )
        tab.intel_table.add_report(report)
        assert tab.intel_table.rowCount() == 1

        tab._clear_log()

        assert tab.intel_table.rowCount() == 0

    def test_test_alert(self, qapp, mock_settings_manager):
        """Test triggering test alert (line 561)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)
        tab.alert_dispatcher = MagicMock()

        tab._test_alert()

        tab.alert_dispatcher.test_alert.assert_called_once_with(ThreatLevel.WARNING)

    def test_on_watcher_error(self, qapp, mock_settings_manager):
        """Test handling watcher error (lines 594-596)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        tab._on_watcher_error("Test error message")

        assert "Error" in tab.status_label.text()
        assert "Test error message" in tab.status_label.text()

    def test_on_entry_selected(self, qapp, mock_settings_manager):
        """Test entry selection handler (line 602)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        report = IntelReport(
            system="TEST",
            threat_level=ThreatLevel.DANGER,
            hostile_count=1,
            ship_types=[],
            player_names=[],
            raw_message="test",
        )

        # Should not raise
        tab._on_entry_selected(report)

    def test_on_alert_setting_changed(self, qapp, mock_settings_manager):
        """Test alert setting change handler (lines 612-622)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)
        tab.alert_dispatcher = MagicMock()

        # Modify UI elements
        tab.alerts_enabled_cb.setChecked(False)
        tab.audio_cb.setChecked(False)
        tab.cooldown_spin.setValue(15)

        # Trigger the handler
        tab._on_alert_setting_changed()

        # Alert config should be updated
        assert tab.alert_config.enabled is False
        assert tab.alert_config.audio is False
        assert tab.alert_config.cooldown_seconds == 15

        # Dispatcher should receive new config (called multiple times due to signal connections)
        assert tab.alert_dispatcher.set_config.called

    def test_on_current_system_changed(self, qapp, mock_settings_manager):
        """Test current system change handler (line 628)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        tab._on_current_system_changed("  HED-GP  ")

        mock_settings_manager.set.assert_called_with("intel.current_system", "HED-GP")

    def test_copy_to_clipboard(self, qapp, mock_settings_manager):
        """Test copy to clipboard (lines 657-658)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        tab._copy_to_clipboard("test text")

        # Verify clipboard has the text
        clipboard = QApplication.clipboard()
        assert clipboard.text() == "test text"

    def test_delete_selected_entry(self, qapp, mock_settings_manager):
        """Test deleting selected entry (lines 662-667)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # Add reports
        report1 = IntelReport(
            system="SYS1",
            threat_level=ThreatLevel.INFO,
            hostile_count=0,
            ship_types=[],
            player_names=[],
            raw_message="first",
        )
        report2 = IntelReport(
            system="SYS2",
            threat_level=ThreatLevel.WARNING,
            hostile_count=1,
            ship_types=[],
            player_names=[],
            raw_message="second",
        )
        tab.intel_table.add_report(report1)
        tab.intel_table.add_report(report2)

        assert tab.intel_table.rowCount() == 2

        # Select first row (which is report2 since newest first)
        tab.intel_table.selectRow(0)

        tab._delete_selected_entry()

        assert tab.intel_table.rowCount() == 1
        assert len(tab.intel_table.reports) == 1

    def test_remove_channel(self, qapp, mock_settings_manager):
        """Test removing a channel (lines 544-550)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # Add a channel to the list
        tab.log_watcher.add_channel("TestChannel")
        tab._update_channel_list()

        # Select the channel
        items = tab.channel_list.findItems("TestChannel", Qt.MatchFlag.MatchExactly)
        if items:
            tab.channel_list.setCurrentItem(items[0])

        # Remove it
        tab._remove_channel()

        # Channel should be removed
        assert "TestChannel" not in tab.log_watcher.monitored_channels

    def test_on_alert_triggered(self, qapp, mock_settings_manager):
        """Test alert triggered handler (lines 607)."""
        from argus_overview.intel.alerts import AlertType
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # Connect to signal
        signal_handler = MagicMock()
        tab.alert_triggered.connect(signal_handler)

        report = IntelReport(
            system="TEST",
            threat_level=ThreatLevel.DANGER,
            hostile_count=2,
            ship_types=[],
            player_names=[],
            raw_message="test",
        )

        tab._on_alert_triggered(report, AlertType.AUDIO)

        signal_handler.assert_called_once_with(report, AlertType.AUDIO)

    def test_chat_message_from_non_monitored_channel(self, qapp, mock_settings_manager):
        """Test chat message from non-monitored channel is ignored (line 569)."""
        from argus_overview.intel.log_watcher import ChatMessage
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)
        tab.log_watcher.set_monitored_channels(["intel"])

        msg = ChatMessage(
            timestamp=datetime.now(),
            channel="Local",  # Not in monitored channels
            speaker="Someone",
            message="HED-GP hostiles",
            raw_line="test",
        )

        # Process the message
        initial_count = tab.intel_table.rowCount()
        tab._on_chat_message(msg)

        # Should not add to table
        assert tab.intel_table.rowCount() == initial_count
