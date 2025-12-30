"""
Unit tests for the Settings Sync Tab module
Tests ScanWorker, SyncWorker, SyncPreviewDialog, SettingsSyncTab
"""
from unittest.mock import MagicMock, patch


# Test ScanWorker
class TestScanWorker:
    """Tests for ScanWorker thread"""

    @patch('eve_overview_pro.ui.settings_sync_tab.QThread.__init__')
    def test_init(self, mock_thread):
        """Test ScanWorker initialization"""
        mock_thread.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import ScanWorker

        mock_settings_sync = MagicMock()
        worker = ScanWorker(mock_settings_sync)

        assert worker.settings_sync is mock_settings_sync

    def test_signals_exist(self):
        """Test ScanWorker has expected signals"""
        from eve_overview_pro.ui.settings_sync_tab import ScanWorker

        assert hasattr(ScanWorker, 'scan_progress')
        assert hasattr(ScanWorker, 'scan_complete')
        assert hasattr(ScanWorker, 'scan_error')


# Test SyncWorker
class TestSyncWorker:
    """Tests for SyncWorker thread"""

    @patch('eve_overview_pro.ui.settings_sync_tab.QThread.__init__')
    def test_init(self, mock_thread):
        """Test SyncWorker initialization"""
        mock_thread.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SyncWorker

        mock_settings_sync = MagicMock()
        mock_source_char = MagicMock()
        mock_target_chars = [MagicMock(), MagicMock()]

        worker = SyncWorker(mock_settings_sync, mock_source_char, mock_target_chars)

        assert worker.settings_sync is mock_settings_sync
        assert worker.source_char is mock_source_char
        assert worker.target_chars is mock_target_chars
        assert worker.backup is True

    @patch('eve_overview_pro.ui.settings_sync_tab.QThread.__init__')
    def test_init_no_backup(self, mock_thread):
        """Test SyncWorker initialization without backup"""
        mock_thread.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SyncWorker

        mock_settings_sync = MagicMock()
        mock_source_char = MagicMock()
        mock_target_chars = [MagicMock()]

        worker = SyncWorker(mock_settings_sync, mock_source_char, mock_target_chars, backup=False)

        assert worker.backup is False

    def test_signals_exist(self):
        """Test SyncWorker has expected signals"""
        from eve_overview_pro.ui.settings_sync_tab import SyncWorker

        assert hasattr(SyncWorker, 'sync_progress')
        assert hasattr(SyncWorker, 'sync_complete')
        assert hasattr(SyncWorker, 'sync_error')


# Test SyncPreviewDialog
class TestSyncPreviewDialog:
    """Tests for SyncPreviewDialog"""

    @patch('eve_overview_pro.ui.settings_sync_tab.QDialog.__init__')
    def test_init(self, mock_dialog):
        """Test SyncPreviewDialog initialization"""
        mock_dialog.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SyncPreviewDialog

        mock_source_char = MagicMock()
        mock_source_char.character_name = "SourcePilot"

        mock_target_chars = [MagicMock(), MagicMock()]
        mock_settings_sync = MagicMock()

        with patch.object(SyncPreviewDialog, 'setWindowTitle') as mock_title:
            with patch.object(SyncPreviewDialog, 'setMinimumSize'):
                with patch.object(SyncPreviewDialog, '_setup_ui'):
                    with patch.object(SyncPreviewDialog, '_populate_preview'):
                        dialog = SyncPreviewDialog(
                            mock_source_char,
                            mock_target_chars,
                            mock_settings_sync
                        )

                        mock_title.assert_called_with("Sync Preview")
                        assert dialog.source_char is mock_source_char
                        assert dialog.target_chars is mock_target_chars


# Test SettingsSyncTab
class TestSettingsSyncTab:
    """Tests for SettingsSyncTab widget"""

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test SettingsSyncTab initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)

            assert tab.settings_sync is mock_settings_sync
            assert tab.character_manager is mock_char_manager
            assert tab.scanned_characters == []
            assert tab.scan_worker is None
            assert tab.sync_worker is None

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    def test_log_method(self, mock_widget):
        """Test _log method adds timestamp"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)
            tab.log_text = MagicMock()

            tab._log("Test message")

            tab.log_text.append.assert_called_once()
            call_arg = tab.log_text.append.call_args[0][0]
            assert "Test message" in call_arg
            assert "[" in call_arg and "]" in call_arg  # Has timestamp brackets

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    def test_select_all_targets(self, mock_widget):
        """Test _select_all_targets selects all items"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)

            # Mock the target list
            mock_item1 = MagicMock()
            mock_item2 = MagicMock()
            tab.target_list = MagicMock()
            tab.target_list.count.return_value = 2
            tab.target_list.item.side_effect = [mock_item1, mock_item2]

            tab._select_all_targets()

            mock_item1.setSelected.assert_called_with(True)
            mock_item2.setSelected.assert_called_with(True)

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    def test_clear_targets(self, mock_widget):
        """Test _clear_targets clears selection"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)
            tab.target_list = MagicMock()

            tab._clear_targets()

            tab.target_list.clearSelection.assert_called_once()

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    def test_get_last_modified_returns_na_for_missing_path(self, mock_widget):
        """Test _get_last_modified returns N/A for missing path"""
        mock_widget.return_value = None

        from pathlib import Path

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)

            # Non-existent path
            result = tab._get_last_modified(Path("/nonexistent/path/12345"))

            assert result == "N/A"

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    def test_on_scan_complete_populates_ui(self, mock_widget):
        """Test _on_scan_complete populates UI elements"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)

            # Mock UI elements
            tab.scan_btn = MagicMock()
            tab.progress_bar = MagicMock()
            tab.source_combo = MagicMock()
            tab.target_list = MagicMock()
            tab.log_text = MagicMock()

            # Mock characters
            mock_char1 = MagicMock()
            mock_char1.character_name = "Pilot1"
            mock_char2 = MagicMock()
            mock_char2.character_name = "Pilot2"
            characters = [mock_char1, mock_char2]

            tab._on_scan_complete(characters)

            assert tab.scanned_characters == characters
            tab.scan_btn.setEnabled.assert_called_with(True)
            tab.progress_bar.setVisible.assert_called_with(False)
            assert tab.source_combo.addItem.call_count == 2
            assert tab.target_list.addItem.call_count == 2

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.settings_sync_tab.QMessageBox')
    def test_on_scan_error_shows_message(self, mock_msgbox, mock_widget):
        """Test _on_scan_error shows error message"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)
            tab.scan_btn = MagicMock()
            tab.progress_bar = MagicMock()
            tab.log_text = MagicMock()

            tab._on_scan_error("Test error message")

            tab.scan_btn.setEnabled.assert_called_with(True)
            tab.progress_bar.setVisible.assert_called_with(False)
            mock_msgbox.critical.assert_called_once()

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.settings_sync_tab.QMessageBox')
    def test_on_sync_complete_shows_message(self, mock_msgbox, mock_widget):
        """Test _on_sync_complete shows completion message"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)
            tab.sync_btn = MagicMock()
            tab.preview_btn = MagicMock()
            tab.progress_bar = MagicMock()
            tab.log_text = MagicMock()

            results = {"Pilot1": True, "Pilot2": False}
            tab._on_sync_complete(results)

            tab.sync_btn.setEnabled.assert_called_with(True)
            tab.preview_btn.setEnabled.assert_called_with(True)
            mock_msgbox.information.assert_called_once()

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.settings_sync_tab.QFileDialog')
    @patch('eve_overview_pro.ui.settings_sync_tab.QMessageBox')
    def test_add_custom_path_adds_to_settings_sync(self, mock_msgbox, mock_dialog, mock_widget):
        """Test _add_custom_path adds path to settings_sync"""
        mock_widget.return_value = None

        from PySide6.QtWidgets import QMessageBox

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        # Simulate user selecting a directory
        mock_dialog.getExistingDirectory.return_value = "/home/user/EVE/settings"

        # Simulate user clicking "No" to rescan prompt
        mock_msgbox.StandardButton = QMessageBox.StandardButton
        mock_msgbox.question.return_value = QMessageBox.StandardButton.No

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)
            tab.log_text = MagicMock()

            tab._add_custom_path()

            # Verify path was added
            mock_settings_sync.add_custom_path.assert_called_once()
            # Verify dialog was shown
            mock_msgbox.question.assert_called_once()

    @patch('eve_overview_pro.ui.settings_sync_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.settings_sync_tab.QFileDialog')
    def test_add_custom_path_cancelled(self, mock_dialog, mock_widget):
        """Test _add_custom_path handles cancelled dialog"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        # Simulate user cancelling the dialog
        mock_dialog.getExistingDirectory.return_value = ""

        with patch.object(SettingsSyncTab, '_setup_ui'):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)

            tab._add_custom_path()

            # Verify nothing was added
            mock_settings_sync.add_custom_path.assert_not_called()
