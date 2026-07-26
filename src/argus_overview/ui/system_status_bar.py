"""Compact system status bar widget for MainWindowV21.

PR3: surfaces per-subsystem health (capture, hotkeys, discovery, intel,
location) as colored dots in the main-window status bar.  Each indicator
has a tooltip with the current status and any detail message.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from argus_overview.ui.design_system import colors as _ds

_STATUS_COLORS = {
    "healthy": _ds.HEALTHY,
    "degraded": _ds.WARNING,
    "unavailable": _ds.CRITICAL,
    "unknown": _ds.UNKNOWN,
}

_STATUS_ICONS = {
    "healthy": "●",
    "degraded": "●",
    "unavailable": "●",
    "unknown": "●",
}


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

        self._indicators: dict[str, QLabel] = {}
        self._status: dict[str, str] = {}
        self._detail: dict[str, str] = {}

        for key, label in (
            ("capture", "Capture"),
            ("hotkeys", "Hotkeys"),
            ("discovery", "Discovery"),
            ("intel", "Intel"),
            ("location", "Location"),
        ):
            indicator = QLabel(f"<span style='color:{_STATUS_COLORS['unknown']}'>●</span> {label}")
            indicator.setTextFormat(Qt.TextFormat.RichText)
            indicator.setToolTip(f"{label}: unknown")
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
        label_text = indicator.text().split(" ", 1)[1]  # strip old colored dot
        indicator.setText(f"<span style='color:{color}'>●</span> {label_text}")
        tooltip_lines = [f"{label_text}: {status}"]
        if detail:
            tooltip_lines.append(detail)
        indicator.setToolTip("\n".join(tooltip_lines))
        self._status[subsystem] = status
        self._detail[subsystem] = detail

    def get_status(self, subsystem: str) -> tuple[str, str]:
        """Return (status, detail) for a subsystem."""
        return self._status.get(subsystem, "unknown"), self._detail.get(subsystem, "")
