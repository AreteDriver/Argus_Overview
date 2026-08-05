"""SYSTEM tab container — Settings + Sync side-by-side.

The operator's mental model: "app + EVE folder configuration."
SettingsTab (the application config panel) on the left; SettingsSyncTab
(the EVE folder sync panel) on the right. Default split is 60/40.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget


class SystemTab(QWidget):
    """Top-level SYSTEM tab. Settings (left) + Sync (right) via QSplitter."""

    def __init__(
        self,
        settings_tab: QWidget,
        settings_sync_tab: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SystemTab")

        splitter = QSplitter(self)
        splitter.setObjectName("SystemSplitter")
        splitter.setOrientation(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(4)

        splitter.addWidget(settings_tab)
        splitter.addWidget(settings_sync_tab)
        # 60/40 default — settings gets the bigger slice.
        splitter.setSizes([600, 400])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(splitter)

        self.splitter = splitter
        self.settings_tab = settings_tab
        self.settings_sync_tab = settings_sync_tab
