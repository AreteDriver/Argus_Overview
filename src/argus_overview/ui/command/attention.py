"""Argus Command Center — Attention Queue & Operations Timeline.

These two widgets form the operator's tactical awareness layer on the
right side of the Command tab. They collapse to a label when empty and
expand smoothly when items arrive.

* AttentionQueue surfaces events that demand operator decision:
  intel threats, capture failures, location staleness, layout apply
  errors. Each item is dismissible and individually actionable.

* OpsTimeline surfaces the recent operational history: layout applied,
  layout restored, pilot focused, intel cleared, hotkey pressed. Acts
  as a confidence-building "what did I just do" feed.

The visual is deliberate: small, dense, monospace-aligned times, color
dots not icons. Information first.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from argus_overview.ui.design_system import colors as ds
from argus_overview.ui.design_system import metrics as dm
from argus_overview.ui.design_system import spacing as sp
from argus_overview.ui.design_system import typography as ty


@dataclass
class AttentionItem:
    """An event demanding operator decision or awareness."""

    id: str
    category: str  # threat | capture | location | layout | system
    title: str
    detail: str = ""
    pilot: str | None = None
    system: str | None = None
    timestamp: float = field(default_factory=time.monotonic)
    severity: str = "info"  # info | warning | critical
    acknowledged: bool = False

    def severity_color(self) -> str:
        return {
            "info": ds.INFO,
            "warning": ds.WARNING,
            "critical": ds.CRITICAL,
        }.get(self.severity, ds.TEXT_SECONDARY)


@dataclass
class OpsEntry:
    """A passive operational log entry."""

    timestamp: float
    label: str  # e.g., "Layout applied"
    detail: str = ""
    pilot: str | None = None
    category: str = "system"  # layout | capture | intel | hotkey | pilot | system

    def category_color(self) -> str:
        return {
            "layout": ds.BORDER_FOCUS,
            "capture": ds.INFO,
            "intel": ds.CRITICAL,
            "hotkey": ds.WARNING,
            "pilot": ds.HEALTHY,
            "system": ds.TEXT_MUTED,
        }.get(self.category, ds.TEXT_MUTED)


@dataclass
class AttentionItemRow(QFrame):
    """One row in the Attention Queue.

    A compact card with a colored left rule (severity), title in
    primary weight, detail in muted, dismiss button on the right.
    """

    item_dismissed = Signal(str)  # item id
    item_acted = Signal(str)  # item id

    def __init__(self, item: AttentionItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item = item
        self.setObjectName(f"AttentionRow::{item.id}")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp.SPACE_3, sp.SPACE_2, sp.SPACE_2, sp.SPACE_2)
        layout.setSpacing(sp.SPACE_3)

        # Severity rule
        self._rule = QWidget(self)
        self._rule.setObjectName("AttentionRule")
        self._rule.setFixedSize(3, 28)
        self._rule.setStyleSheet(f"background-color: {item.severity_color()};")
        layout.addWidget(self._rule)

        # Text block
        text_block = QWidget(self)
        text_layout = QVBoxLayout(text_block)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        title = QLabel(item.title)
        title.setStyleSheet(
            f"color: {ds.TEXT_PRIMARY}; font-weight: 700; font-size: 10pt;"
        )
        title.setWordWrap(False)
        text_layout.addWidget(title)
        sub_text = " · ".join(filter(None, [
            f"[{item.category.upper()}]",
            item.pilot,
            item.system,
        ])) + ("  " + item.detail if item.detail else "")
        if sub_text.strip():
            sub = QLabel(sub_text.strip())
            sub.setStyleSheet(
                f"color: {ds.TEXT_MUTED}; font-size: 9pt;"
            )
            sub.setWordWrap(True)
            text_layout.addWidget(sub)
        layout.addWidget(text_block, 1)

        # Action button
        action_btn = QPushButton("·", self)
        action_btn.setObjectName("AttentionAct")
        action_btn.setFixedSize(24, 24)
        action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        action_btn.setToolTip("Acknowledge this item")
        action_btn.clicked.connect(lambda: self.item_acted.emit(self.item.id))
        action_btn.setStyleSheet(
            f"""
            QPushButton#AttentionAct {{
                background: transparent;
                border: 1px solid {ds.BORDER_SUBTLE};
                border-radius: 12px;
                color: {ds.TEXT_SECONDARY};
                font-weight: 800;
            }}
            QPushButton#AttentionAct:hover {{
                background: {ds.SURFACE_RAISED};
                border-color: {ds.BORDER_FOCUS};
                color: {ds.TEXT_PRIMARY};
            }}
            """
        )
        layout.addWidget(action_btn)

        # Style the row itself
        self.setStyleSheet(
            f"""
            QFrame#{self.objectName()} {{
                background-color: {ds.SURFACE};
                border: 1px solid {ds.BORDER_SUBTLE};
                border-radius: {dm.RADIUS_CARD}px;
            }}
            QFrame#{self.objectName()}:hover {{
                border-color: {ds.BORDER_STRONG};
                background-color: {ds.SURFACE_RAISED};
            }}
            """
        )


class AttentionQueue(QWidget):
    """Right-side panel of events demanding operator response.

    Items appear at top, age out after 5 minutes unless acknowledged.
    Empty state shows a quiet 'All clear' line.
    """

    item_acted = Signal(str)

    RETENTION_SECONDS = 300

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: dict[str, AttentionItem] = {}
        self._rows: dict[str, AttentionItemRow] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(sp.SPACE_2)

        # Header
        header = QWidget(self)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(sp.SPACE_3, sp.SPACE_2, sp.SPACE_3, sp.SPACE_2)
        h_layout.setSpacing(0)
        title = QLabel("ATTENTION QUEUE", self)
        title.setObjectName("AttentionTitle")
        f = QFont(title.font())
        f.setPointSize(ty.SECTION_HEADING_PT)
        f.setWeight(QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 180)
        title.setFont(f)
        h_layout.addWidget(title)
        h_layout.addStretch(1)
        self._count_label = QLabel("·", self)
        self._count_label.setObjectName("AttentionCount")
        self._count_label.setStyleSheet(f"color: {ds.CRITICAL}; font-weight: 800; font-size: 10pt;")
        h_layout.addWidget(self._count_label)
        layout.addWidget(header)

        # Content
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self._scroll, 1)

        self._content = QWidget(self)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(sp.SPACE_2, sp.SPACE_2, sp.SPACE_2, sp.SPACE_2)
        self._content_layout.setSpacing(sp.SPACE_2)
        self._content_layout.addStretch(1)
        self._scroll.setWidget(self._content)

        self._render_empty()

    def _render_empty(self) -> None:
        # Clear existing children except the trailing stretch
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            w = item.widget() if item else None
            if w:
                w.deleteLater()

        empty = QLabel("·  ALL CLEAR  ·", self)
        empty.setObjectName("AttentionEmptyState")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setStyleSheet(
            f"color: {ds.HEALTHY}; font-weight: 800; letter-spacing: 220%;"
            f" font-size: 9pt; padding: {sp.SPACE_5}px;"
        )
        # Insert at index 0 so stretch remains at end
        self._content_layout.insertWidget(0, empty)

    def _refresh_count(self) -> None:
        active = sum(1 for i in self._items.values() if not i.acknowledged)
        if active == 0:
            self._count_label.setText("")
        else:
            self._count_label.setText(str(active))

    def add_item(self, item: AttentionItem) -> None:
        self._items[item.id] = item
        # Remove the ALL CLEAR placeholder first (synchronous), so the
        # next paint pass can't briefly show both empty + row.
        self._invalidate_empty()
        row = AttentionItemRow(item, parent=self._content)
        row.item_acted.connect(self._on_ack)
        row.item_acted.connect(self.item_acted.emit)
        # Insert at index 0 (newest first)
        self._content_layout.insertWidget(0, row)
        self._rows[item.id] = row
        self._refresh_count()

    def _invalidate_empty(self) -> None:
        # Remove the ALL CLEAR placeholder if present. We tag it with
        # an objectName "AttentionEmptyState" so we can identify it
        # without relying on type checks.
        for i in range(self._content_layout.count()):
            item = self._content_layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if w is None or w is self:
                continue
            if w.objectName() == "AttentionEmptyState":
                self._content_layout.removeWidget(w)
                w.deleteLater()
                return

    def _on_ack(self, item_id: str) -> None:
        item = self._items.get(item_id)
        if item is None:
            return
        item.acknowledged = True
        row = self._rows.pop(item_id, None)
        if row is not None:
            self._content_layout.removeWidget(row)
            row.deleteLater()
        self._refresh_count()
        if not self._rows and self._items:
            self._render_empty()

    def has_active(self) -> bool:
        return any(not i.acknowledged for i in self._items.values())


class OpsTimeline(QWidget):
    """Right-side panel of recent operational history.

    Acts as a confidence feed — operators see their last few actions
    immediately reflected, which builds trust that the system is
    capturing intent correctly.
    """

    ENTRIES_MAX = 24

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entries: list[OpsEntry] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(sp.SPACE_2)

        header = QWidget(self)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(sp.SPACE_3, sp.SPACE_2, sp.SPACE_3, sp.SPACE_2)
        h_layout.setSpacing(0)
        title = QLabel("OPERATIONS TIMELINE", self)
        title.setObjectName("OpsTimelineTitle")
        f = QFont(title.font())
        f.setPointSize(ty.SECTION_HEADING_PT)
        f.setWeight(QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 180)
        title.setFont(f)
        h_layout.addWidget(title)
        layout.addWidget(header)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self._scroll, 1)

        self._body = QWidget(self)
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(sp.SPACE_2, sp.SPACE_2, sp.SPACE_2, sp.SPACE_2)
        self._body_layout.setSpacing(0)
        self._body_layout.addStretch(1)
        self._scroll.setWidget(self._body)

        self._render_empty()

    def _render_empty(self) -> None:
        # Clear children that are placeholders (QLabel) but not real rows
        while self._body_layout.count() > 1:
            item = self._body_layout.takeAt(0)
            w = item.widget() if item else None
            if w:
                w.deleteLater()
        empty = QLabel("Awaiting first operator input…", self)
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setStyleSheet(
            f"color: {ds.TEXT_MUTED}; font-style: italic; padding: {sp.SPACE_5}px;"
        )
        self._body_layout.insertWidget(0, empty)

    def add_entry(self, entry: OpsEntry) -> None:
        # Insert at top, evict oldest at bottom
        self._entries.insert(0, entry)
        if len(self._entries) > self.ENTRIES_MAX:
            self._entries.pop()
        # Remove placeholder
        for i in range(self._body_layout.count()):
            item = self._body_layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if w is None or w is self:
                continue
            # The placeholder is a QLabel; ops rows are _OpsRow widgets
            if w.__class__.__name__ == "QLabel":
                try:
                    txt = w.text()  # type: ignore[attr-defined]
                except AttributeError:
                    continue
                if txt.startswith("Awaiting"):
                    self._body_layout.removeWidget(w)
                    w.deleteLater()
                    break
        # Add visual row
        row = _OpsRow(entry, parent=self._body)
        self._body_layout.insertWidget(0, row)
        # Trim UI rows
        while self._body_layout.count() > self.ENTRIES_MAX + 1:
            item = self._body_layout.takeAt(self._body_layout.count() - 2)
            w = item.widget() if item else None
            if w:
                w.deleteLater()


class _OpsRow(QWidget):
    """Single compact row in the operations timeline."""

    def __init__(self, entry: OpsEntry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(22)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        from PySide6.QtWidgets import QHBoxLayout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp.SPACE_2, 0, sp.SPACE_2, 0)
        layout.setSpacing(sp.SPACE_2)

        self._time = QLabel(self._format_time(entry.timestamp))
        self._time.setObjectName("OpsRowTime")
        self._time.setStyleSheet(
            f"color: {ds.TEXT_MUTED}; font-family: monospace; font-size: 9pt;"
        )
        self._time.setMinimumWidth(56)
        layout.addWidget(self._time)

        self._dot = QLabel("●", self)
        self._dot.setStyleSheet(
            f"color: {entry.category_color()}; font-size: 8pt;"
        )
        self._dot.setFixedWidth(10)
        layout.addWidget(self._dot)

        text = entry.label
        if entry.pilot:
            text += f" · {entry.pilot}"
        if entry.detail:
            text += f" — {entry.detail}"
        self._text = QLabel(text, self)
        self._text.setStyleSheet(
            f"color: {ds.TEXT_SECONDARY}; font-size: 9pt;"
        )
        layout.addWidget(self._text, 1)

    def _format_time(self, ts: float) -> str:
        return datetime.fromtimestamp(ts).strftime("%H:%M:%S")
