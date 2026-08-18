"""Argus Command Center — flagship top-level shell.

The Command Center is the operator's primary landing surface. It is
not another tab alongside the others — it is the *identity* of Argus.
Other tabs (Layouts, Characters, Hotkeys, Intel, Sync, Settings)
remain; the Command tab is what users open first and what they come
back to.

Composition (3x3 grid):

  +----------------+--------------------+--------------------+
  |  HEADER BAR    |                    |                    |
  +----------------+--------------------+--------------------+
  |                |  TACTICAL GRID     |  ATTENTION QUEUE   |
  |  FLEET RAIL    |  (preview cards)   |  + OPS TIMELINE    |
  |  (pinned       |                    |                    |
  |  identity)     |                    |                    |
  +----------------+--------------------+--------------------+
  |  OPERATIONAL TRUTH BAR  (health, alerts, layout, version) |

This module exposes one QWidget: ``CommandCenterWidget``. It is built
to slot into an existing QTabWidget as a top-level tab without
disrupting the other tabs.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QWidget  # noqa: F401 — kept for back-compat type hints

from argus_overview.ui.command.attention import AttentionQueue, OpsTimeline
from argus_overview.ui.command.fleet_rail import FleetRail
from argus_overview.ui.command.header import CommandCenterHeader
from argus_overview.ui.command.operational_truth import OperationalTruthBar
from argus_overview.ui.command.palette import CommandPalette, PaletteEntry
from argus_overview.ui.command.tactical_grid import TacticalGrid
from argus_overview.ui.design_system import colors as ds


class CommandCenterWidget(QWidget):
    """Flagship Command Center layout."""

    palette_requested = Signal()
    layout_chooser_requested = Signal()
    pilot_focus_requested = Signal(str)
    pilot_context_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CommandCenter")

        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setHorizontalSpacing(0)
        root.setVerticalSpacing(0)

        # ROW 1 — Header (spans all three columns)
        self._header = CommandCenterHeader(self)
        self._header.layout_chooser_clicked.connect(self.layout_chooser_requested.emit)
        self._header.palette_hint_activated.connect(self.palette_requested.emit)
        root.addWidget(self._header, 0, 0, 1, 3)
        root.setRowMinimumHeight(0, self._header.height())

        # ROW 2 COL 0 — Fleet Rail (left strip)
        self._fleet_rail = FleetRail(self)
        self._fleet_rail.pilot_focus_requested.connect(self.pilot_focus_requested.emit)
        self._fleet_rail.pilot_context_requested.connect(self.pilot_context_requested.emit)
        root.addWidget(self._fleet_rail, 1, 0)
        root.setColumnMinimumWidth(0, 192)

        # ROW 2 COL 1 — Tactical Grid (center preview/identity host)
        self._grid_holder = TacticalGrid(self)
        self._grid_holder.setObjectName("TacticalGridHolder")
        self._grid_holder.pilot_focus_requested.connect(self.pilot_focus_requested.emit)
        self._grid_holder.pilot_context_requested.connect(self.pilot_context_requested.emit)
        root.addWidget(self._grid_holder, 1, 1)
        root.setColumnStretch(1, 1)

        # ROW 2 COL 2 — Attention Queue + Ops Timeline
        from PySide6.QtWidgets import QVBoxLayout

        right_panel = QWidget(self)
        right_panel.setObjectName("CommandRightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._attention = AttentionQueue(right_panel)
        self._ops = OpsTimeline(right_panel)
        right_layout.addWidget(self._attention, 1)
        right_layout.addWidget(self._ops, 1)
        root.addWidget(right_panel, 1, 2)
        root.setColumnMinimumWidth(2, 280)
        root.setColumnStretch(2, 0)

        # ROW 3 — Operational Truth (spans all three columns)
        self._truth = OperationalTruthBar(self)
        self._truth.layout_chooser_clicked.connect(self.layout_chooser_requested.emit)
        root.addWidget(self._truth, 2, 0, 1, 3)
        root.setRowMinimumHeight(2, self._truth.height())

        # Set stretch so the grid grows
        root.setRowStretch(1, 1)

        self.setStyleSheet(
            f"""
            QWidget#CommandCenter {{
                background-color: {ds.CANVAS};
            }}
            QWidget#TacticalGridHolder {{
                background-color: {ds.CANVAS};
                border-left: 1px solid {ds.BORDER_SUBTLE};
                border-right: 1px solid {ds.BORDER_SUBTLE};
            }}
            QWidget#CommandRightPanel {{
                background-color: {ds.CANVAS};
                border-left: 1px solid {ds.BORDER_SUBTLE};
            }}
            """
        )

    # ---- accessors ---------------------------------------------------------
    def header(self) -> CommandCenterHeader:
        return self._header

    def fleet_rail(self) -> FleetRail:
        return self._fleet_rail

    def grid_holder(self) -> TacticalGrid:
        return self._grid_holder

    def attention(self) -> AttentionQueue:
        return self._attention

    def ops_timeline(self) -> OpsTimeline:
        return self._ops

    def truth(self) -> OperationalTruthBar:
        return self._truth

    def palette(  # type: ignore[override]
        self, entries: list[PaletteEntry] | None = None
    ) -> CommandPalette:
        pal = CommandPalette(self.window())
        if entries is not None:
            pal.set_entries(entries)
        return pal
