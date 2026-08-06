"""
Replay strip — small horizontal row of recent capture frames.

Docked at the bottom of a WindowPreviewWidget when the user toggles
"Show replay strip" from the context menu. Hovering a cell emits
frame_hovered(idx) so the parent widget can swap its main image to the
buffered frame; leaving the strip emits -1 so the parent restores live
capture.

PR10 of the intel-aware UI uplift. Memory cost is bounded: the parent
holds the QPixmaps; the strip just paints references.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class ReplayStrip(QWidget):
    """
    Horizontal row of recent frame thumbnails.

    Stateless beyond its frame list + hover index — the parent widget
    owns the ring buffer and the live/buffered display swap.

    Signals:
        frame_hovered(int): The cell index under the mouse, or -1 when
            no cell is hovered (mouse left the strip).
    """

    frame_hovered = Signal(int)  # cell index, or -1 when not hovering

    STRIP_HEIGHT = 32
    CELL_PADDING = 2

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._frames: list[QPixmap] = []
        self._hover_index: int = -1

        self.setFixedHeight(self.STRIP_HEIGHT)
        self.setMouseTracking(True)
        from argus_overview.ui.design_system import colors as ds

        self.setStyleSheet(
            f"""
            ReplayStrip {{
                background-color: {ds.SURFACE};
                border-top: 1px solid {ds.BORDER_SUBTLE};
            }}
            """
        )

    # ----- Public API -------------------------------------------------------
    def set_frames(self, frames: list[QPixmap]) -> None:
        """Update the strip with a new ordered list (oldest → newest)."""
        self._frames = list(frames)
        # Re-clamp hover if it now points past the end.
        if self._hover_index >= len(self._frames):
            self._hover_index = -1
        self.update()

    def frame_count(self) -> int:
        return len(self._frames)

    def hover_index(self) -> int:
        return self._hover_index

    # ----- Internals --------------------------------------------------------
    def _cell_width(self) -> int:
        if not self._frames:
            return 0
        usable = max(0, self.width() - self.CELL_PADDING * 2)
        return usable // max(1, len(self._frames))

    def _index_at(self, x: int) -> int:
        cell_w = self._cell_width()
        if cell_w <= 0:
            return -1
        idx = (x - self.CELL_PADDING) // cell_w
        if idx < 0 or idx >= len(self._frames):
            return -1
        return int(idx)

    def sizeHint(self) -> QSize:
        return QSize(200, self.STRIP_HEIGHT)

    # ----- Events -----------------------------------------------------------
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._frames:
            return

        from argus_overview.ui.design_system import colors as ds

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            cell_w = self._cell_width()
            if cell_w <= 0:
                return
            inner_h = self.height() - self.CELL_PADDING * 2
            for i, pixmap in enumerate(self._frames):
                x = self.CELL_PADDING + i * cell_w
                y = self.CELL_PADDING
                # Draw thumbnail clipped to cell rect, preserving aspect.
                if pixmap is not None and not pixmap.isNull():
                    scaled = pixmap.scaled(
                        cell_w - 2,
                        inner_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.FastTransformation,
                    )
                    # Center in cell
                    cx = x + (cell_w - scaled.width()) // 2
                    cy = y + (inner_h - scaled.height()) // 2
                    painter.drawPixmap(cx, cy, scaled)
                # Cell border
                painter.setPen(QPen(QColor(ds.BORDER_SUBTLE), 1))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawRect(x, y, cell_w - 1, inner_h - 1)

            # Highlight the hovered cell.
            if 0 <= self._hover_index < len(self._frames):
                hx = self.CELL_PADDING + self._hover_index * cell_w
                hy = self.CELL_PADDING
                painter.setPen(QPen(QColor(ds.INFO), 2))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawRect(hx, hy, cell_w - 1, inner_h - 1)
        finally:
            painter.end()

    def mouseMoveEvent(self, event):
        idx = self._index_at(int(event.position().x()))
        if idx != self._hover_index:
            self._hover_index = idx
            self.frame_hovered.emit(idx)
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._hover_index != -1:
            self._hover_index = -1
            self.frame_hovered.emit(-1)
            self.update()
        super().leaveEvent(event)
