"""IA-aligned tab containers introduced in v3.3 OPS.

The four top-level tabs (``COMMAND``, ``FLEET``, ``LAYOUTS``, ``SYSTEM``)
are thin :class:`QWidget` containers that compose the existing v2.2
widgets. Each container is named after its operator-facing label so
:mod:`argus_overview.ui.main_window_v21` can wire it directly.

Construction signatures:

- ``CommandTab(parent=None)`` — no project dependencies; the inner
  ``CommandCenterWidget`` is created unseeded.
- ``FleetTab(characters_tab, intel_tab, parent=None)`` — pass already-
  constructed ``CharactersTeamsTab`` and ``IntelTab`` widgets.
- ``LayoutsContainer(layouts_panel, hotkeys_tab, parent=None)`` — pass
  already-constructed ``LayoutsTab`` and ``HotkeysTab``.
- ``SystemTab(settings_tab, settings_sync_tab, parent=None)`` — pass
  already-constructed ``SettingsTab`` and ``SettingsSyncTab``.

The containers don't reach into the MainWindowV21 init dance; they
take already-built inner widgets and stitch them together.
"""
from __future__ import annotations

from argus_overview.ui.tabs.command_tab import CommandTab
from argus_overview.ui.tabs.fleet_tab import FleetTab
from argus_overview.ui.tabs.layouts_tab import LayoutsContainer
from argus_overview.ui.tabs.system_tab import SystemTab

__all__ = ["CommandTab", "FleetTab", "LayoutsContainer", "SystemTab"]
