"""Argus Command Center — Tactical Grid.

The Tactical Grid is the *preview host* in the center of the Command
tab. It is not a frame-grabber grid (those live in MainTab's scroll
area). It is an **identity / status grid**: each connected EVE client
is represented by a fixed-shape card that surfaces:

  * Accent avatar (deterministic, MD5-derived)
  * Pilot name + system + threat state
  * Capture health + last-update age
  * Click-to-focus affordance

The grid is fixed-column (3 cols), so layout is predictable at any
window width. Cards do not capture live frames — the operator's
"what does the screen look like" question is still answered by the
Overview tab's ``WindowPreviewWidget``. The grid answers the
complementary question: **"which windows are connected, where are
they, and which are flagged?"**
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from argus_overview.intel.parser import ThreatLevel
from argus_overview.ui.design_system import colors as ds
from argus_overview.ui.design_system import metrics as dm
from argus_overview.ui.design_system import spacing as sp
from argus_overview.ui.design_system import typography as ty
from argus_overview.ui.design_system.painting import draw_threat_accent

# Re-use the threat RGB palette from main_tab so visual semantics match.
try:
    from argus_overview.ui.main_tab import THREAT_BORDER_COLORS
except ImportError:  # pragma: no cover — fallback if main_tab relocated
    THREAT_BORDER_COLORS = {
        ThreatLevel.CLEAR: (0, 200, 100),
        ThreatLevel.INFO: (0, 180, 230),
        ThreatLevel.WARNING: (255, 170, 0),
        ThreatLevel.DANGER: (255, 90, 30),
        ThreatLevel.CRITICAL: (255, 40, 40),
    }


THREAT_LETTERS = {"danger": "D", "warning": "W", "critical": "C", "info": "I"}


def _initials(name: str) -> str:
    parts = [p for p in name.replace("_", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


class TacticalCard(QFrame):
    """Wide identity card rendered in the Tactical Grid.

    Unlike ``FleetCard`` (vertical strip, 64px tall), this card is
    ~120px tall and shows more at a glance: avatar, name, system,
    capture-health pill, last-update timestamp, and a "PREVIEW"
    surface placeholder where live frames would mount if/when this
    widget hosts them.
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
        self._stale: bool = False
        self._capture_health: str = "live"
        self._last_update: float = time.monotonic()
        self._threat_level: ThreatLevel | None = None
        self._threat_alpha: float = 0.0
        self._threat_distance: int | None = None
        self._has_focus: bool = False

        self.setObjectName(f"TacticalCard::{window_id}")
        self.setMinimumSize(220, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(120)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(sp.SPACE_3, sp.SPACE_3, sp.SPACE_3, sp.SPACE_3)
        layout.setSpacing(sp.SPACE_2)

        # Top row — avatar + name + focus indicator
        from PySide6.QtWidgets import QHBoxLayout

        top = QWidget(self)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(sp.SPACE_2)
        self._avatar = QLabel(_initials(character_name))
        self._avatar.setObjectName("TacticalAvatar")
        self._avatar.setFixedSize(28, 28)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self._avatar)

        name_block = QWidget(top)
        name_layout = QVBoxLayout(name_block)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(0)
        self._name = QLabel(character_name)
        self._name.setObjectName("TacticalName")
        f = QFont(self._name.font())
        f.setPointSize(ty.PRIMARY_LABEL_PT)
        f.setWeight(QFont.Weight.Bold)
        self._name.setFont(f)
        name_layout.addWidget(self._name)
        self._system_label = QLabel("—")
        self._system_label.setObjectName("TacticalSystem")
        sf = QFont(self._system_label.font())
        sf.setPointSize(ty.SECONDARY_LABEL_PT)
        self._system_label.setFont(sf)
        name_layout.addWidget(self._system_label)
        top_layout.addWidget(name_block, 1)

        self._threat_chip = QLabel("")
        self._threat_chip.setObjectName("TacticalThreatChip")
        self._threat_chip.setFixedHeight(20)
        self._threat_chip.setMinimumWidth(34)
        self._threat_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self._threat_chip)
        layout.addWidget(top)

        # Body row — capture health pill + last update + preview surface
        body = QWidget(self)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(sp.SPACE_2)

        self._preview_surface = QWidget(self)
        self._preview_surface.setObjectName("TacticalPreviewSurface")
        self._preview_surface.setMinimumHeight(36)
        body_layout.addWidget(self._preview_surface, 1)

        meta_block = QWidget(body)
        meta_layout = QVBoxLayout(meta_block)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(0)
        self._health_label = QLabel("LIVE")
        self._health_label.setObjectName("TacticalHealth")
        meta_layout.addWidget(self._health_label)
        self._age_label = QLabel("now")
        self._age_label.setObjectName("TacticalAge")
        self._age_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        meta_layout.addWidget(self._age_label)
        body_layout.addWidget(meta_block)
        layout.addWidget(body, 1)

        self._apply_styles()
        self._update_threat_chip()
        self._update_tooltip()

    # ---- public API --------------------------------------------------------
    def window_id(self) -> str:
        return self._window_id

    def character_name(self) -> str:
        return self._character_name

    def set_system(self, system: str | None, *, stale: bool = False) -> None:
        self._system = system
        self._stale = stale
        if system and not stale:
            self._update_system_label()
        self._update_tooltip()
        self._apply_styles()

    def set_capture_health(self, health: str) -> None:
        self._capture_health = health
        self._health_label.setText(health.upper())
        self._apply_styles()
        self._update_tooltip()

    def set_last_update(self, ts: float | None = None) -> None:
        self._last_update = ts if ts is not None else time.monotonic()
        self._age_label.setText(self._format_age(self._last_update))
        self._update_tooltip()

    def set_focused(self, focused: bool) -> None:
        self._has_focus = focused
        self._apply_styles()

    def set_threat_state(
        self,
        level: ThreatLevel | None,
        *,
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
        if system is not None:
            self.set_system(system)
        self._update_threat_chip()
        self._update_tooltip()
        self.update()

    def tick_age(self) -> None:
        """Refresh the age label without state change."""
        self._age_label.setText(self._format_age(self._last_update))

    # ---- private helpers ---------------------------------------------------
    def _update_system_label(self) -> None:
        if self._system and not self._stale:
            self._system_label.setText(self._system)
        else:
            self._system_label.setText("Unknown")

    def _update_threat_chip(self) -> None:
        if self._threat_level and self._threat_alpha > 0.0:
            letter = THREAT_LETTERS.get(
                self._threat_level.value.lower(), self._threat_level.value[0].upper()
            )
            if self._threat_distance and self._threat_distance > 0:
                self._threat_chip.setText(f"{letter}+{self._threat_distance}j")
            else:
                self._threat_chip.setText(letter)
        else:
            self._threat_chip.setText("")

    def _format_age(self, ts: float) -> str:
        secs = int(max(0, time.monotonic() - ts))
        if secs < 60:
            return f"{secs}s"
        if secs < 3600:
            return f"{secs // 60}m"
        return f"{secs // 3600}h"

    def _health_color(self) -> str:
        return {
            "live": ds.HEALTHY,
            "static": ds.UNKNOWN,
            "stale": ds.WARNING,
            "error": ds.CRITICAL,
            "paused": ds.TEXT_MUTED,
        }.get(self._capture_health, ds.UNKNOWN)

    def _apply_styles(self) -> None:
        accent = self._accent
        darker = accent.darker(160)
        a_name = accent.name()
        d_name = darker.name()
        text_color = (
            "#0f0f0f"
            if (accent.redF() * 0.299 + accent.greenF() * 0.587 + accent.blueF() * 0.114) > 0.55
            else "#f5f5f5"
        )

        focus_border = ds.BORDER_FOCUS if self._has_focus else ds.BORDER_SUBTLE
        bg = ds.SURFACE if not self._stale else ds.CANVAS

        self.setStyleSheet(
            f"""
            QFrame#{self.objectName()} {{
                background-color: {bg};
                border: 1px solid {focus_border};
                border-left: 3px solid {a_name};
                border-radius: {dm.RADIUS_CARD}px;
            }}
            QFrame#{self.objectName()}:hover {{
                border-color: {ds.BORDER_FOCUS};
                background-color: {ds.SURFACE_HOVER};
            }}
            QLabel#TacticalAvatar {{
                background-color: {a_name};
                border: 1px solid {d_name};
                border-radius: 14px;
                color: {text_color};
                font-weight: 800;
                font-size: 10pt;
            }}
            QLabel#TacticalName {{
                color: {ds.TEXT_PRIMARY};
            }}
            QLabel#TacticalSystem {{
                color: {ds.TEXT_MUTED if self._stale else ds.TEXT_SECONDARY};
            }}
            QLabel#TacticalThreatChip {{
                color: {ds.TEXT_PRIMARY};
                font-weight: 800;
                font-size: 9pt;
                background-color: transparent;
                padding: 0 {sp.SPACE_2}px;
                border-radius: 10px;
            }}
            QLabel#TacticalHealth {{
                color: {self._health_color()};
                font-weight: 800;
                font-size: 9pt;
                letter-spacing: 140%;
            }}
            QLabel#TacticalAge {{
                color: {ds.TEXT_MUTED};
                font-size: 8pt;
                font-family: monospace;
            }}
            QWidget#TacticalPreviewSurface {{
                background-color: {ds.CANVAS};
                border: 1px dashed {ds.BORDER_SUBTLE};
                border-radius: {dm.RADIUS_CARD - 2}px;
            }}
            """
        )

    def _update_tooltip(self) -> None:
        parts = [f"{self._character_name}"]
        if self._system and not self._stale:
            parts.append(f"System: {self._system}")
        if self._threat_level and self._threat_alpha > 0.0:
            line = f"Threat: {self._threat_level.value.upper()}"
            if self._threat_distance:
                line += f" ({self._threat_distance}j)"
            parts.append(line)
        parts.append(f"Capture: {self._capture_health.upper()}")
        parts.append(f"Last update: {self._format_age(self._last_update)} ago")
        if self._has_focus:
            parts.append("● ACTIVE WINDOW")
        parts.append("Click: focus window")
        self.setToolTip("\n".join(parts))

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
        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Space,
        ):
            self.clicked.emit(self._window_id)
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._threat_level and self._threat_alpha > 0.0:
            rgb = THREAT_BORDER_COLORS.get(self._threat_level, (255, 0, 0))
            p = QPainter(self)
            try:
                draw_threat_accent(
                    p,
                    self.rect(),
                    rgb,
                    alpha=self._threat_alpha,
                    edge="right",
                    ribbon_width=3,
                    glow_height=1,
                )
            finally:
                p.end()


class TacticalGrid(QWidget):
    """3-column responsive grid of TacticalCards.

    Columns are fixed at 3 — the grid is wide enough at 1280px to host
    3 columns of ~280px each with comfortable gutter. New cards fill
    column-by-column, top-to-bottom. The grid is a *passive* container:
    it does not capture frames; it renders identity cards from the
    same window manager data the Fleet Rail uses.
    """

    pilot_focus_requested = Signal(str)
    pilot_context_requested = Signal(str, object)

    DEFAULT_COLUMNS = 3

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: dict[str, TacticalCard] = {}
        self._columns: int = self.DEFAULT_COLUMNS

        self.setObjectName("TacticalGrid")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(sp.SPACE_4, sp.SPACE_4, sp.SPACE_4, sp.SPACE_4)
        self._grid.setHorizontalSpacing(sp.SPACE_3)
        self._grid.setVerticalSpacing(sp.SPACE_3)

        self._render_empty()

        self.setStyleSheet(
            f"""
            QWidget#TacticalGrid {{
                background-color: {ds.CANVAS};
            }}
            QWidget#TacticalEmpty {{
                color: {ds.TEXT_MUTED};
                font-style: italic;
                font-size: 10pt;
                padding: {sp.SPACE_5}px;
            }}
            """
        )

    # ---- public API --------------------------------------------------------
    def card_count(self) -> int:
        return len(self._cards)

    def card_for(self, window_id: str) -> TacticalCard | None:
        return self._cards.get(window_id)

    def card_order(self) -> list[str]:
        return list(self._cards.keys())

    def upsert_card(
        self,
        window_id: str,
        character_name: str,
        accent: tuple[int, int, int],
    ) -> TacticalCard:
        if window_id in self._cards:
            return self._cards[window_id]
        card = TacticalCard(window_id, character_name, accent, parent=self)
        card.clicked.connect(self.pilot_focus_requested.emit)
        card.context_requested.connect(self.pilot_context_requested.emit)
        self._cards[window_id] = card
        self._relayout()
        return card

    def remove_card(self, window_id: str) -> bool:
        card = self._cards.pop(window_id, None)
        if card is None:
            return False
        self._grid.removeWidget(card)
        card.deleteLater()
        self._relayout()
        return True

    def clear(self) -> None:
        for window_id in list(self._cards.keys()):
            self.remove_card(window_id)

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
        *,
        system: str | None = None,
        alpha: float = 1.0,
        distance: int | None = None,
    ) -> bool:
        card = self._cards.get(window_id)
        if card is None:
            return False
        card.set_threat_state(level, system=system, alpha=alpha, distance=distance)
        return True

    def set_pilot_last_update(self, window_id: str, ts: float) -> bool:
        card = self._cards.get(window_id)
        if card is None:
            return False
        card.set_last_update(ts)
        return True

    def tick_all(self) -> None:
        for card in self._cards.values():
            card.tick_age()

    # ---- layout ------------------------------------------------------------
    def _clear_grid(self) -> None:
        # Remove all widgets (including the placeholder) without deleting cards
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget() if item else None
            if w and w.parent() is self:
                self._grid.removeWidget(w)
                # Do NOT deleteLater() — cards are owned by self._cards

    def _relayout(self) -> None:
        self._clear_grid()
        if not self._cards:
            self._render_empty()
            return
        # Remove placeholder if present
        placeholder = self._find_placeholder()
        if placeholder is not None:
            self._grid.removeWidget(placeholder)
            placeholder.deleteLater()
        # Lay out by column index, row index
        for idx, wid in enumerate(self._cards.keys()):
            card = self._cards[wid]
            col = idx % self._columns
            row = idx // self._columns
            self._grid.addWidget(card, row, col)

    def _find_placeholder(self) -> QWidget | None:
        for i in range(self._grid.count()):
            item = self._grid.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if w and w.objectName() == "TacticalEmpty":
                return w
        return None

    def _render_empty(self) -> None:
        placeholder = QLabel("Awaiting EVE client connections…", self)
        placeholder.setObjectName("TacticalEmpty")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._grid.addWidget(placeholder, 0, 0, 1, self._columns)
