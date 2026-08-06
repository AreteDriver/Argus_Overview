"""Argus Command Center — Operational Truth bar (footer).

Replaces the generic system status bar with a stylized, semantically
labeled strip. Carries:
  * Subsystem health (capture / hotkeys / discovery / intel / location)
  * Active alert counter (pulsing)
  * Layout applied + last applied timestamp
  * Theme + version pinned right
"""

from __future__ import annotations

from PySide6.QtCore import Property, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from argus_overview.ui.design_system import colors as ds
from argus_overview.ui.design_system import spacing as sp
from argus_overview.ui.design_system import typography as ty

_HEALTH_COLOR = {
    "healthy": ds.HEALTHY,
    "degraded": ds.WARNING,
    "unavailable": ds.CRITICAL,
    "unknown": ds.UNKNOWN,
}

_SUBSYSTEM_LABEL = {
    "capture": "CAPTURE",
    "hotkeys": "HOTKEYS",
    "discovery": "DISCOVERY",
    "intel": "INTEL",
    "location": "LOCATION",
    "layout": "LAYOUT",
}


class _SubsystemCell(QWidget):
    """A single subsystem health cell with a colored dot and label."""

    def __init__(self, key: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._key = key
        self._label = label
        self._status = "unknown"
        self._detail = ""
        self.setFixedHeight(22)
        self.setMinimumWidth(86)
        self.setToolTip(f"{label}: unknown")

    def set_status(self, status: str, detail: str = "") -> None:
        self._status = status
        self._detail = detail
        lines = [f"{self._label}: {status.upper()}"]
        if detail:
            lines.append(detail)
        self.setToolTip("\n".join(lines))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ARG002
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            r = self.rect()
            color = _HEALTH_COLOR.get(self._status, ds.UNKNOWN)
            f = QFont(self.font())
            f.setPointSize(ty.BADGE_TEXT_PT + 1)
            f.setWeight(QFont.Weight.Bold)
            f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 160)
            p.setFont(f)
            fm = QFontMetrics(f)
            text = self._label
            dot_r = 3
            spacing = sp.SPACE_2
            x = 0
            cy = r.height() // 2
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(color))
            p.drawEllipse(x, cy - dot_r, dot_r * 2, dot_r * 2)
            x += dot_r * 2 + spacing
            p.setPen(QPen(QColor(ds.TEXT_SECONDARY)))
            p.drawText(x, cy + fm.ascent() // 2 - 1, text)
        finally:
            p.end()


class OperationalTruthBar(QWidget):
    """Bottom footer of the Command Center.

    Composition (left to right):
      [ subsystem cells ]  |  [ alert pulse ]  |  [ layout state ]  |  [ version ]
    """

    layout_chooser_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setObjectName("OperationalTruthBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp.SPACE_4, sp.SPACE_2, sp.SPACE_4, sp.SPACE_2)
        layout.setSpacing(sp.SPACE_5)

        self._cells: dict[str, _SubsystemCell] = {}
        for key in ("capture", "hotkeys", "discovery", "intel", "location"):
            label = _SUBSYSTEM_LABEL[key]
            cell = _SubsystemCell(key, label)
            cell.set_status("unknown")
            layout.addWidget(cell)
            self._cells[key] = cell

        layout.addStretch(1)

        # Alert pulse cell
        self._alert_cell = QWidget(self)
        self._alert_cell.setFixedHeight(22)
        a_layout = QHBoxLayout(self._alert_cell)
        a_layout.setContentsMargins(0, 0, 0, 0)
        a_layout.setSpacing(sp.SPACE_2)
        self._alert_dot = QLabel("●", self._alert_cell)
        self._alert_dot.setStyleSheet(f"color: {ds.HEALTHY}; font-size: 12pt;")
        self._alert_text = QLabel("0 ALERTS", self._alert_cell)
        f = QFont(self._alert_text.font())
        f.setPointSize(ty.BADGE_TEXT_PT + 1)
        f.setWeight(QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 160)
        self._alert_text.setFont(f)
        self._alert_text.setStyleSheet(f"color: {ds.TEXT_SECONDARY};")
        a_layout.addWidget(self._alert_dot)
        a_layout.addWidget(self._alert_text)
        layout.addWidget(self._alert_cell)

        # Layout state cell
        self._layout_cell = QLabel("·", self)
        self._layout_cell.setStyleSheet(
            f"color: {ds.TEXT_SECONDARY}; font-size: 9pt; font-weight: 600;"
        )
        layout.addWidget(self._layout_cell)

        # Version cell
        self._version_cell = QLabel("ARGUS // v3.3 OPS", self)
        self._version_cell.setStyleSheet(
            f"color: {ds.TEXT_MUTED}; font-size: 8pt; letter-spacing: 180%; font-weight: 600;"
        )
        layout.addWidget(self._version_cell)

        # Pulse animation for alert dot
        self._pulse = 0.0
        self._pulse_anim = QPropertyAnimation(self, b"pulse")
        self._pulse_anim.setDuration(1100)
        self._pulse_anim.setStartValue(1.0)
        self._pulse_anim.setEndValue(0.35)
        from PySide6.QtCore import QEasingCurve

        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Top hairline
        original = self.paintEvent

        def _paint(ev):  # noqa: ARG001
            original(ev)
            pp = QPainter(self)
            try:
                pp.fillRect(0, 0, self.width(), 1, QColor(ds.BORDER_SUBTLE))
            finally:
                pp.end()

        self.paintEvent = _paint

    # ---- properties --------------------------------------------------------
    def _get_pulse(self) -> float:
        return self._pulse

    def _set_pulse(self, v: float) -> None:
        self._pulse = v
        if self._alert_text.text().startswith("0"):
            return
        # Pulse the dot by ramping alpha
        self._alert_dot.setStyleSheet(f"color: rgba(240, 100, 100, {v}); font-size: 12pt;")

    pulse = Property(float, _get_pulse, _set_pulse)

    # ---- API ---------------------------------------------------------------
    def set_subsystem(self, key: str, status: str, detail: str = "") -> None:
        cell = self._cells.get(key)
        if cell is None:
            return
        cell.set_status(status, detail)

    def set_alert_count(self, count: int) -> None:
        if count <= 0:
            self._pulse_anim.stop()
            self._alert_cell.hide()
        else:
            self._alert_cell.show()
            self._pulse_anim.start()
            plural = "S" if count != 1 else ""
            self._alert_text.setText(f"{count} ALERT{plural}")
            self._alert_text.setStyleSheet(f"color: {ds.CRITICAL};")

    def set_layout_state(self, label: str | None, *, applied_at: float | None = None) -> None:
        if not label:
            self._layout_cell.setText("·")
            return
        import datetime

        suffix = ""
        if applied_at:
            suffix = f"  @ {datetime.datetime.fromtimestamp(applied_at).strftime('%H:%M:%S')}"
        self._layout_cell.setText(f"LAYOUT  {label.upper()}{suffix}")
