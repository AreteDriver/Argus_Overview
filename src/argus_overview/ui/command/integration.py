"""Integration helpers — connect CommandCenter widgets to existing
MainWindow signals and data sources.

This module is intentionally additive: it provides wiring helpers
without modifying MainWindowV21. Existing call sites can register an
integration via:

    from argus_overview.ui.command.integration import CommandIntegrator

    integrator = CommandIntegrator(window)
    integrator.attach()

Where ``window`` is any object that exposes the same signals and
properties as MainWindowV21.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from PySide6.QtCore import QObject, Qt, QTimer, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication

from argus_overview.ui.command.attention import AttentionItem, OpsEntry
from argus_overview.ui.command.operational_truth import OperationalTruthBar
from argus_overview.ui.command.palette import CommandPalette, PaletteEntry
from argus_overview.ui.command.shell import CommandCenterWidget


class CommandIntegrator(QObject):
    """Wires a CommandCenterWidget to an existing MainWindow.

    The integrator calls the documented contract surface on the
    ``window`` argument — see :class:`MainWindowV21` for the canonical
    methods (``activate_window``, ``show_layout_chooser``, ``theme_manager``,
    ``layout_manager``, ``auto_discovery``, ``system_status_bar``). The
    integrator is permissive *only* at the boundary so window-less
    command-center previews don't crash; signal-path calls go through
    the real methods.
    """

    def __init__(self, window: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._window = window
        self._logger = logging.getLogger(__name__)
        self._command: CommandCenterWidget | None = None
        self._palette: CommandPalette | None = None
        self._shortcut: QShortcut | None = None
        self._alert_count: int = 0
        self._last_attention_threats: dict[str, float] = {}

    # ---- attach -----------------------------------------------------------
    def attach(self) -> CommandCenterWidget:
        """Create the CommandCenter, return its widget. Idempotent."""
        if self._command is not None:
            return self._command
        self._command = CommandCenterWidget()
        self._wire_header()
        self._wire_fleet_rail()
        self._install_palette_shortcut()
        self._seed_subsystem_health()
        self._install_polling()
        # Seed alert count + header state from existing UI
        self._refresh_command_state()
        return self._command

    def command(self) -> CommandCenterWidget | None:
        return self._command

    def palette(self) -> CommandPalette | None:
        return self._palette

    # ---- header wiring -----------------------------------------------------
    def _wire_header(self) -> None:
        if not self._command:
            return
        self._command.layout_chooser_requested.connect(self._open_layout_chooser)
        self._command.palette_requested.connect(self._open_palette)

    @Slot()
    def _open_layout_chooser(self) -> None:
        # Defer to existing main window's layout chooser if available.
        for attr in ("show_layout_chooser", "_show_layout_chooser"):
            if hasattr(self._window, attr):
                getattr(self._window, attr)()
                self._record_ops("layout", "Layout chooser opened")
                return
        self._logger.info("Layout chooser requested but MainWindow has no show_layout_chooser")

    @Slot()
    def _open_palette(self) -> None:
        if self._palette is None:
            self._palette = CommandPalette(self._window)
            self._wire_palette_entries()
        rect = self._window.geometry()
        self._palette.open_over(rect)

    # ---- palette ------------------------------------------------------------
    def _install_palette_shortcut(self) -> None:
        sc = QShortcut(self._window)
        sc.setKey(QKeySequence("Ctrl+K"))
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(self._open_palette)
        self._shortcut = sc

    def _wire_palette_entries(self) -> None:
        if not self._palette:
            return
        entries: list[PaletteEntry] = []

        def make_focus_entry(wid: str, name: str) -> PaletteEntry:
            def _handler():
                # Pivot through main_window's chip click for symmetry.
                if hasattr(self._window, "_on_chip_clicked"):
                    self._window._on_chip_clicked(wid)
                    self._record_ops("pilot", f"Focused {name}", pilot=name)
                elif hasattr(self._window, "focus_window"):
                    self._window.focus_window(wid)
                self._open_palette()  # ensure palette close; entry already close on accept

            return PaletteEntry(
                id=f"focus::{wid}",
                title=f"Focus {name}",
                subtitle="Bring this client's window to front",
                category="pilot",
                keywords=("focus", "window", "client", name.lower()),
                handler=_handler,
            )

        rail = self._command.fleet_rail() if self._command else None
        if rail:
            for wid in rail.card_order():
                card = rail.card_for(wid)
                if card:
                    entries.append(make_focus_entry(wid, card.character_name()))

        # Layout preset entries (read-only summaries)
        entries.append(
            PaletteEntry(
                id="system::refresh",
                title="Refresh window list",
                subtitle="Rescan for EVE clients and rebuild previews",
                category="system",
                keywords=("refresh", "scan", "discover"),
                handler=lambda: (
                    getattr(self._window, "auto_discovery", None)
                    and self._window.auto_discovery.run_once()
                ),
            )
        )
        entries.append(
            PaletteEntry(
                id="system::lock",
                title="Lock windows",
                subtitle="Prevent EVE windows from being moved by Argus",
                category="action",
                keywords=("lock", "stop moving"),
                handler=lambda: (
                    hasattr(self._window, "layout_manager")
                    and self._window.layout_manager.set_locked(True)
                ),
            )
        )
        entries.append(
            PaletteEntry(
                id="system::unlock",
                title="Unlock windows",
                subtitle="Allow layout operations to move EVE windows",
                category="action",
                keywords=("unlock", "move", "layout"),
                handler=lambda: (
                    hasattr(self._window, "layout_manager")
                    and self._window.layout_manager.set_locked(False)
                ),
            )
        )
        # Theme switching
        for theme in ("dark", "light", "eve", "high_contrast"):
            entries.append(
                PaletteEntry(
                    id=f"theme::{theme}",
                    title=f"Theme: {theme.replace('_', ' ').title()}",
                    subtitle="Switch Argus appearance theme",
                    category="theme",
                    keywords=("theme", "appearance", "color", theme),
                    handler=lambda t=theme: self._apply_theme(t),
                )
            )
        self._palette.set_entries(entries)

    def _apply_theme(self, theme: str) -> None:
        mgr = getattr(self._window, "theme_manager", None)
        if mgr and hasattr(mgr, "apply_theme"):
            try:
                # Real signature is apply_theme(name, app=None) — pass the
                # running QApplication instance so stylesheet propagation
                # cascades to every existing widget.
                mgr.apply_theme(theme, QApplication.instance())
                self._record_ops("system", f"Theme switched to {theme}")
            except (RuntimeError, ValueError, TypeError) as exc:
                self._logger.warning("Theme switch failed: %s", exc)

    # ---- fleet rail wiring -------------------------------------------------
    def _wire_fleet_rail(self) -> None:
        if not self._command:
            return
        self._command.pilot_focus_requested.connect(self._on_pilot_focus)
        self._command.pilot_context_requested.connect(self._on_pilot_context)
        self._command.grid_holder().pilot_focus_requested.connect(self._on_pilot_focus)
        self._command.grid_holder().pilot_context_requested.connect(self._on_pilot_context)
        # Mirror existing main tab characters into the rail on demand
        self._mirror_main_tab_characters()

    def _mirror_main_tab_characters(self) -> None:
        """Read the main_tab preview list and create FleetCards + TacticalCards."""
        try:
            main_tab = getattr(self._window, "main_tab", None)
            if not main_tab or not self._command:
                return
            rail = self._command.fleet_rail()
            grid = self._command.grid_holder()
            wm = getattr(main_tab, "window_manager", None)
            # Pre-existing helpers vary across versions. Defensive walk.
            if wm and hasattr(wm, "known_windows"):
                from argus_overview.ui.main_tab import character_accent_color

                for wid, display_name in wm.known_windows().items():
                    accent_color = character_accent_color(display_name)
                    accent = (
                        accent_color.red(),
                        accent_color.green(),
                        accent_color.blue(),
                    )
                    if not rail.card_for(wid):
                        rail.upsert_card(wid, display_name, accent)
                    if not grid.card_for(wid):
                        grid.upsert_card(wid, display_name, accent)
        except (AttributeError, RuntimeError) as exc:
            self._logger.debug("Character mirror skipped: %s", exc)

    @Slot(str)
    def _on_pilot_focus(self, window_id: str) -> None:
        rail = self._command.fleet_rail() if self._command else None
        name = window_id
        if rail:
            card = rail.card_for(window_id)
            if card:
                name = card.character_name()
        if hasattr(self._window, "activate_window"):
            try:
                self._window.activate_window(window_id)
                self._record_ops("pilot", f"Focused {name}", pilot=name)
                return
            except (TypeError, RuntimeError) as exc:
                self._logger.debug("activate_window(%s) failed: %s", window_id, exc)
        # Fallback: at minimum, set the rail's focus state for visual feedback
        if self._command:
            self._command.fleet_rail().set_pilot_focused(window_id, True)

    @Slot(str, object)
    def _on_pilot_context(self, window_id: str, global_pos: object) -> None:
        # Forward to main_tab context menu if available
        main_tab = getattr(self._window, "main_tab", None)
        if main_tab:
            for attr in ("show_window_context_menu", "_on_window_context_menu"):
                if hasattr(main_tab, attr):
                    try:
                        getattr(main_tab, attr)(window_id, global_pos)
                        return
                    except (TypeError, RuntimeError):
                        pass

    # ---- operational truth bar -------------------------------------------
    def _seed_subsystem_health(self) -> None:
        if not self._command:
            return
        bar: OperationalTruthBar = self._command.truth()
        # Forward existing system status bar state where available
        existing = getattr(self._window, "system_status_bar", None)
        if existing and hasattr(existing, "_status"):
            for key, status in existing._status.items():
                detail = existing._detail.get(key, "")
                bar.set_subsystem(key, status, detail)
        else:
            bar.set_subsystem("capture", "healthy", "capture workers running")
            bar.set_subsystem("hotkeys", "healthy", "hotkey listener active")
            bar.set_subsystem("discovery", "healthy", "auto-discovery idle")
            bar.set_subsystem("intel", "healthy", "intel pipeline active")
            bar.set_subsystem("location", "healthy", "location tracker active")

    # ---- polling ----------------------------------------------------------
    def _install_polling(self) -> None:
        # 1-second timer for header alert count + ops timestamp updates.
        self._poll = QTimer(self)
        self._poll.setInterval(1000)
        self._poll.timeout.connect(self._refresh_command_state)
        self._poll.start()

    def _refresh_command_state(self) -> None:
        if not self._command:
            return
        rail = self._command.fleet_rail()
        header = self._command.header()
        truth = self._command.truth()
        grid = self._command.grid_holder()

        fleet_count = rail.card_count()
        active_threats = sum(
            1
            for wid in rail.card_order()
            if getattr(rail.card_for(wid), "_threat_level", None)
            and getattr(rail.card_for(wid), "_threat_alpha", 0.0) > 0.0
        )
        self._alert_count = active_threats
        header.update_state(
            fleet_count=fleet_count, alert_count=active_threats, intel_health="live"
        )
        truth.set_alert_count(active_threats)
        # Refresh age labels on TacticalCards so the operator sees
        # freshness at a glance during long sessions.
        grid.tick_all()

    # ---- ops timeline ----------------------------------------------------
    def _record_ops(
        self, category: str, label: str, detail: str = "", pilot: str | None = None
    ) -> None:
        if not self._command:
            return
        entry = OpsEntry(
            timestamp=time.time(), label=label, detail=detail, pilot=pilot, category=category
        )
        self._command.ops_timeline().add_entry(entry)

    def record_ops(
        self, category: str, label: str, detail: str = "", pilot: str | None = None
    ) -> None:
        """Public method for callers to log operational events."""
        self._record_ops(category, label, detail=detail, pilot=pilot)

    # ---- attention queue --------------------------------------------------
    def surface_attention(
        self,
        category: str,
        title: str,
        *,
        detail: str = "",
        pilot: str | None = None,
        system: str | None = None,
        severity: str = "info",
    ) -> None:
        if not self._command:
            return
        item = AttentionItem(
            id=f"{category}::{title}::{time.monotonic()}",
            category=category,
            title=title,
            detail=detail,
            pilot=pilot,
            system=system,
            severity=severity,
        )
        self._command.attention().add_item(item)
