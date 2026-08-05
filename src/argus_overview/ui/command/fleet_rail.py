"""Argus Command Center — Fleet Rail.

The Fleet Rail is the operator's primary fleet identity surface on the
Command tab. It is a vertical strip pinned to the left side of the
Command Center shell. Every active pilot has a permanent card with:

  - Accent avatar (always-color; carries character identity)
  - Pilot name + EVE-class role chip
  - System + distance pill
  - Threat indicator (color + letter + age)
  - Focus state (active dot when window has focus)
  - Stale state (dimmed + 'last:' suffix)

Click a card to focus the matching window. Hover surfaces a tooltip
with full context: capture health, last report, distance from threat.

The Fleet Rail replaces the floating StatusDock as the primary identity
read — it is always visible, always ordered, and never collapses.
"""
from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from argus_overview.intel.parser import ThreatLevel
from argus_overview.ui.design_system import colors as ds
from argus_overview.ui.design_system import metrics as dm
from argus_overview.ui.design_system import spacing as sp
from argus_overview.ui.design_system import typography as ty
from argus_overview.ui.design_system.painting import (
    draw_threat_accent,
)

THREAT_LETTERS = {"danger": "D", "warning": "W", "critical": "C", "clear": "OK"}


def _initials(name: str) -> str:
    parts = [p for p in name.replace("_", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


class FleetCard(QFrame):
    """A single persistent pilot identity card.

    Always rendered in the same position, full opacity (with subtle
    variation by state), never expands or contracts based on layout
    decisions. Tap to focus; long-press for context menu (forwarded
    via right-click).
    """

    clicked = Signal(str)  # window_id
    context_requested = Signal(str, object)  # window_id, QPoint

    def __init__(
        self,
        window_id: str,
        character_name: str,
        accent: tuple[int, int, int],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._window_id = window_id
        self._character_name = character_name
        self._accent = QColor(*accent)
        self._system: str | None = None
        self._last_system: str | None = None
        self._has_focus: bool = False
        self._capture_health: str = "live"  # live | static | stale | error | paused
        self._threat_level: ThreatLevel | None = None
        self._threat_alpha: float = 0.0
        self._threat_set_at: float = 0.0
        self._threat_distance: int | None = None
        self._stale: bool = False

        self.setObjectName(f"FleetCard::{window_id}")
        self.setMinimumWidth(168)
        self.setMaximumWidth(220)
        self.setFixedHeight(64)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(sp.SPACE_3, sp.SPACE_2, sp.SPACE_3, sp.SPACE_2)
        layout.setSpacing(2)

        # Top row — avatar + name + focus dot
        top = QWidget(self)
        from PySide6.QtWidgets import QHBoxLayout
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(sp.SPACE_2)
        self._avatar = QLabel(_initials(character_name))
        self._avatar.setObjectName("FleetAvatar")
        self._avatar.setFixedSize(22, 22)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self._avatar)
        self._name = QLabel(character_name)
        self._name.setObjectName("FleetName")
        top_layout.addWidget(self._name, 1)
        self._focus_dot = QWidget(self)
        self._focus_dot.setFixedSize(8, 8)
        top_layout.addWidget(self._focus_dot)
        layout.addWidget(top)

        # Bottom row — system + threat chip
        bottom = QWidget(self)
        b_layout = QHBoxLayout(bottom)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(sp.SPACE_2)
        self._system_label = QLabel("—")
        self._system_label.setObjectName("FleetSystemLabel")
        b_layout.addWidget(self._system_label, 1)
        self._threat_badge = QLabel("")
        self._threat_badge.setObjectName("FleetThreatBadge")
        self._threat_badge.setFixedHeight(16)
        self._threat_badge.setMinimumWidth(28)
        self._threat_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b_layout.addWidget(self._threat_badge)
        layout.addWidget(bottom)

        self._apply_styles()
        self._update_tooltip()
        self._update_accessible()

    # ---- public API --------------------------------------------------------
    def window_id(self) -> str:
        return self._window_id

    def character_name(self) -> str:
        return self._character_name

    def set_system(self, system: str | None, *, stale: bool = False) -> None:
        self._system = system
        self._stale = stale
        if system and not stale:
            self._last_system = system
        self._update_system_label()
        self._update_tooltip()
        self._update_accessible()
        self._apply_styles()

    def set_capture_health(self, health: str) -> None:
        self._capture_health = health
        self._update_tooltip()
        self._update_accessible()
        self.update()

    def set_focused(self, focused: bool) -> None:
        self._has_focus = focused
        self._apply_styles()
        self.update()

    def set_threat_state(
        self,
        level: ThreatLevel | None,
        system: str | None = None,
        alpha: float = 1.0,
        distance: int | None = None,
    ) -> None:
        if level is None or level == ThreatLevel.CLEAR:
            self._threat_level = None
            self._threat_alpha = 0.0
            self._threat_distance = None
        else:
            self._threat_level = level
            self._threat_alpha = max(0.0, min(1.0, alpha))
            self._threat_distance = distance if distance and distance > 0 else None
            self._threat_set_at = time.monotonic()
        if system is not None:
            self.set_system(system)
        self._update_threat_badge()
        self._update_tooltip()
        self._update_accessible()
        self.update()

    # ---- styling & rendering ----------------------------------------------
    def _update_system_label(self) -> None:
        if self._system and not self._stale:
            self._system_label.setText(self._system)
        elif self._last_system and self._stale:
            self._system_label.setText(f"Unknown · last: {self._last_system}")
        else:
            self._system_label.setText("Unknown")

    def _update_threat_badge(self) -> None:
        if self._threat_level and self._threat_alpha > 0.0:
            letter = THREAT_LETTERS.get(self._threat_level.value.lower(), "?")
            if self._threat_distance and self._threat_distance > 0:
                self._threat_badge.setText(f"{letter}+{self._threat_distance}j")
            else:
                self._threat_badge.setText(letter)
        else:
            self._threat_badge.setText("")

    def _apply_styles(self) -> None:
        accent = self._accent
        darker = accent.darker(160)
        a_name = accent.name()
        d_name = darker.name()
        text_color = "#0f0f0f" if (accent.redF() * 0.299 + accent.greenF() * 0.587 + accent.blueF() * 0.114) > 0.55 else "#f5f5f5"

        focus_border = ds.BORDER_FOCUS if self._has_focus else ds.BORDER_SUBTLE
        focus_bg = ds.SURFACE if not self._has_focus else ds.SURFACE_RAISED
        if self._stale:
            focus_bg = ds.CANVAS

        self.setStyleSheet(
            f"""
            QFrame#{self.objectName()} {{
                background-color: {focus_bg};
                border: 1px solid {focus_border};
                border-left: 3px solid {a_name};
                border-radius: {dm.RADIUS_CARD}px;
            }}
            QFrame#{self.objectName()}:hover {{
                background-color: {ds.SURFACE_HOVER};
                border-color: {ds.BORDER_FOCUS};
                border-left: 3px solid {d_name};
            }}
            QLabel#FleetAvatar {{
                background-color: {a_name};
                border: 1px solid {d_name};
                border-radius: 9px;
                color: {text_color};
                font-weight: 800;
                font-size: 9pt;
            }}
            QLabel#FleetName {{
                color: {ds.TEXT_PRIMARY};
                font-weight: 700;
                font-size: 10pt;
            }}
            QLabel#FleetSystemLabel {{
                color: {ds.TEXT_MUTED if self._stale else ds.TEXT_SECONDARY};
                font-size: 9pt;
            }}
            QLabel#FleetThreatBadge {{
                color: {ds.TEXT_PRIMARY};
                font-size: 8pt;
                font-weight: 700;
                padding: 0 {sp.SPACE_2}px;
                border-radius: 8px;
                background-color: transparent;
            }}
            """
        )
        # Focus dot: visible only when character has window focus
        from PySide6.QtGui import QPixmap
        pix = QPixmap(self._focus_dot.size())
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        try:
            color = QColor(ds.BORDER_FOCUS) if self._has_focus else QColor(ds.BORDER_SUBTLE)
            color.setAlpha(255 if self._has_focus else 80)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawEllipse(0, 0, 8, 8)
        finally:
            p.end()
        # Wrap pixmap on a label would over-complicate; use a CSS class instead
        self._focus_dot.setStyleSheet(
            f"background-color: {ds.BORDER_FOCUS if self._has_focus else 'transparent'};"
            f"border-radius: 4px;"
        )

    def _update_tooltip(self) -> None:
        parts = [self._character_name]
        if self._system and not self._stale:
            parts.append(f"System: {self._system}")
        elif self._last_system:
            parts.append(f"System: Unknown (last: {self._last_system})")
        if self._threat_level is not None and self._threat_alpha > 0.0:
            line = f"Threat: {self._threat_level.value.upper()}"
            if self._threat_distance and self._threat_distance > 0:
                line += f" ({self._threat_distance}j)"
            if self._threat_set_at > 0.0:
                secs = int(time.monotonic() - self._threat_set_at)
                line += f" · {secs}s ago"
            parts.append(line)
        parts.append(f"Capture: {self._capture_health.upper()}")
        if self._has_focus:
            parts.append("● ACTIVE WINDOW")
        parts.append("Click: focus window")
        parts.append("Right-click: pilot menu")
        self.setToolTip("\n".join(parts))

    def _update_accessible(self) -> None:
        parts = [f"Pilot {self._character_name}"]
        sys = self._system if self._system and not self._stale else (
            f"unknown last {self._last_system}" if self._last_system else "unknown")
        parts.append(f"system {sys}")
        parts.append(f"capture {self._capture_health}")
        if self._threat_level and self._threat_alpha > 0.0:
            parts.append(f"threat {self._threat_level.value}")
        if self._has_focus:
            parts.append("active focus")
        self.setAccessibleName(", ".join(parts))

    # ---- events ------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._window_id)
            event.accept()
            return
        if event.button() == Qt.MouseButton.RightButton:
            self.context_requested.emit(self._window_id, event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit(self._window_id)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Right:
            self.parentWidget().focusNextChild()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Left:
            self.parentWidget().focusPreviousChild()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        # Threat accent overlay on the right edge — preserves skill of
        # reading identity + state from a glance.
        if self._threat_level and self._threat_alpha > 0.0:
            from argus_overview.ui.main_tab import THREAT_BORDER_COLORS
            rgb = THREAT_BORDER_COLORS.get(self._threat_level, (255, 0, 0))
            p = QPainter(self)
            try:
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                draw_threat_accent(
                    p,
                    self.rect(),
                    rgb,
                    alpha=self._threat_alpha,
                    edge="right",
                    ribbon_width=2,
                    glow_height=1,
                )
            finally:
                p.end()


class FleetRail(QWidget):
    """Vertical strip of FleetCards.

    Always rendered in the same position with a fixed order. The rail
    is the operator's identity surface — pilots are never hidden,
    collapsed, or reordered without explicit action.
    """

    pilot_focus_requested = Signal(str)
    pilot_context_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: dict[str, FleetCard] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(sp.SPACE_3, sp.SPACE_4, sp.SPACE_3, sp.SPACE_4)
        layout.setSpacing(sp.SPACE_2)
        layout.addStretch(0)  # Push cards to top

        # Label the strip
        self._label = QLabel("FLEET RAIL", self)
        self._label.setObjectName("FleetRailLabel")
        f = QFont(self._label.font())
        f.setPointSize(ty.BADGE_TEXT_PT)
        f.setWeight(QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 180)
        self._label.setFont(f)
        self._label.setStyleSheet(f"color: {ds.TEXT_MUTED}; padding-bottom: {sp.SPACE_2}px;")
        layout.addWidget(self._label)

        self._cards_holder = QWidget(self)
        self._cards_layout = QVBoxLayout(self._cards_holder)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(sp.SPACE_2)
        self._cards_layout.addStretch(1)
        layout.addWidget(self._cards_holder, 1)

        # Style the rail itself
        self.setObjectName("FleetRail")
        self.setStyleSheet(
            f"""
            QWidget#FleetRail {{
                background-color: {ds.CANVAS};
                border-right: 1px solid {ds.BORDER_SUBTLE};
            }}
            QLabel#FleetRailLabel {{
                color: {ds.TEXT_MUTED};
                background: transparent;
            }}
            """
        )

    # ---- public API --------------------------------------------------------
    def card_count(self) -> int:
        return len(self._cards)

    def card_for(self, window_id: str) -> FleetCard | None:
        return self._cards.get(window_id)

    def upsert_card(self, window_id: str, character_name: str, accent: tuple[int, int, int]) -> FleetCard:
        if window_id in self._cards:
            return self._cards[window_id]
        card = FleetCard(window_id, character_name, accent, parent=self._cards_holder)
        card.clicked.connect(self.pilot_focus_requested.emit)
        card.context_requested.connect(self.pilot_context_requested.emit)
        # Insert before the trailing stretch (last item)
        insert_at = max(0, self._cards_layout.count() - 1)
        self._cards_layout.insertWidget(insert_at, card)
        self._cards[window_id] = card
        return card

    def remove_card(self, window_id: str) -> bool:
        card = self._cards.pop(window_id, None)
        if card is None:
            return False
        self._cards_layout.removeWidget(card)
        card.deleteLater()
        return True

    def clear(self) -> None:
        for window_id in list(self._cards.keys()):
            self.remove_card(window_id)

    def card_order(self) -> list[str]:
        return list(self._cards.keys())

    def set_pilot_system(self, window_id: str, system: str | None, *, stale: bool = False) -> bool:
        card = self._cards.get(window_id)
        if card is None:
            return False
        card.set_system(system, stale=stale)
        return True

    def set_pilot_capture_health(self, window_id: str, health: str) -> bool:
        card = self._cards.get(window_id)
        if card is None:
            return False
        card.set_capture_health(health)
        return True

    def set_pilot_focused(self, window_id: str, focused: bool) -> None:
        for wid, card in self._cards.items():
            card.set_focused(wid == window_id and focused)

    def set_pilot_threat(
        self,
        window_id: str,
        level: ThreatLevel | None,
        system: str | None = None,
        alpha: float = 1.0,
        distance: int | None = None,
    ) -> bool:
        card = self._cards.get(window_id)
        if card is None:
            return False
        card.set_threat_state(level, system, alpha=alpha, distance=distance)
        return True
