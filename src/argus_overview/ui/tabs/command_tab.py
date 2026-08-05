"""COMMAND tab container — hosts the flagship Command Center.

Replaces the v2.2 Overview/MainTab at the IA level. The legacy
:class:`MainTab` remains the source of ``window_manager`` (consumed by
:class:`CommandIntegrator` for character mirroring) — it is not
hosted inside this container, only referenced.

The container exposes the CommandCenterWidget directly so the
:mod:`argus_overview.ui.command.integration` module can wire its
signals and slots without knowing about the IA layer.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from argus_overview.ui.command.shell import CommandCenterWidget


class CommandTab(QWidget):
    """Top-level COMMAND tab. Hosts the flagship Command Center.

    Forwards the CommandCenterWidget's signals verbatim so the
    :class:`CommandIntegrator` can subscribe at the IA boundary rather
    than reach into the inner widget. Adds nothing on top of the
    center — IA overlays go elsewhere.
    """

    palette_requested = Signal()
    layout_chooser_requested = Signal()
    pilot_focus_requested = Signal(str)
    pilot_context_requested = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CommandTab")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.command_center = CommandCenterWidget(self)
        self.command_center.palette_requested.connect(self.palette_requested.emit)
        self.command_center.layout_chooser_requested.connect(
            self.layout_chooser_requested.emit
        )
        self.command_center.pilot_focus_requested.connect(self.pilot_focus_requested.emit)
        self.command_center.pilot_context_requested.connect(self.pilot_context_requested.emit)

        layout.addWidget(self.command_center)
