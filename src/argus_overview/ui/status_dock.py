"""
Character Status Dock — horizontal strip of character chips.

Each chip surfaces per-character state that EVE-O Preview cannot:
character avatar (initials in an accent color), system name, and a
threat-tint dot driven by the same intel pipeline that tints preview
borders. Click a chip to focus the matching window.

PR2 of the intel-aware UI uplift. Pairs with WindowPreviewWidget's
threat-tint border (PR1) so glanceable threat state is visible whether
you're looking at a thumbnail grid or the dock.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from argus_overview.intel.parser import ThreatLevel
from argus_overview.ui.main_tab import THREAT_BORDER_COLORS

# Stable accent palette — same hue per character across sessions
CHIP_ACCENT_COLORS: list[tuple[int, int, int]] = [
    (255, 100, 100),
    (100, 255, 100),
    (100, 150, 255),
    (255, 200, 80),
    (220, 120, 220),
    (100, 220, 220),
    (255, 165, 60),
    (170, 130, 255),
]


def accent_for(name: str) -> QColor:
    """Deterministic accent color for a character name."""
    r, g, b = CHIP_ACCENT_COLORS[abs(hash(name)) % len(CHIP_ACCENT_COLORS)]
    return QColor(r, g, b)


def _initials(name: str) -> str:
    parts = [p for p in name.replace("_", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


class CharacterChip(QFrame):
    """
    A single chip in the StatusDock.

    Layout (left to right):
      [ avatar 28x28 ] [ name ]      [ system pill ]   [ threat dot ]
    """

    clicked = Signal(str)  # window_id

    AVATAR_SIZE = 28
    DOT_SIZE = 10

    def __init__(
        self,
        window_id: str,
        character_name: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.window_id = window_id
        self.character_name = character_name
        self._accent: QColor = accent_for(character_name)
        self._system: str | None = None
        self._threat_level: ThreatLevel | None = None
        self._threat_alpha: float = 0.0

        self.setFixedHeight(40)
        self.setMinimumWidth(160)
        self.setMaximumWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_base_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 8, 4)
        layout.setSpacing(8)

        # Avatar — a fixed-size frame painted with initials in the accent color
        self._avatar = QLabel(_initials(character_name))
        self._avatar.setFixedSize(self.AVATAR_SIZE, self.AVATAR_SIZE)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_avatar_style()
        layout.addWidget(self._avatar)

        # Name label (primary, bold)
        self._name_label = QLabel(character_name)
        self._name_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        self._name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._name_label)

        # System label (secondary)
        self._system_label = QLabel("—")
        self._system_label.setStyleSheet("color: #aaa; font-size: 9pt;")
        self._system_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._system_label)

        # Threat dot is painted in paintEvent (no widget needed — keeps chip compact)

        self.setToolTip(self._tooltip_text())

    # ----- styling helpers --------------------------------------------------
    def _apply_base_style(self) -> None:
        self.setStyleSheet(
            """
            CharacterChip {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 6px;
            }
            CharacterChip:hover {
                background-color: #353535;
                border-color: #6a6a6a;
            }
            """
        )

    def _update_avatar_style(self) -> None:
        a = self._accent
        darker = a.darker(160)
        # luminance-based contrast for the initials text
        luminance = (a.red() * 299 + a.green() * 587 + a.blue() * 114) / 1000
        text_color = "#0f0f0f" if luminance > 140 else "#f5f5f5"
        self._avatar.setStyleSheet(
            f"""
            background-color: {a.name()};
            border: 1px solid {darker.name()};
            border-radius: {self.AVATAR_SIZE // 2}px;
            color: {text_color};
            font-weight: bold;
            font-size: 10pt;
            """
        )

    def _tooltip_text(self) -> str:
        parts = [self.character_name]
        if self._system:
            parts.append(f"System: {self._system}")
        if self._threat_level is not None:
            parts.append(f"Threat: {self._threat_level.value}")
        parts.append("Click to focus window")
        return "\n".join(parts)

    # ----- public API -------------------------------------------------------
    def set_system(self, system: str | None) -> None:
        self._system = system
        self._system_label.setText(system or "—")
        self.setToolTip(self._tooltip_text())

    def set_threat_state(
        self, level: ThreatLevel | None, system: str | None = None, alpha: float = 1.0
    ) -> None:
        if level is None or level == ThreatLevel.CLEAR:
            self._threat_level = None
            self._threat_alpha = 0.0
        else:
            self._threat_level = level
            self._threat_alpha = max(0.0, min(1.0, alpha))
        if system is not None:
            self.set_system(system)
        else:
            self.setToolTip(self._tooltip_text())
        self.update()

    # ----- events -----------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.window_id)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._threat_level is None or self._threat_alpha <= 0.0:
            return

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            r, g, b = THREAT_BORDER_COLORS.get(self._threat_level, (255, 255, 255))
            alpha = max(0, min(255, int(230 * self._threat_alpha)))
            color = QColor(r, g, b, alpha)
            painter.setPen(QPen(color.darker(140), 1))
            painter.setBrush(QBrush(color))
            # Draw threat dot vertically centered, left of the right edge
            x = self.width() - self.DOT_SIZE - 8
            y = (self.height() - self.DOT_SIZE) // 2
            painter.drawEllipse(x, y, self.DOT_SIZE, self.DOT_SIZE)
        finally:
            painter.end()


class StatusDock(QWidget):
    """
    Horizontal strip of CharacterChip widgets.

    Mounts above the preview grid in MainTab. Designed to mirror the set
    of active preview windows: one chip per window_id. Chips emit
    chip_clicked when activated; the dock re-emits to the parent.
    """

    chip_clicked = Signal(str)  # window_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._chips: dict[str, CharacterChip] = {}

        self.setFixedHeight(56)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(self._scroll)

        self._strip = QWidget()
        self._strip_layout = QHBoxLayout(self._strip)
        self._strip_layout.setContentsMargins(4, 2, 4, 2)
        self._strip_layout.setSpacing(6)
        self._strip_layout.addStretch()  # push chips left, fill empty space right
        self._scroll.setWidget(self._strip)

        self.setStyleSheet(
            """
            StatusDock {
                background-color: #1f1f1f;
                border-bottom: 1px solid #3a3a3a;
            }
            """
        )

    # ----- public API -------------------------------------------------------
    def chip_count(self) -> int:
        return len(self._chips)

    def has_chip(self, window_id: str) -> bool:
        return window_id in self._chips

    def add_chip(self, window_id: str, character_name: str) -> CharacterChip | None:
        if window_id in self._chips:
            return None
        chip = CharacterChip(window_id, character_name, parent=self._strip)
        chip.clicked.connect(self.chip_clicked.emit)
        # Insert before the trailing stretch (last item)
        insert_at = max(0, self._strip_layout.count() - 1)
        self._strip_layout.insertWidget(insert_at, chip)
        self._chips[window_id] = chip
        return chip

    def remove_chip(self, window_id: str) -> bool:
        chip = self._chips.pop(window_id, None)
        if chip is None:
            return False
        self._strip_layout.removeWidget(chip)
        chip.deleteLater()
        return True

    def clear(self) -> None:
        for window_id in list(self._chips.keys()):
            self.remove_chip(window_id)

    def set_threat_state(self, level: ThreatLevel | None, system: str | None = None) -> int:
        """Fan out a single threat state to every chip. Returns count updated."""
        count = 0
        for chip in list(self._chips.values()):
            try:
                chip.set_threat_state(level, system)
                count += 1
            except RuntimeError:
                continue
        return count

    def set_chip_system(self, window_id: str, system: str | None) -> bool:
        chip = self._chips.get(window_id)
        if chip is None:
            return False
        chip.set_system(system)
        return True

    def sync_from_window_ids(self, desired: dict[str, str]) -> tuple[list[str], list[str]]:
        """
        Bulk diff: ensure chips match `desired` mapping of window_id -> name.

        Returns (added_ids, removed_ids).
        """
        existing = set(self._chips.keys())
        target = set(desired.keys())
        added = []
        removed = []
        for window_id in existing - target:
            if self.remove_chip(window_id):
                removed.append(window_id)
        for window_id in target - existing:
            name = desired[window_id]
            if self.add_chip(window_id, name) is not None:
                added.append(window_id)
        return added, removed
