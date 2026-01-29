"""
Main Tab - Window Preview Management System
Implements 30 FPS capture loop with window previews and interactions
v2.2: Added one-click import, hover effects, activity indicators, session timers
v2.3: Merged layouts functionality - group-based window arrangement
"""

import logging
import subprocess
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from PIL import Image
from PySide6.QtCore import (
    QPoint,
    QRect,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QBrush, QColor, QImage, QKeyEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from argus_overview.core.discovery import scan_eve_windows
from argus_overview.ui.action_registry import PrimaryHome
from argus_overview.ui.menu_builder import ContextMenuBuilder, ToolbarBuilder
from argus_overview.utils.screen import ScreenGeometry, get_screen_geometry


class FlowLayout(QLayout):
    """
    A layout that arranges widgets in a flow pattern, wrapping to new rows
    when the available width is exceeded. Perfect for thumbnail grids.
    """

    def __init__(self, parent=None, margin=10, spacing=10):
        super().__init__(parent)
        self._item_list = []
        self._margin = margin
        self._spacing = spacing

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self._margin, 2 * self._margin)
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x() + self._margin
        y = rect.y() + self._margin
        line_height = 0
        row_items = []

        for item in self._item_list:
            widget = item.widget()
            if widget is None:
                continue

            item_size = item.sizeHint()
            next_x = x + item_size.width() + self._spacing

            # Check if we need to wrap to next row
            if next_x - self._spacing > rect.right() - self._margin and line_height > 0:
                # Center the current row before moving to next
                if not test_only:
                    self._center_row(row_items, rect, y, line_height)
                row_items = []
                x = rect.x() + self._margin
                y = y + line_height + self._spacing
                next_x = x + item_size.width() + self._spacing
                line_height = 0

            if not test_only:
                row_items.append((item, x, item_size))

            x = next_x
            line_height = max(line_height, item_size.height())

        # Center the last row
        if not test_only and row_items:
            self._center_row(row_items, rect, y, line_height)

        return y + line_height - rect.y() + self._margin

    def _center_row(self, row_items, rect, y, line_height):
        """Center items in a row"""
        if not row_items:
            return

        # Calculate total width of items in row
        total_width = sum(size.width() for _, _, size in row_items)
        total_width += self._spacing * (len(row_items) - 1)

        # Calculate starting x to center the row
        available_width = rect.width() - 2 * self._margin
        start_x = rect.x() + self._margin + (available_width - total_width) // 2

        # Position each item
        x = start_x
        for item, _, size in row_items:
            item.setGeometry(QRect(QPoint(x, y), size))
            x += size.width() + self._spacing


def get_all_layout_patterns():
    """Get all available layout patterns"""
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
    ]


# Pattern position mappings - shared between ArrangementGrid implementations
PATTERN_POSITIONS = {
    "2x2 Grid": [(0, 0), (0, 1), (1, 0), (1, 1)],
    "3x1 Row": [(0, 0), (0, 1), (0, 2)],
    "1x3 Column": [(0, 0), (1, 0), (2, 0)],
    "4x1 Row": [(0, 0), (0, 1), (0, 2), (0, 3)],
    "2x3 Grid": [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
    "3x2 Grid": [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
}


def get_pattern_positions(pattern: str, count: int, grid_cols: int = 4) -> List[Tuple[int, int]]:
    """Get grid positions for a layout pattern.

    Args:
        pattern: Layout pattern name
        count: Number of items to arrange
        grid_cols: Number of columns for default grid (used for fallback)

    Returns:
        List of (row, col) tuples for each item position
    """
    if pattern in PATTERN_POSITIONS:
        return PATTERN_POSITIONS[pattern]
    elif pattern == "Main + Sides":
        # First window is main (full height), rest stacked on right
        return [(0, 0)] + [(i - 1, 1) for i in range(1, count)]
    elif pattern == "Cascade":
        return [(i, i) for i in range(count)]
    elif pattern == "Stacked (All Same Position)":
        return [(0, 0)] * count
    else:
        # Default: sequential grid fill
        return [(i // grid_cols, i % grid_cols) for i in range(count)]


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

        self.setFixedSize(100, 60)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self._update_style()

        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(0)

        self.name_label = QLabel(char_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 9pt;")
        layout.addWidget(self.name_label)

        self.pos_label = QLabel("(0, 0)")
        self.pos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pos_label.setStyleSheet("color: #888; font-size: 7pt;")
        layout.addWidget(self.pos_label)

        self.setLayout(layout)

    def _update_style(self):
        bg_color = self.color.name()
        border_color = self.color.darker(150).name()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 4px;
            }}
        """)

    def set_position(self, row: int, col: int):
        self.grid_row = row
        self.grid_col = col
        self.pos_label.setText(f"({row}, {col})")

    def set_stacked(self, stacked: bool):
        self.is_stacked = stacked
        if stacked:
            self.pos_label.setText("(Stacked)")


class ArrangementGrid(QWidget):
    """Compact grid for arranging character tiles - accepts drops from window previews"""

    arrangement_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.tiles: Dict[str, DraggableTile] = {}
        self.grid_rows = 2
        self.grid_cols = 3

        self.setAcceptDrops(True)  # Enable drop support
        self._setup_ui()

    def _setup_ui(self):
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)

        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                cell = QFrame()
                cell.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
                cell.setMinimumSize(105, 65)
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
        self.grid_rows = rows
        self.grid_cols = cols

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for row in range(rows):
            for col in range(cols):
                cell = QFrame()
                cell.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
                cell.setMinimumSize(105, 65)
                cell.setStyleSheet("""
                    QFrame {
                        background-color: #2a2a2a;
                        border: 1px dashed #555;
                        border-radius: 3px;
                    }
                """)
                self.grid_layout.addWidget(cell, row, col)

        for _char_name, tile in list(self.tiles.items()):
            try:
                row = min(tile.grid_row, rows - 1)
                col = min(tile.grid_col, cols - 1)
                tile.set_position(row, col)
                self.grid_layout.addWidget(tile, row, col)
            except RuntimeError:
                # Tile was deleted, remove from tracking
                del self.tiles[_char_name]

    def clear_tiles(self):
        for tile in list(self.tiles.values()):
            self.grid_layout.removeWidget(tile)
            tile.deleteLater()
        self.tiles.clear()

    def add_character(self, char_name: str, row: int = 0, col: int = 0):
        if char_name in self.tiles:
            return

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

    def dragEnterEvent(self, event):
        """Accept drags with EVE character data"""
        if event.mimeData().hasFormat("application/x-eve-character"):
            event.acceptProposedAction()
        elif event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Show drop indicator while dragging"""
        event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop - add character to grid at drop position"""
        # Get character name from drag data
        if event.mimeData().hasFormat("application/x-eve-character"):
            char_name = event.mimeData().data("application/x-eve-character").data().decode()
        elif event.mimeData().hasText():
            char_name = event.mimeData().text()
        else:
            return

        # Calculate which grid cell was dropped on
        pos = event.position().toPoint()
        cell_width = self.width() // max(1, self.grid_cols)
        cell_height = self.height() // max(1, self.grid_rows)

        col = min(pos.x() // cell_width, self.grid_cols - 1)
        row = min(pos.y() // cell_height, self.grid_rows - 1)

        self.logger.info(f"Dropped {char_name} at grid position ({row}, {col})")

        # Remove existing tile if same character
        if char_name in self.tiles:
            old_tile = self.tiles[char_name]
            try:
                self.grid_layout.removeWidget(old_tile)
                old_tile.deleteLater()
            except RuntimeError:
                pass  # Already deleted
            del self.tiles[char_name]

        # Add character at drop position
        self.add_character(char_name, row, col)
        self.arrangement_changed.emit(self.get_arrangement())

        event.acceptProposedAction()


class GridApplier:
    """Applies grid patterns to actual windows using xdotool"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_screen_geometry(self, monitor: int = 0) -> ScreenGeometry:
        """Get screen geometry for a monitor (delegates to shared utility)"""
        return get_screen_geometry(monitor)

    def apply_arrangement(
        self,
        arrangement: Dict[str, Tuple[int, int]],
        window_map: Dict[str, str],
        screen: ScreenGeometry,
        grid_rows: int,
        grid_cols: int,
        spacing: int = 10,
        stacked: bool = False,
        stacked_use_grid_size: bool = True,
    ) -> bool:
        try:
            # Calculate grid cell size (used for both grid and optionally stacked)
            cell_width = (screen.width - spacing * (grid_cols + 1)) // grid_cols
            cell_height = (screen.height - spacing * (grid_rows + 1)) // grid_rows

            if stacked:
                # Stack all windows at same position
                x = screen.x + spacing
                y = screen.y + spacing

                for _char_name, window_id in window_map.items():
                    if stacked_use_grid_size:
                        # Use grid cell size for stacked windows
                        self._move_window(window_id, x, y, cell_width, cell_height)
                    else:
                        # Keep current size, just move to stack position
                        self._move_window_position_only(window_id, x, y)
            else:
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
        """Move and resize a window, with validation, retry, and Wine/Proton fallback"""
        import time

        from argus_overview.utils.window_utils import is_valid_window_id, run_x11_subprocess

        if not is_valid_window_id(window_id):
            self.logger.warning("Invalid window ID format for move: %s", window_id)
            return

        # Try with --sync first, fallback to no-sync for Wine/Proton windows
        try:
            run_x11_subprocess(
                ["xdotool", "windowmove", "--sync", window_id, str(x), str(y)],
                timeout=2,
            )
        except subprocess.TimeoutExpired:
            run_x11_subprocess(["xdotool", "windowmove", window_id, str(x), str(y)], timeout=2)
            time.sleep(0.1)  # Brief pause for window to settle

        try:
            run_x11_subprocess(
                ["xdotool", "windowsize", "--sync", window_id, str(w), str(h)],
                timeout=2,
            )
        except subprocess.TimeoutExpired:
            run_x11_subprocess(["xdotool", "windowsize", window_id, str(w), str(h)], timeout=2)
            time.sleep(0.1)

    def _move_window_position_only(self, window_id: str, x: int, y: int):
        """Move a window without resizing, with validation, retry, and Wine/Proton fallback"""
        import time

        from argus_overview.utils.window_utils import is_valid_window_id, run_x11_subprocess

        if not is_valid_window_id(window_id):
            self.logger.warning("Invalid window ID format for position move: %s", window_id)
            return

        try:
            run_x11_subprocess(
                ["xdotool", "windowmove", "--sync", window_id, str(x), str(y)],
                timeout=2,
            )
        except subprocess.TimeoutExpired:
            run_x11_subprocess(["xdotool", "windowmove", window_id, str(x), str(y)], timeout=2)
            time.sleep(0.1)


def pil_to_qimage(pil_image: Image.Image) -> QImage:
    """
    Convert PIL Image to QImage

    Args:
        pil_image: PIL Image object

    Returns:
        QImage: Converted image, or None if input is None
    """
    if pil_image is None:
        return None
    if pil_image.mode == "RGB":
        bytes_per_line = 3 * pil_image.width
        return QImage(
            pil_image.tobytes(),
            pil_image.width,
            pil_image.height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        )
    elif pil_image.mode == "RGBA":
        bytes_per_line = 4 * pil_image.width
        return QImage(
            pil_image.tobytes(),
            pil_image.width,
            pil_image.height,
            bytes_per_line,
            QImage.Format.Format_RGBA8888,
        )
    elif pil_image.mode == "L":
        bytes_per_line = pil_image.width
        return QImage(
            pil_image.tobytes(),
            pil_image.width,
            pil_image.height,
            bytes_per_line,
            QImage.Format.Format_Grayscale8,
        )
    else:
        # Convert to RGB if unknown mode
        rgb_image = pil_image.convert("RGB")
        bytes_per_line = 3 * rgb_image.width
        return QImage(
            rgb_image.tobytes(),
            rgb_image.width,
            rgb_image.height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        )


class WindowPreviewWidget(QWidget):
    """
    Individual window preview with interactions
    v2.2: Added hover effects, activity indicator, session timer, custom labels
    """

    window_activated = Signal(str)  # window_id
    window_removed = Signal(str)  # window_id
    label_changed = Signal(str, str)  # window_id, new_label

    def __init__(
        self,
        window_id: str,
        character_name: str,
        capture_system,
        settings_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.window_id = window_id
        self.character_name = character_name
        self.capture_system = capture_system
        self.settings_manager = settings_manager

        # State
        self.current_pixmap: Optional[QPixmap] = None
        self.zoom_factor = 0.3  # 30% scale

        # v2.2 State
        self.custom_label: Optional[str] = None
        self.session_start: datetime = datetime.now()
        self.last_activity: datetime = datetime.now()
        self.is_focused: bool = False
        self._is_hovered: bool = False
        self._positions_locked: bool = False

        # v2.2 Settings (from settings_manager or defaults)
        self._opacity_on_hover = 0.3
        self._zoom_on_hover = 1.5
        self._show_activity_indicator = True
        self._show_session_timer = False
        self._load_settings()

        # Setup UI
        self.setMinimumSize(200, 150)
        self.setMaximumSize(600, 450)
        self._update_tooltip()

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(layout)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setText("Loading...")
        layout.addWidget(self.image_label)

        # Info label (shows custom label or character name)
        self.info_label = QLabel(self._get_display_name())
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-weight: bold; padding: 2px;")
        layout.addWidget(self.info_label)

        # Session timer label (v2.2)
        self.timer_label = QLabel("")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("color: #888; font-size: 9px;")
        self.timer_label.setVisible(self._show_session_timer)
        layout.addWidget(self.timer_label)

        # Session timer update (every minute)
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)
        if self._show_session_timer:
            self.session_timer.start(60000)  # Update every minute

        # Opacity effect for hover
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity_effect)

    def _load_settings(self):
        """Load settings from settings_manager"""
        if self.settings_manager:
            self._opacity_on_hover = self.settings_manager.get("thumbnails.opacity_on_hover", 0.3)
            self._zoom_on_hover = self.settings_manager.get("thumbnails.zoom_on_hover", 1.5)
            self._show_activity_indicator = self.settings_manager.get(
                "thumbnails.show_activity_indicator", True
            )
            self._show_session_timer = self.settings_manager.get(
                "thumbnails.show_session_timer", False
            )
            self._positions_locked = self.settings_manager.get("thumbnails.lock_positions", False)

            # Load custom label
            labels = self.settings_manager.get("character_labels", {})
            self.custom_label = labels.get(self.character_name)

    def _get_display_name(self) -> str:
        """Get the display name (custom label or character name)"""
        if self.custom_label:
            return f"{self.custom_label} ({self.character_name})"
        return self.character_name

    def _update_tooltip(self):
        """Update tooltip text"""
        tooltip = f"{self.character_name}"
        if self.custom_label:
            tooltip = f"{self.custom_label}\n{self.character_name}"
        tooltip += f"\nWindow ID: {self.window_id}"
        tooltip += "\nClick to activate | Right-click for menu"
        self.setToolTip(tooltip)

    def update_frame(self, image: Image.Image):
        """
        Update preview with new captured frame

        Args:
            image: PIL Image
        """
        try:
            # Convert PIL to QImage
            qimage = pil_to_qimage(image)
            if qimage is None:
                return  # Skip frame if capture failed

            # Convert to pixmap
            self.current_pixmap = QPixmap.fromImage(qimage)

            # Scale to fit widget while maintaining aspect ratio
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

            self.image_label.setPixmap(scaled_pixmap)

        except Exception as e:
            self.logger.error(f"Failed to update frame for {self.window_id}: {e}")

    def _update_session_timer(self):
        """Update the session timer display"""
        if not self._show_session_timer:
            return

        elapsed = datetime.now() - self.session_start
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)

        if hours > 0:
            self.timer_label.setText(f"{hours}h {minutes}m")
        else:
            self.timer_label.setText(f"{minutes}m")

    def set_custom_label(self, label: Optional[str]):
        """
        Set a custom label for this thumbnail

        Args:
            label: Custom label text or None to clear
        """
        self.custom_label = label
        self.info_label.setText(self._get_display_name())
        self._update_tooltip()
        self.label_changed.emit(self.window_id, label or "")

        # Save to settings if available
        if self.settings_manager:
            labels = self.settings_manager.get("character_labels", {})
            if label:
                labels[self.character_name] = label
            elif self.character_name in labels:
                del labels[self.character_name]
            self.settings_manager.set("character_labels", labels)

    def set_focused(self, focused: bool):
        """Set whether this window has focus (for activity indicator)"""
        self.is_focused = focused
        if focused:
            self.last_activity = datetime.now()
        self.update()

    def mark_activity(self):
        """Mark that activity occurred on this window"""
        self.last_activity = datetime.now()
        self.update()

    def get_activity_state(self) -> str:
        """
        Get activity state for indicator

        Returns:
            'focused', 'recent', or 'idle'
        """
        if self.is_focused:
            return "focused"

        elapsed = (datetime.now() - self.last_activity).total_seconds()
        if elapsed < 5:
            return "recent"
        return "idle"

    def enterEvent(self, event):
        """Handle mouse enter - apply hover effects"""
        self._is_hovered = True

        # Opacity effect
        self.opacity_effect.setOpacity(self._opacity_on_hover)

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave - restore normal state"""
        self._is_hovered = False

        # Restore opacity
        self.opacity_effect.setOpacity(1.0)

        super().leaveEvent(event)

    def paintEvent(self, event):
        """Custom paint for activity indicator"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw activity indicator (v2.2)
        if self._show_activity_indicator:
            activity = self.get_activity_state()
            if activity == "focused":
                indicator_color = QColor(0, 255, 0, 220)  # Green
            elif activity == "recent":
                indicator_color = QColor(255, 200, 0, 220)  # Yellow
            else:
                indicator_color = QColor(128, 128, 128, 180)  # Gray

            # Draw small dot in top-right corner
            painter.setBrush(QBrush(indicator_color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawEllipse(self.width() - 14, 6, 8, 8)

        # Draw lock icon if positions are locked
        if self._positions_locked:
            painter.setPen(QPen(QColor(200, 200, 200, 180)))
            painter.drawText(6, 14, "🔒")

        painter.end()

    def mousePressEvent(self, event):
        """Handle mouse click - start drag or activate"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        """Handle mouse move - initiate drag if moved far enough"""
        if not hasattr(self, "_drag_start_pos") or self._drag_start_pos is None:
            return

        # Check if moved far enough to start drag
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < 10:
            return

        # Start drag operation
        from PySide6.QtCore import QMimeData
        from PySide6.QtGui import QDrag

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.character_name)  # Pass character name
        mime_data.setData("application/x-eve-character", self.character_name.encode())
        drag.setMimeData(mime_data)

        # Create a small preview for the drag
        pixmap = self.grab().scaled(80, 50, Qt.AspectRatioMode.KeepAspectRatio)
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())

        self._drag_start_pos = None
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, event):
        """Handle mouse release - activate window if not dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, "_drag_start_pos") and self._drag_start_pos is not None:
                # Didn't drag far enough, treat as click
                self.window_activated.emit(self.window_id)
                self.logger.info(f"Activating window: {self.window_id}")
            self._drag_start_pos = None

    def contextMenuEvent(self, event):
        """Handle right-click context menu (v2.3 - uses ActionRegistry)"""
        # Build context menu from ActionRegistry
        context_builder = ContextMenuBuilder()

        # Handler map for context actions
        handlers = {
            "focus_window": lambda: self.window_activated.emit(self.window_id),
            "minimize_window": self._minimize_window,
            "close_window": self._close_window,
            "set_label": self._show_label_dialog,
            "remove_from_preview": lambda: self.window_removed.emit(self.window_id),
        }

        menu = context_builder.build_window_context_menu(
            handlers=handlers,
            zoom_handler=self._set_zoom,
            current_zoom=self.zoom_factor,
            parent=self,
        )

        menu.exec(event.globalPos())

    def _show_label_dialog(self):
        """Show dialog to set custom label"""
        current = self.custom_label or ""
        text, ok = QInputDialog.getText(
            self, "Set Label", f"Enter label for {self.character_name}:", text=current
        )
        if ok:
            self.set_custom_label(text if text.strip() else None)

    def _close_window(self):
        """Close the EVE window with confirmation"""
        reply = QMessageBox.question(
            self,
            "Close Window",
            f"Close the EVE window for {self.character_name}?\n\nThis will close the game client.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            from argus_overview.utils.window_utils import run_x11_subprocess

            try:
                run_x11_subprocess(["wmctrl", "-i", "-c", self.window_id], timeout=2)
                self.logger.info(f"Closed window: {self.window_id}")
                self.window_removed.emit(self.window_id)
            except Exception as e:
                self.logger.warning(f"Failed to close window after retries: {e}")

    def _minimize_window(self):
        """Minimize the window"""
        try:
            result = self.capture_system.minimize_window(self.window_id)
            if result:
                self.logger.info(f"Minimized window: {self.window_id}")
            else:
                self.logger.warning(f"Failed to minimize window: {self.window_id}")
        except Exception as e:
            self.logger.error(f"Error minimizing window: {e}")

    def _set_zoom(self, zoom: float):
        """Set zoom factor"""
        self.zoom_factor = zoom
        self.logger.debug(f"Zoom set to {int(zoom * 100)}% for {self.window_id}")


class WindowManager:
    """
    Orchestrates 30 FPS capture loop for all preview widgets
    v2.2: Added settings_manager support for thumbnail settings
    """

    def __init__(self, character_manager, capture_system, settings_manager=None):
        self.logger = logging.getLogger(__name__)
        self.character_manager = character_manager
        self.capture_system = capture_system
        self.settings_manager = settings_manager

        # State
        self.preview_frames: Dict[str, WindowPreviewWidget] = {}
        self.pending_requests: Dict[str, str] = {}  # request_id -> window_id
        self._pending_lock = threading.Lock()  # Protect pending_requests access
        # Read refresh rate from settings (default 5 FPS for efficiency)
        if settings_manager:
            self.refresh_rate = settings_manager.get("performance.default_refresh_rate", 5)
        else:
            self.refresh_rate = 5  # Low default for efficiency

        # Timer for capture loop
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self._capture_cycle)

        self.logger.info("WindowManager initialized")

    def start_capture_loop(self):
        """Start the 30 FPS capture loop"""
        interval = 1000 // self.refresh_rate  # ms
        self.capture_timer.start(interval)
        self.logger.info(f"Capture loop started at {self.refresh_rate} FPS ({interval}ms interval)")

    def stop_capture_loop(self):
        """Stop the capture loop"""
        self.capture_timer.stop()
        self.logger.info("Capture loop stopped")

    def set_refresh_rate(self, fps: int):
        """
        Set refresh rate

        Args:
            fps: Frames per second (1-60)
        """
        self.refresh_rate = max(1, min(60, fps))
        if self.capture_timer.isActive():
            self.stop_capture_loop()
            self.start_capture_loop()

    def add_window(self, window_id: str, character_name: str) -> Optional[WindowPreviewWidget]:
        """
        Add window to preview

        Args:
            window_id: X11 window ID
            character_name: Character name

        Returns:
            WindowPreviewWidget or None
        """
        if window_id in self.preview_frames:
            self.logger.warning(f"Window {window_id} already in preview")
            return None

        # Create preview widget with settings_manager for v2.2 features
        frame = WindowPreviewWidget(
            window_id, character_name, self.capture_system, settings_manager=self.settings_manager
        )
        self.preview_frames[window_id] = frame

        self.logger.info(f"Added window {window_id} ({character_name}) to preview")
        return frame

    def remove_window(self, window_id: str):
        """
        Remove window from preview

        Args:
            window_id: X11 window ID
        """
        if window_id in self.preview_frames:
            # Remove from dict
            frame = self.preview_frames.pop(window_id)
            frame.deleteLater()

            self.logger.info(f"Removed window {window_id} from preview")

    def _capture_cycle(self):
        """
        Capture cycle - called by timer

        Requests captures for all visible frames, then polls for results
        """
        # Request captures for all visible preview frames
        for window_id, frame in self.preview_frames.items():
            if frame.isVisible():
                try:
                    request_id = self.capture_system.capture_window_async(
                        window_id, scale=frame.zoom_factor
                    )
                    with self._pending_lock:
                        self.pending_requests[request_id] = window_id
                except Exception as e:
                    self.logger.error(f"Failed to request capture for {window_id}: {e}")

        # Poll for results (non-blocking)
        self._process_capture_results()

    def _process_capture_results(self):
        """Poll and process capture results from worker threads"""
        # Process up to 10 results per cycle to avoid blocking UI
        max_per_cycle = 10
        processed = 0

        for _ in range(max_per_cycle):
            result = self.capture_system.get_result(timeout=0.0)  # Non-blocking
            if not result:
                break

            processed += 1
            request_id, window_id, image = result

            # Update preview
            if window_id in self.preview_frames:
                try:
                    self.preview_frames[window_id].update_frame(image)
                except Exception as e:
                    self.logger.error(f"Failed to process frame for {window_id}: {e}")

            # Remove from pending
            with self._pending_lock:
                self.pending_requests.pop(request_id, None)

        if processed > 0:
            self.logger.debug(f"Processed {processed} capture results")

    def get_active_window_count(self) -> int:
        """Get count of active preview windows"""
        return len(self.preview_frames)


class MainTab(QWidget):
    """
    Main Tab - Window Preview Management
    v2.2: One-click import, auto-discovery integration, position management
    v2.3: Merged layouts - group-based window arrangement
    """

    character_detected = Signal(str, str)  # window_id, char_name
    thumbnails_toggled = Signal(bool)  # visible
    layout_applied = Signal(str)  # pattern name

    def __init__(self, capture_system, character_manager, settings_manager=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.capture_system = capture_system
        self.character_manager = character_manager
        self.settings_manager = settings_manager

        # v2.2 State
        self._thumbnails_visible = True
        self._positions_locked = False
        # Load auto-minimize state from settings
        self._windows_minimized = (
            settings_manager.get("performance.auto_minimize_inactive", False)
            if settings_manager
            else False
        )

        # v2.3: Layout controls
        self._refresh_sources_timer = QTimer()
        self._refresh_sources_timer.setSingleShot(True)
        self._refresh_sources_timer.setInterval(150)
        self._refresh_sources_timer.timeout.connect(self._do_refresh_layout_sources)

        self.grid_applier = GridApplier()
        self.cycling_groups: Dict[str, List[str]] = {}
        self._load_cycling_groups()

        # Create window manager
        self.window_manager = WindowManager(character_manager, capture_system, settings_manager)

        self._setup_ui()

        # Enable keyboard focus for number key shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Start capture loop (unless disabled for GPU/CPU savings)
        if not (settings_manager and settings_manager.get("performance.disable_previews", False)):
            self.window_manager.start_capture_loop()
        else:
            self.logger.info("Previews disabled - capture loop not started (GPU/CPU savings)")

        self.logger.info("Main tab initialized")

    def _load_cycling_groups(self):
        """Load cycling groups from settings"""
        if self.settings_manager:
            groups = self.settings_manager.get("cycling_groups", {})
            if isinstance(groups, dict):
                self.cycling_groups = groups
        if "Default" not in self.cycling_groups:
            self.cycling_groups["Default"] = []

    def _setup_ui(self):
        """Setup UI layout"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Quick Layout controls
        layout_controls = self._create_layout_controls()
        layout.addWidget(layout_controls)

        # Scroll area for preview frames
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container for preview frames with flow/grid layout
        self.preview_container = QWidget()
        self.preview_layout = FlowLayout(margin=15, spacing=15)  # Grid-style flow layout
        self.preview_container.setLayout(self.preview_layout)

        scroll.setWidget(self.preview_container)
        layout.addWidget(scroll)

        # Status bar
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)

    def _create_toolbar(self) -> QWidget:
        """Create toolbar using ActionRegistry (v2.3)"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 5)
        toolbar.setLayout(toolbar_layout)

        # Build toolbar buttons from ActionRegistry
        toolbar_builder = ToolbarBuilder()
        handlers = {
            "import_windows": self.one_click_import,
            "add_window": self.show_add_window_dialog,
            "remove_all_windows": self._remove_all_windows,
            "lock_positions": self._toggle_lock,
            "minimize_inactive": self.minimize_inactive_windows,
            "refresh_capture": self._refresh_all,
        }

        # Create buttons in specific order with layout control
        action_order = [
            "import_windows",
            "add_window",
            "remove_all_windows",
        ]

        buttons = toolbar_builder.build_toolbar_buttons(
            PrimaryHome.OVERVIEW_TOOLBAR,
            handlers,
            action_order,
        )

        # Add first group of buttons
        for action_id in action_order:
            if action_id in buttons:
                toolbar_layout.addWidget(buttons[action_id])

        toolbar_layout.addStretch()

        # Add lock button (store reference for state updates)
        self.lock_btn = toolbar_builder.create_button("lock_positions", self._toggle_lock)
        if self.lock_btn:
            toolbar_layout.addWidget(self.lock_btn)

        # Add minimize inactive button (store reference for state indicator)
        self.minimize_inactive_btn = toolbar_builder.create_button(
            "minimize_inactive", self.minimize_inactive_windows
        )
        if self.minimize_inactive_btn:
            self.minimize_inactive_btn.setCheckable(True)
            self._update_minimize_button_style()  # Apply saved state
            toolbar_layout.addWidget(self.minimize_inactive_btn)

        # Add refresh button
        refresh_btn = toolbar_builder.create_button("refresh_capture", self._refresh_all)
        if refresh_btn:
            toolbar_layout.addWidget(refresh_btn)

        toolbar_layout.addStretch()

        # Refresh Rate (not from registry - it's a widget, not an action)
        toolbar_layout.addWidget(QLabel("FPS:"))
        self.refresh_rate_spin = QSpinBox()
        self.refresh_rate_spin.setRange(1, 60)
        self.refresh_rate_spin.setValue(30)
        self.refresh_rate_spin.setToolTip("Capture framerate (higher = smoother but more CPU)")
        self.refresh_rate_spin.valueChanged.connect(self._on_refresh_rate_changed)
        toolbar_layout.addWidget(self.refresh_rate_spin)

        # Search/filter field
        toolbar_layout.addSpacing(10)
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Filter...")
        self.search_field.setMaximumWidth(150)
        self.search_field.setClearButtonEnabled(True)
        self.search_field.setToolTip("Filter windows by character name")
        self.search_field.textChanged.connect(self._filter_previews)
        toolbar_layout.addWidget(self.search_field)

        return toolbar

    def _create_layout_controls(self) -> QWidget:
        """Create comprehensive layout controls panel with arrangement grid"""
        section = QGroupBox("Window Layouts")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Top row: Controls
        controls_row = QHBoxLayout()

        # Source selector (group or all active)
        controls_row.addWidget(QLabel("Source:"))
        self.layout_source_combo = QComboBox()
        self._refresh_layout_sources()
        self.layout_source_combo.setMinimumWidth(120)
        self.layout_source_combo.currentTextChanged.connect(self._on_layout_source_changed)
        controls_row.addWidget(self.layout_source_combo)

        # Pattern selector
        controls_row.addWidget(QLabel("Pattern:"))
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(get_all_layout_patterns())
        self.pattern_combo.setMinimumWidth(120)
        self.pattern_combo.currentTextChanged.connect(self._on_pattern_changed)
        controls_row.addWidget(self.pattern_combo)

        # Grid size
        controls_row.addWidget(QLabel("Grid:"))
        self.grid_rows_spin = QSpinBox()
        self.grid_rows_spin.setRange(1, 4)
        self.grid_rows_spin.setValue(2)
        self.grid_rows_spin.setPrefix("R:")
        self.grid_rows_spin.valueChanged.connect(self._update_arrangement_grid_size)
        controls_row.addWidget(self.grid_rows_spin)

        self.grid_cols_spin = QSpinBox()
        self.grid_cols_spin.setRange(1, 4)
        self.grid_cols_spin.setValue(3)
        self.grid_cols_spin.setPrefix("C:")
        self.grid_cols_spin.valueChanged.connect(self._update_arrangement_grid_size)
        controls_row.addWidget(self.grid_cols_spin)

        # Spacing
        controls_row.addWidget(QLabel("Gap:"))
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 50)
        self.spacing_spin.setValue(10)
        self.spacing_spin.setSuffix("px")
        controls_row.addWidget(self.spacing_spin)

        # Monitor
        controls_row.addWidget(QLabel("Mon:"))
        self.monitor_spin = QSpinBox()
        self.monitor_spin.setRange(0, 3)
        self.monitor_spin.setValue(0)
        controls_row.addWidget(self.monitor_spin)

        # Stack checkbox
        self.stack_checkbox = QCheckBox("Stack")
        self.stack_checkbox.setToolTip("Place all windows at the same position")
        self.stack_checkbox.stateChanged.connect(self._on_stack_changed)
        controls_row.addWidget(self.stack_checkbox)

        # Resize stacked windows checkbox
        self.stack_resize_checkbox = QCheckBox("Resize")
        self.stack_resize_checkbox.setChecked(True)
        self.stack_resize_checkbox.setToolTip(
            "When stacking:\n"
            "• Checked: Resize windows to grid cell size\n"
            "• Unchecked: Keep current window sizes"
        )
        self.stack_resize_checkbox.setEnabled(False)  # Only enabled when stacking
        controls_row.addWidget(self.stack_resize_checkbox)

        controls_row.addStretch()

        main_layout.addLayout(controls_row)

        # Bottom row: Arrangement grid + Apply button
        bottom_row = QHBoxLayout()

        # Arrangement grid (compact)
        self.arrangement_grid = ArrangementGrid()
        self.arrangement_grid.setMaximumHeight(150)
        bottom_row.addWidget(self.arrangement_grid, stretch=1)

        # Buttons column
        buttons_col = QVBoxLayout()

        auto_arrange_btn = QPushButton("Auto-Arrange")
        auto_arrange_btn.clicked.connect(self._auto_arrange_tiles)
        auto_arrange_btn.setToolTip("Arrange tiles based on selected pattern")
        buttons_col.addWidget(auto_arrange_btn)

        apply_btn = QPushButton("Apply Layout")
        apply_btn.setToolTip("Arrange EVE windows on screen")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff8c00;
                color: black;
                font-weight: bold;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: #ffa500; }
        """)
        apply_btn.clicked.connect(self._apply_layout_to_windows)
        buttons_col.addWidget(apply_btn)

        buttons_col.addStretch()
        bottom_row.addLayout(buttons_col)

        main_layout.addLayout(bottom_row)

        section.setLayout(main_layout)
        return section

    def _refresh_layout_sources(self):
        """Schedule debounced layout sources refresh"""
        if hasattr(self, "_refresh_sources_timer"):
            self._refresh_sources_timer.start()
        else:
            self._do_refresh_layout_sources()

    def _do_refresh_layout_sources(self):
        """Refresh available sources (groups and active windows) (debounced)"""
        self._load_cycling_groups()

        current = (
            self.layout_source_combo.currentText()
            if hasattr(self, "layout_source_combo") and self.layout_source_combo.count() > 0
            else None
        )

        self.layout_source_combo.blockSignals(True)
        self.layout_source_combo.clear()
        self.layout_source_combo.addItem("All Active Windows")

        for group_name in sorted(self.cycling_groups.keys()):
            self.layout_source_combo.addItem(group_name)

        if current:
            idx = self.layout_source_combo.findText(current)
            if idx >= 0:
                self.layout_source_combo.setCurrentIndex(idx)

        self.layout_source_combo.blockSignals(False)

    def _on_layout_source_changed(self):
        """Handle source selection change"""
        source = self.layout_source_combo.currentText()
        self.arrangement_grid.clear_tiles()

        if source == "All Active Windows":
            for _window_id, frame in self.window_manager.preview_frames.items():
                self.arrangement_grid.add_character(frame.character_name)
        else:
            members = self.cycling_groups.get(source, [])
            for idx, char_name in enumerate(members):
                row = idx // self.arrangement_grid.grid_cols
                col = idx % self.arrangement_grid.grid_cols
                self.arrangement_grid.add_character(char_name, row, col)

        if self.pattern_combo.currentText() != "Custom":
            self._auto_arrange_tiles()

    def _on_pattern_changed(self):
        """Handle pattern change"""
        pattern = self.pattern_combo.currentText()
        is_stacked = pattern == "Stacked (All Same Position)"
        self.stack_checkbox.setChecked(is_stacked)
        self.stack_resize_checkbox.setEnabled(is_stacked)
        self._auto_arrange_tiles()

    def _on_stack_changed(self):
        """Handle stack checkbox change"""
        is_stacked = self.stack_checkbox.isChecked()
        self.stack_resize_checkbox.setEnabled(is_stacked)

    def _update_arrangement_grid_size(self):
        """Update arrangement grid dimensions"""
        rows = self.grid_rows_spin.value()
        cols = self.grid_cols_spin.value()
        self.arrangement_grid.set_grid_size(rows, cols)

    def _auto_arrange_tiles(self):
        """Auto-arrange tiles based on pattern"""
        pattern = self.pattern_combo.currentText()
        self.arrangement_grid.auto_arrange_grid(pattern)

    def _apply_layout_to_windows(self):
        """Apply layout to active windows"""
        arrangement = self.arrangement_grid.get_arrangement()
        if not arrangement:
            QMessageBox.warning(
                self,
                "No Windows",
                "No windows in arrangement.\n\nSelect a source or import EVE windows first.",
            )
            return

        # Build window map (char_name -> window_id)
        window_map = {}
        for window_id, frame in self.window_manager.preview_frames.items():
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
            screen = ScreenGeometry(0, 0, 1920, 1080, True)

        # Apply arrangement
        success = self.grid_applier.apply_arrangement(
            arrangement=arrangement,
            window_map=window_map,
            screen=screen,
            grid_rows=self.grid_rows_spin.value(),
            grid_cols=self.grid_cols_spin.value(),
            spacing=self.spacing_spin.value(),
            stacked=self.stack_checkbox.isChecked(),
            stacked_use_grid_size=self.stack_resize_checkbox.isChecked(),
        )

        if success:
            pattern = self.pattern_combo.currentText()
            self.status_label.setText(f"Applied {pattern} layout to {len(window_map)} windows")
            self.layout_applied.emit(pattern)
            self.logger.info(f"Applied {pattern} layout to {len(window_map)} windows")
        else:
            QMessageBox.warning(self, "Error", "Failed to apply layout. Check logs for details.")

    def refresh_layout_groups(self):
        """Called when groups change in hotkeys tab"""
        self._refresh_layout_sources()
        self._on_layout_source_changed()

    def one_click_import(self):
        """
        v2.2 One-Click Import: Scan and import all EVE windows automatically
        """
        self.logger.info("Starting one-click import...")

        # Scan for EVE windows
        eve_windows = scan_eve_windows()

        if not eve_windows:
            QMessageBox.information(
                self,
                "No EVE Windows Found",
                "No EVE Online windows were detected.\n\n"
                "Make sure EVE Online clients are running and visible.",
            )
            return

        # Count how many are new
        added_count = 0
        skipped_count = 0

        for window_id, _window_title, char_name in eve_windows:
            # Skip if already in preview
            if window_id in self.window_manager.preview_frames:
                skipped_count += 1
                continue

            # Add to window manager
            frame = self.window_manager.add_window(window_id, char_name)
            if frame:
                # Connect signals
                frame.window_activated.connect(
                    self._on_window_activated, Qt.ConnectionType.UniqueConnection
                )
                frame.window_removed.connect(
                    self._on_window_removed, Qt.ConnectionType.UniqueConnection
                )

                # Add to layout
                self.preview_layout.addWidget(frame)
                added_count += 1

                # Emit character detected signal
                self.character_detected.emit(window_id, char_name)

        # Show result
        if added_count > 0:
            self.status_label.setText(f"Imported {added_count} character(s)")
            self.logger.info(
                f"One-click import: Added {added_count}, skipped {skipped_count} duplicates"
            )
        elif skipped_count > 0:
            self.status_label.setText(f"All {skipped_count} EVE windows already imported")
        else:
            self.status_label.setText("No new EVE windows found")

        self._update_status()

    def _toggle_lock(self):
        """Toggle thumbnail position lock"""
        self._positions_locked = self.lock_btn.isChecked()

        if self._positions_locked:
            self.lock_btn.setText("Unlock")
            self.lock_btn.setStyleSheet("QPushButton { background-color: #ff4444; }")
            self.status_label.setText("Positions locked")
        else:
            self.lock_btn.setText("Lock")
            self.lock_btn.setStyleSheet("")
            self.status_label.setText("Positions unlocked")

        # Update all preview widgets
        for frame in self.window_manager.preview_frames.values():
            frame._positions_locked = self._positions_locked
            frame.update()

        # Save to settings
        if self.settings_manager:
            self.settings_manager.set("thumbnails.lock_positions", self._positions_locked)

        self.logger.info(f"Positions {'locked' if self._positions_locked else 'unlocked'}")

    def toggle_thumbnails_visibility(self):
        """Toggle visibility of all thumbnails"""
        self._thumbnails_visible = not self._thumbnails_visible

        for frame in self.window_manager.preview_frames.values():
            frame.setVisible(self._thumbnails_visible)

        self.thumbnails_toggled.emit(self._thumbnails_visible)
        self.logger.info(f"Thumbnails {'shown' if self._thumbnails_visible else 'hidden'}")

    def _create_status_bar(self) -> QWidget:
        """Create status bar"""
        status_bar = QWidget()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 5, 0, 0)
        status_bar.setLayout(status_layout)

        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.active_count_label = QLabel("Active: 0")
        status_layout.addWidget(self.active_count_label)

        # Update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(2000)  # Every 2 seconds (status display doesn't need 1s updates)

        return status_bar

    def _get_available_windows(self) -> list:
        """Get windows not already in preview. Returns list of (window_id, title) tuples."""
        try:
            windows = self.capture_system.get_window_list()
        except Exception as e:
            self.logger.error(f"Failed to get window list: {e}")
            raise

        return [
            (wid, title) for wid, title in windows if wid not in self.window_manager.preview_frames
        ]

    def _add_window_to_preview(self, window_id: str, window_title: str) -> bool:
        """Add a single window to preview. Returns True if successful."""
        # Extract character name from window title
        char_name = window_title.replace("EVE -", "").replace("EVE Online -", "").strip()
        if not char_name:
            char_name = f"Unknown ({window_id})"

        # Try auto-assign to character
        assignments = self.character_manager.auto_assign_windows([(window_id, window_title)])
        if assignments:
            for detected_name, wid in assignments.items():
                if wid == window_id:
                    char_name = detected_name
                    self.character_detected.emit(window_id, char_name)
                    break

        # Add to window manager
        frame = self.window_manager.add_window(window_id, char_name)
        if frame:
            frame.window_activated.connect(
                self._on_window_activated, Qt.ConnectionType.UniqueConnection
            )
            frame.window_removed.connect(
                self._on_window_removed, Qt.ConnectionType.UniqueConnection
            )
            self.preview_layout.addWidget(frame)
            return True
        return False

    def show_add_window_dialog(self):
        """Show dialog to add windows"""
        try:
            available = self._get_available_windows()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get window list:\n{e}")
            return

        if not available:
            QMessageBox.information(
                self, "No Windows", "No windows found.\n\nMake sure EVE Online clients are running."
            )
            return

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Windows to Preview")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QVBoxLayout()
        dialog.setLayout(layout)
        layout.addWidget(QLabel("Select EVE Online windows to add to preview:"))

        # List widget with available windows
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for window_id, window_title in available:
            item = QListWidgetItem(f"{window_title} ({window_id})")
            item.setData(Qt.ItemDataRole.UserRole, (window_id, window_title))
            list_widget.addItem(item)
        layout.addWidget(list_widget)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Process selection
        if dialog.exec() == QDialog.DialogCode.Accepted:
            added = sum(
                1
                for item in list_widget.selectedItems()
                if self._add_window_to_preview(*item.data(Qt.ItemDataRole.UserRole))
            )
            if added:
                self.logger.info(f"Added {added} windows to preview")
                self._update_status()

    def _on_window_activated(self, window_id: str):
        """Handle window activation with optional auto-minimize of previous window"""
        from argus_overview.utils.window_utils import run_x11_subprocess

        try:
            # Check if auto-minimize is enabled
            auto_minimize = (
                self.settings_manager.get("performance.auto_minimize_inactive", False)
                if self.settings_manager
                else False
            )

            if auto_minimize and self.settings_manager:
                # Get the last activated EVE window
                last_window = self.settings_manager.get_last_activated_window()
                if last_window and last_window != window_id:
                    # Minimize the previous EVE window
                    try:
                        run_x11_subprocess(["xdotool", "windowminimize", last_window], timeout=2)
                        self.logger.info(f"Auto-minimized previous EVE window: {last_window}")
                    except Exception as e:
                        self.logger.warning(f"Failed to auto-minimize window {last_window}: {e}")

            # Track this as the last activated EVE window
            if self.settings_manager:
                self.settings_manager.set_last_activated_window(window_id)

            result = self.capture_system.activate_window(window_id)
            if result:
                self.logger.info(f"Activated window: {window_id}")
            else:
                self.logger.warning(f"Failed to activate window: {window_id}")
        except Exception as e:
            self.logger.error(f"Error activating window: {e}")

    def _on_window_removed(self, window_id: str):
        """Handle window removal — disconnect frame signals before deletion"""
        frame = self.window_manager.preview_frames.get(window_id)
        if frame:
            try:
                frame.window_activated.disconnect(self._on_window_activated)
            except (RuntimeError, TypeError):
                pass
            try:
                frame.window_removed.disconnect(self._on_window_removed)
            except (RuntimeError, TypeError):
                pass
            # Stop per-frame timers
            frame.session_timer.stop()
        self.window_manager.remove_window(window_id)
        self._update_status()

    def _remove_all_windows(self):
        """Remove all windows from preview"""
        if not self.window_manager.preview_frames:
            return

        reply = QMessageBox.question(
            self,
            "Remove All Windows",
            "Remove all windows from preview?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Copy list to avoid modification during iteration
            window_ids = list(self.window_manager.preview_frames.keys())
            for window_id in window_ids:
                self.window_manager.remove_window(window_id)

            self._update_status()

    def minimize_inactive_windows(self):
        """Toggle auto-minimize mode - when enabled, cycling minimizes previous window"""
        try:
            # Toggle the setting
            current = (
                self.settings_manager.get("performance.auto_minimize_inactive", False)
                if self.settings_manager
                else False
            )
            new_value = not current

            if self.settings_manager:
                self.settings_manager.set("performance.auto_minimize_inactive", new_value)

            self._windows_minimized = new_value
            self._update_minimize_button_style()

            if new_value:
                # Mode enabled - also minimize inactive windows now
                from argus_overview.utils.window_utils import run_x11_subprocess

                try:
                    result = run_x11_subprocess(
                        ["xdotool", "getwindowfocus"], timeout=2, max_attempts=2
                    )
                except Exception:
                    result = None
                if result and result.returncode == 0:
                    focused_id = result.stdout.decode("utf-8", errors="replace").strip()
                    minimized_count = 0
                    for window_id in self.window_manager.preview_frames.keys():
                        if window_id != focused_id:
                            if self.capture_system.minimize_window(window_id):
                                minimized_count += 1
                    self.logger.info(f"Auto-minimize enabled, minimized {minimized_count} windows")
                    self.status_label.setText(f"Auto-minimize ON ({minimized_count} minimized)")
                else:
                    self.status_label.setText("Auto-minimize ON")
            else:
                # Mode disabled - restore all windows
                restored_count = 0
                for window_id in self.window_manager.preview_frames.keys():
                    if self.capture_system.restore_window(window_id):
                        restored_count += 1
                self.logger.info(f"Auto-minimize disabled, restored {restored_count} windows")
                self.status_label.setText(f"Auto-minimize OFF ({restored_count} restored)")

        except Exception as e:
            self.logger.error(f"Error toggling auto-minimize: {e}")

    def _update_minimize_button_style(self):
        """Update minimize button visual state"""
        if hasattr(self, "minimize_inactive_btn") and self.minimize_inactive_btn:
            self.minimize_inactive_btn.setChecked(self._windows_minimized)
            if self._windows_minimized:
                self.minimize_inactive_btn.setText("⚡ Auto-Min ON")
                self.minimize_inactive_btn.setStyleSheet(
                    "QPushButton { background-color: #e67e22; color: white; font-weight: bold; }"
                    "QPushButton:hover { background-color: #f39c12; }"
                )
            else:
                self.minimize_inactive_btn.setText("Auto-Minimize")
                self.minimize_inactive_btn.setStyleSheet("")

    def _refresh_all(self):
        """Refresh all captures"""
        self.logger.info("Refreshing all captures")
        self.status_label.setText("Refreshed all captures")

    def _on_refresh_rate_changed(self, value):
        """Handle refresh rate change"""
        self.window_manager.set_refresh_rate(value)
        self.logger.info(f"Refresh rate changed to {value} FPS")

    def _filter_previews(self, text: str):
        """Filter preview windows by character name"""
        search_text = text.lower().strip()

        visible_count = 0
        for _window_id, frame in self.window_manager.preview_frames.items():
            char_name = frame.character_name.lower()
            # Show if search is empty or character name contains search text
            matches = not search_text or search_text in char_name
            frame.setVisible(matches)
            if matches:
                visible_count += 1

        # Update status to show filtered count
        total = len(self.window_manager.preview_frames)
        if search_text and visible_count < total:
            self.status_label.setText(f"Showing {visible_count}/{total} windows (filtered)")
        else:
            self._update_status()

    def _update_status(self):
        """Update status bar"""
        count = self.window_manager.get_active_window_count()
        self.active_count_label.setText(f"Active: {count}")

        if count == 0:
            self.status_label.setText("No windows in preview - Click 'Add Window' to start")
        else:
            self.status_label.setText(
                f"Capturing {count} window(s) at {self.window_manager.refresh_rate} FPS"
            )

    def stop_capture_loop(self):
        """Stop capture loop and status timer for clean shutdown"""
        self.window_manager.stop_capture_loop()
        self.status_timer.stop()
        # Stop per-frame timers
        for frame in self.window_manager.preview_frames.values():
            frame.session_timer.stop()

    def set_previews_enabled(self, enabled: bool):
        """
        Enable or disable window preview captures.
        When disabled, saves GPU/CPU but window cycling still works.

        Args:
            enabled: True to enable captures, False to disable
        """
        if enabled:
            if not self.window_manager.capture_timer.isActive():
                self.window_manager.start_capture_loop()
                self.status_label.setText("Previews enabled")
                self.logger.info("Preview captures enabled")
        else:
            if self.window_manager.capture_timer.isActive():
                self.window_manager.stop_capture_loop()
                self.status_label.setText("Previews disabled (GPU/CPU savings)")
                self.logger.info("Preview captures disabled - GPU/CPU savings active")

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts for window navigation"""
        key = event.key()

        # Number keys 1-9 to activate window by index
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            index = key - Qt.Key.Key_1  # 0-8
            self._activate_window_by_index(index)
            event.accept()
            return

        # Pass unhandled keys to parent
        super().keyPressEvent(event)

    def _activate_window_by_index(self, index: int):
        """Activate a window by its index in the preview list"""
        windows = list(self.window_manager.preview_frames.items())
        if 0 <= index < len(windows):
            window_id, frame = windows[index]
            # Activate the window
            if self.capture_system.activate_window(window_id):
                self.logger.info(f"Activated window {index + 1}: {frame.character_name}")
                self.status_label.setText(f"Activated: {frame.character_name}")
            else:
                self.logger.warning(f"Failed to activate window {index + 1}")
        else:
            self.logger.debug(
                f"Window index {index + 1} out of range (have {len(windows)} windows)"
            )
