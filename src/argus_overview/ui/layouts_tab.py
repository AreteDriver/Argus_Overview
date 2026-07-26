"""
Layouts Tab - Group-based window arrangement with drag-and-drop tiles
Supports grid patterns, stacking, and custom positioning
"""

import logging
import re
import subprocess

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from argus_overview.core.layout_manager import GridPattern
from argus_overview.ui.layout_widgets import MonitorCardStrip, PatternThumbStrip
from argus_overview.ui.main_tab import get_pattern_positions
from argus_overview.utils.screen import ScreenGeometry, get_all_monitors, get_screen_geometry


def get_all_patterns():
    """Get all available grid patterns as display strings"""
    return [
        "2x2 Grid",
        "3x1 Row",
        "1x3 Column",
        "4x1 Row",
        "2x3 Grid",
        "3x2 Grid",
        "Main + Sides",
        "Cascade",
        "Stacked (All Same Position)",
        "Custom",
    ]


def pattern_display_to_enum(display_name: str) -> GridPattern:
    """Convert display name to GridPattern enum"""
    mapping = {
        "2x2 Grid": GridPattern.GRID_2X2,
        "3x1 Row": GridPattern.GRID_3X1,
        "1x3 Column": GridPattern.GRID_1X3,
        "4x1 Row": GridPattern.GRID_4X1,
        "Main + Sides": GridPattern.MAIN_PLUS_SIDES,
        "Cascade": GridPattern.CASCADE,
        "Custom": GridPattern.CUSTOM,
    }
    return mapping.get(display_name, GridPattern.CUSTOM)


class DraggableTile(QFrame):
    """Draggable tile representing a character window"""

    tile_moved = Signal(str, int, int)  # char_name, grid_row, grid_col

    def __init__(self, char_name: str, color: QColor, parent=None):
        super().__init__(parent)
        self.char_name = char_name
        self.color = color
        self.grid_row = 0
        self.grid_col = 0
        self.is_stacked = False

        self.setFixedSize(120, 80)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self._update_style()

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Character name label
        self.name_label = QLabel(char_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(self.name_label)

        # Position label
        self.pos_label = QLabel("(0, 0)")
        self.pos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pos_label.setStyleSheet("color: #888; font-size: 8pt;")
        layout.addWidget(self.pos_label)

        self.setLayout(layout)

    def _update_style(self):
        """Update tile appearance"""
        bg_color = self.color.name()
        border_color = self.color.darker(150).name()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 5px;
            }}
        """)

    def set_position(self, row: int, col: int):
        """Set grid position"""
        self.grid_row = row
        self.grid_col = col
        self.pos_label.setText(f"({row}, {col})")

    def set_stacked(self, stacked: bool):
        """Mark tile as stacked"""
        self.is_stacked = stacked
        if stacked:
            self.pos_label.setText("(Stacked)")


class ArrangementGrid(QWidget):
    """Grid for arranging character tiles"""

    arrangement_changed = Signal(dict)  # {char_name: (row, col)}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.tiles: dict[str, DraggableTile] = {}
        self.grid_rows = 3
        self.grid_cols = 4

        self._setup_ui()

    def _setup_ui(self):
        """Setup grid UI"""
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)

        # Create placeholder cells
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                cell = QFrame()
                cell.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
                cell.setMinimumSize(130, 90)
                cell.setAcceptDrops(True)
                cell.setStyleSheet("""
                    QFrame {
                        background-color: #2a2a2a;
                        border: 1px dashed #555;
                        border-radius: 3px;
                    }
                """)
                self.grid_layout.addWidget(cell, row, col)

        self.setLayout(self.grid_layout)

    def set_grid_size(self, rows: int, cols: int):
        """Resize the grid"""
        self.grid_rows = rows
        self.grid_cols = cols

        # Clear and rebuild
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Recreate cells
        for row in range(rows):
            for col in range(cols):
                cell = QFrame()
                cell.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
                cell.setMinimumSize(130, 90)
                cell.setStyleSheet("""
                    QFrame {
                        background-color: #2a2a2a;
                        border: 1px dashed #555;
                        border-radius: 3px;
                    }
                """)
                self.grid_layout.addWidget(cell, row, col)

        # Re-add tiles
        for _char_name, tile in self.tiles.items():
            row = min(tile.grid_row, rows - 1)
            col = min(tile.grid_col, cols - 1)
            tile.set_position(row, col)
            self.grid_layout.addWidget(tile, row, col)

    def clear_tiles(self):
        """Remove all tiles"""
        for tile in list(self.tiles.values()):
            self.grid_layout.removeWidget(tile)
            tile.deleteLater()
        self.tiles.clear()

    def add_character(self, char_name: str, row: int = 0, col: int = 0):
        """Add a character tile to the grid"""
        if char_name in self.tiles:
            return

        # Generate color based on character name hash
        colors = [
            QColor(255, 100, 100, 200),
            QColor(100, 255, 100, 200),
            QColor(100, 100, 255, 200),
            QColor(255, 255, 100, 200),
            QColor(255, 100, 255, 200),
            QColor(100, 255, 255, 200),
            QColor(255, 165, 0, 200),
            QColor(165, 100, 255, 200),
        ]
        color = colors[hash(char_name) % len(colors)]

        tile = DraggableTile(char_name, color)
        tile.set_position(row, col)

        self.tiles[char_name] = tile
        self.grid_layout.addWidget(tile, row, col)

    def get_arrangement(self) -> dict[str, tuple[int, int]]:
        """Get current arrangement as dict"""
        return {name: (tile.grid_row, tile.grid_col) for name, tile in self.tiles.items()}

    def auto_arrange_grid(self, pattern: str):
        """Auto-arrange tiles based on pattern"""
        chars = list(self.tiles.keys())
        if not chars:
            return

        # Get positions from shared function
        grid_cols = getattr(self, "grid_cols", 4)
        positions = get_pattern_positions(pattern, len(chars), grid_cols)

        # Handle stacked pattern special case
        if pattern == "Stacked (All Same Position)":
            for tile in self.tiles.values():
                tile.set_stacked(True)

        # Apply positions to tiles
        for idx, char_name in enumerate(chars):
            if idx < len(positions):
                row, col = positions[idx]
                tile = self.tiles[char_name]
                self.grid_layout.removeWidget(tile)
                tile.set_position(row, col)
                self.grid_layout.addWidget(tile, row, col)

        self.arrangement_changed.emit(self.get_arrangement())


class GridApplier:
    """Applies grid patterns to actual windows using xdotool"""

    def __init__(self, layout_manager):
        self.layout_manager = layout_manager
        self.logger = logging.getLogger(__name__)

    def get_screen_geometry(self, monitor: int = 0) -> ScreenGeometry:
        """Get screen geometry for a monitor (delegates to shared utility)"""
        return get_screen_geometry(monitor)

    def apply_arrangement(
        self,
        arrangement: dict[str, tuple[int, int]],
        window_map: dict[str, str],
        screen: ScreenGeometry,
        grid_rows: int,
        grid_cols: int,
        spacing: int = 10,
        stacked: bool = False,
    ) -> bool:
        """
        Apply arrangement to windows

        Args:
            arrangement: {char_name: (row, col)}
            window_map: {char_name: window_id}
            screen: Screen geometry
            grid_rows, grid_cols: Grid dimensions
            spacing: Spacing between windows
            stacked: If True, all windows at same position
        """
        try:
            if stacked:
                # All windows same size and position
                for _char_name, window_id in window_map.items():
                    x = screen.x + spacing
                    y = screen.y + spacing
                    w = screen.width - spacing * 2
                    h = screen.height - spacing * 2

                    self._move_window(window_id, x, y, w, h)
            else:
                # Grid-based arrangement
                cell_width = (screen.width - spacing * (grid_cols + 1)) // grid_cols
                cell_height = (screen.height - spacing * (grid_rows + 1)) // grid_rows

                for char_name, (row, col) in arrangement.items():
                    if char_name not in window_map:
                        continue

                    window_id = window_map[char_name]

                    x = screen.x + spacing + col * (cell_width + spacing)
                    y = screen.y + spacing + row * (cell_height + spacing)

                    self._move_window(window_id, x, y, cell_width, cell_height)

            self.logger.info(f"Applied arrangement to {len(window_map)} windows")
            return True

        except (OSError, subprocess.SubprocessError, KeyError, ValueError) as e:
            self.logger.error(f"Failed to apply arrangement: {e}")
            return False

    def _move_window(self, window_id: str, x: int, y: int, w: int, h: int):
        """Move and resize a single window, with fallback for Wine/Proton windows"""
        import time

        # Validate window ID format (X11: 0x followed by hex digits)
        if not window_id or not re.match(r"^0x[0-9a-fA-F]+$", window_id):
            self.logger.warning(f"Invalid window ID format: {window_id}")
            return

        # Try with --sync first, fallback to no-sync for Wine/Proton windows
        try:
            subprocess.run(
                ["xdotool", "windowmove", "--sync", window_id, str(x), str(y)],
                capture_output=True,
                timeout=2,
            )
        except subprocess.TimeoutExpired:
            # Wine windows don't respond to sync, retry without it
            subprocess.run(
                ["xdotool", "windowmove", window_id, str(x), str(y)],
                capture_output=True,
                timeout=2,
            )
            time.sleep(0.1)  # Brief pause for window to settle

        try:
            subprocess.run(
                ["xdotool", "windowsize", "--sync", window_id, str(w), str(h)],
                capture_output=True,
                timeout=2,
            )
        except subprocess.TimeoutExpired:
            subprocess.run(
                ["xdotool", "windowsize", window_id, str(w), str(h)],
                capture_output=True,
                timeout=2,
            )
            time.sleep(0.1)


class LayoutsTab(QWidget):
    """Main Layouts Tab with group-based arrangement"""

    layout_applied = Signal(str)

    def __init__(self, layout_manager, main_tab, settings_manager=None, character_manager=None):
        super().__init__()
        self.layout_manager = layout_manager
        self.main_tab = main_tab
        self.settings_manager = settings_manager
        self.character_manager = character_manager
        self.logger = logging.getLogger(__name__)

        self.grid_applier = GridApplier(layout_manager)
        self.cycling_groups: dict[str, list[str]] = {}

        self._load_groups()
        self._setup_ui()

    def _load_groups(self):
        """Load cycling groups from settings"""
        if self.settings_manager:
            groups = self.settings_manager.get("cycling_groups", {})
            if isinstance(groups, dict):
                self.cycling_groups = groups

        # Ensure default group exists
        if "Default" not in self.cycling_groups:
            self.cycling_groups["Default"] = []

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Top section: Group selector and pattern
        top_section = self._create_top_section()
        layout.addWidget(top_section)

        # Middle section: Arrangement grid
        grid_section = self._create_grid_section()
        layout.addWidget(grid_section, stretch=1)

        # Bottom section: Apply buttons
        bottom_section = self._create_bottom_section()
        layout.addWidget(bottom_section)

        self.setLayout(layout)

        # Initial update
        self._on_group_selected()

    def _create_top_section(self) -> QWidget:
        """Create the redesigned top section with thumbnails + monitor cards.

        Legacy widgets (group_combo, pattern_combo, monitor_spin, etc.) are
        constructed but NOT added to any visible layout — they continue to
        hold the canonical state. The new widgets sync into them. This
        keeps the existing apply path and ~58 test references working
        without a destabilizing rename.
        """
        # ---- Legacy state holders (invisible) -------------------------
        # The user no longer interacts with these directly, but the apply
        # path and ~58 existing tests still read .currentText() / .value().
        self.group_combo = QComboBox()
        self._refresh_groups()
        self.group_combo.currentTextChanged.connect(self._on_group_selected)

        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(get_all_patterns())
        self.pattern_combo.currentTextChanged.connect(self._on_pattern_changed)

        self.monitor_spin = QSpinBox()
        self.monitor_spin.setRange(0, 3)
        self.monitor_spin.setValue(0)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 6)
        self.rows_spin.setValue(3)
        self.rows_spin.setPrefix("Rows: ")
        self.rows_spin.valueChanged.connect(self._update_grid_size)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 6)
        self.cols_spin.setValue(4)
        self.cols_spin.setPrefix("Cols: ")
        self.cols_spin.valueChanged.connect(self._update_grid_size)

        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 50)
        self.spacing_spin.setValue(10)
        self.spacing_spin.setSuffix(" px")

        self.stack_checkbox = QCheckBox("Stack Windows")

        self.refresh_groups_btn = QPushButton("Refresh Groups")
        self.refresh_groups_btn.clicked.connect(self._refresh_groups)

        self.auto_arrange_btn = QPushButton("Auto-Arrange")
        self.auto_arrange_btn.clicked.connect(self._auto_arrange)

        # ---- Visible top section --------------------------------------
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # 1. Characters — radio toggle "All / Group: ..."
        outer.addWidget(self._build_characters_section())
        # 2. Pattern — thumbnail strip + spacing slider
        outer.addWidget(self._build_pattern_section())
        # 3. Monitor — card strip
        outer.addWidget(self._build_monitor_section())
        # 4. Grid size — kept compact for Custom pattern users
        outer.addWidget(self._build_grid_size_section())

        return container

    def _build_characters_section(self) -> QGroupBox:
        section = QGroupBox("1. Characters")
        layout = QVBoxLayout()

        radio_row = QHBoxLayout()
        self._all_radio = QRadioButton("All Active Windows")
        self._all_radio.setChecked(True)
        self._group_radio = QRadioButton("Group:")
        # Parent left as None — Qt re-parents the buttons via addButton anyway,
        # and bypassed-init test sites can't safely pass `self` as parent.
        self._group_btn_group = QButtonGroup()
        self._group_btn_group.addButton(self._all_radio)
        self._group_btn_group.addButton(self._group_radio)

        # Inline group selector — only enabled when group_radio is on.
        self._group_inline_combo = QComboBox()
        self._group_inline_combo.addItem("Default")
        self._group_inline_combo.setEnabled(False)
        # Keep the inline combo in sync with the legacy group_combo.
        self._group_inline_combo.currentTextChanged.connect(self._on_inline_group_changed)
        self._all_radio.toggled.connect(self._on_chars_radio_toggled)
        self._group_radio.toggled.connect(self._on_chars_radio_toggled)

        radio_row.addWidget(self._all_radio)
        radio_row.addWidget(self._group_radio)
        radio_row.addWidget(self._group_inline_combo, stretch=1)
        radio_row.addWidget(self.refresh_groups_btn)
        layout.addLayout(radio_row)

        # Sync inline combo with legacy combo's current items.
        self._sync_inline_group_combo()

        section.setLayout(layout)
        return section

    def _build_pattern_section(self) -> QGroupBox:
        section = QGroupBox("2. Pattern")
        layout = QVBoxLayout()

        # PR2: progressive disclosure — 6 core patterns visible immediately,
        # remaining 4 behind a toggle to reduce decision fatigue.
        core_patterns = [
            "2x2 Grid",
            "3x1 Row",
            "1x3 Column",
            "4x1 Row",
            "Main + Sides",
            "Custom",
        ]
        more_patterns = [
            "2x3 Grid",
            "3x2 Grid",
            "Cascade",
            "Stacked (All Same Position)",
        ]

        self._pattern_strip = PatternThumbStrip(patterns=core_patterns)
        self._pattern_strip.pattern_selected.connect(self._on_pattern_strip_selected)
        initial_pattern = self.pattern_combo.currentText() or "2x2 Grid"
        if initial_pattern in core_patterns:
            self._pattern_strip.set_selected(initial_pattern)
        layout.addWidget(self._pattern_strip)

        # More layouts toggle
        self._more_patterns_widget = QWidget()
        more_layout = QVBoxLayout()
        more_layout.setContentsMargins(0, 0, 0, 0)
        self._more_patterns_widget.setLayout(more_layout)
        self._more_pattern_strip = PatternThumbStrip(patterns=more_patterns)
        self._more_pattern_strip.pattern_selected.connect(self._on_pattern_strip_selected)
        if initial_pattern in more_patterns:
            self._more_pattern_strip.set_selected(initial_pattern)
            self._more_patterns_widget.setVisible(True)
        else:
            self._more_patterns_widget.setVisible(False)
        more_layout.addWidget(self._more_pattern_strip)
        layout.addWidget(self._more_patterns_widget)

        self._more_toggle_btn = QPushButton("More layouts ▼")
        self._more_toggle_btn.setCheckable(True)
        self._more_toggle_btn.setChecked(self._more_patterns_widget.isVisible())
        self._more_toggle_btn.clicked.connect(self._toggle_more_patterns)
        layout.addWidget(self._more_toggle_btn)

        # Spacing belongs with the pattern — it tunes the rendered output,
        # not a separate concept. Move from the old "Grid Size" cluster.
        spacing_row = QHBoxLayout()
        spacing_row.addWidget(QLabel("Spacing:"))
        spacing_row.addWidget(self.spacing_spin)
        spacing_row.addStretch()
        spacing_row.addWidget(self.auto_arrange_btn)
        layout.addLayout(spacing_row)

        section.setLayout(layout)
        return section

    def _toggle_more_patterns(self) -> None:
        """Show or hide the additional pattern strip."""
        show = self._more_toggle_btn.isChecked()
        self._more_patterns_widget.setVisible(show)
        self._more_toggle_btn.setText("More layouts ▲" if show else "More layouts ▼")

    def _build_monitor_section(self) -> QGroupBox:
        section = QGroupBox("3. Monitor")
        layout = QVBoxLayout()

        self._monitor_strip = MonitorCardStrip()
        self._monitor_strip.monitor_selected.connect(self._on_monitor_strip_selected)
        layout.addWidget(self._monitor_strip)

        # Populate from real screen geometry; fall back to a single-card
        # placeholder when display detection fails (e.g., tests, headless).
        try:
            monitors = get_all_monitors() or []
        except (OSError, RuntimeError, AttributeError):
            monitors = []
        cards = [
            (i, mon.width, mon.height, getattr(mon, "is_primary", i == 0))
            for i, mon in enumerate(monitors)
        ]
        if not cards:
            cards = [(0, 1920, 1080, True)]
        self._monitor_strip.set_monitors(cards)
        self._monitor_strip.set_selected(cards[0][0])
        # Resize the legacy spin range to match real monitor count.
        self.monitor_spin.setRange(0, max(0, len(cards) - 1))

        section.setLayout(layout)
        return section

    def _build_grid_size_section(self) -> QGroupBox:
        section = QGroupBox("4. Grid Size")
        layout = QHBoxLayout()
        layout.addWidget(self.rows_spin)
        layout.addWidget(self.cols_spin)
        layout.addStretch()
        self.stack_checkbox.setToolTip("Place all windows at the same position (overlapping).")
        layout.addWidget(self.stack_checkbox)
        section.setLayout(layout)
        return section

    # ---- New-widget → legacy-state sync -----------------------------------
    def _on_chars_radio_toggled(self) -> None:
        """Mirror the radio choice into the legacy group_combo."""
        if self._all_radio.isChecked():
            self._group_inline_combo.setEnabled(False)
            # Trigger the legacy "All Active Windows" code path.
            idx = self.group_combo.findText("All Active Windows")
            if idx >= 0:
                self.group_combo.setCurrentIndex(idx)
        else:
            self._group_inline_combo.setEnabled(True)
            # Switch to the currently-selected inline group.
            self._on_inline_group_changed(self._group_inline_combo.currentText())

    def _on_inline_group_changed(self, group_name: str) -> None:
        """Mirror the inline group combo into the legacy combo."""
        if not group_name:
            return
        idx = self.group_combo.findText(group_name)
        if idx >= 0:
            self.group_combo.setCurrentIndex(idx)

    def _on_pattern_strip_selected(self, pattern_name: str) -> None:
        """Mirror the thumbnail strip choice into the legacy pattern combo.

        PR2: ensures only one pattern is highlighted across both the core and
        the expanded "more" strips.
        """
        idx = self.pattern_combo.findText(pattern_name)
        if idx >= 0:
            self.pattern_combo.setCurrentIndex(idx)
        # Deselect the other strip so exactly one pattern is active
        source = self.sender()
        if source is self._pattern_strip and hasattr(self, "_more_pattern_strip"):
            self._more_pattern_strip.set_selected(None)
        elif source is self._more_pattern_strip and hasattr(self, "_pattern_strip"):
            self._pattern_strip.set_selected(None)

    def _on_monitor_strip_selected(self, index: int) -> None:
        """Mirror the monitor card choice into the legacy spinbox."""
        self.monitor_spin.setValue(index)

    def _sync_inline_group_combo(self) -> None:
        """Refresh the inline group combo from cycling_groups.

        No-op on bypassed-init test sites that don't have the inline combo
        or cycling_groups dict.
        """
        if not hasattr(self, "_group_inline_combo"):
            return
        groups = getattr(self, "cycling_groups", None)
        if groups is None:
            return
        current = self._group_inline_combo.currentText()
        self._group_inline_combo.blockSignals(True)
        self._group_inline_combo.clear()
        for name in sorted(groups.keys()):
            self._group_inline_combo.addItem(name)
        if current:
            i = self._group_inline_combo.findText(current)
            if i >= 0:
                self._group_inline_combo.setCurrentIndex(i)
        self._group_inline_combo.blockSignals(False)

    def _create_grid_section(self) -> QWidget:
        """Create arrangement grid"""
        section = QGroupBox("Window Arrangement")
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Characters from the selected group are shown below. "
            "Click 'Auto-Arrange' to position them based on the selected pattern, "
            "or drag tiles to customize positions."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        layout.addWidget(instructions)

        # Scroll area for grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)

        self.arrangement_grid = ArrangementGrid()
        scroll.setWidget(self.arrangement_grid)

        layout.addWidget(scroll)

        section.setLayout(layout)
        return section

    def _create_bottom_section(self) -> QWidget:
        """Create apply buttons section"""
        section = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Info label
        self.info_label = QLabel("Select a group to begin")
        self.info_label.setStyleSheet("color: #888;")
        layout.addWidget(self.info_label)

        layout.addStretch()

        # Apply to active windows button
        self.apply_active_btn = QPushButton("Apply to Active Windows")
        self.apply_active_btn.setToolTip("Apply layout to currently detected EVE windows")
        self.apply_active_btn.clicked.connect(self._apply_to_active_windows)
        self.apply_active_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff8c00;
                color: black;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #ffa500;
            }
        """)
        layout.addWidget(self.apply_active_btn)

        section.setLayout(layout)
        return section

    def _refresh_groups(self):
        """Refresh group list from settings"""
        self._load_groups()

        current = self.group_combo.currentText() if self.group_combo.count() > 0 else None

        self.group_combo.blockSignals(True)
        self.group_combo.clear()

        # Add "All Active Windows" option
        self.group_combo.addItem("All Active Windows")

        for group_name in sorted(self.cycling_groups.keys()):
            self.group_combo.addItem(group_name)

        # Restore selection
        if current:
            idx = self.group_combo.findText(current)
            if idx >= 0:
                self.group_combo.setCurrentIndex(idx)

        self.group_combo.blockSignals(False)

        # Keep the new inline group combo in sync.
        self._sync_inline_group_combo()

        self.logger.info(f"Loaded {len(self.cycling_groups)} groups")

    def _on_group_selected(self):
        """Handle group selection"""
        group_name = self.group_combo.currentText()

        # Clear current tiles
        self.arrangement_grid.clear_tiles()

        if group_name == "All Active Windows":
            # Get all active windows from main_tab
            if hasattr(self.main_tab, "window_manager"):
                for (
                    _window_id,
                    frame,
                ) in self.main_tab.window_manager.preview_frames.items():
                    self.arrangement_grid.add_character(frame.character_name)

            self.info_label.setText("Showing all active windows")
        else:
            # Get characters from group
            members = self.cycling_groups.get(group_name, [])
            for idx, char_name in enumerate(members):
                row = idx // self.arrangement_grid.grid_cols
                col = idx % self.arrangement_grid.grid_cols
                self.arrangement_grid.add_character(char_name, row, col)

            self.info_label.setText(f"Group '{group_name}': {len(members)} characters")

        # Auto-arrange if pattern is selected
        if self.pattern_combo.currentText() != "Custom":
            self._auto_arrange()

    def _on_pattern_changed(self):
        """Handle pattern change"""
        pattern = self.pattern_combo.currentText()

        # Update stacking checkbox
        if pattern == "Stacked (All Same Position)":
            self.stack_checkbox.setChecked(True)
        else:
            self.stack_checkbox.setChecked(False)

        # Auto-arrange with new pattern
        self._auto_arrange()

    def _update_grid_size(self):
        """Update grid dimensions"""
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        self.arrangement_grid.set_grid_size(rows, cols)

    def _auto_arrange(self):
        """Auto-arrange tiles based on pattern"""
        pattern = self.pattern_combo.currentText()
        self.arrangement_grid.auto_arrange_grid(pattern)

    def _apply_to_active_windows(self):
        """Apply layout to active windows"""
        if not hasattr(self.main_tab, "window_manager"):
            QMessageBox.warning(self, "Error", "Main tab not initialized")
            return

        # Get arrangement
        arrangement = self.arrangement_grid.get_arrangement()
        if not arrangement:
            QMessageBox.warning(self, "No Windows", "No windows in arrangement")
            return

        # Build window map (char_name -> window_id)
        window_map = {}
        wm = self.main_tab.window_manager

        for window_id, frame in wm.preview_frames.items():
            if frame.character_name in arrangement:
                window_map[frame.character_name] = window_id

        if not window_map:
            QMessageBox.warning(
                self,
                "No Matching Windows",
                "None of the characters in the arrangement have active windows.\n\n"
                "Make sure the EVE clients are running and detected.",
            )
            return

        # Get screen geometry
        monitor = self.monitor_spin.value()
        screen = self.grid_applier.get_screen_geometry(monitor)

        if not screen:
            QMessageBox.warning(self, "Error", "Could not get screen geometry")
            return

        # Apply arrangement
        success = self.grid_applier.apply_arrangement(
            arrangement=arrangement,
            window_map=window_map,
            screen=screen,
            grid_rows=self.rows_spin.value(),
            grid_cols=self.cols_spin.value(),
            spacing=self.spacing_spin.value(),
            stacked=self.stack_checkbox.isChecked(),
        )

        if success:
            QMessageBox.information(
                self, "Success", f"Applied layout to {len(window_map)} windows!"
            )
            self.layout_applied.emit(self.pattern_combo.currentText())
        else:
            QMessageBox.warning(self, "Error", "Failed to apply layout. Check logs for details.")

    def refresh_groups_from_settings(self):
        """Called when groups change in hotkeys tab"""
        self._refresh_groups()
        self._on_group_selected()
