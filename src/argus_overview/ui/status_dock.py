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
        # PR7: jumps from this chip's character to the alert system. None when
        # same-system or unknown; positive int for adjacent. Renders as +Nj.
        self._threat_distance: int | None = None

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
            line = f"Threat: {self._threat_level.value}"
            if self._threat_distance and self._threat_distance > 0:
                line += f" ({self._threat_distance}j away)"
            parts.append(line)
        parts.append("Click to focus window")
        return "\n".join(parts)

    # ----- public API -------------------------------------------------------
    def set_system(self, system: str | None) -> None:
        self._system = system
        self._system_label.setText(system or "—")
        self.setToolTip(self._tooltip_text())

    def set_threat_state(
        self,
        level: ThreatLevel | None,
        system: str | None = None,
        alpha: float = 1.0,
        distance: int | None = None,
    ) -> None:
        """
        Update threat state for this chip.

        Args:
            level: Threat level. None or CLEAR clears state.
            system: System the alert refers to.
            alpha: Initial alpha [0, 1] for the threat dot. PR6 falloff for
                adjacent-system alerts uses < 1.0.
            distance: Jumps from this chip's character to the alert system.
                None for same-system or unknown. Positive ints render as
                "+Nj" badge next to the threat dot (PR7).
        """
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
            dot_x = self.width() - self.DOT_SIZE - 8
            dot_y = (self.height() - self.DOT_SIZE) // 2
            painter.drawEllipse(dot_x, dot_y, self.DOT_SIZE, self.DOT_SIZE)

            # PR7: distance badge for adjacent-system alerts.
            # Renders as "+Nj" just left of the threat dot in the same color.
            if self._threat_distance and self._threat_distance > 0:
                from PySide6.QtGui import QFont

                badge_text = f"+{self._threat_distance}j"
                font = painter.font()
                badge_font = QFont(font)
                badge_font.setPointSize(7)
                badge_font.setBold(True)
                painter.setFont(badge_font)
                # Foreground stays in the threat color but bumped opaque so
                # it stays legible even when the dot itself is dim.
                text_color = QColor(r, g, b, max(180, alpha))
                painter.setPen(QPen(text_color))
                metrics = painter.fontMetrics()
                text_w = metrics.horizontalAdvance(badge_text)
                # Place to the left of the dot, vertically centered.
                text_x = dot_x - text_w - 3
                text_y = (self.height() + metrics.ascent() - metrics.descent()) // 2
                painter.drawText(text_x, text_y, badge_text)
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
        # PR6 jumps-from filter — set via set_jump_calculator. Default
        # max_jumps=0 keeps the PR5 exact-match-only behavior.
        self._jump_calculator = None
        self._jump_max: int = 0

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

    def set_jump_calculator(self, calculator, max_jumps: int = 1) -> None:
        """Wire an adjacency calculator for the jumps-from filter (PR6)."""
        self._jump_calculator = calculator
        self._jump_max = max(0, int(max_jumps))

    def set_threat_state(self, level: ThreatLevel | None, system: str | None = None) -> int:
        """
        Fan a threat state out to chips, filtered by system.

        Filter rules (mirror WindowManager.apply_threat_state for symmetry):
          1. CLEAR / None level → flush every chip.
          2. system is None / empty → fan to all (legacy fallback).
          3. Otherwise → resolve_tint() per chip. Same-system at full alpha,
             adjacent within max_jumps at falloff alpha, beyond skipped,
             unknown chip-system tinted at full alpha (graceful upgrade).

        Returns count of chips updated.
        """
        from argus_overview.intel.threat_filter import resolve_tint

        flush = level is None or level == ThreatLevel.CLEAR or not system
        count = 0
        calculator = getattr(self, "_jump_calculator", None)
        max_jumps = getattr(self, "_jump_max", 0)
        for chip in list(self._chips.values()):
            try:
                if flush:
                    chip.set_threat_state(level, system)
                    count += 1
                    continue
                chip_system = getattr(chip, "_system", None)
                should_apply, alpha = resolve_tint(
                    known_system=chip_system,
                    alert_system=system,
                    jump_calculator=calculator,
                    max_jumps=max_jumps,
                )
                if not should_apply:
                    continue
                # PR7: surface the jump distance for the +Nj badge.
                distance: int | None = None
                if (
                    alpha < 1.0
                    and chip_system
                    and calculator is not None
                    and chip_system.lower() != system.lower()
                ):
                    try:
                        distance = calculator.distance(chip_system, system)
                    except (AttributeError, TypeError, ValueError):
                        distance = None
                chip.set_threat_state(level, system, alpha=alpha, distance=distance)
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

    def set_character_system(self, character_name: str, system: str | None) -> int:
        """
        Update every chip for a given character. Returns count updated.

        Multi-boxers can run the same character in multiple windows, so
        chips are matched by character_name, not window_id. Source of the
        update is typically CharacterLocationTracker.
        """
        count = 0
        for chip in list(self._chips.values()):
            try:
                if chip.character_name == character_name:
                    chip.set_system(system)
                    count += 1
            except RuntimeError:
                continue
        return count

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
