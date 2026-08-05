"""Argus Command Center — Command Palette.

Press ⌘K (Ctrl+K on Linux/Windows) to open. Type to filter across:
  * Pilot names (focus window)
  * Layout presets (apply)
  * Themes (switch)
  * Subsystem checks (status)
  * Hard actions (lock windows, refresh, save layout)

The palette is the operator's muscle-memory gateway — every action is
reachable in two keystrokes from anywhere in Argus.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QPropertyAnimation,
    QRect,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QFont,
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from argus_overview.ui.design_system import colors as ds
from argus_overview.ui.design_system import metrics as dm
from argus_overview.ui.design_system import spacing as sp


@dataclass
class PaletteEntry:
    """One entry in the palette — display + filter + handler."""
    id: str
    title: str
    subtitle: str = ""
    category: str = "action"  # pilot | layout | theme | system | action
    keywords: tuple[str, ...] = field(default_factory=tuple)
    handler: Callable[[], None] | None = None
    enabled: bool = True


class CommandPalette(QDialog):
    """Modal palette dialog.

    Opens centered over the main window. Filter narrows as user types.
    Enter executes the highlighted entry. Esc closes. Up/Down arrows
    move the highlight.
    """

    executed = Signal(str)  # entry id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CommandPalette")
        self.setWindowTitle("Argus // Command Palette")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setModal(True)
        self.setFixedSize(720, 460)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._entries: list[PaletteEntry] = []
        self._build_ui()
        self._wire_shortcuts()
        self._apply_styles()

    # ---- public API --------------------------------------------------------
    def set_entries(self, entries: list[PaletteEntry]) -> None:
        self._entries = list(entries)
        self._refresh_list("")

    def register(self, entry: PaletteEntry) -> None:
        self._entries.append(entry)

    def open_over(self, parent_rect: QRect) -> None:
        """Open the palette horizontally centered, vertically anchored
        to the upper third of the parent window for visibility.
        """
        x = parent_rect.center().x() - self.width() // 2
        y = parent_rect.top() + int(parent_rect.height() * 0.18)
        self.move(max(parent_rect.left() + 24, x), max(parent_rect.top() + 24, y))
        self._input.clear()
        self._refresh_list("")
        self.show()
        self.raise_()
        self._input.setFocus()
        # Subtle scale-in animation for confidence
        self._scale_effect()

    # ---- UI construction ---------------------------------------------------
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Body
        body = QFrame(self)
        body.setObjectName("CommandPaletteBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        outer.addWidget(body)

        # Header — input
        header = QFrame(body)
        header.setObjectName("CommandPaletteHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(sp.SPACE_5, sp.SPACE_4, sp.SPACE_4, sp.SPACE_4)
        h_layout.setSpacing(sp.SPACE_3)

        glyph = QLabel("⌘", self)
        glyph.setObjectName("CommandPaletteGlyph")
        g = QFont(glyph.font())
        g.setPointSize(18)
        g.setBold(True)
        glyph.setFont(g)
        h_layout.addWidget(glyph)

        self._input = QLineEdit(header)
        self._input.setObjectName("CommandPaletteInput")
        self._input.setPlaceholderText("Focus pilot, apply layout, switch theme…")
        self._input.textChanged.connect(self._refresh_list)
        self._input.returnPressed.connect(self._activate_current)
        # Forward arrow keys to the list
        self._input.installEventFilter(self)
        h_layout.addWidget(self._input, 1)

        body_layout.addWidget(header)

        # Sub-header — categories legend
        legend = QFrame(body)
        legend.setObjectName("CommandPaletteLegend")
        l_layout = QHBoxLayout(legend)
        l_layout.setContentsMargins(sp.SPACE_5, sp.SPACE_2, sp.SPACE_4, sp.SPACE_2)
        l_layout.setSpacing(sp.SPACE_5)
        for label, color in (
            ("PILOT", ds.BORDER_FOCUS),
            ("LAYOUT", ds.HEALTHY),
            ("THEME", ds.WARNING),
            ("SYSTEM", ds.INFO),
            ("ACTION", ds.CRITICAL),
        ):
            chip = QLabel(f"● {label}")
            chip.setStyleSheet(f"color: {color}; font-size: 8pt; font-weight: 700; letter-spacing: 140%;")
            l_layout.addWidget(chip)
        l_layout.addStretch(1)
        body_layout.addWidget(legend)

        # List
        self._list = QListWidget(body)
        self._list.setObjectName("CommandPaletteList")
        self._list.itemActivated.connect(self._activate_item)
        self._list.itemClicked.connect(self._activate_item)
        body_layout.addWidget(self._list, 1)

        # Footer
        footer = QFrame(body)
        footer.setObjectName("CommandPaletteFooter")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(sp.SPACE_5, sp.SPACE_2, sp.SPACE_4, sp.SPACE_2)
        f_layout.setSpacing(sp.SPACE_5)
        for label, key in (
            ("↵  EXECUTE", "ENTER"),
            ("↑↓  NAVIGATE", "ARROWS"),
            ("ESC  CLOSE", "ESC"),
        ):
            cell = QLabel(f"<b style='color:{ds.TEXT_SECONDARY}'>{label}</b>"
                          f"  <span style='color:{ds.TEXT_MUTED}'>{key}</span>")
            cell.setTextFormat(Qt.TextFormat.RichText)
            f_layout.addWidget(cell)
        f_layout.addStretch(1)
        body_layout.addWidget(footer)

    def _wire_shortcuts(self) -> None:
        pass
        # Esc to close handled in keyPressEvent

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            QDialog#CommandPalette {{
                background-color: transparent;
            }}
            QFrame#CommandPaletteBody {{
                background-color: {ds.CANVAS};
                border: 1px solid {ds.BORDER_STRONG};
                border-radius: {dm.RADIUS_PANEL}px;
            }}
            QFrame#CommandPaletteHeader {{
                background-color: {ds.SURFACE};
                border: none;
                border-bottom: 1px solid {ds.BORDER_SUBTLE};
                border-top-left-radius: {dm.RADIUS_PANEL}px;
                border-top-right-radius: {dm.RADIUS_PANEL}px;
            }}
            QLabel#CommandPaletteGlyph {{
                color: {ds.BORDER_FOCUS};
            }}
            QLineEdit#CommandPaletteInput {{
                background-color: transparent;
                color: {ds.TEXT_PRIMARY};
                border: none;
                font-size: 14pt;
                font-weight: 500;
            }}
            QLineEdit#CommandPaletteInput:focus {{
                border: none;
            }}
            QFrame#CommandPaletteLegend {{
                background-color: transparent;
                border-bottom: 1px solid {ds.BORDER_SUBTLE};
            }}
            QListWidget#CommandPaletteList {{
                background-color: transparent;
                border: none;
                outline: 0;
            }}
            QListWidget#CommandPaletteList::item {{
                color: {ds.TEXT_PRIMARY};
                padding: 12px 24px;
                border-bottom: 1px solid {ds.SURFACE};
                font-size: 11pt;
                font-weight: 500;
            }}
            QListWidget#CommandPaletteList::item:selected {{
                background-color: {ds.SURFACE_RAISED};
                border-left: 3px solid {ds.BORDER_FOCUS};
                color: {ds.TEXT_PRIMARY};
            }}
            QFrame#CommandPaletteFooter {{
                background-color: transparent;
                border-top: 1px solid {ds.BORDER_SUBTLE};
            }}
            """
        )

    # ---- interactions ------------------------------------------------------
    def _refresh_list(self, query: str) -> None:
        self._list.clear()
        q = query.strip().lower()
        # Score: exact start > contains > keyword match
        scored = []
        for entry in self._entries:
            if not entry.enabled:
                continue
            score = self._score(entry, q)
            if q == "" or score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: (-x[0], x[1].title.lower()))
        if not scored:
            placeholder = QListWidgetItem("No matches")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self._list.addItem(placeholder)
            return
        for _, entry in scored[:30]:
            label = QListWidgetItem(f"  {entry.title}")
            if entry.subtitle:
                label.setToolTip(entry.subtitle)
                label.setText(f"  {entry.title}\n    {entry.subtitle}")
            label.setData(Qt.ItemDataRole.UserRole, entry.id)
            label.setData(Qt.ItemDataRole.UserRole + 1, entry)
            self._list.addItem(label)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _score(self, entry: PaletteEntry, q: str) -> int:
        if not q:
            return 1  # show everything in declared order
        haystack = " ".join([entry.title.lower(), entry.subtitle.lower(),
                             entry.category.lower(), *entry.keywords]).strip()
        if entry.title.lower().startswith(q):
            return 100
        if q in haystack:
            return 50
        # Loose word match (each word in q is a prefix of some word in haystack)
        words = [w for w in q.split() if w]
        if all(any(tok.startswith(w) for tok in haystack.split()) for w in words):
            return 25
        return 0

    def _activate_current(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        self._activate_item(item)

    def _activate_item(self, item: QListWidgetItem) -> None:
        entry = item.data(Qt.ItemDataRole.UserRole + 1)
        if not isinstance(entry, PaletteEntry):
            return
        if entry.handler:
            entry.handler()
        self.executed.emit(entry.id)
        self.accept()

    def _scale_effect(self) -> None:
        # Subtle pop-in via window opacity (avoids QGraphicsEffect cost).
        original_opacity = self.windowOpacity()
        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(120)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(original_opacity or 1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.start()

    # ---- events ------------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            if self._list.hasFocus():
                super().keyPressEvent(event)
                return
            # Move focus to list first
            self._list.setFocus()
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self._activate_current()
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self._input and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                self._list.setFocus()
                self._list.keyPressEvent(event)
                return True
        return super().eventFilter(obj, event)
