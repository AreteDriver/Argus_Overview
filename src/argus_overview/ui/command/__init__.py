"""Argus Command Center — flagship widgets.

The ``command`` package groups the widgets that compose the
identity-defining Command tab:

* :class:`CommandCenterHeader` — top brand chrome
* :class:`FleetRail` — pinned pilot identity surface
* :class:`AttentionQueue` and :class:`OpsTimeline` — right-side overlays
* :class:`OperationalTruthBar` — bottom status footer
* :class:`CommandPalette` — ⌘K action gateway
* :class:`CommandCenterWidget` — assembled flagship shell
"""
from __future__ import annotations

from argus_overview.ui.command.attention import (
    AttentionItem,
    AttentionItemRow,
    AttentionQueue,
    OpsEntry,
    OpsTimeline,
)
from argus_overview.ui.command.fleet_rail import FleetCard, FleetRail
from argus_overview.ui.command.header import (
    BrandMark,
    CommandCenterHeader,
    OperationalStatusLine,
)
from argus_overview.ui.command.operational_truth import OperationalTruthBar
from argus_overview.ui.command.palette import CommandPalette, PaletteEntry
from argus_overview.ui.command.shell import CommandCenterWidget

__all__ = [
    "AttentionItem",
    "AttentionItemRow",
    "AttentionQueue",
    "BrandMark",
    "CommandCenterHeader",
    "CommandCenterWidget",
    "CommandPalette",
    "FleetCard",
    "FleetRail",
    "OperationalStatusLine",
    "OperationalTruthBar",
    "OpsEntry",
    "OpsTimeline",
    "PaletteEntry",
]
