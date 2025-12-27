"""
Layouts Tab - Group-based window arrangement with drag-and-drop tiles
Supports grid patterns, stacking, and custom positioning
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox, QLabel, QComboBox, QSpinBox, QDialog,
    QLineEdit, QTextEdit, QMessageBox, QSplitter, QGraphicsView,
    QGraphicsScene, QGraphicsRectItem, QDialogButtonBox, QFormLayout,
    QCheckBox, QFrame, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QMimeData
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QDrag, QPainter
import logging
import subprocess
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from eve_overview_pro.core.layout_manager import GridPattern


@dataclass
class ScreenGeometry:
    """Screen/monitor geometry"""
    x: int
    y: int
    width: int
    height: int
    is_primary: bool = False


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
        "Custom"
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
        "Custom": GridPattern.CUSTOM
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
        self.tiles: Dict[str, DraggableTile] = {}
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
        for char_name, tile in self.tiles.items():
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

    def get_arrangement(self) -> Dict[str, Tuple[int, int]]:
        """Get current arrangement as dict"""
        return {
            name: (tile.grid_row, tile.grid_col)
            for name, tile in self.tiles.items()
        }

    def auto_arrange_grid(self, pattern: str):
        """Auto-arrange tiles based on pattern"""
        chars = list(self.tiles.keys())
        if not chars:
            return

        # Calculate positions based on pattern
        if pattern == "2x2 Grid":
            positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        elif pattern == "3x1 Row":
            positions = [(0, 0), (0, 1), (0, 2)]
        elif pattern == "1x3 Column":
            positions = [(0, 0), (1, 0), (2, 0)]
        elif pattern == "4x1 Row":
            positions = [(0, 0), (0, 1), (0, 2), (0, 3)]
        elif pattern == "2x3 Grid":
            positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        elif pattern == "3x2 Grid":
            positions = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        elif pattern == "Main + Sides":
            # First window is main (full height), rest are stacked on right
            positions = [(0, 0)]
            for i in range(1, len(chars)):
                positions.append((i - 1, 1))
        elif pattern == "Cascade":
            positions = [(i, i) for i in range(len(chars))]
        elif pattern == "Stacked (All Same Position)":
            positions = [(0, 0)] * len(chars)
            for tile in self.tiles.values():
                tile.set_stacked(True)
        else:
            # Default: sequential grid fill
            positions = []
            for i in range(len(chars)):
                row = i // self.grid_cols
                col = i % self.grid_cols
                positions.append((row, col))

        # Apply positions
        for idx, char_name in enumerate(chars):
            if idx < len(positions):
                row, col = positions[idx]
                tile = self.tiles[char_name]

                # Remove from old position
                self.grid_layout.removeWidget(tile)

                # Add to new position
                tile.set_position(row, col)
                self.grid_layout.addWidget(tile, row, col)

        self.arrangement_changed.emit(self.get_arrangement())


class GridApplier:
    """Applies grid patterns to actual windows using xdotool"""

    def __init__(self, layout_manager):
        self.layout_manager = layout_manager
        self.logger = logging.getLogger(__name__)

    def get_screen_geometry(self, monitor: int = 0) -> Optional[ScreenGeometry]:
        """Get screen geometry using xrandr"""
        try:
            result = subprocess.run(
                ['xrandr', '--query'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                self.logger.error("xrandr failed")
                return None

            monitors = []
            for line in result.stdout.split('\n'):
                if ' connected' in line:
                    match = re.search(r'(\d+)x(\d+)\+(\d+)\+(\d+)', line)
                    if match:
                        w, h, x, y = map(int, match.groups())
                        is_primary = 'primary' in line
                        monitors.append(ScreenGeometry(x, y, w, h, is_primary))

            if monitor < len(monitors):
                return monitors[monitor]
            elif monitors:
                return monitors[0]

            self.logger.warning("Could not parse xrandr output, using default geometry")
            return ScreenGeometry(0, 0, 1920, 1080, True)

        except Exception as e:
            self.logger.error(f"Failed to get screen geometry: {e}")
            return ScreenGeometry(0, 0, 1920, 1080, True)

    def apply_arrangement(self, arrangement: Dict[str, Tuple[int, int]],
                         window_map: Dict[str, str],
                         screen: ScreenGeometry,
                         grid_rows: int, grid_cols: int,
                         spacing: int = 10,
                         stacked: bool = False) -> bool:
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
                for char_name, window_id in window_map.items():
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

        except Exception as e:
            self.logger.error(f"Failed to apply arrangement: {e}")
            return False

    def _move_window(self, window_id: str, x: int, y: int, w: int, h: int):
        """Move and resize a single window"""
        subprocess.run(
            ['xdotool', 'windowmove', '--sync', window_id, str(x), str(y)],
            capture_output=True, timeout=2
        )
        subprocess.run(
            ['xdotool', 'windowsize', '--sync', window_id, str(w), str(h)],
            capture_output=True, timeout=2
        )


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
        self.cycling_groups: Dict[str, List[str]] = {}

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
        """Create group selector and pattern options"""
        section = QGroupBox("Layout Configuration")
        layout = QHBoxLayout()

        # Group selector
        group_layout = QVBoxLayout()
        group_layout.addWidget(QLabel("Select Group:"))

        self.group_combo = QComboBox()
        self._refresh_groups()
        self.group_combo.currentTextChanged.connect(self._on_group_selected)
        group_layout.addWidget(self.group_combo)

        self.refresh_groups_btn = QPushButton("Refresh Groups")
        self.refresh_groups_btn.clicked.connect(self._refresh_groups)
        group_layout.addWidget(self.refresh_groups_btn)

        layout.addLayout(group_layout)

        # Pattern selector
        pattern_layout = QVBoxLayout()
        pattern_layout.addWidget(QLabel("Grid Pattern:"))

        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(get_all_patterns())
        self.pattern_combo.currentTextChanged.connect(self._on_pattern_changed)
        pattern_layout.addWidget(self.pattern_combo)

        self.auto_arrange_btn = QPushButton("Auto-Arrange")
        self.auto_arrange_btn.clicked.connect(self._auto_arrange)
        pattern_layout.addWidget(self.auto_arrange_btn)

        layout.addLayout(pattern_layout)

        # Grid size options
        size_layout = QVBoxLayout()
        size_layout.addWidget(QLabel("Grid Size:"))

        size_row = QHBoxLayout()
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 6)
        self.rows_spin.setValue(3)
        self.rows_spin.setPrefix("Rows: ")
        self.rows_spin.valueChanged.connect(self._update_grid_size)
        size_row.addWidget(self.rows_spin)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 6)
        self.cols_spin.setValue(4)
        self.cols_spin.setPrefix("Cols: ")
        self.cols_spin.valueChanged.connect(self._update_grid_size)
        size_row.addWidget(self.cols_spin)

        size_layout.addLayout(size_row)

        # Spacing
        spacing_row = QHBoxLayout()
        spacing_row.addWidget(QLabel("Spacing:"))
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 50)
        self.spacing_spin.setValue(10)
        self.spacing_spin.setSuffix(" px")
        spacing_row.addWidget(self.spacing_spin)
        size_layout.addLayout(spacing_row)

        layout.addLayout(size_layout)

        # Monitor selector
        monitor_layout = QVBoxLayout()
        monitor_layout.addWidget(QLabel("Monitor:"))

        self.monitor_spin = QSpinBox()
        self.monitor_spin.setRange(0, 3)
        self.monitor_spin.setValue(0)
        monitor_layout.addWidget(self.monitor_spin)

        # Stacking checkbox
        self.stack_checkbox = QCheckBox("Stack Windows")
        self.stack_checkbox.setToolTip("Place all windows at the same position (overlapping)")
        monitor_layout.addWidget(self.stack_checkbox)

        layout.addLayout(monitor_layout)

        section.setLayout(layout)
        return section

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

        self.logger.info(f"Loaded {len(self.cycling_groups)} groups")

    def _on_group_selected(self):
        """Handle group selection"""
        group_name = self.group_combo.currentText()

        # Clear current tiles
        self.arrangement_grid.clear_tiles()

        if group_name == "All Active Windows":
            # Get all active windows from main_tab
            if hasattr(self.main_tab, 'window_manager'):
                for window_id, frame in self.main_tab.window_manager.preview_frames.items():
                    self.arrangement_grid.add_character(frame.character_name)

            self.info_label.setText(f"Showing all active windows")
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
        if not hasattr(self.main_tab, 'window_manager'):
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
                self, "No Matching Windows",
                "None of the characters in the arrangement have active windows.\n\n"
                "Make sure the EVE clients are running and detected."
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
            stacked=self.stack_checkbox.isChecked()
        )

        if success:
            QMessageBox.information(
                self, "Success",
                f"Applied layout to {len(window_map)} windows!"
            )
            self.layout_applied.emit(self.pattern_combo.currentText())
        else:
            QMessageBox.warning(
                self, "Error",
                "Failed to apply layout. Check logs for details."
            )

    def refresh_groups_from_settings(self):
        """Called when groups change in hotkeys tab"""
        self._refresh_groups()
        self._on_group_selected()
