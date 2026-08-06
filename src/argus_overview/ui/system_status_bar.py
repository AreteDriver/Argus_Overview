"""Compact system status bar widget for MainWindowV21.

PR3: surfaces per-subsystem health (capture, hotkeys, discovery, intel,
location) as colored dots in the main-window status bar.  Each indicator
has a tooltip with the current status and any detail message.

PR8: Migrated from rich-text QLabel to custom paintEvent so coloured dots
render reliably across Qt versions and DPI scales (no raw HTML leakage).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QWidget

from argus_overview.ui.design_system import colors as _ds
from argus_overview.ui.design_system import metrics as _dm
from argus_overview.ui.design_system import spacing as _sp
from argus_overview.ui.design_system import typography as _ty

_STATUS_COLORS = {
    "healthy": _ds.HEALTHY,
    "degraded": _ds.WARNING,
    "unavailable": _ds.CRITICAL,
    "unknown": _ds.UNKNOWN,
}

_DOT_RADIUS = 4  # px, visually tuned for status-bar scale


class _StatusIndicator(QWidget):
    """Single subsystem indicator: coloured dot + label, drawn with QPainter."""

    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = label
        self._color = _ds.UNKNOWN
        self._detail = ""
        self.setToolTip(f"{label}: unknown")
        self.setFixedHeight(_dm.CONTROL_HEIGHT_SMALL)
        # Calculate minimum width from font metrics once
        fm = self.fontMetrics()
        self._text_width = fm.horizontalAdvance(label) + _sp.SPACE_4  # pad
        self.setMinimumWidth(_sp.SPACE_3 + _DOT_RADIUS * 2 + _sp.SPACE_2 + self._text_width)

    def set_status(self, color: str, detail: str = "") -> None:
        """Update dot colour and tooltip."""
        self._color = color
        self._detail = detail
        tooltip_lines = [f"{self._label}: {self._status_name_from_colour(color)}"]
        if detail:
            tooltip_lines.append(detail)
        self.setToolTip("\n".join(tooltip_lines))
        self.update()

    @staticmethod
    def _status_name_from_colour(color: str) -> str:
        """Reverse-lookup for tooltip text — cosmetic only."""
        for name, c in _STATUS_COLORS.items():
            if c == color:
                return name
        return "unknown"

    def paintEvent(self, event) -> None:  # noqa: ARG002
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect()
            # Draw dot
            dot_x = _sp.SPACE_2
            dot_y = rect.center().y()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._color)
            painter.drawEllipse(dot_x, dot_y - _DOT_RADIUS, _DOT_RADIUS * 2, _DOT_RADIUS * 2)
            # Draw label
            text_x = dot_x + _DOT_RADIUS * 2 + _sp.SPACE_2
            text_y = rect.center().y() + _sp.SPACE_1 // 2  # slight baseline shift
            painter.setPen(QPen(_ds.TEXT_SECONDARY))
            font = QFont(self.font())
            font.setPointSize(_ty.BADGE_TEXT_PT)
            painter.setFont(font)
            painter.drawText(text_x, text_y, self._label)
        finally:
            painter.end()


class SystemStatusBar(QWidget):
    """
    Horizontal strip of status indicators.

    Each indicator is a small colored dot + subsystem name.  Update via
    ``set_status(subsystem, status, detail)``.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(12)

        self._indicators: dict[str, _StatusIndicator] = {}
        self._status: dict[str, str] = {}
        self._detail: dict[str, str] = {}

        for key, label in (
            ("capture", "Capture"),
            ("hotkeys", "Hotkeys"),
            ("discovery", "Discovery"),
            ("intel", "Intel"),
            ("location", "Location"),
        ):
            indicator = _StatusIndicator(label)
            indicator.set_status(_STATUS_COLORS["unknown"])
            layout.addWidget(indicator)
            self._indicators[key] = indicator
            self._status[key] = "unknown"
            self._detail[key] = ""

        layout.addStretch()

    def set_status(self, subsystem: str, status: str, detail: str = "") -> None:
        """Update a subsystem indicator.

        Args:
            subsystem: one of capture, hotkeys, discovery, intel, location.
            status: healthy, degraded, unavailable, unknown.
            detail: optional tooltip detail message.
        """
        indicator = self._indicators.get(subsystem)
        if indicator is None:
            return
        color = _STATUS_COLORS.get(status, _STATUS_COLORS["unknown"])
        indicator.set_status(color, detail)
        self._status[subsystem] = status
        self._detail[subsystem] = detail

    def get_status(self, subsystem: str) -> tuple[str, str]:
        """Return (status, detail) for a subsystem."""
        return self._status.get(subsystem, "unknown"), self._detail.get(subsystem, "")

    def snapshot(self) -> dict[str, tuple[str, str]]:
        """Return a copy of all subsystem (status, detail) pairs.

        Used by peer subsystems (e.g. :class:`CommandIntegrator`) to
        seed a parallel status view without reaching into private
        state. Returns a fresh dict so callers cannot mutate ours.
        """
        return {
            key: (self._status.get(key, "unknown"), self._detail.get(key, ""))
            for key in self._status
        }
