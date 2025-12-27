"""
Settings Sync Tab - EVE Online settings synchronization
Scan and sync EVE client settings between characters
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox,
    QLabel, QComboBox, QListWidget, QTextEdit, QProgressBar,
    QMessageBox, QDialog, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QCheckBox, QFileDialog, QSplitter
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QColor
import logging
from typing import List, Dict, Optional
from pathlib import Path


class ScanWorker(QThread):
    """Background worker for scanning EVE settings"""
    scan_progress = Signal(int, str)  # percentage, current_path
    scan_complete = Signal(list)  # List of EVECharacterSettings
    scan_error = Signal(str)  # error message

    def __init__(self, settings_sync):
        super().__init__()
        self.settings_sync = settings_sync
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Run scan in background thread"""
        try:
            self.scan_progress.emit(0, "Starting scan...")

            # Scan for characters
            characters = self.settings_sync.scan_for_characters()

            # Emit progress updates
            total = len(characters) if characters else 1
            for idx, char in enumerate(characters):
                progress = int((idx + 1) / total * 100)
                self.scan_progress.emit(progress, f"Scanning {char.character_name}...")

            self.scan_progress.emit(100, "Scan complete")
            self.scan_complete.emit(characters)

        except Exception as e:
            self.logger.error(f"Scan failed: {e}")
            self.scan_error.emit(str(e))


class SyncWorker(QThread):
    """Background worker for syncing EVE settings"""
    sync_progress = Signal(str, int)  # character_name, percentage
    sync_complete = Signal(dict)  # {character_name: success/failure}
    sync_error = Signal(str)  # error message

    def __init__(self, settings_sync, source_char, target_chars, backup=True):
        super().__init__()
        self.settings_sync = settings_sync
        self.source_char = source_char
        self.target_chars = target_chars
        self.backup = backup
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Run sync in background thread"""
        results = {}

        try:
            total = len(self.target_chars)

            for idx, target_char in enumerate(self.target_chars):
                self.sync_progress.emit(target_char.character_name, int(idx / total * 100))

                try:
                    success = self.settings_sync.sync_settings(
                        self.source_char.character_name,
                        [target_char.character_name],
                        backup=self.backup
                    )
                    results[target_char.character_name] = success.get(target_char.character_name, False)

                    progress = int((idx + 1) / total * 100)
                    self.sync_progress.emit(target_char.character_name, progress)

                except Exception as e:
                    self.logger.error(f"Failed to sync {target_char.character_name}: {e}")
                    results[target_char.character_name] = False

            self.sync_complete.emit(results)

        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            self.sync_error.emit(str(e))


class SyncPreviewDialog(QDialog):
    """Preview what will be synced before executing"""

    def __init__(self, source_char, target_chars, settings_sync, parent=None):
        super().__init__(parent)
        self.source_char = source_char
        self.target_chars = target_chars
        self.settings_sync = settings_sync
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("Sync Preview")
        self.setMinimumSize(700, 500)
        self._setup_ui()
        self._populate_preview()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Info header
        info_label = QLabel(
            f"Syncing settings from <b>{self.source_char.character_name}</b> "
            f"to {len(self.target_chars)} character(s)"
        )
        info_label.setStyleSheet("font-size: 11pt; padding: 10px;")
        layout.addWidget(info_label)

        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(4)
        self.preview_table.setHorizontalHeaderLabels([
            "File", "Source Date", "Target Date", "Action"
        ])
        self.preview_table.horizontalHeader().setStretchLastSection(False)
        self.preview_table.setColumnWidth(0, 250)
        self.preview_table.setColumnWidth(1, 150)
        self.preview_table.setColumnWidth(2, 150)
        self.preview_table.setColumnWidth(3, 120)
        layout.addWidget(self.preview_table)

        # Warning label
        warning_label = QLabel(
            "⚠️ Settings will be backed up before syncing. "
            "Backups are stored in the backup/ directory."
        )
        warning_label.setStyleSheet("color: #f39c12; padding: 5px;")
        layout.addWidget(warning_label)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _populate_preview(self):
        """Populate preview table with files to be synced"""
        self.preview_table.setRowCount(0)

        # Get source files
        source_dir = Path(self.source_char.settings_dir)
        if not source_dir.exists():
            QMessageBox.warning(self, "Error", f"Source directory not found: {source_dir}")
            return

        source_files = list(source_dir.glob("*.dat")) + list(source_dir.glob("*.yaml"))

        # For each target character
        for target_char in self.target_chars:
            target_dir = Path(target_char.settings_dir)

            for source_file in source_files:
                target_file = target_dir / source_file.name

                row = self.preview_table.rowCount()
                self.preview_table.insertRow(row)

                # File name
                file_item = QTableWidgetItem(source_file.name)
                self.preview_table.setItem(row, 0, file_item)

                # Source date
                source_date = self._get_file_date(source_file)
                source_item = QTableWidgetItem(source_date)
                self.preview_table.setItem(row, 1, source_item)

                # Target date
                target_date = self._get_file_date(target_file) if target_file.exists() else "N/A"
                target_item = QTableWidgetItem(target_date)
                self.preview_table.setItem(row, 2, target_item)

                # Action
                if not target_file.exists():
                    action = "Create"
                    color = QColor(100, 200, 100)
                else:
                    action = "Overwrite"
                    color = QColor(255, 200, 100)

                action_item = QTableWidgetItem(action)
                action_item.setForeground(color)
                self.preview_table.setItem(row, 3, action_item)

    def _get_file_date(self, file_path: Path) -> str:
        """Get file modification date as string"""
        if file_path.exists():
            from datetime import datetime
            mtime = file_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            return dt.strftime("%Y-%m-%d %H:%M")
        return "N/A"


class SettingsSyncTab(QWidget):
    """Main Settings Sync Tab widget"""

    def __init__(self, settings_sync, character_manager):
        super().__init__()
        self.settings_sync = settings_sync
        self.character_manager = character_manager
        self.logger = logging.getLogger(__name__)

        self.scanned_characters = []
        self.scan_worker = None
        self.sync_worker = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Top toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Splitter for character panel and log
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Character panel
        char_panel = self._create_character_panel()
        splitter.addWidget(char_panel)

        # Log panel
        log_panel = self._create_log_panel()
        splitter.addWidget(log_panel)

        splitter.setSizes([400, 200])
        layout.addWidget(splitter)

        self.setLayout(layout)

    def _create_toolbar(self) -> QWidget:
        """Create top toolbar"""
        toolbar = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Scan button
        self.scan_btn = QPushButton("Scan for EVE Settings")
        self.scan_btn.setToolTip("Scan EVE Online directory for character settings")
        self.scan_btn.clicked.connect(self._scan_settings)
        layout.addWidget(self.scan_btn)

        # Add custom path button
        self.add_path_btn = QPushButton("Add Custom Path")
        self.add_path_btn.setToolTip("Add custom EVE settings directory")
        self.add_path_btn.clicked.connect(self._add_custom_path)
        layout.addWidget(self.add_path_btn)

        layout.addStretch()

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        layout.addWidget(self.progress_bar)

        toolbar.setLayout(layout)
        return toolbar

    def _create_character_panel(self) -> QWidget:
        """Create character selection panel"""
        panel = QWidget()
        layout = QHBoxLayout()

        # Source character group
        source_group = QGroupBox("Source Character")
        source_layout = QVBoxLayout()

        self.source_combo = QComboBox()
        self.source_combo.currentIndexChanged.connect(self._on_source_selected)
        source_layout.addWidget(self.source_combo)

        # Source info
        self.source_info_label = QLabel("No character selected")
        self.source_info_label.setStyleSheet("color: #888; font-size: 9pt;")
        self.source_info_label.setWordWrap(True)
        source_layout.addWidget(self.source_info_label)

        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # Target characters group
        target_group = QGroupBox("Target Characters")
        target_layout = QVBoxLayout()

        # Target list
        self.target_list = QListWidget()
        self.target_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        target_layout.addWidget(self.target_list)

        # Quick select buttons
        quick_buttons = QHBoxLayout()

        self.select_team_btn = QPushButton("Select Team")
        self.select_team_btn.clicked.connect(self._select_team)
        quick_buttons.addWidget(self.select_team_btn)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all_targets)
        quick_buttons.addWidget(self.select_all_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_targets)
        quick_buttons.addWidget(self.clear_btn)

        target_layout.addLayout(quick_buttons)

        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        # Backup checkbox
        self.backup_checkbox = QCheckBox("Create backup before syncing")
        self.backup_checkbox.setChecked(True)
        options_layout.addWidget(self.backup_checkbox)

        # Action buttons
        action_layout = QVBoxLayout()

        self.preview_btn = QPushButton("Preview Sync")
        self.preview_btn.setToolTip("Preview what will be synced")
        self.preview_btn.clicked.connect(self._preview_sync)
        self.preview_btn.setEnabled(False)
        action_layout.addWidget(self.preview_btn)

        self.sync_btn = QPushButton("Sync Settings")
        self.sync_btn.setToolTip("Sync settings from source to targets")
        self.sync_btn.clicked.connect(self._sync_settings)
        self.sync_btn.setEnabled(False)
        action_layout.addWidget(self.sync_btn)

        action_layout.addStretch()
        options_layout.addLayout(action_layout)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        panel.setLayout(layout)
        return panel

    def _create_log_panel(self) -> QWidget:
        """Create log output panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Sync Log")
        font = QFont()
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

        # Clear log button
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_log_btn)

        panel.setLayout(layout)
        return panel

    def _scan_settings(self):
        """Start scanning for EVE settings"""
        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._log("Starting EVE settings scan...")

        # Create and start worker
        self.scan_worker = ScanWorker(self.settings_sync)
        self.scan_worker.scan_progress.connect(self._on_scan_progress)
        self.scan_worker.scan_complete.connect(self._on_scan_complete)
        self.scan_worker.scan_error.connect(self._on_scan_error)
        self.scan_worker.start()

    def _on_scan_progress(self, percentage: int, message: str):
        """Handle scan progress updates"""
        self.progress_bar.setValue(percentage)
        self._log(message)

    def _on_scan_complete(self, characters: list):
        """Handle scan completion"""
        self.scanned_characters = characters
        self.scan_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        self._log(f"Scan complete. Found {len(characters)} character(s).")

        # Populate source combo
        self.source_combo.clear()
        for char in characters:
            self.source_combo.addItem(char.character_name, char)

        # Populate target list
        self.target_list.clear()
        for char in characters:
            self.target_list.addItem(char.character_name)

        if characters:
            self._log("Select source character and target character(s), then click 'Sync Settings'.")

    def _on_scan_error(self, error_msg: str):
        """Handle scan error"""
        self.scan_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log(f"ERROR: {error_msg}")
        QMessageBox.critical(self, "Scan Error", f"Failed to scan settings:\n{error_msg}")

    def _on_source_selected(self):
        """Handle source character selection"""
        source_char = self.source_combo.currentData()
        if source_char:
            path = Path(source_char.settings_dir)
            file_count = len(list(path.glob("*.dat"))) + len(list(path.glob("*.yaml")))
            self.source_info_label.setText(
                f"Path: {path}\n"
                f"Files: {file_count}\n"
                f"Last modified: {self._get_last_modified(path)}"
            )

            # Enable preview/sync buttons if we have targets
            targets_selected = len(self.target_list.selectedItems()) > 0
            self.preview_btn.setEnabled(targets_selected)
            self.sync_btn.setEnabled(targets_selected)

    def _get_last_modified(self, path: Path) -> str:
        """Get last modified date of directory contents"""
        if not path.exists():
            return "N/A"

        try:
            files = list(path.glob("*.dat")) + list(path.glob("*.yaml"))
            if not files:
                return "N/A"

            latest = max(f.stat().st_mtime for f in files)
            from datetime import datetime
            dt = datetime.fromtimestamp(latest)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (OSError, ValueError) as e:
            self.logger.debug(f"Could not get last sync time: {e}")
            return "N/A"

    def _select_team(self):
        """Select characters from a team"""
        teams = self.character_manager.get_all_teams()
        if not teams:
            QMessageBox.information(self, "No Teams", "No teams available. Create a team first.")
            return

        # Simple dialog to select team
        from PySide6.QtWidgets import QInputDialog
        team_names = [team.name for team in teams]
        team_name, ok = QInputDialog.getItem(
            self, "Select Team", "Team:", team_names, 0, False
        )

        if ok and team_name:
            team = next((t for t in teams if t.name == team_name), None)
            if team:
                # Select members in target list
                for i in range(self.target_list.count()):
                    item = self.target_list.item(i)
                    if item.text() in team.members:
                        item.setSelected(True)

                self._log(f"Selected team '{team_name}' ({len(team.members)} members)")

    def _select_all_targets(self):
        """Select all target characters"""
        for i in range(self.target_list.count()):
            self.target_list.item(i).setSelected(True)

    def _clear_targets(self):
        """Clear target selection"""
        self.target_list.clearSelection()

    def _preview_sync(self):
        """Preview sync before executing"""
        source_char = self.source_combo.currentData()
        if not source_char:
            QMessageBox.warning(self, "Error", "Please select a source character.")
            return

        # Get selected targets
        target_chars = []
        for item in self.target_list.selectedItems():
            char = next((c for c in self.scanned_characters if c.character_name == item.text()), None)
            if char:
                target_chars.append(char)

        if not target_chars:
            QMessageBox.warning(self, "Error", "Please select at least one target character.")
            return

        # Show preview dialog
        dialog = SyncPreviewDialog(source_char, target_chars, self.settings_sync, self)
        dialog.exec()

    def _sync_settings(self):
        """Start syncing settings"""
        source_char = self.source_combo.currentData()
        if not source_char:
            QMessageBox.warning(self, "Error", "Please select a source character.")
            return

        # Get selected targets
        target_chars = []
        for item in self.target_list.selectedItems():
            char = next((c for c in self.scanned_characters if c.character_name == item.text()), None)
            if char:
                target_chars.append(char)

        if not target_chars:
            QMessageBox.warning(self, "Error", "Please select at least one target character.")
            return

        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm Sync",
            f"Sync settings from '{source_char.character_name}' to {len(target_chars)} character(s)?\n\n"
            f"Backup: {'Yes' if self.backup_checkbox.isChecked() else 'No'}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Disable buttons
        self.sync_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self._log(f"Starting sync from '{source_char.character_name}' to {len(target_chars)} character(s)...")

        # Create and start worker
        self.sync_worker = SyncWorker(
            self.settings_sync,
            source_char,
            target_chars,
            backup=self.backup_checkbox.isChecked()
        )
        self.sync_worker.sync_progress.connect(self._on_sync_progress)
        self.sync_worker.sync_complete.connect(self._on_sync_complete)
        self.sync_worker.sync_error.connect(self._on_sync_error)
        self.sync_worker.start()

    def _on_sync_progress(self, character_name: str, percentage: int):
        """Handle sync progress updates"""
        self.progress_bar.setValue(percentage)
        self._log(f"Syncing {character_name}... {percentage}%")

    def _on_sync_complete(self, results: dict):
        """Handle sync completion"""
        self.sync_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Log results
        self._log("Sync complete!")
        success_count = sum(1 for success in results.values() if success)
        self._log(f"Success: {success_count}/{len(results)}")

        for char_name, success in results.items():
            status = "✓" if success else "✗"
            self._log(f"{status} {char_name}")

        # Show completion message
        QMessageBox.information(
            self,
            "Sync Complete",
            f"Synced settings to {success_count}/{len(results)} character(s)."
        )

    def _on_sync_error(self, error_msg: str):
        """Handle sync error"""
        self.sync_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log(f"ERROR: {error_msg}")
        QMessageBox.critical(self, "Sync Error", f"Failed to sync settings:\n{error_msg}")

    def _add_custom_path(self):
        """Add custom EVE settings path"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select EVE Settings Directory",
            str(Path.home())
        )

        if path:
            self._log(f"Custom path: {path}")
            # TODO: Add custom path to settings_sync
            QMessageBox.information(
                self,
                "Feature Coming Soon",
                "Custom path support will be added in a future update."
            )

    def _log(self, message: str):
        """Add message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
