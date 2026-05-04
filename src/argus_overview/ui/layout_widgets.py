"""
Layout-tab widgets: pattern thumbnails and monitor cards.

The legacy Layouts tab uses a QComboBox of pattern names ("2x2 Grid",
"Cascade", etc.) and a QSpinBox for monitor selection (just a number,
0-3). Both fail at the user's actual job — recognizing what the layout
looks like at a glance and which physical monitor they're picking.

This module defines visual replacements:
- ``PatternThumbnail``: a small QFrame rendering each pattern's grid
  shape via QPainter. Click to select; selected state has an accent
  border in the user's character accent palette.
- ``PatternThumbStrip``: a horizontal row of PatternThumbnails. Emits
  ``pattern_selected(str)`` with the pattern's display name.
- ``MonitorCard``: a click-target showing monitor index + dimensions
  + primary marker. Replaces the bare 0-3 spinbox.
- ``MonitorCardStrip``: a horizontal row of MonitorCards.

PR L1: layout-tab UX pass 1.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Cell-position layouts for each pattern, normalized to a 4x4 grid so
# every thumbnail draws into the same canvas. Each entry is a list of
# (row, col, rowspan, colspan) tuples to stamp into the canvas.
#
# Cells are drawn at unit size (100/cols × 100/rows of the canvas) so
# any pattern fits in the same thumbnail dimensions.
PATTERN_CELLS: dict[str, list[tuple[int, int, int, int]]] = {
    "2x2 Grid": [(0, 0, 1, 1), (0, 1, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1)],
    "3x1 Row": [(0, 0, 1, 1), (0, 1, 1, 1), (0, 2, 1, 1)],
    "1x3 Column": [(0, 0, 1, 1), (1, 0, 1, 1), (2, 0, 1, 1)],
    "4x1 Row": [(0, 0, 1, 1), (0, 1, 1, 1), (0, 2, 1, 1), (0, 3, 1, 1)],
    "2x3 Grid": [
        (0, 0, 1, 1),
        (0, 1, 1, 1),
        (0, 2, 1, 1),
        (1, 0, 1, 1),
        (1, 1, 1, 1),
        (1, 2, 1, 1),
    ],
    "3x2 Grid": [
        (0, 0, 1, 1),
        (0, 1, 1, 1),
        (1, 0, 1, 1),
        (1, 1, 1, 1),
        (2, 0, 1, 1),
        (2, 1, 1, 1),
    ],
    # "Main + Sides": one big cell on the left (full height, 2/3 width),
    # 3 stacked cells on the right (1/3 width each).
    "Main + Sides": [(0, 0, 3, 2), (0, 2, 1, 1), (1, 2, 1, 1), (2, 2, 1, 1)],
    # Cascade — overlapping diagonal step
    "Cascade": [(0, 0, 2, 2), (1, 1, 2, 2), (2, 2, 2, 2)],
    # All overlapping — render as one cell with a small stack indicator
    "Stacked (All Same Position)": [(1, 1, 2, 2)],
    # Custom — empty grid outline only, no cells
    "Custom": [],
}


# Pattern dimensions used to scale unit cells. Format: (rows, cols).
PATTERN_DIMS: dict[str, tuple[int, int]] = {
    "2x2 Grid": (2, 2),
    "3x1 Row": (1, 3),
    "1x3 Column": (3, 1),
    "4x1 Row": (1, 4),
    "2x3 Grid": (2, 3),
    "3x2 Grid": (3, 2),
    "Main + Sides": (3, 3),
    "Cascade": (4, 4),
    "Stacked (All Same Position)": (4, 4),
    "Custom": (4, 4),
}


# =============================================================================
# Pattern thumbnail
# =============================================================================


class PatternThumbnail(QFrame):
    """
    Click-to-select thumbnail rendering a single pattern.

    Signals:
        clicked(str): The pattern's display name when clicked.
    """

    clicked = Signal(str)

    THUMB_W = 88
    THUMB_H = 64
    LABEL_H = 20

    def __init__(self, pattern_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pattern_name = pattern_name
        self._selected = False

        self.setFixedSize(self.THUMB_W, self.THUMB_H + self.LABEL_H)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Spacer for the painted area; the label is drawn underneath.
        self._canvas_spacer = QWidget()
        self._canvas_spacer.setFixedHeight(self.THUMB_H)
        layout.addWidget(self._canvas_spacer)

        self._label = QLabel(pattern_name)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: #bbb; font-size: 8pt; padding: 0px;")
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(self.THUMB_W)
        layout.addWidget(self._label)

        self._update_style()

    def is_selected(self) -> bool:
        return self._selected

    def set_selected(self, selected: bool) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self._update_style()
        self.update()

    def _update_style(self) -> None:
        if self._selected:
            self.setStyleSheet(
                """
                PatternThumbnail {
                    background-color: #2d3a4a;
                    border: 2px solid #5a9fff;
                    border-radius: 4px;
                }
                """
            )
            self._label.setStyleSheet(
                "color: #ffffff; font-size: 8pt; font-weight: bold; padding: 0px;"
            )
        else:
            self.setStyleSheet(
                """
                PatternThumbnail {
                    background-color: #2a2a2a;
                    border: 1px solid #444;
                    border-radius: 4px;
                }
                PatternThumbnail:hover {
                    background-color: #353535;
                    border-color: #6a6a6a;
                }
                """
            )
            self._label.setStyleSheet("color: #bbb; font-size: 8pt; padding: 0px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.pattern_name)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        cells = PATTERN_CELLS.get(self.pattern_name, [])
        rows, cols = PATTERN_DIMS.get(self.pattern_name, (4, 4))

        # Canvas inset inside the frame border, above the label.
        pad = 6
        canvas_x = pad
        canvas_y = pad
        canvas_w = self.THUMB_W - pad * 2
        canvas_h = self.THUMB_H - pad * 2

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

            # Custom: render an empty placeholder
            if not cells:
                painter.setPen(QPen(QColor(120, 120, 120), 1, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawRect(canvas_x, canvas_y, canvas_w - 1, canvas_h - 1)
                # Draw a "?" centered
                font = QFont(painter.font())
                font.setPointSize(14)
                font.setBold(True)
                painter.setFont(font)
                painter.setPen(QPen(QColor(150, 150, 150)))
                painter.drawText(
                    canvas_x,
                    canvas_y,
                    canvas_w,
                    canvas_h,
                    Qt.AlignmentFlag.AlignCenter,
                    "?",
                )
                return

            # Stacked is a special case — render overlapping cards
            if self.pattern_name == "Stacked (All Same Position)":
                for offset in (0, 4, 8):
                    rect_x = canvas_x + canvas_w // 4 + offset
                    rect_y = canvas_y + canvas_h // 4 + offset
                    rect_w = canvas_w // 2
                    rect_h = canvas_h // 2
                    self._draw_cell(painter, rect_x, rect_y, rect_w, rect_h)
                return

            # Cell-grid render
            cell_w = canvas_w / cols
            cell_h = canvas_h / rows
            for r, c, rspan, cspan in cells:
                x = canvas_x + int(c * cell_w)
                y = canvas_y + int(r * cell_h)
                w = max(1, int(cspan * cell_w) - 2)
                h = max(1, int(rspan * cell_h) - 2)
                self._draw_cell(painter, x, y, w, h)
        finally:
            painter.end()

    def _draw_cell(self, painter: QPainter, x: int, y: int, w: int, h: int) -> None:
        """Draw a single cell rect with the selected/unselected fill."""
        if self._selected:
            fill = QColor(90, 159, 255, 200)
            border = QColor(90, 159, 255)
        else:
            fill = QColor(110, 110, 110, 180)
            border = QColor(150, 150, 150)
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(border, 1))
        painter.drawRect(x, y, w, h)


# =============================================================================
# Pattern thumb strip
# =============================================================================


class PatternThumbStrip(QWidget):
    """
    Horizontal row of PatternThumbnails. Single-selection.

    Signals:
        pattern_selected(str): The pattern display name on selection.
    """

    pattern_selected = Signal(str)

    def __init__(
        self,
        patterns: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._thumbnails: dict[str, PatternThumbnail] = {}
        self._selected: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(8)

        names = patterns or list(PATTERN_CELLS.keys())
        for name in names:
            thumb = PatternThumbnail(name, parent=self)
            thumb.clicked.connect(self._on_thumb_clicked)
            layout.addWidget(thumb)
            self._thumbnails[name] = thumb

        layout.addStretch()

    def selected_pattern(self) -> str | None:
        return self._selected

    def set_selected(self, pattern_name: str) -> None:
        """Highlight the named pattern. Emits pattern_selected if changed."""
        if pattern_name not in self._thumbnails:
            return
        if self._selected == pattern_name:
            return
        if self._selected and self._selected in self._thumbnails:
            self._thumbnails[self._selected].set_selected(False)
        self._thumbnails[pattern_name].set_selected(True)
        self._selected = pattern_name
        self.pattern_selected.emit(pattern_name)

    def _on_thumb_clicked(self, pattern_name: str) -> None:
        self.set_selected(pattern_name)


# =============================================================================
# Monitor card
# =============================================================================


class MonitorCard(QFrame):
    """
    Click-to-select card showing one monitor's index + dimensions.

    Signals:
        clicked(int): The monitor index when clicked.
    """

    clicked = Signal(int)

    CARD_W = 140
    CARD_H = 80

    def __init__(
        self,
        index: int,
        width: int,
        height: int,
        is_primary: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.index = index
        self.width_px = width
        self.height_px = height
        self.is_primary = is_primary
        self._selected = False

        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        index_label = QLabel(f"Monitor {index}")
        index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        index_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(index_label)

        dims_label = QLabel(f"{width} × {height}")
        dims_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dims_label.setStyleSheet("color: #aaa; font-size: 9pt;")
        layout.addWidget(dims_label)

        if is_primary:
            primary_label = QLabel("Primary")
            primary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            primary_label.setStyleSheet("color: #5a9fff; font-size: 8pt; font-style: italic;")
            layout.addWidget(primary_label)
        else:
            layout.addStretch()

        self._update_style()

    def is_selected(self) -> bool:
        return self._selected

    def set_selected(self, selected: bool) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self._update_style()

    def _update_style(self) -> None:
        if self._selected:
            self.setStyleSheet(
                """
                MonitorCard {
                    background-color: #2d3a4a;
                    border: 2px solid #5a9fff;
                    border-radius: 4px;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                MonitorCard {
                    background-color: #2a2a2a;
                    border: 1px solid #444;
                    border-radius: 4px;
                }
                MonitorCard:hover {
                    background-color: #353535;
                    border-color: #6a6a6a;
                }
                """
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
            event.accept()
            return
        super().mousePressEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(self.CARD_W, self.CARD_H)


# =============================================================================
# Monitor card strip
# =============================================================================


class MonitorCardStrip(QWidget):
    """
    Horizontal row of MonitorCards. Single-selection.

    Signals:
        monitor_selected(int): The monitor index when a card is clicked.
    """

    monitor_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: dict[int, MonitorCard] = {}
        self._selected: int | None = None

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(8)
        self._layout.addStretch()

    def card_count(self) -> int:
        return len(self._cards)

    def selected_index(self) -> int | None:
        return self._selected

    def set_monitors(self, monitors: list[tuple[int, int, int, bool]]) -> None:
        """Replace the strip contents.

        Args:
            monitors: list of (index, width, height, is_primary) tuples.
        """
        # Tear down existing cards.
        for card in list(self._cards.values()):
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        self._selected = None

        # Add new cards before the trailing stretch.
        for index, width, height, is_primary in monitors:
            card = MonitorCard(index, width, height, is_primary, parent=self)
            card.clicked.connect(self._on_card_clicked)
            insert_at = max(0, self._layout.count() - 1)
            self._layout.insertWidget(insert_at, card)
            self._cards[index] = card

    def set_selected(self, index: int) -> None:
        """Highlight the given monitor index. Emits monitor_selected on change."""
        if index not in self._cards:
            return
        if self._selected == index:
            return
        if self._selected is not None and self._selected in self._cards:
            self._cards[self._selected].set_selected(False)
        self._cards[index].set_selected(True)
        self._selected = index
        self.monitor_selected.emit(index)

    def _on_card_clicked(self, index: int) -> None:
        self.set_selected(index)
