"""
Unit tests for the Settings Sync Tab module
Tests ScanWorker, SyncWorker, SyncPreviewDialog, SettingsSyncTab
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

# =============================================================================
# ScanWorker Tests
# =============================================================================


class TestScanWorker:
    """Tests for ScanWorker class"""

    @patch("argus_overview.ui.settings_sync_tab.QThread.__init__")
    def test_init(self, mock_thread):
        """Test ScanWorker initialization"""
        mock_thread.return_value = None

        from argus_overview.ui.settings_sync_tab import ScanWorker

        mock_settings_sync = MagicMock()

        worker = ScanWorker(mock_settings_sync)

        assert worker.settings_sync is mock_settings_sync

    @patch("argus_overview.ui.settings_sync_tab.QThread.__init__")
    def test_run_success(self, mock_thread):
        """Test successful scan run"""
        mock_thread.return_value = None

        from argus_overview.ui.settings_sync_tab import ScanWorker

        mock_settings_sync = MagicMock()
        mock_char1 = MagicMock()
        mock_char1.character_name = "Char1"
        mock_char2 = MagicMock()
        mock_char2.character_name = "Char2"
        mock_settings_sync.scan_for_characters.return_value = [mock_char1, mock_char2]

        worker = ScanWorker(mock_settings_sync)
        worker.scan_progress = MagicMock()
        worker.scan_complete = MagicMock()
        worker.scan_error = MagicMock()

        worker.run()

        worker.scan_progress.emit.assert_called()
        worker.scan_complete.emit.assert_called_once_with([mock_char1, mock_char2])

    @patch("argus_overview.ui.settings_sync_tab.QThread.__init__")
    def test_run_error(self, mock_thread):
        """Test scan run with error"""
        mock_thread.return_value = None

        from argus_overview.ui.settings_sync_tab import ScanWorker

        mock_settings_sync = MagicMock()
        mock_settings_sync.scan_for_characters.side_effect = Exception("Scan failed")

        worker = ScanWorker(mock_settings_sync)
        worker.scan_progress = MagicMock()
        worker.scan_complete = MagicMock()
        worker.scan_error = MagicMock()

        worker.run()

        worker.scan_error.emit.assert_called_once_with("Scan failed")

    @patch("argus_overview.ui.settings_sync_tab.QThread.__init__")
    def test_run_empty_results(self, mock_thread):
        """Test scan with no characters found"""
        mock_thread.return_value = None

        from argus_overview.ui.settings_sync_tab import ScanWorker

        mock_settings_sync = MagicMock()
        mock_settings_sync.scan_for_characters.return_value = []

        worker = ScanWorker(mock_settings_sync)
        worker.scan_progress = MagicMock()
        worker.scan_complete = MagicMock()
        worker.scan_error = MagicMock()

        worker.run()

        worker.scan_complete.emit.assert_called_once_with([])


# =============================================================================
# SyncWorker Tests
# =============================================================================


class TestSyncWorker:
    """Tests for SyncWorker class"""

    @patch("argus_overview.ui.settings_sync_tab.QThread.__init__")
    def test_init(self, mock_thread):
        """Test SyncWorker initialization"""
        mock_thread.return_value = None

        from argus_overview.ui.settings_sync_tab import SyncWorker

        mock_settings_sync = MagicMock()
        mock_source = MagicMock()
        mock_targets = [MagicMock()]

        worker = SyncWorker(mock_settings_sync, mock_source, mock_targets, backup=True)

        assert worker.settings_sync is mock_settings_sync
        assert worker.source_char is mock_source
        assert worker.target_chars is mock_targets
        assert worker.backup is True

    @patch("argus_overview.ui.settings_sync_tab.QThread.__init__")
    def test_run_success(self, mock_thread):
        """Test successful sync run"""
        mock_thread.return_value = None

        from argus_overview.ui.settings_sync_tab import SyncWorker

        mock_settings_sync = MagicMock()
        mock_settings_sync.sync_settings.return_value = {"Target1": True}

        mock_source = MagicMock()
        mock_source.character_name = "Source"

        mock_target = MagicMock()
        mock_target.character_name = "Target1"

        worker = SyncWorker(mock_settings_sync, mock_source, [mock_target])
        worker.sync_progress = MagicMock()
        worker.sync_complete = MagicMock()
        worker.sync_error = MagicMock()

        worker.run()

        worker.sync_progress.emit.assert_called()
        worker.sync_complete.emit.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QThread.__init__")
    def test_run_partial_failure(self, mock_thread):
        """Test sync with partial failures"""
        mock_thread.return_value = None

        from argus_overview.ui.settings_sync_tab import SyncWorker

        mock_settings_sync = MagicMock()

        def sync_side_effect(source, targets, backup):
            if targets[0] == "Target1":
                return {"Target1": True}
            else:
                raise Exception("Sync failed")

        mock_settings_sync.sync_settings.side_effect = sync_side_effect

        mock_source = MagicMock()
        mock_source.character_name = "Source"

        mock_target1 = MagicMock()
        mock_target1.character_name = "Target1"
        mock_target2 = MagicMock()
        mock_target2.character_name = "Target2"

        worker = SyncWorker(mock_settings_sync, mock_source, [mock_target1, mock_target2])
        worker.sync_progress = MagicMock()
        worker.sync_complete = MagicMock()
        worker.sync_error = MagicMock()

        worker.run()

        worker.sync_complete.emit.assert_called_once()
        results = worker.sync_complete.emit.call_args[0][0]
        assert results["Target1"] is True
        assert results["Target2"] is False

    @patch("argus_overview.ui.settings_sync_tab.QThread.__init__")
    def test_run_empty_targets(self, mock_thread):
        """Test sync with empty targets"""
        mock_thread.return_value = None

        from argus_overview.ui.settings_sync_tab import SyncWorker

        mock_settings_sync = MagicMock()
        mock_source = MagicMock()
        mock_source.character_name = "Source"

        worker = SyncWorker(mock_settings_sync, mock_source, [])
        worker.sync_progress = MagicMock()
        worker.sync_complete = MagicMock()
        worker.sync_error = MagicMock()

        worker.run()

        worker.sync_complete.emit.assert_called_once_with({})


# =============================================================================
# SyncPreviewDialog Tests
# =============================================================================


class TestSyncPreviewDialog:
    """Tests for SyncPreviewDialog class"""

    @patch("argus_overview.ui.settings_sync_tab.QDialog.__init__")
    def test_init(self, mock_dialog):
        """Test SyncPreviewDialog initialization"""
        mock_dialog.return_value = None

        from argus_overview.ui.settings_sync_tab import SyncPreviewDialog

        mock_source = MagicMock()
        mock_source.character_name = "Source"
        mock_source.settings_dir = "/tmp/source"

        mock_targets = [MagicMock()]
        mock_settings_sync = MagicMock()

        with patch.object(SyncPreviewDialog, "setWindowTitle"):
            with patch.object(SyncPreviewDialog, "setMinimumSize"):
                with patch.object(SyncPreviewDialog, "_setup_ui"):
                    with patch.object(SyncPreviewDialog, "_populate_preview"):
                        dialog = SyncPreviewDialog(mock_source, mock_targets, mock_settings_sync)

                        assert dialog.source_char is mock_source
                        assert dialog.target_chars is mock_targets

    def test_setup_ui(self):
        """Test _setup_ui creates layout"""
        from argus_overview.ui.settings_sync_tab import SyncPreviewDialog

        with patch.object(SyncPreviewDialog, "__init__", return_value=None):
            dialog = SyncPreviewDialog.__new__(SyncPreviewDialog)
            dialog.source_char = MagicMock()
            dialog.source_char.character_name = "Source"
            dialog.target_chars = [MagicMock()]
            dialog.logger = MagicMock()

            mock_layout = MagicMock()

            with patch("argus_overview.ui.settings_sync_tab.QVBoxLayout", return_value=mock_layout):
                with patch("argus_overview.ui.settings_sync_tab.QLabel"):
                    with patch("argus_overview.ui.settings_sync_tab.QTableWidget") as mock_table:
                        mock_table_instance = MagicMock()
                        mock_table.return_value = mock_table_instance
                        with patch("argus_overview.ui.settings_sync_tab.QDialogButtonBox"):
                            with patch.object(dialog, "setLayout"):
                                dialog._setup_ui()

                                mock_layout.addWidget.assert_called()

    def test_populate_preview_no_source_dir(self):
        """Test _populate_preview with missing source directory"""
        from argus_overview.ui.settings_sync_tab import SyncPreviewDialog

        with patch.object(SyncPreviewDialog, "__init__", return_value=None):
            dialog = SyncPreviewDialog.__new__(SyncPreviewDialog)
            dialog.source_char = MagicMock()
            dialog.source_char.settings_dir = "/nonexistent/path"
            dialog.target_chars = []
            dialog.preview_table = MagicMock()
            dialog.logger = MagicMock()

            with patch("argus_overview.ui.settings_sync_tab.QMessageBox") as mock_msgbox:
                dialog._populate_preview()

                mock_msgbox.warning.assert_called_once()

    def test_populate_preview_with_files(self, tmp_path):
        """Test _populate_preview with files"""
        from argus_overview.ui.settings_sync_tab import SyncPreviewDialog

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.dat").write_text("data")
        (source_dir / "config.yaml").write_text("config")

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        (target_dir / "test.dat").write_text("old")

        with patch.object(SyncPreviewDialog, "__init__", return_value=None):
            dialog = SyncPreviewDialog.__new__(SyncPreviewDialog)
            dialog.source_char = MagicMock()
            dialog.source_char.settings_dir = str(source_dir)

            mock_target = MagicMock()
            mock_target.settings_dir = str(target_dir)
            dialog.target_chars = [mock_target]

            dialog.preview_table = MagicMock()
            dialog.preview_table.rowCount.return_value = 0
            dialog.logger = MagicMock()

            with patch("argus_overview.ui.settings_sync_tab.QTableWidgetItem"):
                with patch("argus_overview.ui.settings_sync_tab.QColor"):
                    dialog._populate_preview()

                    assert dialog.preview_table.insertRow.call_count >= 2

    def test_get_file_date_exists(self, tmp_path):
        """Test _get_file_date with existing file"""
        from argus_overview.ui.settings_sync_tab import SyncPreviewDialog

        test_file = tmp_path / "test.dat"
        test_file.write_text("data")

        with patch.object(SyncPreviewDialog, "__init__", return_value=None):
            dialog = SyncPreviewDialog.__new__(SyncPreviewDialog)

            result = dialog._get_file_date(test_file)

            assert result != "N/A"
            assert "-" in result

    def test_get_file_date_not_exists(self, tmp_path):
        """Test _get_file_date with non-existing file"""
        from argus_overview.ui.settings_sync_tab import SyncPreviewDialog

        test_file = tmp_path / "nonexistent.dat"

        with patch.object(SyncPreviewDialog, "__init__", return_value=None):
            dialog = SyncPreviewDialog.__new__(SyncPreviewDialog)

            result = dialog._get_file_date(test_file)

            assert result == "N/A"


# =============================================================================
# SettingsSyncTab Tests
# =============================================================================


class TestSettingsSyncTab:
    """Tests for SettingsSyncTab class"""

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test SettingsSyncTab initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()
        mock_char_manager = MagicMock()

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(mock_settings_sync, mock_char_manager)

            assert tab.settings_sync is mock_settings_sync
            assert tab.character_manager is mock_char_manager
            assert tab.scanned_characters == []

    def test_setup_ui(self):
        """Test _setup_ui creates layout"""
        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "__init__", return_value=None):
            tab = SettingsSyncTab.__new__(SettingsSyncTab)
            tab.logger = MagicMock()
            tab.settings_sync = MagicMock()
            tab.character_manager = MagicMock()

            mock_layout = MagicMock()
            mock_splitter = MagicMock()

            with patch("argus_overview.ui.settings_sync_tab.QVBoxLayout", return_value=mock_layout):
                with patch(
                    "argus_overview.ui.settings_sync_tab.QSplitter", return_value=mock_splitter
                ):
                    with patch.object(tab, "_create_toolbar", return_value=MagicMock()):
                        with patch.object(tab, "_create_character_panel", return_value=MagicMock()):
                            with patch.object(tab, "_create_log_panel", return_value=MagicMock()):
                                with patch.object(tab, "setLayout"):
                                    tab._setup_ui()

                                    mock_splitter.setSizes.assert_called_with([400, 200])

    def test_create_toolbar(self):
        """Test _create_toolbar creates toolbar"""
        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "__init__", return_value=None):
            tab = SettingsSyncTab.__new__(SettingsSyncTab)
            tab.logger = MagicMock()

            mock_toolbar = MagicMock()
            mock_layout = MagicMock()

            with patch("argus_overview.ui.settings_sync_tab.QWidget", return_value=mock_toolbar):
                with patch(
                    "argus_overview.ui.settings_sync_tab.QHBoxLayout", return_value=mock_layout
                ):
                    with patch("argus_overview.ui.settings_sync_tab.ToolbarBuilder"):
                        with patch("argus_overview.ui.settings_sync_tab.QPushButton"):
                            with patch("argus_overview.ui.settings_sync_tab.QProgressBar"):
                                result = tab._create_toolbar()

                                assert result == mock_toolbar

    def test_create_character_panel(self):
        """Test _create_character_panel creates panel"""
        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "__init__", return_value=None):
            tab = SettingsSyncTab.__new__(SettingsSyncTab)
            tab.logger = MagicMock()
            tab.character_manager = MagicMock()

            mock_panel = MagicMock()
            mock_layout = MagicMock()

            with patch("argus_overview.ui.settings_sync_tab.QWidget", return_value=mock_panel):
                with patch(
                    "argus_overview.ui.settings_sync_tab.QHBoxLayout", return_value=mock_layout
                ):
                    with patch("argus_overview.ui.settings_sync_tab.QGroupBox"):
                        with patch("argus_overview.ui.settings_sync_tab.QVBoxLayout"):
                            with patch("argus_overview.ui.settings_sync_tab.QComboBox"):
                                with patch("argus_overview.ui.settings_sync_tab.QLabel"):
                                    with patch("argus_overview.ui.settings_sync_tab.QListWidget"):
                                        with patch(
                                            "argus_overview.ui.settings_sync_tab.QPushButton"
                                        ):
                                            with patch(
                                                "argus_overview.ui.settings_sync_tab.QCheckBox"
                                            ):
                                                with patch(
                                                    "argus_overview.ui.settings_sync_tab.ToolbarBuilder"
                                                ):
                                                    result = tab._create_character_panel()

                                                    assert result == mock_panel

    def test_create_log_panel(self):
        """Test _create_log_panel creates panel"""
        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "__init__", return_value=None):
            tab = SettingsSyncTab.__new__(SettingsSyncTab)

            mock_panel = MagicMock()
            mock_layout = MagicMock()

            with patch("argus_overview.ui.settings_sync_tab.QWidget", return_value=mock_panel):
                with patch(
                    "argus_overview.ui.settings_sync_tab.QVBoxLayout", return_value=mock_layout
                ):
                    with patch("argus_overview.ui.settings_sync_tab.QLabel"):
                        with patch("argus_overview.ui.settings_sync_tab.QFont"):
                            with patch("argus_overview.ui.settings_sync_tab.QTextEdit"):
                                with patch("argus_overview.ui.settings_sync_tab.QPushButton"):
                                    result = tab._create_log_panel()

                                    assert result == mock_panel

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_scan_settings(self, mock_widget):
        """Test _scan_settings starts worker"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.scan_btn = MagicMock()
            tab.progress_bar = MagicMock()
            tab.log_text = MagicMock()

            with patch("argus_overview.ui.settings_sync_tab.ScanWorker") as mock_worker_class:
                mock_worker = MagicMock()
                mock_worker_class.return_value = mock_worker

                tab._scan_settings()

                tab.scan_btn.setEnabled.assert_called_with(False)
                tab.progress_bar.setVisible.assert_called_with(True)
                mock_worker.start.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_on_scan_progress(self, mock_widget):
        """Test _on_scan_progress updates UI"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.progress_bar = MagicMock()
            tab.log_text = MagicMock()

            tab._on_scan_progress(50, "Scanning...")

            tab.progress_bar.setValue.assert_called_with(50)

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_on_scan_complete(self, mock_widget):
        """Test _on_scan_complete populates lists"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        mock_char = MagicMock()
        mock_char.character_name = "TestChar"

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.scan_btn = MagicMock()
            tab.progress_bar = MagicMock()
            tab.source_combo = MagicMock()
            tab.target_list = MagicMock()
            tab.log_text = MagicMock()

            tab._on_scan_complete([mock_char])

            assert tab.scanned_characters == [mock_char]
            tab.source_combo.clear.assert_called_once()
            tab.source_combo.addItem.assert_called_with("TestChar", mock_char)
            tab.target_list.clear.assert_called_once()
            tab.target_list.addItem.assert_called_with("TestChar")

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QMessageBox")
    def test_on_scan_error(self, mock_msgbox, mock_widget):
        """Test _on_scan_error shows error"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.scan_btn = MagicMock()
            tab.progress_bar = MagicMock()
            tab.log_text = MagicMock()

            tab._on_scan_error("Test error")

            tab.scan_btn.setEnabled.assert_called_with(True)
            mock_msgbox.critical.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_on_source_selected(self, mock_widget):
        """Test _on_source_selected updates info"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        mock_char = MagicMock()
        mock_char.settings_dir = "/tmp/test"

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.source_combo = MagicMock()
            tab.source_combo.currentData.return_value = mock_char
            tab.source_info_label = MagicMock()
            tab.preview_btn = MagicMock()
            tab.sync_btn = MagicMock()
            tab.target_list = MagicMock()
            tab.target_list.selectedItems.return_value = []

            with patch.object(tab, "_get_last_modified", return_value="2024-01-01"):
                with patch("argus_overview.ui.settings_sync_tab.Path") as mock_path:
                    mock_path_obj = MagicMock()
                    mock_path_obj.glob.return_value = []
                    mock_path.return_value = mock_path_obj

                    tab._on_source_selected()

                    tab.source_info_label.setText.assert_called()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_get_last_modified_no_path(self, mock_widget):
        """Test _get_last_modified with non-existent path"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())

            result = tab._get_last_modified(Path("/nonexistent"))

            assert result == "N/A"

    def test_get_last_modified_with_files(self, tmp_path):
        """Test _get_last_modified with files"""
        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        (tmp_path / "test.dat").write_text("data")

        with patch.object(SettingsSyncTab, "__init__", return_value=None):
            tab = SettingsSyncTab.__new__(SettingsSyncTab)
            tab.logger = MagicMock()

            result = tab._get_last_modified(tmp_path)

            assert result != "N/A"

    def test_get_last_modified_no_files(self, tmp_path):
        """Test _get_last_modified with empty directory"""
        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "__init__", return_value=None):
            tab = SettingsSyncTab.__new__(SettingsSyncTab)
            tab.logger = MagicMock()

            result = tab._get_last_modified(tmp_path)

            assert result == "N/A"

    def test_get_last_modified_exception(self, tmp_path):
        """Test _get_last_modified with exception"""
        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "__init__", return_value=None):
            tab = SettingsSyncTab.__new__(SettingsSyncTab)
            tab.logger = MagicMock()

            with patch("pathlib.Path.glob", side_effect=OSError("Test error")):
                with patch("pathlib.Path.exists", return_value=True):
                    result = tab._get_last_modified(tmp_path)

                    assert result == "N/A"

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QMessageBox")
    def test_select_team_no_teams(self, mock_msgbox, mock_widget):
        """Test _select_team with no teams"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_teams.return_value = []

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), mock_char_manager)

            tab._select_team()

            mock_msgbox.information.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("PySide6.QtWidgets.QInputDialog")
    def test_select_team_success(self, mock_dialog, mock_widget):
        """Test _select_team with successful selection"""
        mock_widget.return_value = None
        mock_dialog.getItem.return_value = ("TestTeam", True)

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        mock_team = MagicMock()
        mock_team.name = "TestTeam"
        mock_team.members = ["Char1", "Char2"]

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_teams.return_value = [mock_team]

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), mock_char_manager)
            tab.target_list = MagicMock()

            mock_item1 = MagicMock()
            mock_item1.text.return_value = "Char1"
            mock_item2 = MagicMock()
            mock_item2.text.return_value = "Char2"
            mock_item3 = MagicMock()
            mock_item3.text.return_value = "OtherChar"

            tab.target_list.count.return_value = 3
            tab.target_list.item.side_effect = [mock_item1, mock_item2, mock_item3]
            tab.log_text = MagicMock()

            tab._select_team()

            mock_item1.setSelected.assert_called_with(True)
            mock_item2.setSelected.assert_called_with(True)
            mock_item3.setSelected.assert_not_called()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_select_all_targets(self, mock_widget):
        """Test _select_all_targets selects all"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.target_list = MagicMock()
            tab.preview_btn = MagicMock()
            tab.sync_btn = MagicMock()
            tab.source_combo = MagicMock()
            tab.source_combo.currentData.return_value = None

            mock_item = MagicMock()
            tab.target_list.count.return_value = 2
            tab.target_list.item.return_value = mock_item
            tab.target_list.selectedItems.return_value = []

            tab._select_all_targets()

            assert mock_item.setSelected.call_count == 2

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_clear_targets(self, mock_widget):
        """Test _clear_targets clears selection"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.target_list = MagicMock()
            tab.preview_btn = MagicMock()
            tab.sync_btn = MagicMock()
            tab.source_combo = MagicMock()
            tab.source_combo.currentData.return_value = None
            tab.target_list.selectedItems.return_value = []

            tab._clear_targets()

            tab.target_list.clearSelection.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_update_button_states(self, mock_widget):
        """Test _update_button_states enables/disables buttons"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.source_combo = MagicMock()
            tab.source_combo.currentData.return_value = MagicMock()
            tab.target_list = MagicMock()
            tab.target_list.selectedItems.return_value = [MagicMock()]
            tab.preview_btn = MagicMock()
            tab.sync_btn = MagicMock()

            tab._update_button_states()

            tab.preview_btn.setEnabled.assert_called_with(True)
            tab.sync_btn.setEnabled.assert_called_with(True)

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QMessageBox")
    def test_preview_sync_no_source(self, mock_msgbox, mock_widget):
        """Test _preview_sync with no source"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.source_combo = MagicMock()
            tab.source_combo.currentData.return_value = None

            tab._preview_sync()

            mock_msgbox.warning.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QMessageBox")
    def test_preview_sync_no_targets(self, mock_msgbox, mock_widget):
        """Test _preview_sync with no targets"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.source_combo = MagicMock()
            tab.source_combo.currentData.return_value = MagicMock()
            tab.target_list = MagicMock()
            tab.target_list.selectedItems.return_value = []
            tab.scanned_characters = []

            tab._preview_sync()

            mock_msgbox.warning.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.SyncPreviewDialog")
    def test_preview_sync_success(self, mock_dialog_class, mock_widget):
        """Test _preview_sync shows dialog"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        mock_char = MagicMock()
        mock_char.character_name = "TestChar"

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.source_combo = MagicMock()
            tab.source_combo.currentData.return_value = mock_char
            tab.target_list = MagicMock()

            mock_item = MagicMock()
            mock_item.text.return_value = "TestChar"
            tab.target_list.selectedItems.return_value = [mock_item]
            tab.scanned_characters = [mock_char]

            tab._preview_sync()

            mock_dialog_class.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QMessageBox")
    def test_sync_settings_no_source(self, mock_msgbox, mock_widget):
        """Test _sync_settings with no source"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.source_combo = MagicMock()
            tab.source_combo.currentData.return_value = None

            tab._sync_settings()

            mock_msgbox.warning.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QMessageBox")
    @patch("argus_overview.ui.settings_sync_tab.SyncWorker")
    def test_sync_settings_success(self, mock_worker_class, mock_msgbox, mock_widget):
        """Test _sync_settings starts worker"""
        mock_widget.return_value = None

        from PySide6.QtWidgets import QMessageBox

        mock_msgbox.StandardButton = QMessageBox.StandardButton
        mock_msgbox.question.return_value = QMessageBox.StandardButton.Yes

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        mock_char = MagicMock()
        mock_char.character_name = "TestChar"

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.source_combo = MagicMock()
            tab.source_combo.currentData.return_value = mock_char
            tab.target_list = MagicMock()

            mock_item = MagicMock()
            mock_item.text.return_value = "TestChar"
            tab.target_list.selectedItems.return_value = [mock_item]
            tab.scanned_characters = [mock_char]
            tab.backup_checkbox = MagicMock()
            tab.backup_checkbox.isChecked.return_value = True
            tab.sync_btn = MagicMock()
            tab.preview_btn = MagicMock()
            tab.progress_bar = MagicMock()
            tab.log_text = MagicMock()

            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker

            tab._sync_settings()

            mock_worker.start.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_on_sync_progress(self, mock_widget):
        """Test _on_sync_progress updates UI"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.progress_bar = MagicMock()
            tab.log_text = MagicMock()

            tab._on_sync_progress("TestChar", 50)

            tab.progress_bar.setValue.assert_called_with(50)

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QMessageBox")
    def test_on_sync_complete(self, mock_msgbox, mock_widget):
        """Test _on_sync_complete shows results"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.sync_btn = MagicMock()
            tab.preview_btn = MagicMock()
            tab.progress_bar = MagicMock()
            tab.log_text = MagicMock()

            tab._on_sync_complete({"Char1": True, "Char2": False})

            mock_msgbox.information.assert_called_once()
            tab.progress_bar.setVisible.assert_called_with(False)

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QMessageBox")
    def test_on_sync_error(self, mock_msgbox, mock_widget):
        """Test _on_sync_error shows error"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.sync_btn = MagicMock()
            tab.preview_btn = MagicMock()
            tab.progress_bar = MagicMock()
            tab.log_text = MagicMock()

            tab._on_sync_error("Test error")

            mock_msgbox.critical.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QFileDialog")
    @patch("argus_overview.ui.settings_sync_tab.QMessageBox")
    def test_add_custom_path(self, mock_msgbox, mock_dialog, mock_widget):
        """Test _add_custom_path adds path"""
        mock_widget.return_value = None
        mock_dialog.getExistingDirectory.return_value = "/tmp/test"
        mock_msgbox.StandardButton.Yes = 1
        mock_msgbox.StandardButton.No = 2
        mock_msgbox.question.return_value = 2

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(mock_settings_sync, MagicMock())
            tab.log_text = MagicMock()

            tab._add_custom_path()

            mock_settings_sync.add_custom_path.assert_called_once()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_sync_tab.QFileDialog")
    def test_add_custom_path_cancelled(self, mock_dialog, mock_widget):
        """Test _add_custom_path when cancelled"""
        mock_widget.return_value = None
        mock_dialog.getExistingDirectory.return_value = ""

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        mock_settings_sync = MagicMock()

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(mock_settings_sync, MagicMock())

            tab._add_custom_path()

            mock_settings_sync.add_custom_path.assert_not_called()

    @patch("argus_overview.ui.settings_sync_tab.QWidget.__init__")
    def test_log(self, mock_widget):
        """Test _log adds message to log"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        with patch.object(SettingsSyncTab, "_setup_ui"):
            tab = SettingsSyncTab(MagicMock(), MagicMock())
            tab.log_text = MagicMock()

            tab._log("Test message")

            tab.log_text.append.assert_called_once()
            call_arg = tab.log_text.append.call_args[0][0]
            assert "Test message" in call_arg
