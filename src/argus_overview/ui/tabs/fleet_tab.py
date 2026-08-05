"""FLEET tab container — Roster + Intel side-by-side.

The operator's mental model: "your people, and the intel that affects
them." CharactersTeamsTab on the left, IntelTab on the right. Default
split is 60/40 so the character/team grid gets the room it needs.

This is a thin container — both inner widgets keep their existing
dependencies and signal surface. The split state is persisted only in
memory; future work could write it to settings.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget


class FleetTab(QWidget):
    """Top-level FLEET tab. Roster (left) + Intel (right) via QSplitter.

    Args:
        characters_tab: A constructed ``CharactersTeamsTab``.
        intel_tab: A constructed ``IntelTab``.
    """

    def __init__(
        self,
        characters_tab: QWidget,
        intel_tab: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("FleetTab")

        splitter = QSplitter(self)
        splitter.setObjectName("FleetSplitter")
        splitter.setOrientation(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(4)

        splitter.addWidget(characters_tab)
        splitter.addWidget(intel_tab)
        # 60/40 default — characters tab gets the bigger slice.
        splitter.setSizes([600, 400])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(splitter)

        self.splitter = splitter
        self.characters_tab = characters_tab
        self.intel_tab = intel_tab
