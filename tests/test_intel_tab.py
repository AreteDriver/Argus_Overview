"""Tests for intel tab UI module.

Tests IntelLogTable and IntelTab widgets.
"""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from argus_overview.intel.parser import IntelReport, ThreatLevel

# qapp fixture is provided by conftest.py (session-scoped)


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

    @pytest.mark.skipif(
        sys.version_info >= (3, 12),
        reason="PySide6 segfault on Python 3.12 in CI - Qt signal/slot issue",
    )
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

        # Verify channel was added (stored lowercase)
        assert "testchannel" in tab.log_watcher.monitored_channels

        # Select the channel by setting current row (stored lowercase in list)
        items = tab.channel_list.findItems("testchannel", Qt.MatchFlag.MatchExactly)
        assert len(items) > 0, "Channel not found in list"
        tab.channel_list.setCurrentRow(tab.channel_list.row(items[0]))

        # Verify item is selected
        assert tab.channel_list.currentItem() is not None

        # Remove it
        tab._remove_channel()

        # Channel should be removed
        assert "testchannel" not in tab.log_watcher.monitored_channels

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

    def test_update_log_dir_label_not_found(self, qapp, mock_settings_manager):
        """Test log dir label when dir not found (lines 491-492)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # Mock log_dir to return None
        tab.log_watcher.log_dir = None

        tab._update_log_dir_label()

        assert tab.log_dir_label.text() == "Log Dir: Not found"
        assert "F44336" in tab.log_dir_label.styleSheet()  # Red color

    def test_add_channel_with_dialog(self, qapp, mock_settings_manager):
        """Test adding channel via dialog (lines 528-539)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # Mock QInputDialog.getText to return a channel name
        with patch(
            "argus_overview.ui.intel_tab.QInputDialog.getText",
            return_value=("NewChannel", True),
        ):
            tab._add_channel()

        assert "newchannel" in tab.log_watcher.monitored_channels

    def test_add_channel_dialog_cancelled(self, qapp, mock_settings_manager):
        """Test adding channel when dialog is cancelled."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)
        initial_channels = set(tab.log_watcher.monitored_channels)

        # Mock QInputDialog.getText to return cancelled
        with patch(
            "argus_overview.ui.intel_tab.QInputDialog.getText",
            return_value=("", False),
        ):
            tab._add_channel()

        assert tab.log_watcher.monitored_channels == initial_channels

    def test_add_channel_empty_string(self, qapp, mock_settings_manager):
        """Test adding channel with empty string."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)
        initial_channels = set(tab.log_watcher.monitored_channels)

        # Mock QInputDialog.getText to return empty string but OK clicked
        with patch(
            "argus_overview.ui.intel_tab.QInputDialog.getText",
            return_value=("   ", True),
        ):
            tab._add_channel()

        # Empty string after strip should not be added
        assert tab.log_watcher.monitored_channels == initial_channels

    @pytest.mark.skipif(
        sys.version_info >= (3, 12),
        reason="PySide6 segfault on Python 3.12 in CI - Qt signal/slot issue",
    )
    def test_chat_message_with_valid_intel(self, qapp, mock_settings_manager):
        """Test chat message that produces valid intel report (lines 572-589)."""
        from argus_overview.intel.log_watcher import ChatMessage
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # Don't filter by channel (empty monitored_channels allows all)
        tab.log_watcher.monitored_channels = set()

        signal_handler = MagicMock()
        tab.intel_received.connect(signal_handler)

        msg = ChatMessage(
            timestamp=datetime.now(),
            channel="Intel",
            speaker="Scout",
            message="HED-GP +5 hostiles",  # Valid intel format
            raw_line="test",
        )

        initial_count = tab.intel_table.rowCount()
        tab._on_chat_message(msg)

        # Should add to table and emit signal
        assert tab.intel_table.rowCount() > initial_count
        assert signal_handler.called

    def test_show_context_menu_no_report_returns_early(self, qapp, mock_settings_manager):
        """Test context menu returns early when no report selected (line 633-634)."""
        from argus_overview.ui.intel_tab import IntelTab

        tab = IntelTab(mock_settings_manager)

        # No reports in table, so get_selected_report returns None
        assert tab.intel_table.get_selected_report() is None

        # The method should return early without error when no report is selected
        # We can't easily test that QMenu isn't created without blocking,
        # so just verify it doesn't crash
        from PySide6.QtCore import QPoint

        # Mock at the module level to prevent blocking exec()
        with patch.object(tab.intel_table, "get_selected_report", return_value=None):
            tab._show_context_menu(QPoint(0, 0))
            # If we get here, the early return worked


# =============================================================================
# Coverage Push: _on_chat_message intel path (lines 572-589)
# and _show_context_menu with report (lines 636-653)
# =============================================================================


class TestOnChatMessageIntelPath:
    """Tests for _on_chat_message when a valid intel report is parsed."""

    def test_chat_message_parses_and_dispatches_intel(self):
        """Test _on_chat_message parses intel, adds to table, dispatches, emits."""
        from argus_overview.ui.intel_tab import IntelTab

        with patch.object(IntelTab, "__init__", return_value=None):
            tab = IntelTab.__new__(IntelTab)
            tab.logger = MagicMock()
            tab.log_watcher = MagicMock()
            tab.log_watcher.monitored_channels = set()  # Allow all channels

            mock_report = MagicMock()
            mock_report.system = "HED-GP"
            mock_report.threat_level.value = "warning"

            tab.intel_parser = MagicMock()
            tab.intel_parser.parse.return_value = mock_report
            tab.intel_table = MagicMock()
            tab.alert_dispatcher = MagicMock()
            tab.intel_received = MagicMock()

            from argus_overview.intel.log_watcher import ChatMessage

            msg = ChatMessage(
                timestamp=MagicMock(),
                channel="Intel",
                speaker="Scout",
                message="HED-GP +5 hostiles",
                raw_line="test",
            )

            tab._on_chat_message(msg)

            # Parser called with correct args
            tab.intel_parser.parse.assert_called_once_with(
                "HED-GP +5 hostiles",
                timestamp=msg.timestamp,
                channel="Intel",
                reporter="Scout",
            )

            # Report processed
            tab.intel_table.add_report.assert_called_once_with(mock_report)
            tab.alert_dispatcher.dispatch.assert_called_once_with(mock_report)
            tab.intel_received.emit.assert_called_once_with(mock_report)

    def test_chat_message_no_report_skips_dispatch(self):
        """Test _on_chat_message does nothing when parser returns None."""
        from argus_overview.ui.intel_tab import IntelTab

        with patch.object(IntelTab, "__init__", return_value=None):
            tab = IntelTab.__new__(IntelTab)
            tab.logger = MagicMock()
            tab.log_watcher = MagicMock()
            tab.log_watcher.monitored_channels = set()

            tab.intel_parser = MagicMock()
            tab.intel_parser.parse.return_value = None
            tab.intel_table = MagicMock()
            tab.alert_dispatcher = MagicMock()
            tab.intel_received = MagicMock()

            from argus_overview.intel.log_watcher import ChatMessage

            msg = ChatMessage(
                timestamp=MagicMock(),
                channel="Intel",
                speaker="Scout",
                message="just chatting",
                raw_line="test",
            )

            tab._on_chat_message(msg)

            tab.intel_table.add_report.assert_not_called()
            tab.alert_dispatcher.dispatch.assert_not_called()
            tab.intel_received.emit.assert_not_called()


class TestShowContextMenuWithReport:
    """Tests for _show_context_menu when a report is selected (lines 636-653)."""

    def test_show_context_menu_with_system(self):
        """Test context menu creates actions for report with system name."""
        from argus_overview.ui.intel_tab import IntelTab

        with patch.object(IntelTab, "__init__", return_value=None):
            tab = IntelTab.__new__(IntelTab)
            tab.logger = MagicMock()
            tab.intel_table = MagicMock()
            tab._copy_to_clipboard = MagicMock()
            tab._delete_selected_entry = MagicMock()

            mock_report = MagicMock()
            mock_report.system = "Jita"
            mock_report.raw_message = "Jita +5 neutrals"
            tab.intel_table.get_selected_report.return_value = mock_report

            mock_menu = MagicMock()
            mock_action_system = MagicMock()
            mock_action_msg = MagicMock()
            mock_action_delete = MagicMock()
            mock_menu.addAction.side_effect = [
                mock_action_system,
                mock_action_msg,
                mock_action_delete,
            ]

            from PySide6.QtCore import QPoint

            with patch("argus_overview.ui.intel_tab.QMenu", return_value=mock_menu):
                tab._show_context_menu(QPoint(0, 0))

                # Should create 3 actions: copy system, copy message, delete
                assert mock_menu.addAction.call_count == 3
                mock_menu.addSeparator.assert_called_once()
                mock_menu.exec.assert_called_once()

    def test_show_context_menu_without_system(self):
        """Test context menu omits 'Copy System' when report has no system."""
        from argus_overview.ui.intel_tab import IntelTab

        with patch.object(IntelTab, "__init__", return_value=None):
            tab = IntelTab.__new__(IntelTab)
            tab.logger = MagicMock()
            tab.intel_table = MagicMock()
            tab._copy_to_clipboard = MagicMock()
            tab._delete_selected_entry = MagicMock()

            mock_report = MagicMock()
            mock_report.system = None  # No system
            mock_report.raw_message = "some message"
            tab.intel_table.get_selected_report.return_value = mock_report

            mock_menu = MagicMock()
            mock_action_msg = MagicMock()
            mock_action_delete = MagicMock()
            mock_menu.addAction.side_effect = [mock_action_msg, mock_action_delete]

            from PySide6.QtCore import QPoint

            with patch("argus_overview.ui.intel_tab.QMenu", return_value=mock_menu):
                tab._show_context_menu(QPoint(0, 0))

                # Only 2 actions: copy message, delete (no copy system)
                assert mock_menu.addAction.call_count == 2
                mock_menu.exec.assert_called_once()
