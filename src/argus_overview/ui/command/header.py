"""Argus Command Center — Header chrome.

The header is the identity moment. It establishes the brand ("ARGUS") as
a deliberate piece of operating-environment typography, not a window
title. Subtitle carries the operational state summary so the operator
never has to scan for context.

Design intent:
  * Banner-style brand mark: "ARGUS" in heavy weight, smaller "// 0PS"
    tagline, version pinned right.
  * Live status line: fleet count, alert count, intel pipeline health.
  * Right-side cluster: command palette hint and global action buttons.
  * Bottom 1px focus line in BORDER_FOCUS to anchor the eye.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QWidget

from argus_overview.ui.design_system import colors as ds
from argus_overview.ui.design_system import metrics as dm
from argus_overview.ui.design_system import spacing as sp
from argus_overview.ui.design_system import typography as ty


class BrandMark(QWidget):
    """Heavy-weight brand block: 'ARGUS' with // 0PS tagline.

    Painted (not a label) so type rendering is consistent across themes
    and DPI scales, and so we can layer the cursor/underline accent.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setFixedWidth(180)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def sizeHint(self):  # noqa: D401
        from PySide6.QtCore import QSize

        return QSize(180, 48)

    def paintEvent(self, event) -> None:  # noqa: ARG002
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            r = self.rect()
            # Brand word
            f = QFont(self.font())
            f.setPointSize(ty.WINDOW_TITLE_PT + 6)
            f.setWeight(QFont.Weight.Black)
            f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 105)
            p.setFont(f)
            p.setPen(QColor(ds.TEXT_PRIMARY))
            fm = QFontMetrics(f)
            brand_y = (r.height() + fm.ascent() - fm.descent()) // 2
            p.drawText(r.left(), brand_y, "ARGUS")
            # "//"  divider in muted color
            divider_w = fm.horizontalAdvance("ARGUS")
            f2 = QFont(self.font())
            f2.setPointSize(ty.WINDOW_TITLE_PT + 2)
            f2.setWeight(QFont.Weight.Light)
            p.setFont(f2)
            fm2 = QFontMetrics(f2)
            div_x = r.left() + divider_w + sp.SPACE_2
            p.setPen(QColor(ds.TEXT_MUTED))
            p.drawText(div_x, brand_y, "//")
            # OPS in accent (0 = signal-amber tone, OPS = operational)
            tag_x = div_x + fm2.horizontalAdvance("//") + sp.SPACE_1
            f3 = QFont(self.font())
            f3.setPointSize(ty.WINDOW_TITLE_PT + 2)
            f3.setWeight(QFont.Weight.Bold)
            f3.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 140)
            p.setFont(f3)
            fm3 = QFontMetrics(f3)
            p.setPen(QColor(ds.BORDER_FOCUS))
            p.drawText(tag_x, brand_y, "OPS")
            # Underline accent rule below the brand
            accent_x = r.left()
            accent_w = tag_x + fm3.horizontalAdvance("OPS") - r.left()
            accent_y = r.height() - 1
            p.fillRect(accent_x, accent_y, accent_w, 2, QColor(ds.BORDER_FOCUS))
        finally:
            p.end()


class OperationalStatusLine(QWidget):
    """Animated status line — fleet count, alert count, intel health.

    When alerts are present the line gains a 1px danger underline and
    the alert counter pulses gently so the operator feels the priority
    without staring at the screen.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fleet_count: int = 0
        self._alert_count: int = 0
        self._intel_health: str = "idle"  # idle | live | degraded | offline
        self._pulse_strength: float = 0.0
        self._pulse_anim = QPropertyAnimation(self, b"pulse_strength")
        self._pulse_anim.setDuration(900)
        self._pulse_anim.setStartValue(1.0)
        self._pulse_anim.setEndValue(0.2)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(2000)
        self._pulse_timer.timeout.connect(self._restart_pulse)
        self.setFixedHeight(28)
        self.setMinimumWidth(280)

    def _get_pulse_strength(self) -> float:
        return self._pulse_strength

    def _set_pulse_strength(self, v: float) -> None:
        self._pulse_strength = v
        self.update()

    pulse_strength = Property(float, _get_pulse_strength, _set_pulse_strength)

    def _restart_pulse(self) -> None:
        if self._alert_count > 0:
            self._pulse_anim.start()

    def update_state(
        self,
        fleet_count: int,
        alert_count: int = 0,
        intel_health: str = "live",
    ) -> None:
        self._fleet_count = fleet_count
        self._alert_count = alert_count
        self._intel_health = intel_health
        if alert_count > 0 and not self._pulse_timer.isActive():
            self._pulse_timer.start()
            self._pulse_anim.start()
        elif alert_count == 0:
            self._pulse_timer.stop()
            self._pulse_strength = 0.0
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ARG002
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            r = self.rect()
            y = (
                r.height()
                + QFontMetrics(self.font()).ascent()
                - QFontMetrics(self.font()).descent()
            ) // 2

            segments = []
            # Fleet count — word-bound pluralization
            pilot_word = "PILOT" if self._fleet_count == 1 else "PILOTS"
            segments.append((ds.TEXT_SECONDARY, f"{self._fleet_count} {pilot_word}"))
            segments.append((ds.TEXT_MUTED, "·"))
            # Intel health
            intel_color = {
                "live": ds.HEALTHY,
                "idle": ds.UNKNOWN,
                "degraded": ds.WARNING,
                "offline": ds.CRITICAL,
            }.get(self._intel_health, ds.UNKNOWN)
            intel_label = self._intel_health.upper()
            segments.append((intel_color, "●"))
            segments.append((ds.TEXT_SECONDARY, f"INTEL {intel_label}"))
            # Alert count
            segments.append((ds.TEXT_MUTED, "·"))
            pulse_alpha = int(255 * self._pulse_strength)
            if self._alert_count > 0:
                alert_word = "ALERT" if self._alert_count == 1 else "ALERTS"
                segments.append(("alert", f" {self._alert_count} {alert_word}"))
            x = 0
            f = QFont(self.font())
            f.setPointSize(ty.PRIMARY_LABEL_PT)
            f.setWeight(QFont.Weight.Medium)
            f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 110)
            p.setFont(f)
            fm = QFontMetrics(f)
            for color, text in segments:
                if color == "alert":
                    # Blend CRITICAL with current pulse alpha
                    c = QColor(ds.CRITICAL)
                    c.setAlpha(pulse_alpha)
                    p.setPen(QPen(c))
                else:
                    p.setPen(QPen(QColor(color)))
                p.drawText(x, y, text)
                x += fm.horizontalAdvance(text) + sp.SPACE_2
            # Bottom pulse rule
            if self._alert_count > 0:
                rule = QColor(ds.CRITICAL)
                rule.setAlpha(int(180 * self._pulse_strength))
                p.fillRect(0, self.height() - 1, int(x * 0.6), 1, rule)
        finally:
            p.end()


class CommandCenterHeader(QWidget):
    """Top chrome of the Command Center tab.

    Composition (left to right):
      [ Brand Mark ] [ Status Line ]   spacer   [ Layout chooser ] [ Palette hint ]
    """

    layout_chooser_clicked = Signal()
    palette_hint_activated = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(dm.CONTROL_HEIGHT_LARGE + 22)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp.SPACE_5, sp.SPACE_3, sp.SPACE_5, sp.SPACE_3)
        layout.setSpacing(sp.SPACE_4)

        # Brand — fixed-width container ensures the status line has space
        self._brand = BrandMark(self)
        self._brand.setFixedWidth(180)
        layout.addWidget(self._brand)

        # Vertical separator
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setStyleSheet(f"color: {ds.BORDER_SUBTLE};")
        sep.setFixedHeight(28)
        layout.addWidget(sep)

        # Operational status — use a fixed-width container so it never
        # competes with the brand for layout space, but the inner widget
        # uses ellipsis if it ever overflows.
        self._status = OperationalStatusLine(self)
        self._status.setMinimumWidth(220)
        self._status.setMaximumWidth(420)
        layout.addWidget(self._status, 1)

        # Spacer pushes right cluster to edge
        layout.addStretch(1)

        # Layout chooser button (Tier 2 action becomes 1-click from Command)
        self._layout_btn = QPushButton("Layout  ▾", self)
        self._layout_btn.setObjectName("CommandLayoutChooser")
        self._layout_btn.setFixedHeight(dm.CONTROL_HEIGHT)
        self._layout_btn.setMinimumWidth(120)
        self._layout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._layout_btn.clicked.connect(self.layout_chooser_clicked.emit)
        self._apply_button_style(self._layout_btn)
        layout.addWidget(self._layout_btn)

        # Palette hint (cmd+k)
        self._palette_btn = QPushButton("⌘ K", self)
        self._palette_btn.setObjectName("CommandPaletteHint")
        self._palette_btn.setFixedHeight(dm.CONTROL_HEIGHT)
        self._palette_btn.setFixedWidth(72)
        self._palette_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._palette_btn.clicked.connect(self.palette_hint_activated.emit)
        self._apply_button_style(self._palette_btn, secondary=True)
        layout.addWidget(self._palette_btn)

        # Drop shadow at bottom to anchor the eye
        self._paint_focus_line()

    def _apply_button_style(self, btn: QPushButton, *, secondary: bool = False) -> None:
        if secondary:
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {ds.TEXT_SECONDARY};
                    border: 1px solid {ds.BORDER_SUBTLE};
                    border-radius: {dm.RADIUS_CONTROL}px;
                    padding: 0 {sp.SPACE_4}px;
                    font-size: {ty.PRIMARY_LABEL_PT}pt;
                    font-weight: 600;
                    letter-spacing: 110%;
                }}
                QPushButton:hover {{
                    background-color: {ds.SURFACE_RAISED};
                    color: {ds.TEXT_PRIMARY};
                    border-color: {ds.BORDER_STRONG};
                }}
                QPushButton:pressed {{
                    background-color: {ds.SURFACE_HOVER};
                }}
                """
            )
        else:
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {ds.SURFACE_RAISED};
                    color: {ds.TEXT_PRIMARY};
                    border: 1px solid {ds.BORDER_STRONG};
                    border-radius: {dm.RADIUS_CONTROL}px;
                    padding: 0 {sp.SPACE_4}px;
                    font-size: {ty.PRIMARY_LABEL_PT}pt;
                    font-weight: 700;
                    letter-spacing: 110%;
                }}
                QPushButton:hover {{
                    background-color: {ds.SURFACE_HOVER};
                    border-color: {ds.BORDER_FOCUS};
                }}
                QPushButton:pressed {{
                    background-color: {ds.SURFACE};
                }}
                """
            )

    def _paint_focus_line(self) -> None:
        """1px focus line at the very bottom to anchor the header."""
        original = self.paintEvent

        def paintEvent(event):  # noqa: ARG001
            original(event)
            p = QPainter(self)
            try:
                p.fillRect(0, self.height() - 1, self.width(), 1, QColor(ds.BORDER_FOCUS))
            finally:
                p.end()

        self.paintEvent = paintEvent

    def update_state(
        self, fleet_count: int, alert_count: int = 0, intel_health: str = "live"
    ) -> None:
        self._status.update_state(fleet_count, alert_count, intel_health)
