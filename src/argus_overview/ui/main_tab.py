"""
Main Tab - Window Preview Management System
Implements 30 FPS capture loop with window previews and interactions
v2.2: Added one-click import, hover effects, activity indicators, session timers
v2.3: Merged layouts functionality - group-based window arrangement
"""

from __future__ import annotations

import logging
import subprocess
import threading
import time
from datetime import datetime

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
from argus_overview.intel.parser import ThreatLevel
from argus_overview.ui.action_registry import PrimaryHome
from argus_overview.ui.menu_builder import ContextMenuBuilder, ToolbarBuilder
from argus_overview.utils.screen import ScreenGeometry, get_screen_geometry

# Threat-tint config — tuned for a glanceable but non-distracting frame
THREAT_BORDER_COLORS: dict[ThreatLevel, tuple[int, int, int]] = {
    ThreatLevel.CLEAR: (0, 200, 100),
    ThreatLevel.INFO: (0, 180, 230),
    ThreatLevel.WARNING: (255, 170, 0),
    ThreatLevel.DANGER: (255, 90, 30),
    ThreatLevel.CRITICAL: (255, 40, 40),
}
THREAT_LEVEL_RANK: dict[ThreatLevel, int] = {
    ThreatLevel.CLEAR: 0,
    ThreatLevel.INFO: 1,
    ThreatLevel.WARNING: 2,
    ThreatLevel.DANGER: 3,
    ThreatLevel.CRITICAL: 4,
}
THREAT_DECAY_TICK_MS = 100  # decay tick rate
THREAT_DECAY_DURATION_MS = 30_000  # full fade time after last alert
THREAT_PULSE_TICK_MS = 33  # ~30 fps pulse
THREAT_PULSE_DURATION_MS = 600  # one pulse cycle

# Replay strip (PR10) — small ring buffer of recent capture pixmaps.
# 6 cells × 800ms throttle = ~5s of recent history.
REPLAY_BUFFER_SIZE = 6
REPLAY_THROTTLE_MS = 800

# Per-character accent palette (PR8). Shared by both frames + chips so
# the same character renders in the same color across the preview grid
# and the status dock. Palette is fixed-length; deterministic hash maps
# names to indices.
CHARACTER_ACCENT_COLORS: list[tuple[int, int, int]] = [
    (255, 100, 100),
    (100, 255, 100),
    (100, 150, 255),
    (255, 200, 80),
    (220, 120, 220),
    (100, 220, 220),
    (255, 165, 60),
    (170, 130, 255),
]


def character_accent_color(name: str) -> QColor:
    """Deterministic accent color for a character name.

    Used by both WindowPreviewWidget (frame border) and CharacterChip
    (avatar fill) so visual identity is consistent across surfaces.

    Uses MD5 (not Python's built-in hash()) for cross-process determinism:
    PYTHONHASHSEED is randomized by default, so hash() varies between
    app launches, which would make the same character render in a
    different color every session. MD5 is content-addressed and stable.
    """
    import hashlib

    digest = hashlib.md5(name.encode("utf-8"), usedforsecurity=False).digest()
    index = digest[0] % len(CHARACTER_ACCENT_COLORS)
    r, g, b = CHARACTER_ACCENT_COLORS[index]
    return QColor(r, g, b)


# Module-level constant: avoids re-creating the dict on every pil_to_qimage call
_FORMAT_MAP = {
    "RGB": (3, QImage.Format.Format_RGB888),
    "RGBX": (4, QImage.Format.Format_RGBX8888),
    "RGBA": (4, QImage.Format.Format_RGBA8888),
    "L": (1, QImage.Format.Format_Grayscale8),
}


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


def get_pattern_positions(pattern: str, count: int, grid_cols: int = 4) -> list[tuple[int, int]]:
    """Get grid positions for a layout pattern.

    Args:
        pattern: Layout pattern name
        count: Number of items to arrange
        grid_cols: Number of columns for default grid (used for fallback)

    Returns:
        list of (row, col) tuples for each item position
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
        self.tiles: dict[str, DraggableTile] = {}
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

    def get_arrangement(self) -> dict[str, tuple[int, int]]:
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
        self.last_apply_results: dict[str, bool] = {}

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
        stacked_use_grid_size: bool = True,
    ) -> bool:
        results: dict[str, bool] = {}
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
                        results[window_id] = self._move_window(window_id, x, y, cell_width, cell_height)
                    else:
                        results[window_id] = self._move_window_position_only(window_id, x, y)
            else:
                for char_name, (row, col) in arrangement.items():
                    if char_name not in window_map:
                        continue

                    window_id = window_map[char_name]
                    x = screen.x + spacing + col * (cell_width + spacing)
                    y = screen.y + spacing + row * (cell_height + spacing)
                    results[window_id] = self._move_window(window_id, x, y, cell_width, cell_height)

            self.last_apply_results = results
            ok = all(results.values()) if results else True
            self.logger.info(f"Applied arrangement to {len(window_map)} windows ({sum(results.values())}/{len(results)} succeeded)")
            return ok

        except (AttributeError, OSError, RuntimeError, ValueError) as e:
            self.logger.error(f"Failed to apply arrangement: {e}")
            self.last_apply_results = results
            return False

    def _move_window(self, window_id: str, x: int, y: int, w: int, h: int) -> bool:
        """Move and resize a window via platform abstraction layer."""
        from argus_overview.platform import get_window_manager

        try:
            wm = get_window_manager()
            wm.move_window(window_id, x, y, w, h)
            return True
        except (OSError, RuntimeError) as e:
            self.logger.warning(f"Failed to move window {window_id}: {e}")
            return False

    def _move_window_position_only(self, window_id: str, x: int, y: int) -> bool:
        """Move a window without resizing (w=0, h=0 convention)."""
        from argus_overview.platform import get_window_manager

        try:
            wm = get_window_manager()
            wm.move_window(window_id, x, y, 0, 0)
            return True
        except (OSError, RuntimeError) as e:
            self.logger.warning(f"Failed to move window {window_id}: {e}")
            return False


def pil_to_qimage(pil_image: Image.Image, raw_data: bytes | None = None) -> QImage:
    """
    Convert PIL Image to QImage

    Args:
        pil_image: PIL Image object
        raw_data: Optional pre-computed tobytes() to avoid a redundant copy

    Returns:
        QImage: Converted image, or None if input is None
    """
    if pil_image is None:
        return None

    mode = pil_image.mode
    if mode in _FORMAT_MAP:
        bpp, fmt = _FORMAT_MAP[mode]
        data = raw_data if raw_data is not None else pil_image.tobytes()
        return QImage(
            data,
            pil_image.width,
            pil_image.height,
            bpp * pil_image.width,
            fmt,
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
    focus_requested = Signal(str)  # window_id — PR3 spotlight toggle
    retry_requested = Signal(str)  # window_id — PR2 retry capture

    def __init__(
        self,
        window_id: str,
        character_name: str,
        capture_system,
        settings_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        # PR4: accept focus for keyboard navigation (Tab into grid, arrows
        # between frames, Enter/Space to activate, Esc to exit spotlight).
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.logger = logging.getLogger(__name__)
        self.window_id = window_id
        self.character_name = character_name
        self.capture_system = capture_system
        self.settings_manager = settings_manager

        # State
        self.current_pixmap: QPixmap | None = None
        self.zoom_factor = 0.3  # 30% scale

        # v2.2 State
        self.custom_label: str | None = None
        self.session_start: datetime = datetime.now()
        self.last_activity: datetime = datetime.now()
        self.is_focused: bool = False
        self._is_hovered: bool = False
        self._positions_locked: bool = False

        # Frame fingerprint cache — skip identical frames
        self._last_frame_hash: int | None = None

        # PR1: Capture health state — tracks when we last received a frame and
        # whether it was deduplicated, so the UI can show LIVE / STATIC /
        # STALE / ERROR explicitly rather than leaving the operator to guess.
        self._last_frame_received_at: float = 0.0
        self._last_frame_was_dedup: bool = False
        self._capture_error_count: int = 0

        # v2.2 Settings (from settings_manager or defaults)
        self._opacity_on_hover = 0.3
        self._zoom_on_hover = 1.5
        self._show_activity_indicator = True
        self._show_session_timer = False
        self._load_settings()

        # PR4/PR5: known current system for this frame's character.
        # Pushed by WindowManager.set_character_system; consumed by
        # WindowManager.apply_threat_state for smart fan-out.
        self._character_system: str | None = None

        # PR8: per-character accent color, shared with the chip.
        self._accent_color: QColor = character_accent_color(character_name)

        # Intel threat state (PR1: intel-aware preview borders)
        self._threat_level: ThreatLevel | None = None
        self._threat_system: str | None = None
        # PR9: jumps from this character to the alert system. None for
        # same-system / unknown; positive int renders as "+Nj" near the
        # top-left of the threat border.
        self._threat_distance: int | None = None
        # Decay alpha drives the inset border; ranges 0.0 (off) to 1.0 (full)
        self._threat_alpha: float = 0.0
        self._threat_decay_steps: int = max(1, THREAT_DECAY_DURATION_MS // THREAT_DECAY_TICK_MS)
        self._threat_decay_timer = QTimer(self)
        self._threat_decay_timer.timeout.connect(self._tick_threat_decay)

        # PR1: timestamp when the current threat state was set, so paintEvent
        # can render report age and the tooltip can show exact observation time.
        self._threat_set_at: float = 0.0
        # PR1: has ANY intel report ever been received for this character?
        # False until the first set_threat_state call with a non-None level.
        # When False and threat_level is None, the frame shows Unknown instead
        # of the accent "clear" border.
        self._intel_report_received: bool = False

        # Pulse animation (oneshot on transition into danger/critical)
        self._pulse_phase: float = 0.0  # 1.0 -> 0.0 over PULSE_DURATION
        self._pulse_steps: int = max(1, THREAT_PULSE_DURATION_MS // THREAT_PULSE_TICK_MS)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._tick_pulse)

        # Legacy flash_border state (retains existing border_flash_requested wiring)
        self._flash_color: QColor | None = None
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._clear_flash)

        # PR1: periodic timer to evaluate capture health and repaint the badge.
        # Fires every 500 ms so the STALE age text updates smoothly without
        # burning CPU on the UI thread.
        self._capture_health_timer = QTimer(self)
        self._capture_health_timer.timeout.connect(self._tick_capture_health)
        self._capture_health_timer.start(500)

        # PR10: replay strip — bounded ring buffer of recent frame pixmaps,
        # sampled at most once per REPLAY_THROTTLE_MS so the buffer covers
        # ~5 seconds of capture even at high refresh rates.
        from collections import deque

        self._replay_buffer: deque = deque(maxlen=REPLAY_BUFFER_SIZE)
        self._replay_last_sample_ms: int = 0
        self._replay_strip = None  # type: ignore[var-annotated]
        self._replay_view_index: int | None = None  # None = live; int = buffered

        # Setup UI
        self.setMinimumSize(200, 150)
        self.setMaximumSize(600, 450)
        self._update_tooltip()
        self._update_accessible_name()

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

        # Session timer label (v2.2) — PR4: floating child so it does not
        # push the preview image up. Positioned at bottom-left in resizeEvent.
        self.timer_label = QLabel("", self)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.timer_label.setStyleSheet("color: #888; font-size: 9px; background: transparent;")
        self.timer_label.setVisible(self._show_session_timer)

        # Session timer update (every minute)
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)
        if self._show_session_timer:
            self.session_timer.start(60000)  # Update every minute

        # Opacity effect for hover (and PR3 spotlight dim state)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity_effect)

        # PR3 — focus/spotlight mode state.
        # mode is one of: None (normal), "focused" (this widget is the
        # spotlight target), "dimmed" (another widget has spotlight).
        self._spotlight_mode: str | None = None
        # Cached size constraints so we can restore them when leaving focus.
        self._normal_min_size: QSize = self.minimumSize()
        self._normal_max_size: QSize = self.maximumSize()

        # PR10: restore the replay-strip toggle from settings if it was
        # previously enabled for this character.
        if self.settings_manager is not None:
            try:
                store = self.settings_manager.get("replay_strip_enabled", {}) or {}
                if isinstance(store, dict) and store.get(self.character_name):
                    self.enable_replay_strip(True)
            except (AttributeError, TypeError):
                pass

        # PR2: retry button overlay — visible when capture is ERROR or STALE.
        # Created as a floating child widget (not in the layout) so it can be
        # positioned in the top-right corner without affecting flow layout.
        self._retry_button = QPushButton("↻", self)
        self._retry_button.setFixedSize(28, 28)
        self._retry_button.setToolTip("Retry capture")
        self._retry_button.setVisible(False)
        try:
            self._retry_button.clicked.connect(self._on_retry_clicked)
        except RuntimeError:
            pass

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
        """Update tooltip text (PR1: enriched with state, age, and actions)."""
        char_name = getattr(self, "character_name", "")
        tooltip = f"{char_name}"
        custom_label = getattr(self, "custom_label", None)
        if custom_label:
            tooltip = f"{custom_label}\n{char_name}"

        # PR1: system and capture health (use getattr for test resilience)
        system = getattr(self, "_character_system", None)
        if system:
            tooltip += f"\nSystem: {system}"
        health = self._capture_health_label()
        if health:
            tooltip += f"\nCapture: {health}"

        # PR1: threat state with age and source
        threat_level = getattr(self, "_threat_level", None)
        threat_alpha = getattr(self, "_threat_alpha", 0.0)
        if threat_level is not None and threat_alpha > 0.0:
            age = ""
            threat_set_at = getattr(self, "_threat_set_at", 0.0)
            if threat_set_at > 0.0:
                secs = int(time.monotonic() - threat_set_at)
                age = f" · {secs}s ago"
            src = getattr(self, "_threat_system", None) or "unknown"
            tooltip += f"\nThreat: {threat_level.value}{age} · source: {src}"
        elif not getattr(self, "_intel_report_received", False):
            tooltip += "\nThreat: Unknown (no intel data received)"

        # PR4: session timer in tooltip when enabled
        if getattr(self, "_show_session_timer", False):
            elapsed = datetime.now() - self.session_start
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            timer_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            tooltip += f"\nSession: {timer_text}"

        window_id = getattr(self, "window_id", "")
        tooltip += f"\nWindow ID: {window_id}"
        # PR1: focus-mode affordance
        tooltip += "\nDouble-click to spotlight · Esc to exit"
        tooltip += "\nClick to activate · Right-click for menu"
        try:
            self.setToolTip(tooltip)
        except RuntimeError:
            pass

    def update_frame(self, image: Image.Image):
        """
        Update preview with new captured frame

        Args:
            image: PIL Image
        """
        # PR1: record frame arrival time for capture-health badge.
        self._last_frame_received_at = time.monotonic()
        try:
            # Frame fingerprint — sample a small crop to detect duplicates
            # without copying the full image. Only call tobytes() on the full
            # image after we know the frame has changed.
            sample_h = min(32, image.height)
            sample_data = image.crop((0, 0, image.width, sample_h)).tobytes()
            frame_hash = hash(sample_data)
            if frame_hash == self._last_frame_hash:
                self._last_frame_was_dedup = True
                image.close()
                return  # Frame unchanged, skip conversion pipeline
            self._last_frame_was_dedup = False
            self._capture_error_count = 0  # PR1: reset error streak on success
            self._last_frame_hash = frame_hash

            # Full tobytes() only for frames that actually changed
            raw_data = image.tobytes()
            qimage = pil_to_qimage(image, raw_data)
            image.close()  # Release PIL image memory immediately
            if qimage is None:
                return  # Skip frame if capture failed

            # Convert to pixmap — release the previous one first
            self.current_pixmap = QPixmap.fromImage(qimage)
            del qimage  # Release intermediate QImage memory

            # PR10: sample into the replay ring buffer at most once per
            # REPLAY_THROTTLE_MS so the buffer covers ~5s regardless of
            # capture rate. Only sample the unscaled pixmap; the strip
            # rescales itself for display.
            self._sample_replay_buffer(self.current_pixmap)

            # If the user is currently scrubbing through the strip, hold
            # the buffered view — don't overwrite it with the live frame.
            if self._replay_view_index is not None:
                return

            # Scale to fit widget while maintaining aspect ratio
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

            self.image_label.setPixmap(scaled_pixmap)

        except (ValueError, AttributeError, RuntimeError) as e:
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

    def set_custom_label(self, label: str | None):
        """
        Set a custom label for this thumbnail

        Args:
            label: Custom label text or None to clear
        """
        self.custom_label = label
        self.info_label.setText(self._get_display_name())
        self._update_tooltip()
        self._update_accessible_name()
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

    def set_character_system(self, system: str | None) -> None:
        """Record the current system for this frame's character (PR5)."""
        self._character_system = system
        self._update_tooltip()
        self._update_accessible_name()

    def get_character_system(self) -> str | None:
        return self._character_system

    def _update_accessible_name(self) -> None:
        """PR1: expose character, system, and threat state to assistive tech."""
        char_name = getattr(self, "character_name", "")
        parts = [f"Preview of {char_name}"]
        system = getattr(self, "_character_system", None)
        if system:
            parts.append(f"system {system}")
        threat_level = getattr(self, "_threat_level", None)
        threat_alpha = getattr(self, "_threat_alpha", 0.0)
        if threat_level is not None and threat_alpha > 0.0:
            parts.append(f"threat {threat_level.value}")
        elif not getattr(self, "_intel_report_received", False):
            parts.append("threat unknown")
        else:
            parts.append("no active threat")
        try:
            self.setAccessibleName(". ".join(parts))
        except RuntimeError:
            # Defensive: tests that bypass __init__ create half-initialised
            # Qt objects; accessible name is non-critical, so swallow.
            pass

    def set_threat_state(
        self,
        level: ThreatLevel | None,
        system: str | None = None,
        initial_alpha: float = 1.0,
        distance: int | None = None,
    ) -> None:
        """
        Update the intel threat state for this preview frame.

        Args:
            level: Threat level. None or CLEAR clears the border.
            system: System name the threat refers to (kept for tooltip + dock).
            initial_alpha: Starting alpha [0.0, 1.0] for the border. Defaults
                to 1.0 (full intensity for same-system alerts). Lower values
                are used by WindowManager when fanning to characters in
                adjacent systems via the jumps-from filter (PR6).
            distance: Jumps from this character to the alert system.
                None for same-system / unknown. Positive ints render as a
                "+Nj" badge near the top-left of the frame (PR9).
        """
        prev_level = self._threat_level

        # PR1: any non-None report (including CLEAR) proves the intel pipeline
        # has delivered data for this character. Once set, the frame is no longer
        # in the "Unknown" state.
        if level is not None:
            self._intel_report_received = True

        if level is None or level == ThreatLevel.CLEAR:
            self._threat_level = None
            self._threat_system = None
            self._threat_alpha = 0.0
            self._threat_distance = None
            self._threat_decay_timer.stop()
            self._update_tooltip()
            self.update()
            return

        # PR1: record when this report was observed so the UI can show age.
        self._threat_set_at = time.monotonic()
        self._threat_level = level
        self._threat_system = system
        self._threat_alpha = max(0.0, min(1.0, initial_alpha))
        self._threat_distance = distance if distance and distance > 0 else None

        # Pulse on upgrade into danger/critical (only at full-ish intensity —
        # don't pulse for distant adjacent-system alerts).
        upgraded = prev_level is None or THREAT_LEVEL_RANK.get(
            prev_level, 0
        ) < THREAT_LEVEL_RANK.get(level, 0)
        if (
            upgraded
            and level in (ThreatLevel.DANGER, ThreatLevel.CRITICAL)
            and initial_alpha >= 0.9
        ):
            self._start_pulse()

        # Restart decay timer
        self._threat_decay_timer.start(THREAT_DECAY_TICK_MS)
        self._update_tooltip()
        self._update_accessible_name()
        self.update()

    def _tick_threat_decay(self) -> None:
        """Linear decay of the threat-border alpha."""
        if self._threat_alpha <= 0.0:
            self._threat_decay_timer.stop()
            return
        self._threat_alpha = max(0.0, self._threat_alpha - 1.0 / self._threat_decay_steps)
        if self._threat_alpha <= 0.0:
            self._threat_level = None
            self._threat_system = None
            self._threat_distance = None
            self._threat_decay_timer.stop()
        self.update()

    def _start_pulse(self) -> None:
        """Trigger a single pulse cycle on upgrade to danger/critical."""
        self._pulse_phase = 1.0
        self._pulse_timer.start(THREAT_PULSE_TICK_MS)

    def _tick_pulse(self) -> None:
        """Decrement pulse phase toward 0; stop when done."""
        self._pulse_phase = max(0.0, self._pulse_phase - 1.0 / self._pulse_steps)
        if self._pulse_phase <= 0.0:
            self._pulse_timer.stop()
        self.update()

    def _tick_capture_health(self) -> None:
        """PR1: Periodic health evaluation. Triggers repaint so the badge
        text (e.g. 'STALE · 7s') stays current without requiring a frame.

        PR2: toggles the retry button visibility when the frame enters ERROR
        or STALE so the operator can recover without digging into a menu.
        """
        self.update()
        btn = getattr(self, "_retry_button", None)
        if btn is None:
            return
        try:
            health = self._capture_health_label()
            show = health in ("ERROR",) or health.startswith("STALE")
            btn.setVisible(show)
            if show:
                btn.move(self.width() - btn.width() - 4, 4)
        except RuntimeError:
            pass

    def _capture_health_label(self) -> str:
        """PR1: Human-readable capture state for the bottom-right badge.

        Returns empty string when the widget should not display a badge
        (e.g. not yet initialized and not visible).
        """
        try:
            if not self.isVisible():
                return "PAUSED"
        except RuntimeError:
            return ""  # Defensive: mock widgets in tests
        if getattr(self, "_capture_error_count", 0) > 0:
            return "ERROR"
        last_frame_at = getattr(self, "_last_frame_received_at", 0.0)
        if last_frame_at == 0.0:
            return "INITIALIZING"
        elapsed = time.monotonic() - last_frame_at
        if elapsed > 2.0:
            return f"STALE · {int(elapsed)}s"
        if getattr(self, "_last_frame_was_dedup", False):
            return "STATIC"
        return "LIVE"

    def _capture_health_color(self) -> QColor:
        """PR1: Subtle color for the capture-health badge text."""
        label = self._capture_health_label()
        if label.startswith("LIVE"):
            return QColor(68, 255, 68, 220)   # green
        if label == "STATIC":
            return QColor(204, 204, 204, 220)  # white-gray
        if label.startswith("STALE"):
            return QColor(255, 204, 0, 220)    # yellow
        if label == "ERROR":
            return QColor(255, 68, 68, 220)    # red
        return QColor(136, 136, 136, 180)    # gray (INIT/PAUSED)

    def set_spotlight(self, mode: str | None) -> None:
        """
        Apply or clear focus/spotlight presentation.

        Args:
            mode: 'focused' to upscale + full opacity (this widget is the
                spotlight target), 'dimmed' to fade and desaturate (another
                widget owns the spotlight), None to return to normal.
        """
        if mode not in (None, "focused", "dimmed"):
            raise ValueError(f"Invalid spotlight mode: {mode!r}")
        self._spotlight_mode = mode

        if mode == "focused":
            # Allow growth beyond the normal max so the focused widget
            # actually uses the freed space when others are minimized/hidden.
            self.setMinimumSize(QSize(360, 270))
            self.setMaximumSize(QSize(16777215, 16777215))  # QWIDGETSIZE_MAX
            self.opacity_effect.setOpacity(1.0)
        elif mode == "dimmed":
            self.setMinimumSize(self._normal_min_size)
            self.setMaximumSize(self._normal_max_size)
            self.opacity_effect.setOpacity(0.25)
        else:  # None — restore baseline
            self.setMinimumSize(self._normal_min_size)
            self.setMaximumSize(self._normal_max_size)
            # Hover state may want partial opacity; reset to full on exit.
            self.opacity_effect.setOpacity(self._opacity_on_hover if self._is_hovered else 1.0)
        self.update()

    def flash_border(self, color: str, duration_ms: int) -> None:
        """
        Legacy color/duration border flash hook used by border_flash_requested.

        Kept independent of set_threat_state so callers without IntelReport
        context still get visual feedback.
        """
        self._flash_color = QColor(color)
        self._flash_timer.start(max(0, int(duration_ms)))
        self.update()

    def _clear_flash(self) -> None:
        self._flash_color = None
        self.update()

    # ----- PR10 replay strip ------------------------------------------------
    def _sample_replay_buffer(self, pixmap: QPixmap) -> None:
        """Throttle-sample a captured pixmap into the ring buffer."""
        if pixmap is None or pixmap.isNull():
            return
        now_ms = int(time.monotonic() * 1000)
        if now_ms - self._replay_last_sample_ms < REPLAY_THROTTLE_MS:
            return
        # Store an immutable copy at modest size; full-res pixmaps would
        # blow up memory across many widgets. 240×180 keeps it ~170KB max.
        thumb = pixmap.scaled(
            240,
            180,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self._replay_buffer.append(thumb)
        self._replay_last_sample_ms = now_ms
        if self._replay_strip is not None:
            try:
                self._replay_strip.set_frames(list(self._replay_buffer))
            except RuntimeError:
                self._replay_strip = None

    def is_replay_strip_enabled(self) -> bool:
        return self._replay_strip is not None

    def enable_replay_strip(self, enabled: bool) -> None:
        """Show or hide the replay strip below the main image."""
        if enabled and self._replay_strip is None:
            from argus_overview.ui.replay_strip import ReplayStrip

            self._replay_strip = ReplayStrip(parent=self)
            self._replay_strip.frame_hovered.connect(self._on_replay_frame_hovered)
            # Append below the existing image_label / info_label / timer.
            self.layout().addWidget(self._replay_strip)
            self._replay_strip.set_frames(list(self._replay_buffer))
        elif not enabled and self._replay_strip is not None:
            try:
                self._replay_strip.frame_hovered.disconnect(self._on_replay_frame_hovered)
            except (RuntimeError, TypeError):
                pass
            self.layout().removeWidget(self._replay_strip)
            self._replay_strip.deleteLater()
            self._replay_strip = None
            # Drop any held buffered view.
            self._replay_view_index = None

    def _on_retry_clicked(self) -> None:
        """PR2: emit retry_requested so MainTab / WindowManager can restart
        capture for this window."""
        self._capture_error_count = 0
        self._last_frame_received_at = time.monotonic()
        self.retry_requested.emit(self.window_id)

    def resizeEvent(self, event) -> None:
        """PR2: keep the retry button pinned to the top-right corner.
        PR4: keep the session timer label at bottom-left."""
        super().resizeEvent(event)
        btn = getattr(self, "_retry_button", None)
        if btn is not None:
            try:
                btn.move(self.width() - btn.width() - 4, 4)
            except RuntimeError:
                pass
        lbl = getattr(self, "timer_label", None)
        if lbl is not None:
            try:
                lbl.move(4, self.height() - lbl.height() - 2)
            except RuntimeError:
                pass

    def _on_replay_frame_hovered(self, idx: int) -> None:
        """Swap the main image label between live capture and a buffered frame."""
        if idx < 0 or idx >= len(self._replay_buffer):
            self._replay_view_index = None
            # Restore the live capture if we have one cached.
            if self.current_pixmap is not None and not self.current_pixmap.isNull():
                scaled = self.current_pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation,
                )
                self.image_label.setPixmap(scaled)
            return
        self._replay_view_index = idx
        buffered = self._replay_buffer[idx]
        if buffered is None or buffered.isNull():
            return
        scaled = buffered.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.image_label.setPixmap(scaled)

    def paintEvent(self, event):
        """Custom paint: accent, threat border, focus dot, lock icon, flash."""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 0. Per-character accent border (PR8) — only visible when no
        # threat or legacy-flash overlay is active. Gives instant visual
        # identity at small grid sizes and matches the chip avatar color.
        # PR1: if no intel report has ever been received, show Unknown
        # (dashed gray border + question mark) instead of the accent "clear".
        if self._threat_level is None and self._flash_color is None:
            if not self._intel_report_received:
                # Unknown — dashed gray border with question mark
                pen = QPen(QColor(128, 128, 128, 180))
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 4, 4)
                painter.setPen(QPen(QColor(128, 128, 128, 200)))
                painter.drawText(6, 14, "?")
            else:
                pen = QPen(self._accent_color)
                pen.setWidth(2)
                painter.setPen(pen)
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 4, 4)

        # 1. Threat-tint border (PR1) — drawn first so dot/lock paint over it
        if self._threat_level is not None and self._threat_alpha > 0.0:
            r, g, b = THREAT_BORDER_COLORS.get(self._threat_level, (255, 255, 255))
            base_alpha = int(220 * self._threat_alpha)
            # Pulse adds an extra alpha kick for the first ~600ms after upgrade
            pulse_boost = int(35 * self._pulse_phase)
            alpha = max(0, min(255, base_alpha + pulse_boost))
            border_color = QColor(r, g, b, alpha)
            pen_width = 3 + int(2 * self._pulse_phase)  # 3px → 5px during pulse
            pen = QPen(border_color)
            pen.setWidth(pen_width)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            inset = pen_width // 2 + 1
            painter.drawRoundedRect(
                inset,
                inset,
                self.width() - 2 * inset,
                self.height() - 2 * inset,
                4,
                4,
            )

            # PR2: system-name pill — shows the affected system and optional
            # jump distance at the top-left so the operator never has to look
            # away from the preview grid to know which system is hostile.
            if self._threat_system:
                from PySide6.QtGui import QFont

                pill_parts = [self._threat_system]
                if self._threat_distance and self._threat_distance > 0:
                    pill_parts.append(f"+{self._threat_distance}j")
                pill_text = " · ".join(pill_parts)

                pill_font = QFont(painter.font())
                pill_font.setPointSize(8)
                pill_font.setBold(True)
                painter.setFont(pill_font)
                metrics = painter.fontMetrics()
                text_w = metrics.horizontalAdvance(pill_text)
                pad = 4
                pill_w = text_w + pad * 2
                pill_h = metrics.height() + pad
                # Position at top-left, inset from the threat border
                pill_x = 6
                pill_y = 6
                # Semi-transparent dark background so the pill is legible
                # regardless of the underlying preview image
                bg = QColor(10, 10, 15, max(160, alpha))
                painter.setBrush(QBrush(bg))
                painter.setPen(QPen(Qt.PenStyle.NoPen))
                painter.drawRoundedRect(pill_x, pill_y, pill_w, pill_h, 3, 3)
                # Foreground in threat color, opaque
                text_color = QColor(r, g, b, max(220, alpha))
                painter.setPen(QPen(text_color))
                painter.drawText(
                    pill_x + pad,
                    pill_y + pad + metrics.ascent() - 2,
                    pill_text,
                )

            # PR1: report age — small text at bottom-center when the threat
            # is decaying (alpha < 0.9) so the operator knows how old the
            # alert is without hovering for the tooltip.
            if self._threat_alpha < 0.9 and self._threat_set_at > 0.0:
                age_secs = int(time.monotonic() - self._threat_set_at)
                age_text = f"{age_secs}s"
                from PySide6.QtGui import QFont

                age_font = QFont(painter.font())
                age_font.setPointSize(8)
                painter.setFont(age_font)
                age_color = QColor(r, g, b, max(160, alpha))
                painter.setPen(QPen(age_color))
                metrics = painter.fontMetrics()
                text_w = metrics.horizontalAdvance(age_text)
                text_x = (self.width() - text_w) // 2
                text_y = self.height() - 6
                painter.drawText(text_x, text_y, age_text)

        # 2. Legacy flash overlay (compat with border_flash_requested)
        if self._flash_color is not None:
            pen = QPen(self._flash_color)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 4, 4)

        # 3. Activity indicator (v2.2)
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

            # PR4: text label next to dot for colorblind / low-brightness users
            label_text = activity.capitalize()
            text_color = QColor(indicator_color)
            text_color.setAlpha(255)
            painter.setPen(QPen(text_color))
            from PySide6.QtGui import QFont

            label_font = QFont(painter.font())
            label_font.setPointSize(7)
            label_font.setBold(True)
            painter.setFont(label_font)
            metrics = painter.fontMetrics()
            text_w = metrics.horizontalAdvance(label_text)
            text_x = self.width() - 18 - text_w
            text_y = 6 + metrics.ascent()
            painter.drawText(text_x, text_y, label_text)

        # 4. Lock icon if positions are locked
        if self._positions_locked:
            painter.setPen(QPen(QColor(200, 200, 200, 180)))
            painter.drawText(6, 14, "🔒")

        # PR1: Focus-mode affordance — small crosshair icon visible on hover
        # so users can discover the double-click spotlight feature.
        if self._is_hovered and self._spotlight_mode is None:
            painter.setPen(QPen(QColor(200, 200, 200, 160)))
            painter.drawText(self.width() - 22, self.height() - 10, "🔍")

        # PR1: Capture health badge — bottom-right, explicit text label so
        # the operator can distinguish LIVE / STATIC / STALE / ERROR at a
        # glance without inferring it from pixel motion.
        health_text = self._capture_health_label()
        if health_text:
            from PySide6.QtGui import QFont

            badge_font = QFont(painter.font())
            badge_font.setPointSize(9)
            painter.setFont(badge_font)
            metrics = painter.fontMetrics()
            text_w = metrics.horizontalAdvance(health_text)
            pad = 4
            badge_w = text_w + pad * 2
            badge_h = metrics.height() + pad
            badge_x = self.width() - badge_w - 4
            badge_y = self.height() - badge_h - 4
            # Semi-transparent dark background so the badge is legible
            # over any preview content.
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.setBrush(QBrush(QColor(0, 0, 0, 160)))
            painter.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, 3, 3)
            painter.setPen(QPen(self._capture_health_color()))
            painter.drawText(
                badge_x + pad,
                badge_y + metrics.ascent() + (badge_h - metrics.height()) // 2,
                health_text,
            )

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

    def mouseDoubleClickEvent(self, event):
        """PR3: double-click toggles spotlight focus mode for this window."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.focus_requested.emit(self.window_id)
            event.accept()
            # Cancel the pending single-click activation that the
            # preceding press recorded; otherwise the window still
            # activates beneath the focus toggle.
            self._drag_start_pos = None
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """PR4: keyboard navigation — Enter/Space activate, Esc exits spotlight."""
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.window_activated.emit(self.window_id)
            event.accept()
            return
        if key == Qt.Key.Key_Escape:
            if self._spotlight_mode is not None:
                self.focus_requested.emit(self.window_id)  # toggle off
                event.accept()
                return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Handle right-click context menu (v2.3 - uses ActionRegistry)"""
        # Build context menu from ActionRegistry
        context_builder = ContextMenuBuilder()

        # Handler map for context actions. toggle_replay_strip was added
        # to the registry as a tier-3 WINDOW_CONTEXT action; it joins the
        # other handlers here.
        handlers = {
            "focus_window": lambda: self.window_activated.emit(self.window_id),
            "minimize_window": self._minimize_window,
            "close_window": self._close_window,
            "set_label": self._show_label_dialog,
            "toggle_replay_strip": self._toggle_replay_strip,
            "retry_capture": self._on_retry_clicked,
            "remove_from_preview": lambda: self.window_removed.emit(self.window_id),
        }

        menu = context_builder.build_window_context_menu(
            handlers=handlers,
            zoom_handler=self._set_zoom,
            current_zoom=self.zoom_factor,
            parent=self,
        )

        menu.exec(event.globalPos())

    def _toggle_replay_strip(self) -> None:
        """Flip the replay strip on/off and persist the choice per character."""
        new_state = not self.is_replay_strip_enabled()
        self.enable_replay_strip(new_state)
        if self.settings_manager is not None:
            try:
                store = self.settings_manager.get("replay_strip_enabled", {}) or {}
                if not isinstance(store, dict):
                    store = {}
                if new_state:
                    store[self.character_name] = True
                else:
                    store.pop(self.character_name, None)
                self.settings_manager.set("replay_strip_enabled", store)
            except (AttributeError, TypeError) as e:
                self.logger.debug(f"Failed to persist replay-strip toggle: {e}")

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
            except (OSError, subprocess.SubprocessError) as e:
                self.logger.warning(f"Failed to close window after retries: {e}")

    def _minimize_window(self):
        """Minimize the window"""
        try:
            result = self.capture_system.minimize_window(self.window_id)
            if result:
                self.logger.info(f"Minimized window: {self.window_id}")
            else:
                self.logger.warning(f"Failed to minimize window: {self.window_id}")
        except (OSError, RuntimeError) as e:
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
        self.preview_frames: dict[str, WindowPreviewWidget] = {}
        # PR4: per-character current system, fed by CharacterLocationTracker.
        # Survives window add/remove cycles. Used for chip system labels and
        # (in a follow-up PR) smart per-character threat fan-out.
        self._character_systems: dict[str, str] = {}
        # PR6: optional jump calculator + max-jumps threshold for the
        # adjacency-aware fan-out. Default max_jumps=0 preserves the PR5
        # exact-match-only filter when no calculator is wired up.
        self._jump_calculator = None  # type: ignore[var-annotated]
        self._jump_max: int = 0
        self.pending_requests: dict[
            str, tuple[str, float]
        ] = {}  # request_id -> (window_id, timestamp)
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

    def retry_window_capture(self, window_id: str) -> None:
        """PR2: attempt an immediate re-capture for a single window."""
        if window_id not in self.preview_frames:
            return
        frame = self.preview_frames[window_id]
        frame._capture_error_count = 0
        frame._last_frame_received_at = time.monotonic()
        try:
            request_id = self.capture_system.capture_window_async(window_id)
            if request_id:
                with self._pending_lock:
                    self.pending_requests[request_id] = (window_id, time.monotonic())
                self.logger.info(f"Retry capture requested for {window_id}")
        except (OSError, RuntimeError) as e:
            self.logger.error(f"Retry capture failed for {window_id}: {e}")

    def add_window(self, window_id: str, character_name: str) -> WindowPreviewWidget | None:
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
            window_id,
            character_name,
            self.capture_system,
            settings_manager=self.settings_manager,
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

    def set_character_system(self, character_name: str, system: str | None) -> None:
        """
        Record the current system for a character.

        Stored on a per-character map that survives across window add/remove
        cycles, AND pushed to every active frame for that character so the
        smart fan-out (apply_threat_state) can filter by frame state alone.
        """
        if system is None:
            self._character_systems.pop(character_name, None)
        else:
            self._character_systems[character_name] = system

        # Push to active frames whose character matches.
        for frame in list(self.preview_frames.values()):
            try:
                if getattr(frame, "character_name", None) == character_name:
                    frame.set_character_system(system)
            except RuntimeError:
                continue

    def get_character_system(self, character_name: str) -> str | None:
        return self._character_systems.get(character_name)

    def set_jump_calculator(self, calculator, max_jumps: int = 1) -> None:
        """
        Wire an adjacency calculator for the jumps-from threat filter (PR6).

        Args:
            calculator: A JumpCalculator (or None to disable adjacency).
            max_jumps: Maximum jump distance to consider "near"; 0 disables
                adjacency tinting (exact-match-only). Default 1.
        """
        self._jump_calculator = calculator
        self._jump_max = max(0, int(max_jumps))

    def apply_threat_state(self, level: ThreatLevel | None, system: str | None = None) -> int:
        """
        Fan an intel threat state out to preview frames, filtered by system.

        Filter rules:
          1. CLEAR / None level → flush every frame regardless of system.
          2. system is None / empty → fan to all (legacy fallback).
          3. Otherwise → resolve_tint() decides per-frame: same-system at
             full alpha, adjacent within max_jumps at falloff alpha,
             beyond threshold skipped, unknown character system tinted at
             full alpha (graceful upgrade).

        Returns count of frames actually updated.
        """
        from argus_overview.intel.threat_filter import resolve_tint

        # Rule 1 + 2: explicit-flush branches
        if level is None or level == ThreatLevel.CLEAR or not system:
            return self._fan_to_all(level, system)

        count = 0
        for frame in list(self.preview_frames.values()):
            try:
                char_name = getattr(frame, "character_name", None)
                known = self._character_systems.get(char_name) if char_name else None
                should_apply, alpha = resolve_tint(
                    known_system=known,
                    alert_system=system,
                    jump_calculator=self._jump_calculator,
                    max_jumps=self._jump_max,
                )
                if not should_apply:
                    continue
                # PR9: surface the jump distance for the +Nj frame badge.
                # Mirrors StatusDock.set_threat_state behavior (PR7).
                distance: int | None = None
                if (
                    alpha < 1.0
                    and known
                    and self._jump_calculator is not None
                    and known.lower() != system.lower()
                ):
                    try:
                        distance = self._jump_calculator.distance(known, system)
                    except (AttributeError, TypeError, ValueError):
                        distance = None
                frame.set_threat_state(level, system, initial_alpha=alpha, distance=distance)
                count += 1
            except RuntimeError:
                continue
        return count

    def _fan_to_all(self, level: ThreatLevel | None, system: str | None) -> int:
        count = 0
        for frame in list(self.preview_frames.values()):
            try:
                frame.set_threat_state(level, system)
                count += 1
            except RuntimeError:
                continue
        return count

    def _capture_cycle(self):
        """
        Capture cycle - called by timer

        Requests captures for all visible frames, then polls for results.
        Skips windows that already have pending capture requests.
        """
        now = time.monotonic()

        # Build set of windows with pending requests; prune stale entries
        with self._pending_lock:
            stale = [rid for rid, (_, ts) in self.pending_requests.items() if now - ts > 5.0]
            for rid in stale:
                del self.pending_requests[rid]
            pending_windows = {wid for wid, _ in self.pending_requests.values()}

        # Snapshot to avoid RuntimeError if dict changes during iteration
        for window_id, frame in list(self.preview_frames.items()):
            if frame.isVisible() and window_id not in pending_windows:
                try:
                    request_id = self.capture_system.capture_window_async(window_id)
                    if request_id:
                        with self._pending_lock:
                            self.pending_requests[request_id] = (window_id, now)
                except (OSError, RuntimeError) as e:
                    self.logger.error(f"Failed to request capture for {window_id}: {e}")

        # Poll for results (non-blocking)
        self._process_capture_results()

    def _process_capture_results(self):
        """Poll and process capture results from worker threads.

        Collects all available results, deduplicates by window_id
        (last write wins), and only calls update_frame on the latest
        frame per window.
        """
        # Collect all available results
        max_per_cycle = 20
        latest: dict[str, tuple[str, Image.Image]] = {}

        for _ in range(max_per_cycle):
            result = self.capture_system.get_result(timeout=0.0)  # Non-blocking
            if not result:
                break

            request_id, window_id, image = result
            # Dedup: keep only the latest result per window, close superseded frames
            prev = latest.get(window_id)
            if prev is not None and prev[1] is not None:
                prev[1].close()
            latest[window_id] = (request_id, image)

            # Remove from pending
            with self._pending_lock:
                self.pending_requests.pop(request_id, None)

        # Update previews with only the latest frame per window
        for window_id, (_request_id, image) in latest.items():
            frame = self.preview_frames.get(window_id)
            if frame is not None and image is not None:
                try:
                    frame.update_frame(image)
                except (ValueError, AttributeError, RuntimeError) as e:
                    self.logger.error(f"Failed to process frame for {window_id}: {e}")
            elif image is not None:
                image.close()  # Window removed — free the image

        if latest:
            self.logger.debug(f"Processed {len(latest)} capture results")

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

    def __init__(
        self,
        capture_system,
        character_manager,
        settings_manager=None,
        layout_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.capture_system = capture_system
        self.character_manager = character_manager
        self.settings_manager = settings_manager
        # PR2: optional layout manager for preset dropdown in Overview toolbar
        self.layout_manager = layout_manager

        # PR3: focus mode state — None = normal, str = window_id holding spotlight
        self._focus_window_id: str | None = None

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
        self.cycling_groups: dict[str, list[str]] = {}
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

        # PR2: Character status dock — chip strip with per-character system
        # + threat dot. Clicking a chip focuses the matching window.
        # Parent is set when the dock is added to the layout below.
        from argus_overview.ui.status_dock import StatusDock

        self.status_dock = StatusDock()
        self.status_dock.chip_clicked.connect(self._on_window_activated)
        sm = getattr(self, "settings_manager", None)
        show_dock = sm.get("thumbnails.show_status_dock", True) if sm else True
        self.status_dock.setVisible(show_dock)
        layout.addWidget(self.status_dock)

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

    def _sync_status_dock(self) -> None:
        """Mirror window_manager.preview_frames into the status dock."""
        if not hasattr(self, "status_dock") or self.status_dock is None:
            return
        desired: dict[str, str] = {
            wid: getattr(frame, "character_name", wid)
            for wid, frame in self.window_manager.preview_frames.items()
        }
        self.status_dock.sync_from_window_ids(desired)

        # PR4: seed chip system labels from cached per-character state so
        # newly-added chips populate without waiting for the next location
        # change event.
        char_systems = getattr(self.window_manager, "_character_systems", {})
        for char_name, system in char_systems.items():
            self.status_dock.set_character_system(char_name, system)

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
            "toggle_replay_strips": self._toggle_replay_strips_global,
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

        # PR2: global replay-strips toggle
        self.replay_strips_btn = toolbar_builder.create_button(
            "toggle_replay_strips", self._toggle_replay_strips_global
        )
        if self.replay_strips_btn:
            self.replay_strips_btn.setCheckable(True)
            toolbar_layout.addWidget(self.replay_strips_btn)

        # PR2: layout preset dropdown — 2-click apply without tab switching
        if getattr(self, "layout_manager", None) is not None:
            toolbar_layout.addSpacing(10)
            toolbar_layout.addWidget(QLabel("Preset:"))
            self.preset_combo = QComboBox()
            self.preset_combo.setMinimumWidth(140)
            self.preset_combo.setPlaceholderText("Select preset...")
            self._refresh_preset_combo()
            self.preset_combo.activated.connect(self._on_preset_activated)
            toolbar_layout.addWidget(self.preset_combo)

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

        results = self.grid_applier.last_apply_results
        if success:
            pattern = self.pattern_combo.currentText()
            self.status_label.setText(f"Applied {pattern} layout to {len(window_map)} windows")
            self.layout_applied.emit(pattern)
            self.logger.info(f"Applied {pattern} layout to {len(window_map)} windows")
        else:
            # PR3: report partial failures with specific character names
            failed = [wid for wid, ok in results.items() if not ok]
            char_map = {v: k for k, v in window_map.items()}
            failed_names = [char_map.get(wid, wid) for wid in failed]
            total = len(results)
            moved = sum(results.values())
            msg = (
                f"Layout applied: {moved}/{total} windows moved.\n\n"
                f"Failed: {', '.join(failed_names)}"
            )
            QMessageBox.warning(self, "Partial Failure", msg)

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
                frame.focus_requested.connect(
                    self._on_focus_requested, Qt.ConnectionType.UniqueConnection
                )
                frame.retry_requested.connect(
                    self._on_retry_requested, Qt.ConnectionType.UniqueConnection
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
        self._sync_status_dock()

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

    def _toggle_replay_strips_global(self) -> None:
        """PR2: toggle replay strips for all active preview windows."""
        # Determine target state from the first frame (flip current majority)
        frames = list(self.window_manager.preview_frames.values())
        if not frames:
            return
        currently_on = sum(1 for f in frames if f.is_replay_strip_enabled())
        target = currently_on < len(frames) / 2
        for frame in frames:
            frame.enable_replay_strip(target)
        self.logger.info(f"Replay strips toggled globally: {'ON' if target else 'OFF'}")

    def _refresh_preset_combo(self) -> None:
        """PR2: repopulate the layout preset dropdown from LayoutManager."""
        combo = getattr(self, "preset_combo", None)
        lm = getattr(self, "layout_manager", None)
        if combo is None or lm is None:
            return
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Select preset...")
        for preset in lm.get_all_presets():
            combo.addItem(preset.name)
        if current:
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _on_preset_activated(self, index: int) -> None:
        """PR2: apply the selected layout preset to all active windows."""
        combo = getattr(self, "preset_combo", None)
        if combo is None or index <= 0:
            return
        preset_name = combo.itemText(index)
        self._apply_layout_preset(preset_name)
        combo.setCurrentIndex(0)  # Reset to placeholder so same preset can be re-selected

    def _apply_layout_preset(self, preset_name: str) -> None:
        """PR2: apply a saved layout preset to currently active windows."""
        lm = getattr(self, "layout_manager", None)
        if lm is None:
            return
        preset = lm.get_preset(preset_name)
        if preset is None:
            self.status_label.setText(f"Preset '{preset_name}' not found")
            return

        active_chars = [
            getattr(f, "character_name", wid)
            for wid, f in self.window_manager.preview_frames.items()
        ]
        if not active_chars:
            self.status_label.setText("No active windows to arrange")
            return

        pattern = preset.grid_pattern or "custom"
        # Normalise pattern name to the display form used by get_pattern_positions
        display_pattern = pattern.replace("_", " ").replace("2x2", "2x2 Grid").replace("3x1", "3x1 Row").replace("1x3", "1x3 Column").replace("4x1", "4x1 Row").replace("main+sides", "Main + Sides").replace("cascade", "Cascade").replace("custom", "Custom")
        # Fallback: if the normalised name isn't in our map, try title-casing
        if display_pattern not in get_all_layout_patterns() and display_pattern != "Custom":
            display_pattern = "Custom"

        positions = get_pattern_positions(display_pattern, len(active_chars), 4)
        arrangement = {}
        for i, char_name in enumerate(active_chars):
            if i < len(positions):
                arrangement[char_name] = positions[i]

        window_map = {
            f.character_name: wid
            for wid, f in self.window_manager.preview_frames.items()
            if f.character_name in arrangement
        }
        if not window_map:
            self.status_label.setText("No matching windows for preset")
            return

        screen = self.grid_applier.get_screen_geometry(0)
        if not screen:
            screen = ScreenGeometry(0, 0, 1920, 1080, True)

        # Infer grid dimensions from the pattern
        grid_rows = max(1, max((pos[0] for pos in positions), default=0) + 1)
        grid_cols = max(1, max((pos[1] for pos in positions), default=0) + 1)

        success = self.grid_applier.apply_arrangement(
            arrangement=arrangement,
            window_map=window_map,
            screen=screen,
            grid_rows=grid_rows,
            grid_cols=grid_cols,
            spacing=10,
            stacked=(display_pattern == "Stacked (All Same Position)"),
        )
        results = self.grid_applier.last_apply_results
        if success:
            self.status_label.setText(f"Applied preset: {preset_name}")
            self.layout_applied.emit(preset_name)
            self.logger.info(f"Applied layout preset '{preset_name}' to {len(window_map)} windows")
        else:
            # PR3: report partial failures with specific character names
            failed = [wid for wid, ok in results.items() if not ok]
            char_map = {v: k for k, v in window_map.items()}
            failed_names = [char_map.get(wid, wid) for wid in failed]
            moved = sum(results.values())
            self.status_label.setText(
                f"Partial failure: {moved}/{len(results)} moved. Failed: {', '.join(failed_names)}"
            )

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
        except (OSError, RuntimeError) as e:
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
            frame.focus_requested.connect(
                self._on_focus_requested, Qt.ConnectionType.UniqueConnection
            )
            frame.retry_requested.connect(
                self._on_retry_requested, Qt.ConnectionType.UniqueConnection
            )
            self.preview_layout.addWidget(frame)
            self._sync_status_dock()
            return True
        return False

    def show_add_window_dialog(self):
        """Show dialog to add windows"""
        try:
            available = self._get_available_windows()
        except (OSError, RuntimeError) as e:
            QMessageBox.critical(self, "Error", f"Failed to get window list:\n{e}")
            return

        if not available:
            QMessageBox.information(
                self,
                "No Windows",
                "No windows found.\n\nMake sure EVE Online clients are running.",
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

    # ----- PR3 focus mode controller --------------------------------------
    def _on_focus_requested(self, window_id: str) -> None:
        """Toggle spotlight focus for the given window."""
        if self._focus_window_id == window_id:
            self.exit_focus_mode()
        else:
            self.enter_focus_mode(window_id)

    def enter_focus_mode(self, window_id: str) -> None:
        """Spotlight one window: scale up, dim others. Idempotent."""
        if window_id not in self.window_manager.preview_frames:
            self.logger.debug(f"Cannot enter focus mode — unknown window {window_id}")
            return
        self._focus_window_id = window_id
        self._apply_focus_state()

    def exit_focus_mode(self) -> None:
        """Restore normal grid presentation."""
        if self._focus_window_id is None:
            return
        self._focus_window_id = None
        self._apply_focus_state()

    def is_focus_mode_active(self) -> bool:
        return self._focus_window_id is not None

    def _apply_focus_state(self) -> None:
        """Push current focus mode to all preview frames."""
        focus_id = self._focus_window_id
        for wid, frame in list(self.window_manager.preview_frames.items()):
            try:
                if focus_id is None:
                    frame.set_spotlight(None)
                elif wid == focus_id:
                    frame.set_spotlight("focused")
                else:
                    frame.set_spotlight("dimmed")
            except RuntimeError:
                continue

    def _on_retry_requested(self, window_id: str) -> None:
        """PR2: handle retry capture request from a preview frame."""
        self.window_manager.retry_window_capture(window_id)

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
                    except (OSError, subprocess.SubprocessError) as e:
                        self.logger.warning(f"Failed to auto-minimize window {last_window}: {e}")

            # Track this as the last activated EVE window
            if self.settings_manager:
                self.settings_manager.set_last_activated_window(window_id)

            result = self.capture_system.activate_window(window_id)
            if result:
                self.logger.info(f"Activated window: {window_id}")
            else:
                self.logger.warning(f"Failed to activate window: {window_id}")
        except (OSError, RuntimeError, ValueError) as e:
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
            try:
                frame.focus_requested.disconnect(self._on_focus_requested)
            except (RuntimeError, TypeError):
                pass
            try:
                frame.retry_requested.disconnect(self._on_retry_requested)
            except (RuntimeError, TypeError):
                pass
            # Stop per-frame timers
            frame.session_timer.stop()
        # If we just removed the spotlight target, drop focus state.
        if self._focus_window_id == window_id:
            self._focus_window_id = None
        self.window_manager.remove_window(window_id)
        self._update_status()
        self._sync_status_dock()
        # Re-apply (covers both: focus cleared, or other tile removed mid-focus)
        self._apply_focus_state()

    def _remove_all_windows(self):
        """Remove all windows from preview"""
        if not self.window_manager.preview_frames:
            return

        count = len(self.window_manager.preview_frames)
        reply = QMessageBox.question(
            self,
            "Remove All Windows",
            f"Remove all {count} windows from preview?\n\n"
            "This stops capture but does NOT close the EVE clients.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Copy list to avoid modification during iteration
            window_ids = list(self.window_manager.preview_frames.keys())
            for window_id in window_ids:
                self.window_manager.remove_window(window_id)

            self._update_status()
            self._sync_status_dock()

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
                except (OSError, subprocess.SubprocessError):
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

        except (OSError, RuntimeError, ValueError) as e:
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

        # PR3: Escape exits focus mode (only consume the key if active)
        if key == Qt.Key.Key_Escape and self.is_focus_mode_active():
            self.exit_focus_mode()
            event.accept()
            return

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
