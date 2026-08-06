"""LAYOUTS tab container — Layout presets + Cycle Control side-by-side.

The operator's mental model: "how your fleet is arranged on screen."
Layout presets (the existing :class:`LayoutsTab` from
:mod:`argus_overview.ui.layouts_tab`) on the left; Cycle Control
(:class:`HotkeysTab`) on the right. Default split is 70/30 so the
visual arrangement grid gets the room it needs.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from argus_overview.ui.hotkeys_tab import HotkeysTab


class LayoutsContainer(QWidget):
    """Top-level LAYOUTS tab.

    The left panel is the existing :class:`LayoutsTab`; the right panel
    is :class:`HotkeysTab`. Splitter state is in-memory only.
    """

    def __init__(
        self,
        layouts_panel: QWidget,
        hotkeys_tab: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("LayoutsContainer")

        splitter = QSplitter(self)
        splitter.setObjectName("LayoutsSplitter")
        splitter.setOrientation(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(4)

        splitter.addWidget(layouts_panel)
        splitter.addWidget(hotkeys_tab)
        # 70/30 default — presets grid gets the bigger slice.
        splitter.setSizes([700, 300])
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(splitter)

        self.splitter = splitter
        self.layouts_panel = layouts_panel
        self.hotkeys_tab = hotkeys_tab


__all__ = ["LayoutsContainer", "HotkeysTab"]
