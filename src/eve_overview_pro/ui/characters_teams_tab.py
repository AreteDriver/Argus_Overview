"""
Characters & Teams Tab - Character roster and team management
Implements character database, team building with drag-drop, and layout linking
"""
import logging
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from eve_overview_pro.core.character_manager import Character, Team
from eve_overview_pro.ui.action_registry import ActionRegistry, PrimaryHome
from eve_overview_pro.ui.menu_builder import ToolbarBuilder


class CharacterTable(QTableWidget):
    """Table widget displaying all characters"""

    character_selected = Signal(str)  # character name

    ROLES = ["DPS", "Miner", "Scout", "Logi", "Hauler", "Trader", "FC", "Booster"]

    def __init__(self, character_manager, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.character_manager = character_manager

        # Setup table
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(["Name", "Account", "Role", "Status", "Window ID", "Notes"])

        # Configure columns
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)

        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        # Connect signals
        self.itemSelectionChanged.connect(self._on_selection_changed)

        # Initial population
        self.populate_table()

    def populate_table(self):
        """Populate table with all characters"""
        characters = self.character_manager.get_all_characters()

        self.setSortingEnabled(False)
        self.setRowCount(len(characters))

        for row, char in enumerate(characters):
            # Name
            name_item = QTableWidgetItem(char.name)
            if char.is_main:
                name_item.setForeground(QColor(66, 135, 245))  # Blue for main
            self.setItem(row, 0, name_item)

            # Account
            account_item = QTableWidgetItem(char.account or "")
            self.setItem(row, 1, account_item)

            # Role
            role_item = QTableWidgetItem(char.role)
            self.setItem(row, 2, role_item)

            # Status
            status = "Active" if char.window_id else "Offline"
            status_item = QTableWidgetItem(status)
            if char.window_id:
                status_item.setForeground(QColor(0, 200, 0))  # Green
            else:
                status_item.setForeground(QColor(128, 128, 128))  # Gray
            self.setItem(row, 3, status_item)

            # Window ID
            window_item = QTableWidgetItem(char.window_id or "")
            window_item.setForeground(QColor(128, 128, 128))
            self.setItem(row, 4, window_item)

            # Notes
            notes_item = QTableWidgetItem(char.notes or "")
            self.setItem(row, 5, notes_item)

        self.setSortingEnabled(True)
        self.logger.info(f"Populated table with {len(characters)} characters")

    def update_character_status(self, char_name: str, window_id: Optional[str]):
        """
        Update character status in table

        Args:
            char_name: Character name
            window_id: Window ID (None if offline)
        """
        for row in range(self.rowCount()):
            name_item = self.item(row, 0)
            if name_item and name_item.text() == char_name:
                # Update status
                status = "Active" if window_id else "Offline"
                status_item = self.item(row, 3)
                if status_item:
                    status_item.setText(status)
                    if window_id:
                        status_item.setForeground(QColor(0, 200, 0))
                    else:
                        status_item.setForeground(QColor(128, 128, 128))

                # Update window ID
                window_item = self.item(row, 4)
                if window_item:
                    window_item.setText(window_id or "")

                self.logger.debug(f"Updated status for {char_name}: {status}")
                break

    def get_selected_characters(self) -> List[str]:
        """Get names of selected characters"""
        names = []
        for item in self.selectedItems():
            if item.column() == 0:  # Name column
                names.append(item.text())
        return names

    def _on_selection_changed(self):
        """Handle selection change"""
        names = self.get_selected_characters()
        if names:
            self.character_selected.emit(names[0])


class CharacterDialog(QDialog):
    """Dialog for adding/editing characters"""

    def __init__(self, character_manager, character: Optional[Character] = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.character_manager = character_manager
        self.character = character

        self.setWindowTitle("Edit Character" if character else "Add Character")
        self.setModal(True)
        self.resize(400, 300)

        self._setup_ui()

        # Load character data if editing
        if character:
            self._load_character()

    def _setup_ui(self):
        """Setup UI"""
        layout = QFormLayout()
        self.setLayout(layout)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Character name")
        layout.addRow("Name*:", self.name_edit)

        # Account
        self.account_combo = QComboBox()
        self.account_combo.setEditable(True)
        accounts = self.character_manager.get_accounts()
        self.account_combo.addItems([""] + accounts)
        layout.addRow("Account:", self.account_combo)

        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems(CharacterTable.ROLES)
        layout.addRow("Role:", self.role_combo)

        # Is Main
        self.is_main_check = QCheckBox("This is my main character")
        layout.addRow("", self.is_main_check)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Optional notes about this character...")
        self.notes_edit.setMaximumHeight(100)
        layout.addRow("Notes:", self.notes_edit)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def _load_character(self):
        """Load character data into form"""
        self.name_edit.setText(self.character.name)
        self.name_edit.setEnabled(False)  # Can't change name when editing

        self.account_combo.setCurrentText(self.character.account or "")
        self.role_combo.setCurrentText(self.character.role)
        self.is_main_check.setChecked(self.character.is_main)
        self.notes_edit.setPlainText(self.character.notes or "")

    def _on_accept(self):
        """Validate and accept"""
        if not self.validate():
            return

        self.accept()

    def validate(self) -> bool:
        """Validate form data"""
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Character name is required.")
            return False

        # Check uniqueness (only when adding new)
        if not self.character:
            if self.character_manager.get_character(name):
                QMessageBox.warning(self, "Duplicate Name", f"Character '{name}' already exists.")
                return False

        # Warn if account has 3 characters
        account = self.account_combo.currentText().strip()
        if account:
            chars_in_account = self.character_manager.get_characters_by_account(account)
            if len(chars_in_account) >= 3 and (not self.character or self.character.account != account):
                reply = QMessageBox.question(
                    self,
                    "Account Full",
                    f"Account '{account}' already has 3 characters.\n\nContinue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return False

        return True

    def get_character(self) -> Character:
        """Get character from form data"""
        name = self.name_edit.text().strip()
        account = self.account_combo.currentText().strip()
        role = self.role_combo.currentText()
        is_main = self.is_main_check.isChecked()
        notes = self.notes_edit.toPlainText().strip()

        if self.character:
            # Update existing
            self.character.account = account
            self.character.role = role
            self.character.is_main = is_main
            self.character.notes = notes
            return self.character
        else:
            # Create new
            return Character(
                name=name,
                account=account,
                role=role,
                is_main=is_main,
                notes=notes
            )


class TeamBuilder(QWidget):
    """Widget for building and managing teams"""

    team_modified = Signal()

    def __init__(self, character_manager, layout_manager, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.character_manager = character_manager
        self.layout_manager = layout_manager

        self.current_team: Optional[Team] = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Team info group
        info_group = QGroupBox("Team Information")
        info_layout = QFormLayout()
        info_group.setLayout(info_layout)

        # Team name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Team name")
        info_layout.addRow("Name*:", self.name_edit)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Team description...")
        self.description_edit.setMaximumHeight(60)
        info_layout.addRow("Description:", self.description_edit)

        # Layout preset
        self.layout_combo = QComboBox()
        self._refresh_layouts()
        info_layout.addRow("Layout Preset:", self.layout_combo)

        # Color
        color_layout = QHBoxLayout()
        self.color_button = QPushButton()
        self.color_button.setFixedSize(80, 30)
        self.color_button.clicked.connect(self._choose_color)
        self._set_color("#4287f5")
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        info_layout.addRow("Team Color:", color_layout)

        layout.addWidget(info_group)

        # Members group
        members_group = QGroupBox("Team Members")
        members_layout = QVBoxLayout()
        members_group.setLayout(members_layout)

        members_layout.addWidget(QLabel("Drag characters from the table or use the button below:"))

        # Add member button
        add_btn = QPushButton("Add Selected Character")
        add_btn.clicked.connect(self._add_selected_character)
        members_layout.addWidget(add_btn)

        # Member list
        self.member_list = QListWidget()
        self.member_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        members_layout.addWidget(self.member_list)

        # Remove button
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_member)
        members_layout.addWidget(remove_btn)

        layout.addWidget(members_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save Team")
        self.save_btn.clicked.connect(self._save_team)
        button_layout.addWidget(self.save_btn)

        self.new_btn = QPushButton("New Team")
        self.new_btn.clicked.connect(self._new_team)
        button_layout.addWidget(self.new_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _refresh_layouts(self):
        """Refresh layout preset dropdown"""
        self.layout_combo.clear()
        self.layout_combo.addItem("Default")

        presets = self.layout_manager.get_all_presets()
        for preset in presets:
            self.layout_combo.addItem(preset.name)

    def _choose_color(self):
        """Open color picker"""
        color = QColorDialog.getColor(QColor(self.team_color), self, "Choose Team Color")
        if color.isValid():
            self._set_color(color.name())

    def _set_color(self, color_hex: str):
        """Set team color"""
        self.team_color = color_hex
        self.color_button.setStyleSheet(f"background-color: {color_hex};")

    def load_team(self, team: Team):
        """Load team into builder"""
        self.current_team = team

        self.name_edit.setText(team.name)
        self.description_edit.setPlainText(team.description)
        self.layout_combo.setCurrentText(team.layout_name)
        self._set_color(team.color)

        # Load members
        self.member_list.clear()
        for char_name in team.characters:
            char = self.character_manager.get_character(char_name)
            if char:
                self._add_member_to_list(char)

        self.logger.info(f"Loaded team: {team.name}")

    def _new_team(self):
        """Start new team"""
        self.current_team = None
        self.name_edit.clear()
        self.description_edit.clear()
        self.layout_combo.setCurrentText("Default")
        self._set_color("#4287f5")
        self.member_list.clear()

        self.logger.info("Started new team")

    def _add_selected_character(self):
        """Add selected character from table (needs reference from parent)"""
        # This will be connected from parent
        pass

    def add_member(self, char_name: str):
        """Add character to team"""
        char = self.character_manager.get_character(char_name)
        if not char:
            return

        # Check if already in list (compare stored name, not display text)
        for i in range(self.member_list.count()):
            item = self.member_list.item(i)
            stored_name = item.data(Qt.ItemDataRole.UserRole)
            if stored_name == char_name:
                self.logger.debug(f"Character {char_name} already in team")
                return

        self._add_member_to_list(char)
        self.logger.info(f"Added {char_name} to team")

    def _add_member_to_list(self, char: Character):
        """Add character to member list widget"""
        item = QListWidgetItem(f"{char.name} ({char.role})")
        item.setData(Qt.ItemDataRole.UserRole, char.name)

        # Color code by role
        role_colors = {
            "DPS": QColor(255, 100, 100),
            "Miner": QColor(100, 200, 100),
            "Scout": QColor(100, 100, 255),
            "Logi": QColor(200, 100, 200),
            "Hauler": QColor(200, 200, 100),
            "Trader": QColor(100, 200, 200),
            "FC": QColor(255, 200, 100),
            "Booster": QColor(200, 100, 255)
        }
        if char.role in role_colors:
            item.setForeground(role_colors[char.role])

        self.member_list.addItem(item)

    def _remove_selected_member(self):
        """Remove selected member from list"""
        current = self.member_list.currentItem()
        if current:
            char_name = current.data(Qt.ItemDataRole.UserRole)
            self.member_list.takeItem(self.member_list.row(current))
            self.logger.info(f"Removed {char_name} from team")

    def _save_team(self):
        """Save current team"""
        if not self._validate():
            return

        team = self._get_team()

        if self.current_team:
            # Update existing
            self.character_manager.update_team(
                team.name,
                description=team.description,
                layout_name=team.layout_name,
                color=team.color
            )
            # Update characters
            old_chars = set(self.current_team.characters)
            new_chars = set(team.characters)

            # Remove old
            for char_name in old_chars - new_chars:
                self.character_manager.remove_character_from_team(team.name, char_name)

            # Add new
            for char_name in new_chars - old_chars:
                self.character_manager.add_character_to_team(team.name, char_name)

            QMessageBox.information(self, "Success", f"Team '{team.name}' updated successfully!")
        else:
            # Create new
            if self.character_manager.create_team(team):
                # Add members
                for char_name in team.characters:
                    self.character_manager.add_character_to_team(team.name, char_name)

                QMessageBox.information(self, "Success", f"Team '{team.name}' created successfully!")
                self.current_team = team
            else:
                QMessageBox.warning(self, "Error", f"Failed to create team '{team.name}'.\nTeam may already exist.")

        self.team_modified.emit()

    def _validate(self) -> bool:
        """Validate team data"""
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Team name is required.")
            return False

        if self.member_list.count() == 0:
            QMessageBox.warning(self, "Invalid Input", "Team must have at least one member.")
            return False

        # Check uniqueness (only when creating new)
        if not self.current_team:
            if self.character_manager.get_team(name):
                QMessageBox.warning(self, "Duplicate Name", f"Team '{name}' already exists.")
                return False

        return True

    def _get_team(self) -> Team:
        """Get team from form data"""
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        layout_name = self.layout_combo.currentText()

        # Get member names
        members = []
        for i in range(self.member_list.count()):
            char_name = self.member_list.item(i).data(Qt.ItemDataRole.UserRole)
            members.append(char_name)

        if self.current_team:
            # Update existing
            return Team(
                name=name,
                description=description,
                characters=members,
                layout_name=layout_name,
                color=self.team_color,
                created_at=self.current_team.created_at
            )
        else:
            # Create new
            return Team(
                name=name,
                description=description,
                characters=members,
                layout_name=layout_name,
                color=self.team_color
            )


class CharactersTeamsTab(QWidget):
    """Characters & Teams Tab"""

    team_selected = Signal(object)  # Team object
    characters_imported = Signal(int)  # number imported

    def __init__(self, character_manager, layout_manager, settings_sync=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.character_manager = character_manager
        self.layout_manager = layout_manager
        self.settings_sync = settings_sync  # EVESettingsSync for folder scanning

        self._setup_ui()

        self.logger.info("Characters & Teams tab initialized")

    def _setup_ui(self):
        """Setup UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel - Characters
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Teams
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Set initial sizes (60/40 split)
        splitter.setSizes([600, 400])

    def _create_left_panel(self) -> QWidget:
        """Create left panel with character table (v2.3 - uses ActionRegistry)"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Build toolbar from ActionRegistry
        toolbar_layout = QHBoxLayout()
        toolbar_builder = ToolbarBuilder()

        # Roster toolbar actions
        handlers = {
            "add_character": self._add_character,
            "scan_eve_folder": self._scan_eve_folder,
            "new_team": self.team_builder._new_team if hasattr(self, 'team_builder') else None,
        }

        # Add Character button from registry
        add_btn = toolbar_builder.create_button("add_character", self._add_character)
        if add_btn:
            toolbar_layout.addWidget(add_btn)

        # Edit/Delete are context actions but keep in toolbar for convenience
        edit_btn = toolbar_builder.create_button("edit_character", self._edit_character)
        if edit_btn:
            toolbar_layout.addWidget(edit_btn)

        delete_btn = toolbar_builder.create_button("delete_character", self._delete_character)
        if delete_btn:
            toolbar_layout.addWidget(delete_btn)

        toolbar_layout.addStretch()

        # Scan EVE Folder button (if settings_sync available)
        if self.settings_sync is not None:
            scan_btn = toolbar_builder.create_button("scan_eve_folder", self._scan_eve_folder)
            if scan_btn:
                toolbar_layout.addWidget(scan_btn)

        layout.addLayout(toolbar_layout)

        # Character table
        self.character_table = CharacterTable(self.character_manager)
        layout.addWidget(self.character_table)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create right panel with team builder"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Team selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Select Team:"))

        self.team_combo = QComboBox()
        self.team_combo.currentTextChanged.connect(self._on_team_selected)
        self._refresh_teams()
        selector_layout.addWidget(self.team_combo)

        layout.addLayout(selector_layout)

        # Team builder
        self.team_builder = TeamBuilder(self.character_manager, self.layout_manager)
        self.team_builder.team_modified.connect(self._on_team_modified)
        layout.addWidget(self.team_builder)

        # Connect character table to team builder
        self.character_table.character_selected.connect(self.team_builder.add_member)

        return panel

    def _refresh_teams(self):
        """Refresh team dropdown"""
        self.team_combo.blockSignals(True)
        current = self.team_combo.currentText()

        self.team_combo.clear()
        self.team_combo.addItem("-- New Team --")

        teams = self.character_manager.get_all_teams()
        for team in teams:
            self.team_combo.addItem(team.name)

        # Restore selection
        index = self.team_combo.findText(current)
        if index >= 0:
            self.team_combo.setCurrentIndex(index)

        self.team_combo.blockSignals(False)

    def _add_character(self):
        """Add new character"""
        dialog = CharacterDialog(self.character_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            char = dialog.get_character()
            if self.character_manager.add_character(char):
                self.character_table.populate_table()
                self.logger.info(f"Added character: {char.name}")

    def _edit_character(self):
        """Edit selected character"""
        selected = self.character_table.get_selected_characters()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select a character to edit.")
            return

        char_name = selected[0]
        char = self.character_manager.get_character(char_name)
        if not char:
            return

        dialog = CharacterDialog(self.character_manager, char, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_char = dialog.get_character()
            self.character_manager.update_character(
                char_name,
                account=updated_char.account,
                role=updated_char.role,
                is_main=updated_char.is_main,
                notes=updated_char.notes
            )
            self.character_table.populate_table()
            self.logger.info(f"Updated character: {char_name}")

    def _delete_character(self):
        """Delete selected character"""
        selected = self.character_table.get_selected_characters()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select a character to delete.")
            return

        char_name = selected[0]

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete character '{char_name}'?\n\nThis will also remove them from all teams.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.character_manager.remove_character(char_name):
                self.character_table.populate_table()
                self.logger.info(f"Deleted character: {char_name}")

    def _scan_eve_folder(self):
        """Scan EVE installation folder and import all characters"""
        if self.settings_sync is None:
            QMessageBox.warning(self, "Error", "EVE Settings Sync not available.")
            return

        # Show progress message
        QMessageBox.information(
            self,
            "Scanning EVE Folder",
            "Scanning your EVE installation for character data...\n\n"
            "This will import ALL characters that have logged in on this computer."
        )

        try:
            # Get all characters from EVE files
            eve_characters = self.settings_sync.get_all_known_characters()

            if not eve_characters:
                QMessageBox.warning(
                    self,
                    "No Characters Found",
                    "No character data found in EVE installation.\n\n"
                    "Make sure you have logged into EVE Online at least once."
                )
                return

            # Import into character manager
            imported = self.character_manager.import_from_eve_sync(eve_characters)

            # Refresh table
            self.character_table.populate_table()

            # Show results
            QMessageBox.information(
                self,
                "Import Complete",
                f"Found {len(eve_characters)} characters in EVE files.\n"
                f"Imported {imported} new characters.\n"
                f"({len(eve_characters) - imported} were already in database)"
            )

            # Emit signal
            self.characters_imported.emit(imported)

            self.logger.info(f"EVE folder scan complete: {imported} new characters imported")

        except Exception as e:
            self.logger.error(f"EVE folder scan failed: {e}")
            QMessageBox.critical(
                self,
                "Scan Failed",
                f"Failed to scan EVE folder:\n{str(e)}"
            )

    def _on_team_selected(self, team_name: str):
        """Handle team selection from dropdown"""
        if team_name == "-- New Team --":
            self.team_builder._new_team()
        else:
            team = self.character_manager.get_team(team_name)
            if team:
                self.team_builder.load_team(team)
                self.team_selected.emit(team)

    def _on_team_modified(self):
        """Handle team modification"""
        self._refresh_teams()
        self.logger.info("Team modified")

    def update_character_status(self, char_name: str, window_id: Optional[str]):
        """Update character status (called from main window)"""
        self.character_table.update_character_status(char_name, window_id)
