"""
Hotkeys & Cycling Tab - Hotkey assignment and window cycling groups
Drag-and-drop interface for creating cycling groups and assigning hotkeys
"""
import logging
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from eve_overview_pro.ui.action_registry import ActionRegistry, PrimaryHome
from eve_overview_pro.ui.menu_builder import ToolbarBuilder


class DraggableCharacterList(QListWidget):
    """List of characters that can be dragged to cycling groups"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)


class CyclingGroupList(QListWidget):
    """
    Droppable list for cycling group members.
    Supports reordering via drag-and-drop.
    """

    members_changed = Signal()  # Emitted when members are added/removed/reordered

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)

        # Style for drop target
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #555;
                border-radius: 5px;
                min-height: 200px;
            }
            QListWidget:focus {
                border-color: #ff8c00;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() or event.source() == self:
            event.acceptProposedAction()
        else:
            # Accept from character list
            source = event.source()
            if isinstance(source, DraggableCharacterList):
                event.acceptProposedAction()
            else:
                event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        source = event.source()

        if source == self:
            # Internal reorder
            super().dropEvent(event)
            self.members_changed.emit()
        elif isinstance(source, DraggableCharacterList):
            # Add from character list
            for item in source.selectedItems():
                char_name = item.text()
                # Check for duplicates
                existing = [self.item(i).text() for i in range(self.count())]
                if char_name not in existing:
                    new_item = QListWidgetItem(char_name)
                    new_item.setData(Qt.ItemDataRole.UserRole, char_name)
                    self.addItem(new_item)
            self.members_changed.emit()
            event.acceptProposedAction()
        else:
            event.ignore()

    def get_members(self) -> List[str]:
        """Get ordered list of member names"""
        return [self.item(i).text() for i in range(self.count())]


class HotkeysTab(QWidget):
    """
    Hotkeys & Cycling Tab

    Layout:
    - Left: Character list (draggable source)
    - Right Top: Cycling group selector dropdown
    - Right Middle/Bottom: Drag-drop group builder with member list
    """

    group_changed = Signal(str, list)  # group_name, members

    def __init__(self, character_manager, settings_manager, main_tab=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.character_manager = character_manager
        self.settings_manager = settings_manager
        self.main_tab = main_tab  # Reference to main tab for getting active windows

        # Cycling groups data: {group_name: [char_names in order]}
        self.cycling_groups: Dict[str, List[str]] = {}
        self.current_group: Optional[str] = None

        self._load_groups()
        self._setup_ui()

        self.logger.info("Hotkeys & Cycling tab initialized")

    def _load_groups(self):
        """Load cycling groups from settings"""
        groups = self.settings_manager.get("cycling_groups", {})
        if isinstance(groups, dict):
            self.cycling_groups = groups
        else:
            self.cycling_groups = {}

        # Ensure default group exists
        if "Default" not in self.cycling_groups:
            self.cycling_groups["Default"] = []

    def _save_groups(self):
        """Save cycling groups to settings"""
        self.settings_manager.set("cycling_groups", self.cycling_groups, auto_save=True)

    def _setup_ui(self):
        """Setup the UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel - Character list
        left_panel = self._create_character_panel()
        splitter.addWidget(left_panel)

        # Right panel - Cycling groups
        right_panel = self._create_cycling_panel()
        splitter.addWidget(right_panel)

        # Set initial sizes (40/60 split)
        splitter.setSizes([350, 550])

    def _create_character_panel(self) -> QWidget:
        """Create left panel with character list"""
        panel = QGroupBox("Characters")
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Instructions
        instructions = QLabel("Drag characters to the cycling group on the right")
        instructions.setStyleSheet("color: #888; font-style: italic;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Character list
        self.character_list = DraggableCharacterList()
        self._populate_character_list()
        layout.addWidget(self.character_list)

        # Refresh button
        refresh_btn = QPushButton("Refresh Characters")
        refresh_btn.clicked.connect(self._populate_character_list)
        layout.addWidget(refresh_btn)

        return panel

    def _create_cycling_panel(self) -> QWidget:
        """Create right panel with cycling group management (v2.3 - uses ActionRegistry)"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # ToolbarBuilder for registry-based buttons
        toolbar_builder = ToolbarBuilder()

        # Group selector section
        selector_group = QGroupBox("Cycling Group")
        selector_layout = QHBoxLayout()
        selector_group.setLayout(selector_layout)

        selector_layout.addWidget(QLabel("Select Group:"))

        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(150)
        self._refresh_group_combo()
        self.group_combo.currentTextChanged.connect(self._on_group_selected)
        selector_layout.addWidget(self.group_combo)

        selector_layout.addStretch()

        # New group button (from registry)
        new_btn = toolbar_builder.create_button("new_group", self._create_new_group)
        if new_btn:
            new_btn.setText("+ New Group")  # Override label for this context
            selector_layout.addWidget(new_btn)

        # Delete group button (from registry)
        delete_btn = toolbar_builder.create_button("delete_group", self._delete_current_group)
        if delete_btn:
            delete_btn.setText("Delete")  # Override label for this context
            selector_layout.addWidget(delete_btn)

        layout.addWidget(selector_group)

        # Group members section
        members_group = QGroupBox("Group Members (Drag to reorder)")
        members_layout = QVBoxLayout()
        members_group.setLayout(members_layout)

        # Drop zone label
        drop_label = QLabel("Drop characters here to add them to the cycling group")
        drop_label.setStyleSheet("color: #888; font-style: italic;")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        members_layout.addWidget(drop_label)

        # Cycling group member list (drop target)
        self.group_member_list = CyclingGroupList()
        self.group_member_list.members_changed.connect(self._on_members_changed)
        members_layout.addWidget(self.group_member_list)

        # Member controls
        member_controls = QHBoxLayout()

        # Context actions from registry
        remove_btn = toolbar_builder.create_button("remove_group_member", self._remove_selected_member)
        if remove_btn:
            member_controls.addWidget(remove_btn)

        clear_btn = toolbar_builder.create_button("clear_group", self._clear_group_members)
        if clear_btn:
            member_controls.addWidget(clear_btn)

        # Load active windows button (from registry)
        load_active_btn = toolbar_builder.create_button("load_active_windows", self._load_active_windows)
        if load_active_btn:
            member_controls.addWidget(load_active_btn)

        member_controls.addStretch()

        # Move Up/Down are list manipulation, not registry actions
        move_up_btn = QPushButton("Move Up")
        move_up_btn.clicked.connect(self._move_member_up)
        member_controls.addWidget(move_up_btn)

        move_down_btn = QPushButton("Move Down")
        move_down_btn.clicked.connect(self._move_member_down)
        member_controls.addWidget(move_down_btn)

        members_layout.addLayout(member_controls)

        layout.addWidget(members_group)

        # Hotkey assignment section
        hotkey_group = QGroupBox("Hotkey Settings")
        hotkey_layout = QFormLayout()
        hotkey_group.setLayout(hotkey_layout)

        # Cycle forward hotkey
        self.cycle_forward_edit = QLineEdit()
        self.cycle_forward_edit.setPlaceholderText("ctrl+shift+] (brackets auto-added)")
        self.cycle_forward_edit.setText(
            self.settings_manager.get("hotkeys.cycle_next", "<ctrl>+<shift>+<]>")
        )
        hotkey_layout.addRow("Cycle Forward:", self.cycle_forward_edit)

        # Cycle backward hotkey
        self.cycle_backward_edit = QLineEdit()
        self.cycle_backward_edit.setPlaceholderText("ctrl+shift+[ (brackets auto-added)")
        self.cycle_backward_edit.setText(
            self.settings_manager.get("hotkeys.cycle_prev", "<ctrl>+<shift>+<[>")
        )
        hotkey_layout.addRow("Cycle Backward:", self.cycle_backward_edit)

        # Save hotkeys button (from registry)
        save_hotkeys_btn = toolbar_builder.create_button("save_hotkeys", self._save_hotkeys)
        if save_hotkeys_btn:
            hotkey_layout.addRow("", save_hotkeys_btn)

        layout.addWidget(hotkey_group)

        # Load initial group
        if self.cycling_groups:
            first_group = list(self.cycling_groups.keys())[0]
            self.group_combo.setCurrentText(first_group)
            self._load_group_members(first_group)

        return panel

    def _populate_character_list(self):
        """Populate character list from character manager"""
        self.character_list.clear()

        characters = self.character_manager.get_all_characters()
        for char in characters:
            item = QListWidgetItem(char.name)
            item.setData(Qt.ItemDataRole.UserRole, char.name)

            # Color based on online status
            if char.window_id:
                item.setForeground(QColor(0, 200, 0))  # Green for online
            else:
                item.setForeground(QColor(150, 150, 150))  # Gray for offline

            self.character_list.addItem(item)

        self.logger.info(f"Populated character list with {len(characters)} characters")

    def _refresh_group_combo(self):
        """Refresh group selector dropdown"""
        current = self.group_combo.currentText() if self.group_combo.count() > 0 else None

        self.group_combo.blockSignals(True)
        self.group_combo.clear()

        for group_name in sorted(self.cycling_groups.keys()):
            self.group_combo.addItem(group_name)

        # Restore selection
        if current and self.group_combo.findText(current) >= 0:
            self.group_combo.setCurrentText(current)

        self.group_combo.blockSignals(False)

    def _on_group_selected(self, group_name: str):
        """Handle group selection"""
        if group_name:
            self.current_group = group_name
            self._load_group_members(group_name)

    def _load_group_members(self, group_name: str):
        """Load members of selected group into the list"""
        self.group_member_list.clear()

        if group_name in self.cycling_groups:
            for char_name in self.cycling_groups[group_name]:
                item = QListWidgetItem(char_name)
                item.setData(Qt.ItemDataRole.UserRole, char_name)
                self.group_member_list.addItem(item)

    def _on_members_changed(self):
        """Handle changes to group members"""
        if self.current_group:
            members = self.group_member_list.get_members()
            self.cycling_groups[self.current_group] = members
            self._save_groups()
            self.group_changed.emit(self.current_group, members)
            self.logger.info(f"Updated group '{self.current_group}': {members}")

    def _create_new_group(self):
        """Create a new cycling group"""
        name, ok = QInputDialog.getText(
            self, "New Cycling Group",
            "Enter group name:",
            QLineEdit.EchoMode.Normal
        )

        if ok and name:
            if name in self.cycling_groups:
                QMessageBox.warning(self, "Exists", f"Group '{name}' already exists.")
                return

            self.cycling_groups[name] = []
            self._save_groups()
            self._refresh_group_combo()
            self.group_combo.setCurrentText(name)
            self.logger.info(f"Created new cycling group: {name}")

    def _delete_current_group(self):
        """Delete the current cycling group"""
        if not self.current_group:
            return

        if self.current_group == "Default":
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete the Default group.")
            return

        reply = QMessageBox.question(
            self, "Delete Group",
            f"Delete cycling group '{self.current_group}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.cycling_groups[self.current_group]
            self._save_groups()
            self._refresh_group_combo()
            self.logger.info(f"Deleted cycling group: {self.current_group}")

    def _remove_selected_member(self):
        """Remove selected member from group"""
        current = self.group_member_list.currentItem()
        if current:
            self.group_member_list.takeItem(self.group_member_list.row(current))
            self._on_members_changed()

    def _clear_group_members(self):
        """Clear all members from current group"""
        if self.group_member_list.count() == 0:
            return

        reply = QMessageBox.question(
            self, "Clear Group",
            "Remove all members from this group?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.group_member_list.clear()
            self._on_members_changed()

    def _load_active_windows(self):
        """Load all currently active EVE windows into the current group"""
        if not self.main_tab or not hasattr(self.main_tab, 'window_manager'):
            QMessageBox.warning(
                self, "Error",
                "Cannot access active windows. Please try again."
            )
            return

        # Get active character names
        active_chars = []
        for frame in self.main_tab.window_manager.preview_frames.values():
            if frame.character_name not in active_chars:
                active_chars.append(frame.character_name)

        if not active_chars:
            QMessageBox.information(
                self, "No Active Windows",
                "No active EVE windows detected."
            )
            return

        # Clear and add all active characters
        self.group_member_list.clear()

        for char_name in active_chars:
            item = QListWidgetItem(char_name)
            item.setData(Qt.ItemDataRole.UserRole, char_name)
            self.group_member_list.addItem(item)

        self._on_members_changed()

        self.logger.info(f"Loaded {len(active_chars)} active windows into group")
        QMessageBox.information(
            self, "Loaded",
            f"Loaded {len(active_chars)} active EVE windows.\n\n"
            f"Use Move Up/Down to reorder them."
        )

    def _move_member_up(self):
        """Move selected member up in the list"""
        current_row = self.group_member_list.currentRow()
        if current_row > 0:
            item = self.group_member_list.takeItem(current_row)
            self.group_member_list.insertItem(current_row - 1, item)
            self.group_member_list.setCurrentRow(current_row - 1)
            self._on_members_changed()

    def _move_member_down(self):
        """Move selected member down in the list"""
        current_row = self.group_member_list.currentRow()
        if current_row < self.group_member_list.count() - 1:
            item = self.group_member_list.takeItem(current_row)
            self.group_member_list.insertItem(current_row + 1, item)
            self.group_member_list.setCurrentRow(current_row + 1)
            self._on_members_changed()

    def _format_hotkey(self, hotkey: str) -> str:
        """Format hotkey with angle brackets around each key component

        e.g. 'ctrl+shift+]' -> '<ctrl>+<shift>+<]>'
        """
        hotkey = hotkey.strip()
        if not hotkey:
            return hotkey

        # Split by + and wrap each part in brackets if not already
        parts = hotkey.split('+')
        formatted_parts = []

        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Remove existing brackets if present
            if part.startswith('<') and part.endswith('>'):
                part = part[1:-1]
            # Add brackets
            formatted_parts.append(f"<{part}>")

        return '+'.join(formatted_parts)

    def _save_hotkeys(self):
        """Save hotkey settings with auto-formatted brackets"""
        # Auto-format with brackets
        forward = self._format_hotkey(self.cycle_forward_edit.text())
        backward = self._format_hotkey(self.cycle_backward_edit.text())

        # Update display with formatted version
        self.cycle_forward_edit.setText(forward)
        self.cycle_backward_edit.setText(backward)

        self.settings_manager.set("hotkeys.cycle_next", forward, auto_save=False)
        self.settings_manager.set("hotkeys.cycle_prev", backward, auto_save=True)

        QMessageBox.information(
            self, "Saved",
            f"Hotkey settings saved.\n\n"
            f"Forward: {forward}\n"
            f"Backward: {backward}\n\n"
            f"Restart the app for hotkeys to take effect."
        )
        self.logger.info(f"Saved hotkeys: forward={forward}, backward={backward}")

    def get_cycling_group(self, name: str) -> List[str]:
        """Get members of a cycling group"""
        return self.cycling_groups.get(name, [])

    def get_all_groups(self) -> Dict[str, List[str]]:
        """Get all cycling groups"""
        return self.cycling_groups.copy()

    def refresh_characters(self):
        """Refresh character list (called when characters change)"""
        self._populate_character_list()
