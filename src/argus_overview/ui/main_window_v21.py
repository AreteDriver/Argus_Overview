"""Top-level application window (QMainWindow) with tabbed interface.

Architecture role:
    Owns and orchestrates every core subsystem: capture engine, character
    manager, layout manager, alert detector, hotkey manager, auto-discovery,
    settings, and system tray.  Acts as the signal hub connecting tab widgets
    to core modules and to each other.

Threading model:
    The window and all Qt widgets live on the **main (GUI) thread**.
    Background work is delegated to:

    * ``WindowCaptureThreaded`` — daemon worker threads for screenshot
      capture (see ``core.window_capture_threaded``).
    * ``HotkeyManager`` — background listener thread for global hotkeys
      (callbacks are invoked on the listener thread and must be
      thread-safe or use ``QMetaObject.invokeMethod`` to bounce to the
      GUI thread).
    * ``AutoDiscovery`` — uses a ``QTimer`` on the main thread, so its
      signals (``new_character_found``, ``character_gone``) are emitted
      on the main thread and safe to connect directly to slots here.

Key signals (emitted → consumed):
    * ``MainTab.character_detected(str, str)`` → ``_on_character_detected``
      — new EVE window matched to a character name.
    * ``MainTab.layout_applied(str)`` → ``_on_layout_applied``
      — a layout preset was applied to EVE windows.
    * ``CharactersTeamsTab.team_selected(object)`` → ``_on_team_selected``
      — user selected a team in the Roster tab.
    * ``SettingsTab.settings_changed(str, object)`` → ``_apply_setting``
      — a setting value changed; routed to the appropriate subsystem.
    * ``AutoDiscovery.new_character_found(str, str, str)`` →
      ``_on_new_character_discovered`` — EVE client window appeared.
    * ``AutoDiscovery.character_gone(str, str)`` → ``_on_character_gone``
      — EVE client window closed.
    * ``SystemTray.*_requested`` signals → corresponding ``_slots`` above
      for tray menu actions.

Lifecycle:
    ``__init__`` creates all subsystems and starts capture, hotkeys, and
    auto-discovery.  ``closeEvent`` performs ordered teardown: disconnect
    signals, stop timers, stop threads, hide tray, persist settings.
"""

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Import version and core modules
from argus_overview import __version__
from argus_overview.core.character_manager import CharacterManager
from argus_overview.core.cycle_controller import CycleController
from argus_overview.core.discovery import AutoDiscovery
from argus_overview.core.eve_settings_sync import EVESettingsSync
from argus_overview.core.hotkey_manager import HotkeyManager
from argus_overview.core.layout_manager import LayoutManager
from argus_overview.core.window_capture_threaded import WindowCaptureThreaded
from argus_overview.ui.action_registry import ActionRegistry, PrimaryHome
from argus_overview.ui.menu_builder import MenuBuilder
from argus_overview.ui.settings_manager import SettingsManager
from argus_overview.ui.system_status_bar import SystemStatusBar
from argus_overview.ui.themes import get_theme_manager
from argus_overview.ui.tray import SystemTray


class MainWindowV21(QMainWindow):
    """Main application window with tabbed interface v2.2"""

    # v2.2 IA: the original six-tab ordering. Preserved as a class-level
    # constant so callers can look up indices by label (e.g. Settings)
    # without sprinkling magic numbers through the codebase.
    # Tab labels in registration order. Phase 4 IA: 4 tabs only —
    # COMMAND, FLEET, LAYOUTS, SYSTEM. The Settings entry point now lands
    # on the SYSTEM container (which holds SettingsTab on the left).
    _TAB_LABELS: list[str] = [
        "Command",
        "Fleet",
        "Layouts",
        "System",
    ]

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle(f"Argus Overview v{__version__}")
        self.setMinimumSize(960, 600)
        self._is_quitting = False
        self._auto_discovery_connected = False
        self._bulk_import_active = False
        self._bulk_import_dirty_characters = False
        self._bulk_import_dirty_groups = False
        self._pending_discovery_names: list[str] = []
        self._discovery_notification_timer = QTimer(self)
        self._discovery_notification_timer.setSingleShot(True)
        self._discovery_notification_timer.setInterval(1200)
        self._discovery_notification_timer.timeout.connect(self._flush_discovery_notifications)
        self._status_refresh_timer = QTimer(self)
        self._status_refresh_timer.setSingleShot(True)
        self._status_refresh_timer.setInterval(150)
        self._status_refresh_timer.timeout.connect(self._flush_main_tab_status_refresh)

        # Set window icon
        self._set_window_icon()

        # Initialize core modules (singleton instances)
        self.logger.info("Initializing core modules...")
        self.character_manager = CharacterManager()
        self.layout_manager = LayoutManager()
        self.hotkey_manager = HotkeyManager()
        self.settings_sync = EVESettingsSync()
        self.settings_manager = SettingsManager()

        # Initialize capture system with settings (after settings_manager)
        capture_workers = self.settings_manager.get("performance.capture_workers", 4)
        self.capture_system = WindowCaptureThreaded(max_workers=capture_workers)
        self.cycle_controller = CycleController(self.capture_system, self.settings_manager)

        # v2.2: Auto-discovery
        self.auto_discovery = AutoDiscovery(
            interval_seconds=self.settings_manager.get("general.auto_discovery_interval", 5)
        )

        # v2.2: Window cycling state
        self.cycling_index = 0  # Current position in cycling group
        self.current_cycling_group = "Default"  # Active cycling group name
        self._pending_cycle_direction: int | None = None
        self._cycle_timer = QTimer(self)
        self._cycle_timer.setSingleShot(True)
        self._cycle_timer.setInterval(80)  # 80ms debounce — fast enough to feel instant
        self._cycle_timer.timeout.connect(self._perform_cycle)

        # v2.2: Theme manager
        self.theme_manager = get_theme_manager()

        # Validate and apply settings
        self.settings_manager.validate()
        self._apply_initial_settings()

        # v2.2: Apply theme from settings
        theme = self.settings_manager.get("appearance.theme", "dark")
        self.theme_manager.apply_theme(theme)

        # Create menu bar
        self._create_menu_bar()

        # Create central widget with tab system
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Tab widget
        self.tabs = QTabWidget()
        from argus_overview.ui.design_system import colors as ds
        from argus_overview.ui.design_system import metrics as dm

        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {ds.CANVAS};
            }}
            QTabBar::tab {{
                background: {ds.SURFACE};
                color: {ds.TEXT_SECONDARY};
                padding: 6px 14px;
                border-top-left-radius: {dm.RADIUS_CONTROL}px;
                border-top-right-radius: {dm.RADIUS_CONTROL}px;
            }}
            QTabBar::tab:selected {{
                background: {ds.SURFACE_RAISED};
                color: {ds.TEXT_PRIMARY};
            }}
            QTabBar::tab:hover {{
                background: {ds.SURFACE_HOVER};
            }}
            QSplitter::handle:horizontal {{
                background: {ds.BORDER_SUBTLE};
                width: 2px;
            }}
            QSplitter::handle:vertical {{
                background: {ds.BORDER_SUBTLE};
                height: 2px;
            }}
        """)
        layout.addWidget(self.tabs)

        # Create tabs (order is preserved by _TAB_LABELS).
        self._create_tabs()

        # Connect cross-tab signals
        self._connect_signals()

        # v2.2: Create system tray
        self._create_system_tray()

        # PR3: System status bar — per-subsystem health indicators
        self._create_system_status_bar()

        # v2.2: Register hotkeys
        self._register_hotkeys()

        # Start systems
        self.logger.info("Starting capture system, hotkey manager, and auto-discovery...")
        self.capture_system.start()
        self.hotkey_manager.start()

        # v2.2: Start auto-discovery if enabled
        self._ensure_auto_discovery_state()
        QTimer.singleShot(250, self._run_startup_assistant)

        # PR4: per-character location tracker (Local channel logs)
        self._init_location_tracker()

        self.logger.info("Main window v2.2 initialized successfully")

    def _connect_auto_discovery(self):
        """Connect auto-discovery signals exactly once."""
        if self._auto_discovery_connected:
            return

        self.auto_discovery.new_character_found.connect(
            self._on_new_character_discovered,
            Qt.ConnectionType.UniqueConnection,
        )
        self.auto_discovery.character_gone.connect(
            self._on_character_gone,
            Qt.ConnectionType.UniqueConnection,
        )
        self._auto_discovery_connected = True

    def _disconnect_auto_discovery(self):
        """Disconnect auto-discovery signals if they were connected."""
        if not self._auto_discovery_connected:
            return

        try:
            self.auto_discovery.new_character_found.disconnect(self._on_new_character_discovered)
        except (RuntimeError, TypeError):
            pass

        try:
            self.auto_discovery.character_gone.disconnect(self._on_character_gone)
        except (RuntimeError, TypeError):
            pass

        self._auto_discovery_connected = False

    def _ensure_auto_discovery_state(self):
        """Synchronize auto-discovery wiring and runtime state with settings."""
        enabled = self.settings_manager.get("general.auto_discovery", True)
        interval = self.settings_manager.get("general.auto_discovery_interval", 5)

        self.auto_discovery.set_interval(interval)

        if enabled:
            self._connect_auto_discovery()
            if not self.auto_discovery.scan_timer.isActive():
                self.auto_discovery.start()
        else:
            self.auto_discovery.stop()

    def _init_location_tracker(self) -> None:
        """Start the per-character location tracker if enabled."""
        from argus_overview.intel.character_location import CharacterLocationTracker

        enabled = self.settings_manager.get("intel.track_character_locations", True)
        if not enabled:
            self.location_tracker = None
            return
        self.location_tracker = CharacterLocationTracker(parent=self)
        self.location_tracker.character_system_changed.connect(self._on_character_system_changed)
        self.location_tracker.start()

        # PR6: wire one shared JumpCalculator into both threat fan-out paths
        # so adjacent-system alerts also tint at reduced intensity. max_jumps
        # is gated on intel.threat_jumps_threshold (default 1).
        self._init_threat_jump_filter()

    def _init_threat_jump_filter(self) -> None:
        """Wire a shared JumpCalculator into the manager + dock fan-out."""
        from argus_overview.intel.jumps import JumpCalculator

        max_jumps = int(self.settings_manager.get("intel.threat_jumps_threshold", 1))
        if max_jumps <= 0:
            self.jump_calculator = None
            return
        self.jump_calculator = JumpCalculator()
        if not hasattr(self, "main_tab"):
            return
        wm = getattr(self.main_tab, "window_manager", None)
        if wm is not None and hasattr(wm, "set_jump_calculator"):
            wm.set_jump_calculator(self.jump_calculator, max_jumps=max_jumps)
        dock = getattr(self.main_tab, "status_dock", None)
        if dock is not None and hasattr(dock, "set_jump_calculator"):
            dock.set_jump_calculator(self.jump_calculator, max_jumps=max_jumps)

    @Slot(str, str)
    def _on_character_system_changed(self, character_name: str, system: str) -> None:
        """Forward per-character system updates to the dock + window manager."""
        if not hasattr(self, "main_tab"):
            return
        wm = getattr(self.main_tab, "window_manager", None)
        if wm is not None and hasattr(wm, "set_character_system"):
            wm.set_character_system(character_name, system)
        dock = getattr(self.main_tab, "status_dock", None)
        if dock is not None and hasattr(dock, "set_character_system"):
            dock.set_character_system(character_name, system)

    def _create_system_tray(self):
        """Create system tray icon (v2.4 - uses ActionRegistry)"""
        self.system_tray = SystemTray(self)

        # Connect tray signals (all actions sourced from ActionRegistry)
        self.system_tray.show_hide_requested.connect(self._toggle_visibility)
        self.system_tray.toggle_thumbnails_requested.connect(self._toggle_thumbnails)
        self.system_tray.minimize_all_requested.connect(self._minimize_all_windows)
        self.system_tray.restore_all_requested.connect(self._restore_all_windows)
        self.system_tray.profile_selected.connect(self._on_profile_selected)
        self.system_tray.settings_requested.connect(self._show_settings)
        self.system_tray.reload_config_requested.connect(self._reload_config)
        self.system_tray.quit_requested.connect(self._quit_application)

        # Load saved profiles (get_all_presets returns List[LayoutPreset])
        profiles = self.layout_manager.get_all_presets()
        profile_names = [p.name for p in profiles]
        self.system_tray.set_profiles(profile_names)

        # Show tray icon
        self.system_tray.show()
        self.logger.info("System tray initialized (ActionRegistry)")

    def _create_system_status_bar(self) -> None:
        """PR3: create per-subsystem health indicator bar in the status bar."""
        try:
            statusbar = self.statusBar()
        except RuntimeError:
            # Defensive: tests patch QMainWindow.__init__ so statusBar is unavailable.
            self.system_status_bar = None
            return
        self.system_status_bar = SystemStatusBar()
        statusbar.addPermanentWidget(self.system_status_bar)

        # Initial states
        self.system_status_bar.set_status("capture", "healthy", "capture workers running")
        self.system_status_bar.set_status("discovery", "healthy", "auto-discovery idle")
        self.system_status_bar.set_status("intel", "healthy", "intel pipeline active")
        self.system_status_bar.set_status("location", "healthy", "location tracker active")

        # Wire hotkey health signal
        self.hotkey_manager.health_changed.connect(self._on_hotkey_health_changed)

        # Seed current hotkey health if already known
        hk_status, hk_detail = self.hotkey_manager.get_health()
        self.system_status_bar.set_status("hotkeys", hk_status, hk_detail)

    @Slot(str, str)
    def _on_hotkey_health_changed(self, status: str, detail: str) -> None:
        """PR3: update hotkeys indicator when HotkeyManager reports health change."""
        status_bar = getattr(self, "system_status_bar", None)
        if status_bar is not None:
            status_bar.set_status("hotkeys", status, detail)

    def _register_hotkeys(self):
        """Register global hotkeys (v2.2)"""
        # Minimize all
        minimize_combo = self.settings_manager.get("hotkeys.minimize_all", "<ctrl>+<shift>+m")
        self.hotkey_manager.register_hotkey(
            "minimize_all", minimize_combo, self._minimize_all_windows
        )

        # Restore all
        restore_combo = self.settings_manager.get("hotkeys.restore_all", "<ctrl>+<shift>+r")
        self.hotkey_manager.register_hotkey("restore_all", restore_combo, self._restore_all_windows)

        # Toggle thumbnails
        toggle_combo = self.settings_manager.get("hotkeys.toggle_thumbnails", "<ctrl>+<shift>+t")
        self.hotkey_manager.register_hotkey(
            "toggle_thumbnails", toggle_combo, self._toggle_thumbnails
        )

        # Toggle lock
        lock_combo = self.settings_manager.get("hotkeys.toggle_lock", "<ctrl>+<shift>+l")
        self.hotkey_manager.register_hotkey("toggle_lock", lock_combo, self._toggle_lock)

        # Register per-character hotkeys
        char_hotkeys = self.settings_manager.get("character_hotkeys", {})
        for char_name, combo in char_hotkeys.items():

            def make_callback(name=char_name):
                return lambda: self._activate_character(name)

            self.hotkey_manager.register_hotkey(f"char_{char_name}", combo, make_callback())

        self.logger.info(f"Registered {len(char_hotkeys)} per-character hotkeys")

        # v2.2: Cycling hotkeys
        self._register_cycling_hotkeys()

    def _register_cycling_hotkeys(self):
        """Register (or re-register) cycling hotkeys from current settings"""
        # Unregister old cycling hotkeys without restarting listeners (batched)
        self.hotkey_manager.unregister_hotkey("cycle_next", restart=False)
        self.hotkey_manager.unregister_hotkey("cycle_prev", restart=False)

        cycle_next_combo = self.settings_manager.get("hotkeys.cycle_next", "<ctrl>+<tab>")
        cycle_prev_combo = self.settings_manager.get("hotkeys.cycle_prev", "<ctrl>+<shift>+<tab>")

        if cycle_next_combo:
            self.hotkey_manager.register_hotkey("cycle_next", cycle_next_combo, self._cycle_next)
        if cycle_prev_combo:
            self.hotkey_manager.register_hotkey("cycle_prev", cycle_prev_combo, self._cycle_prev)

        self.logger.info(
            f"Registered cycling hotkeys: next={cycle_next_combo}, prev={cycle_prev_combo}"
        )

    @Slot()
    def _toggle_visibility(self):
        """Toggle main window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    @Slot()
    def _toggle_thumbnails(self):
        """Toggle thumbnail visibility"""
        if hasattr(self, "main_tab"):
            self.main_tab.toggle_thumbnails_visibility()

    @Slot()
    def _toggle_replay_strips_global(self):
        """PR2: toggle replay strips for all preview windows (delegates to MainTab)."""
        if hasattr(self, "main_tab"):
            self.main_tab._toggle_replay_strips_global()

    @Slot()
    def _toggle_lock(self):
        """Toggle position lock"""
        if hasattr(self, "main_tab") and hasattr(self.main_tab, "lock_btn"):
            self.main_tab.lock_btn.click()

    def _get_cycling_group_members(self) -> list:
        """Get members of the current cycling group"""
        groups = self.settings_manager.get("cycling_groups", {})

        # Use current cycling group, fall back to Default
        members = []
        if self.current_cycling_group in groups:
            members = groups[self.current_cycling_group]
        elif "Default" in groups:
            members = groups["Default"]

        # If group is empty, use all active windows
        if not members:
            if hasattr(self, "main_tab") and hasattr(self.main_tab, "window_manager"):
                for frame in self.main_tab.window_manager.preview_frames.values():
                    members.append(frame.character_name)

        return members

    def _add_to_default_cycling_group(self, char_name: str, auto_save: bool = True):
        """Add a character to the Default cycling group if not already present."""
        groups = self.settings_manager.get("cycling_groups", {})
        if "Default" not in groups:
            groups["Default"] = []
        if char_name not in groups["Default"]:
            groups["Default"].append(char_name)
            self.settings_manager.set("cycling_groups", groups, auto_save=auto_save)
            # Refresh the hotkeys tab UI if it exists
            if hasattr(self, "hotkeys_tab") and self.hotkeys_tab.current_group == "Default":
                self.hotkeys_tab._load_group_members("Default")
                self.hotkeys_tab.cycling_groups = groups
            self.logger.info(f"Added {char_name} to Default cycling group")

    def _begin_bulk_import(self):
        """Batch persistence during startup import bursts."""
        self._bulk_import_active = True
        self._bulk_import_dirty_characters = False
        self._bulk_import_dirty_groups = False

    def _finish_bulk_import(self):
        """Flush any deferred saves from a bulk import session."""
        if self._bulk_import_dirty_characters:
            self.character_manager.save_data()
        if self._bulk_import_dirty_groups:
            self.settings_manager.save_settings()
        self._bulk_import_active = False
        self._bulk_import_dirty_characters = False
        self._bulk_import_dirty_groups = False

    def _queue_discovery_notification(self, char_name: str):
        """Batch rapid auto-discovery notifications into one tray update."""
        if char_name not in self._pending_discovery_names:
            self._pending_discovery_names.append(char_name)
        self._discovery_notification_timer.start()

    def _flush_discovery_notifications(self):
        """Show a single notification for any queued discoveries."""
        if not self._pending_discovery_names:
            return

        names = self._pending_discovery_names[:]
        self._pending_discovery_names.clear()

        if len(names) == 1:
            title = "New Character Detected"
            message = f"Added: {names[0]}"
        else:
            title = "New Characters Detected"
            preview = ", ".join(names[:3])
            if len(names) > 3:
                preview = f"{preview}, +{len(names) - 3} more"
            message = preview

        self.system_tray.show_notification(title, message)

    def _queue_main_tab_status_refresh(self):
        """Debounce expensive overview status refreshes during burst discovery."""
        if hasattr(self, "_status_refresh_timer"):
            self._status_refresh_timer.start()
        else:
            self._flush_main_tab_status_refresh()

    def _flush_main_tab_status_refresh(self):
        """Refresh overview status if the main tab is available."""
        if hasattr(self, "main_tab"):
            self.main_tab._update_status()

    def _get_window_id_for_character(self, char_name: str) -> str | None:
        """Get window ID for a character name"""
        if hasattr(self, "main_tab") and hasattr(self.main_tab, "window_manager"):
            for window_id, frame in self.main_tab.window_manager.preview_frames.items():
                if frame.character_name == char_name:
                    return window_id
        return None

    def _cycle_window(self, direction: int = 1):
        """Cycle to next/previous window in group

        Args:
            direction: 1 for next, -1 for previous
        """
        members = self._get_cycling_group_members()
        self.cycling_index, _ = self.cycle_controller.cycle(
            members=members,
            current_index=self.cycling_index,
            direction=direction,
            window_lookup=self._get_window_id_for_character,
        )

    @Slot()
    def _cycle_next(self):
        """Queue cycle to next window (debounced to prevent subprocess flood)."""
        self._pending_cycle_direction = 1
        self._cycle_timer.start()

    @Slot()
    def _cycle_prev(self):
        """Queue cycle to previous window (debounced to prevent subprocess flood)."""
        self._pending_cycle_direction = -1
        self._cycle_timer.start()

    def _perform_cycle(self):
        """Execute the queued cycle (called by debounce timer)."""
        if self._pending_cycle_direction is not None:
            self._cycle_window(direction=self._pending_cycle_direction)
            self._pending_cycle_direction = None

    def activate_window(self, window_id: str) -> None:
        """Public alias for :meth:`_activate_window`.

        Peer subsystems (e.g. :class:`CommandIntegrator`) are not
        subclasses of MainWindowV21 — they call into this entry point
        rather than reaching into the private implementation. The body
        is intentionally identical so internal callers can keep using
        ``_activate_window`` without churn.
        """
        self._activate_window(window_id)

    def _activate_window(self, window_id: str):
        """Activate a window by ID."""
        self.cycle_controller.activate_window(window_id)

    @Slot(str)
    def _on_profile_selected(self, profile_name: str):
        """Handle profile selection from tray"""
        self.logger.info(f"Profile selected from tray: {profile_name}")
        preset = self.layout_manager.get_preset(profile_name)
        if preset:
            self.system_tray.set_current_profile(profile_name)
            self.system_tray.show_notification("Profile Loaded", f"Loaded: {profile_name}")

    @Slot()
    def _show_settings(self):
        """Show the SYSTEM tab — Settings lives inside that container.

        Phase 4 IA: there is no top-level Settings tab. The SettingsTab
        inner widget is the left pane of the SYSTEM container. We
        navigate to SYSTEM so the operator lands on (or immediately
        adjacent to) the panel they expect.
        """
        self.show()
        self.raise_()
        self.tabs.setCurrentIndex(self._TAB_LABELS.index("System"))

    @Slot()
    def _show_roster(self):
        """Show the FLEET tab, which contains the roster."""
        self.show()
        self.raise_()
        self.tabs.setCurrentIndex(self._TAB_LABELS.index("Fleet"))

    @Slot()
    def _show_cycle_control(self):
        """Show the LAYOUTS tab, which contains cycle controls."""
        self.show()
        self.raise_()
        self.tabs.setCurrentIndex(self._TAB_LABELS.index("Layouts"))

    @Slot()
    def _reload_config(self):
        """Reload configuration (v2.2 hot reload)"""
        self.logger.info("Reloading configuration...")
        self.settings_manager.load_settings()
        self._apply_initial_settings()

        # Re-apply theme
        theme = self.settings_manager.get("appearance.theme", "dark")
        self.theme_manager.apply_theme(theme)

        self._ensure_auto_discovery_state()

        self.system_tray.show_notification("Config Reloaded", "Settings have been reloaded")
        self.logger.info("Configuration reloaded successfully")

    @Slot()
    def _quit_application(self):
        """Quit the application"""
        self.logger.info("Quit requested from tray")
        self._is_quitting = True
        self.close()

    def _run_startup_assistant(self):
        """Improve first-use UX without interrupting startup."""
        if not hasattr(self, "main_tab") or not hasattr(self.main_tab, "window_manager"):
            return

        if self.main_tab.window_manager.get_active_window_count() > 0:
            return

        if self.settings_manager.get("general.auto_import_on_startup", True):
            self._begin_bulk_import()
            try:
                added_count, _skipped_count, _detected_count = self.main_tab.one_click_import(
                    show_dialogs=False
                )
            finally:
                self._finish_bulk_import()
            if added_count > 0:
                self.statusBar().showMessage(
                    f"Imported {added_count} EVE window(s) automatically",
                    6000,
                )
                if self.settings_manager.get("general.show_notifications", True):
                    self.system_tray.show_notification(
                        "Setup Complete",
                        f"Imported {added_count} running EVE client(s)",
                    )
                return

        if self.settings_manager.get("general.show_setup_guidance", True):
            self.statusBar().showMessage(
                "Quick start: click Import Windows to detect running EVE clients automatically",
                8000,
            )

    def _apply_to_all_windows(self, action: str):
        """Apply action to all EVE windows

        Args:
            action: 'minimize' or 'restore'
        """
        if not hasattr(self, "main_tab"):
            return

        method = getattr(self.capture_system, f"{action}_window", None)
        if not method:
            return

        count = sum(1 for wid in self.main_tab.window_manager.preview_frames.keys() if method(wid))
        action_past = "Minimized" if action == "minimize" else "Restored"
        self.logger.info(f"{action_past} {count} EVE windows")
        self.system_tray.show_notification(
            f"Windows {action_past}", f"{action_past} {count} windows"
        )

    @Slot()
    def _minimize_all_windows(self):
        """Minimize all EVE windows (v2.2)"""
        self._apply_to_all_windows("minimize")

    @Slot()
    def _restore_all_windows(self):
        """Restore all EVE windows (v2.2)"""
        self._apply_to_all_windows("restore")

    def _activate_character(self, char_name: str):
        """Activate window for a specific character (v2.2 per-character hotkeys)"""
        self.cycle_controller.activate_character(char_name, self._get_window_id_for_character)

    @Slot(str, str, str)
    def _on_new_character_discovered(self, char_name: str, window_id: str, window_title: str):
        """Handle new character discovered by auto-discovery (v2.2)"""
        self.logger.info(f"Auto-discovered new character: {char_name}")

        # Add to main tab if not already there
        if hasattr(self, "main_tab"):
            if window_id not in self.main_tab.window_manager.preview_frames:
                if self.main_tab.import_detected_window(window_id, char_name):
                    self._queue_main_tab_status_refresh()

                    # Show notification
                    if self.settings_manager.get("general.show_notifications", True):
                        self._queue_discovery_notification(char_name)

    def _create_menu_bar(self):
        """Create menu bar with App menu and Help menu (v2.4 - uses ActionRegistry)"""
        menubar = self.menuBar()

        # Build App menu (PR2: replay strips toggle + other global actions)
        registry = ActionRegistry.get_instance()
        menu_builder = MenuBuilder(registry)

        app_handlers = {
            "toggle_replay_strips_app": self._toggle_replay_strips_global,
        }
        app_menu = menu_builder.build_menu(PrimaryHome.APP_MENU, parent=self, handlers=app_handlers)
        menubar.addMenu(app_menu)

        # Build Help menu using MenuBuilder (actions from ActionRegistry)
        help_handlers = {
            "about": self._show_about_dialog,
            "donate": self._open_donation_link,
            "documentation": lambda: self._open_url(
                "https://github.com/AreteDriver/Argus_Overview#readme"
            ),
            "report_issue": lambda: self._open_url(
                "https://github.com/AreteDriver/Argus_Overview/issues"
            ),
        }

        help_menu = menu_builder.build_help_menu(parent=self, handlers=help_handlers)
        menubar.addMenu(help_menu)

    def _show_about_dialog(self):
        """Show About dialog"""
        from argus_overview.ui.about_dialog import AboutDialog

        dialog = AboutDialog(self)
        dialog.exec()

    def _open_donation_link(self):
        """Open Buy Me a Coffee link"""
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/aretedriver"))

    def _open_url(self, url: str):
        """Open URL in browser"""
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl(url))

    def _set_window_icon(self):
        """Set the application window icon"""
        icon_paths = [
            Path(__file__).parent.parent.parent.parent / "assets" / "icon.png",  # src/../assets
            Path.home()
            / ".local"
            / "share"
            / "icons"
            / "hicolor"
            / "256x256"
            / "apps"
            / "argus-overview.png",
            Path.home() / ".local" / "share" / "argus-overview" / "icon.png",
        ]

        for icon_path in icon_paths:
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                self.logger.debug(f"Window icon set from: {icon_path}")
                return
        self.logger.warning("No window icon found")

    def _apply_initial_settings(self):
        """Apply settings loaded from config"""
        # Apply performance settings
        workers = self.settings_manager.get("performance.capture_workers", 4)
        self.capture_system.max_workers = workers

        self.logger.info("Initial settings applied")

    def _create_tabs(self) -> None:
        """Create the v3.3 OPS four-tab IA: COMMAND/FLEET/LAYOUTS/SYSTEM.

        Two phases:

        1. Build the v2.2 inner widgets (main_tab, characters_tab,
           hotkeys_tab, intel_tab, settings_sync_tab, settings_tab).
           These remain named attributes on ``self`` so cross-tab
           signal connections keep working.
        2. Wrap them in the v3.3 IA containers
           (:class:`CommandTab`, :class:`FleetTab`,
           :class:`LayoutsContainer`, :class:`SystemTab`) and add those
           to the QTabWidget.

        The inner widget factories are unchanged — they remain the
        source of truth for the cross-tab signal wiring.
        """
        # Phase 1 — build inner widgets (preserves all v2.2 cross-tab wiring)
        self._create_main_tab()
        self._create_layouts_tab()
        self._create_characters_tab()
        self._create_hotkeys_tab()
        self._create_intel_tab()
        self._create_settings_sync_tab()
        self._create_settings_tab()

        # Phase 2 — wrap in IA containers
        self._create_command_tab()
        self._create_fleet_tab()
        self._create_layouts_container()
        self._create_system_tab()

    def _create_command_tab(self) -> None:
        """Build the COMMAND tab container.

        :class:`CommandTab` is parented to the main window's QTabWidget
        but the flagship widget is a :class:`CommandCenterWidget`, not
        the legacy ``MainTab``. ``MainTab`` remains an attribute on
        ``self`` because :class:`CommandIntegrator` reads its
        ``window_manager`` for character mirroring.
        """
        from argus_overview.ui.tabs.command_tab import CommandTab

        self.command_tab = CommandTab()
        self.tabs.addTab(self.command_tab, "Command")

    def _create_fleet_tab(self) -> None:
        """Build the FLEET tab container (Roster + Intel splitter)."""
        from argus_overview.ui.tabs.fleet_tab import FleetTab

        self.fleet_tab = FleetTab(self.characters_tab, self.intel_tab)
        self.tabs.addTab(self.fleet_tab, "Fleet")

    def _create_layouts_container(self) -> None:
        """Build the LAYOUTS tab container (presets + Cycle Control)."""
        from argus_overview.ui.tabs.layouts_tab import LayoutsContainer

        self.layouts_tab = LayoutsContainer(self.presets_panel, self.hotkeys_tab)
        self.tabs.addTab(self.layouts_tab, "Layouts")

    def _create_system_tab(self) -> None:
        """Build the SYSTEM tab container (Settings + Sync)."""
        from argus_overview.ui.tabs.system_tab import SystemTab

        self.system_tab = SystemTab(self.settings_tab, self.settings_sync_tab)
        self.tabs.addTab(self.system_tab, "System")

    def _create_layouts_tab(self) -> None:
        """Build the inner LayoutsTab used by the LAYOUTS container.

        Lives between :meth:`_create_main_tab` (which creates
        ``main_tab`` that the layouts tab references) and
        :meth:`_create_hotkeys_tab`. Stored as ``self.presets_panel``
        so the container attribute can claim ``self.layouts_tab``.
        """
        from argus_overview.ui.layouts_tab import LayoutsTab

        # Signature: LayoutsTab(layout_manager, main_tab,
        # settings_manager=None, character_manager=None). Pass as kwargs
        # to keep the call resilient to signature reorders.
        self.presets_panel = LayoutsTab(
            self.layout_manager,
            self.main_tab,
            settings_manager=self.settings_manager,
            character_manager=self.character_manager,
        )
        # NOTE: layout_applied is NOT connected here — main_tab owns that
        # signal (see _create_main_tab). Connecting both would emit
        # _on_layout_applied twice per apply.

    def _create_main_tab(self):
        """Create the inner MainTab used by the COMMAND container.

        The MainTab is *not* added to the QTabWidget directly. The v3.3
        IA container (:class:`CommandTab`) wraps it inside CommandCenter
        via :class:`CommandIntegrator` which reads MainTab's
        ``window_manager`` for character mirroring. We keep MainTab as
        ``self.main_tab`` so cross-tab signal connections remain stable.
        """
        from argus_overview.ui.main_tab import MainTab

        self.main_tab = MainTab(
            self.capture_system,
            self.character_manager,
            settings_manager=self.settings_manager,
            layout_manager=self.layout_manager,
        )

        # Connect signals
        self.main_tab.character_detected.connect(self._on_character_detected)
        self.main_tab.layout_applied.connect(self._on_layout_applied)
        self.main_tab.window_focus_requested.connect(
            self._activate_window,
            Qt.ConnectionType.UniqueConnection,
        )
        self.main_tab.roster_navigation_requested.connect(
            self._show_roster,
            Qt.ConnectionType.UniqueConnection,
        )
        self.main_tab.cycle_control_navigation_requested.connect(
            self._show_cycle_control,
            Qt.ConnectionType.UniqueConnection,
        )

    def _create_characters_tab(self):
        """Create the inner CharactersTeamsTab used by the FLEET container.

        The Roster widget is *not* added to the QTabWidget directly. The
        v3.3 IA container :class:`FleetTab` wraps it inside a 60/40
        splitter beside :class:`IntelTab`. We keep it as
        ``self.characters_tab`` so cross-tab signal connections remain
        stable.
        """
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        self.characters_tab = CharactersTeamsTab(
            self.character_manager,
            self.layout_manager,
            settings_sync=self.settings_sync,  # v2.2: Enable EVE folder scanning
        )

        # Connect signals
        self.characters_tab.team_selected.connect(self._on_team_selected)

    def _create_hotkeys_tab(self):
        """Create the inner HotkeysTab used by the LAYOUTS container.

        The Cycle Control widget is *not* added to the QTabWidget
        directly. The v3.3 IA container :class:`LayoutsContainer` wraps
        it inside a 70/30 splitter beside :class:`LayoutsTab`. We keep
        it as ``self.hotkeys_tab`` so cross-tab signal connections
        remain stable.
        """
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        self.hotkeys_tab = HotkeysTab(
            self.character_manager, self.settings_manager, main_tab=self.main_tab
        )

        # Connect group changes to refresh layout sources in overview tab
        self.hotkeys_tab.group_changed.connect(self.main_tab.refresh_layout_groups)

        # Re-register cycling hotkeys when user saves new bindings
        self.hotkeys_tab.hotkeys_changed.connect(self._register_cycling_hotkeys)

        # Pause/resume hotkey listeners during key recording to avoid X11 conflicts
        self.hotkeys_tab.cycle_forward_edit.recordingStarted.connect(self.hotkey_manager.pause)
        self.hotkeys_tab.cycle_forward_edit.recordingStopped.connect(self.hotkey_manager.resume)
        self.hotkeys_tab.cycle_backward_edit.recordingStarted.connect(self.hotkey_manager.pause)
        self.hotkeys_tab.cycle_backward_edit.recordingStopped.connect(self.hotkey_manager.resume)

    def _create_intel_tab(self):
        """Create the inner IntelTab used by the FLEET container.

        The Intel widget is *not* added to the QTabWidget directly. The
        v3.3 IA container :class:`FleetTab` wraps it inside a 60/40
        splitter beside :class:`CharactersTeamsTab`. We keep it as
        ``self.intel_tab`` so cross-tab signal connections remain
        stable.
        """
        from argus_overview.ui.intel_tab import IntelTab

        self.intel_tab = IntelTab(self.settings_manager)

        # Connect alert signals to main window for visual feedback
        self.intel_tab.alert_triggered.connect(self._on_intel_alert)
        self.intel_tab.intel_received.connect(self._on_intel_received)

        # Connect alert dispatcher border flash to main tab
        alert_dispatcher = self.intel_tab.get_alert_dispatcher()
        alert_dispatcher.border_flash_requested.connect(self._flash_preview_borders)

        # Connect pipeline health to system status bar
        self.intel_tab.pipeline_health_changed.connect(
            lambda s, d: (
                self.system_status_bar.set_status("intel", s, d)
                if getattr(self, "system_status_bar", None) is not None
                else None
            )
        )

        self.logger.info("Intel tab created")

    @Slot(str, int)
    def _flash_preview_borders(self, color: str, duration_ms: int):
        """Flash all preview window borders with the given color."""
        if hasattr(self, "main_tab") and hasattr(self.main_tab, "window_manager"):
            for frame in self.main_tab.window_manager.preview_frames.values():
                if hasattr(frame, "flash_border"):
                    frame.flash_border(color, duration_ms)

    @Slot(object, object)
    def _on_intel_alert(self, report, alert_type):
        """Handle intel alert from intel tab."""
        from argus_overview.intel.alerts import AlertType
        from argus_overview.intel.parser import IntelReport

        if not isinstance(report, IntelReport):
            return

        # Master toggle (v3.2.0): when off, suppress all visual chrome but
        # still let other AlertTypes fire (audio, tray notification). The
        # parser keeps running, only the preview/dock tints are gated.
        # Defensive getattr: bypassed-init test helpers don't set
        # settings_manager — default to chrome on.
        sm = getattr(self, "settings_manager", None)
        chrome_enabled = sm.get("intel.preview_chrome_enabled", True) if sm is not None else True

        # Fan out threat state to preview frames + status dock once per report
        # (filter on VISUAL_BORDER so we only trigger on a single AlertType
        # emission per report, not on every type the dispatcher fires).
        if chrome_enabled and alert_type == AlertType.VISUAL_BORDER and hasattr(self, "main_tab"):
            window_manager = getattr(self.main_tab, "window_manager", None)
            if window_manager is not None and hasattr(window_manager, "apply_threat_state"):
                window_manager.apply_threat_state(report.threat_level, report.system)
            status_dock = getattr(self.main_tab, "status_dock", None)
            if status_dock is not None and hasattr(status_dock, "set_threat_state"):
                status_dock.set_threat_state(report.threat_level, report.system)

        # Show tray notification for critical alerts
        if report.threat_level.value == "critical":
            if hasattr(self, "system_tray"):
                self.system_tray.show_notification(
                    f"CRITICAL: {report.system or 'Unknown'}",
                    f"{report.hostile_count or '?'} hostiles - {', '.join(report.ship_types[:2]) or 'unknown ships'}",
                )

    def _clear_threat_chrome(self) -> None:
        """Force-clear any active threat tints across previews + chips.

        Called when the user toggles intel.preview_chrome_enabled off so
        the change takes effect immediately rather than waiting for the
        30s decay timer.
        """
        from argus_overview.intel.parser import ThreatLevel

        if not hasattr(self, "main_tab"):
            return
        wm = getattr(self.main_tab, "window_manager", None)
        if wm is not None and hasattr(wm, "apply_threat_state"):
            wm.apply_threat_state(ThreatLevel.CLEAR, None)
        dock = getattr(self.main_tab, "status_dock", None)
        if dock is not None and hasattr(dock, "set_threat_state"):
            dock.set_threat_state(ThreatLevel.CLEAR, None)

    @Slot(object)
    def _on_intel_received(self, report):
        """Handle intel received from intel tab."""
        # Could update status bar or other UI elements
        pass

    def _create_settings_sync_tab(self):
        """Create the inner SettingsSyncTab used by the SYSTEM container.

        The Sync widget is *not* added to the QTabWidget directly. The
        v3.3 IA container :class:`SystemTab` wraps it inside a 60/40
        splitter beside :class:`SettingsTab`. We keep it as
        ``self.settings_sync_tab`` so cross-tab signal connections
        remain stable.
        """
        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        self.settings_sync_tab = SettingsSyncTab(self.settings_sync, self.character_manager)

    def _create_settings_tab(self):
        """Create the inner SettingsTab used by the SYSTEM container.

        The Settings widget is *not* added to the QTabWidget directly.
        The v3.3 IA container :class:`SystemTab` wraps it inside a 60/40
        splitter beside :class:`SettingsSyncTab`. We keep it as
        ``self.settings_tab`` so cross-tab signal connections remain
        stable.
        """
        from argus_overview.ui.settings_tab import SettingsTab

        self.settings_tab = SettingsTab(self.settings_manager, self.hotkey_manager)

        # Connect signals
        self.settings_tab.settings_changed.connect(self._apply_setting)

    def _connect_signals(self):
        """Connect cross-tab signals for integration"""
        # Will be implemented as tabs are completed
        self.logger.debug("Signal connections ready")

    def _disconnect_signals(self):
        """Disconnect all dynamic signals to allow GC on close"""
        pairs = [
            # main_tab signals
            (
                self,
                "main_tab",
                [
                    ("character_detected", self._on_character_detected),
                    ("layout_applied", self._on_layout_applied),
                    ("window_focus_requested", self._activate_window),
                    ("roster_navigation_requested", self._show_roster),
                    ("cycle_control_navigation_requested", self._show_cycle_control),
                ],
            ),
            # characters_tab signals
            (
                self,
                "characters_tab",
                [
                    ("team_selected", self._on_team_selected),
                ],
            ),
            # settings_tab signals
            (
                self,
                "settings_tab",
                [
                    ("settings_changed", self._apply_setting),
                ],
            ),
            # hotkeys_tab signals
            (
                self,
                "hotkeys_tab",
                [
                    ("group_changed", self.main_tab.refresh_layout_groups),
                    ("hotkeys_changed", self._register_cycling_hotkeys),
                ],
            ),
            # system_tray signals
            (
                self,
                "system_tray",
                [
                    ("show_hide_requested", self._toggle_visibility),
                    ("toggle_thumbnails_requested", self._toggle_thumbnails),
                    ("minimize_all_requested", self._minimize_all_windows),
                    ("restore_all_requested", self._restore_all_windows),
                    ("profile_selected", self._on_profile_selected),
                    ("settings_requested", self._show_settings),
                    ("reload_config_requested", self._reload_config),
                    ("quit_requested", self._quit_application),
                ],
            ),
            # intel_tab signals
            (
                self,
                "intel_tab",
                [
                    ("alert_triggered", self._on_intel_alert),
                    ("intel_received", self._on_intel_received),
                ],
            ),
        ]

        for obj, attr, signal_slot_list in pairs:
            if not hasattr(obj, attr):
                continue
            source = getattr(obj, attr)
            for signal_name, slot in signal_slot_list:
                try:
                    getattr(source, signal_name).disconnect(slot)
                except (RuntimeError, TypeError):
                    pass  # Already disconnected or widget destroyed

        # Disconnect alert dispatcher border flash signal
        if hasattr(self, "intel_tab"):
            try:
                alert_dispatcher = self.intel_tab.get_alert_dispatcher()
                alert_dispatcher.border_flash_requested.disconnect(self._flash_preview_borders)
            except (RuntimeError, TypeError, AttributeError):
                pass

        # Disconnect all preview frame signals (dynamic connections)
        if hasattr(self, "main_tab") and hasattr(self.main_tab, "window_manager"):
            for frame in self.main_tab.window_manager.preview_frames.values():
                for sig_name, slot in [
                    ("window_activated", self.main_tab._on_window_activated),
                    ("window_removed", self.main_tab._on_window_removed),
                ]:
                    try:
                        getattr(frame, sig_name).disconnect(slot)
                    except (RuntimeError, TypeError):
                        pass

        # Hotkey recording pause/resume signals
        if hasattr(self, "hotkeys_tab"):
            for edit_name in ("cycle_forward_edit", "cycle_backward_edit"):
                edit = getattr(self.hotkeys_tab, edit_name, None)
                if edit is None:
                    continue
                for sig_name, slot in [
                    ("recordingStarted", self.hotkey_manager.pause),
                    ("recordingStopped", self.hotkey_manager.resume),
                ]:
                    try:
                        getattr(edit, sig_name).disconnect(slot)
                    except (RuntimeError, TypeError):
                        pass

        self.logger.debug("Signals disconnected")

    @Slot(str, object)
    def _apply_setting(self, key: str, value):
        """
        Apply a setting change globally

        Args:
            key: Setting key (e.g., "performance.default_refresh_rate")
            value: New value
        """
        self.logger.info(f"Applying setting: {key} = {value}")

        # Route to appropriate component
        if key.startswith("performance"):
            if key == "performance.low_power_mode":
                # Low power mode: FPS=5, alerts off
                self._apply_low_power_mode(value)
            elif key == "performance.capture_workers":
                # This requires restart of capture system
                self.logger.warning("Capture worker count change requires restart")
            elif key == "performance.default_refresh_rate":
                # Apply to main tab if it exists
                if hasattr(self, "main_tab"):
                    self.main_tab.window_manager.set_refresh_rate(value)
            elif key == "performance.disable_previews":
                # Toggle preview captures on/off (GPU/CPU savings)
                if hasattr(self, "main_tab"):
                    self.main_tab.set_previews_enabled(not value)

        elif key.startswith("hotkeys"):
            # Update hotkey manager
            # Will be implemented with hotkey functionality
            pass

        elif key == "intel.preview_chrome_enabled" and not value:
            # User just turned threat chrome off — flush any active tints
            # so the change is visible immediately, not after the 30s
            # decay window.
            self._clear_threat_chrome()

    def _apply_low_power_mode(self, enabled: bool):
        """
        Apply low power mode settings.
        When enabled: FPS=5.
        When disabled: restore previous settings.

        Args:
            enabled: True to enable low power mode
        """
        if enabled:
            self.logger.info("Enabling Low Power Mode (FPS=5)")

            # Store previous values for restoration
            if not hasattr(self, "_low_power_previous"):
                self._low_power_previous = {
                    "fps": self.settings_manager.get("performance.default_refresh_rate", 30),
                }

            # Set FPS to 5
            if hasattr(self, "main_tab"):
                self.main_tab.window_manager.set_refresh_rate(5)
                # Also update the spinner in main tab toolbar
                if hasattr(self.main_tab, "refresh_rate_spin"):
                    self.main_tab.refresh_rate_spin.blockSignals(True)
                    self.main_tab.refresh_rate_spin.setValue(5)
                    self.main_tab.refresh_rate_spin.blockSignals(False)

            # Update status bar
            self.statusBar().showMessage("⚡ Low Power Mode active (FPS=5)", 5000)

        else:
            self.logger.info("Disabling Low Power Mode (restoring previous settings)")

            # Restore previous values
            if hasattr(self, "_low_power_previous"):
                prev = self._low_power_previous

                # Restore FPS
                if hasattr(self, "main_tab"):
                    self.main_tab.window_manager.set_refresh_rate(prev["fps"])
                    if hasattr(self.main_tab, "refresh_rate_spin"):
                        self.main_tab.refresh_rate_spin.blockSignals(True)
                        self.main_tab.refresh_rate_spin.setValue(prev["fps"])
                        self.main_tab.refresh_rate_spin.blockSignals(False)

                del self._low_power_previous

            self.statusBar().showMessage("Low Power Mode disabled", 3000)

    @Slot(str, str)
    def _on_character_detected(self, window_id: str, char_name: str):
        """
        Handle character detection from Main Tab

        Args:
            window_id: Window ID
            char_name: Character name
        """
        self.logger.info(f"Character detected: {char_name} (window: {window_id})")

        auto_save = not self._bulk_import_active
        self.character_manager.ensure_character(char_name, auto_save=auto_save)
        # Assign window in character manager
        self.character_manager.assign_window(char_name, window_id, auto_save=auto_save)
        self._add_to_default_cycling_group(char_name, auto_save=auto_save)

        if self._bulk_import_active:
            self._bulk_import_dirty_characters = True
            self._bulk_import_dirty_groups = True

        # Update characters tab if it exists and has the method
        if hasattr(self, "characters_tab") and hasattr(
            self.characters_tab, "update_character_status"
        ):
            self.characters_tab.update_character_status(char_name, window_id)

    @Slot(str, str)
    def _on_character_gone(self, char_name: str, window_id: str):
        """
        Handle character window closing from auto-discovery

        Args:
            char_name: Character name
            window_id: Window ID that closed
        """
        self.logger.info(f"Character gone: {char_name} (window: {window_id})")

        # Clear window assignment in character manager
        self.character_manager.unassign_window(char_name)

        # Remove preview frame so capture loop stops hitting dead window
        if hasattr(self, "main_tab") and hasattr(self.main_tab, "window_manager"):
            self.main_tab.window_manager.remove_window(window_id)
            self._queue_main_tab_status_refresh()

        # Update characters tab if it exists and has the method
        if hasattr(self, "characters_tab") and hasattr(
            self.characters_tab, "update_character_status"
        ):
            self.characters_tab.update_character_status(char_name, None)

        # Drop stale system from location tracker so chips clear on logoff
        location_tracker = getattr(self, "location_tracker", None)
        if location_tracker is not None:
            location_tracker.on_character_gone(char_name, window_id)

    @Slot(object)
    def _on_team_selected(self, team):
        """
        Handle team selection from Characters Tab

        Args:
            team: Team object
        """
        self.logger.info(f"Team selected: {team.name}")

    @Slot(str)
    def _on_layout_applied(self, preset_name: str):
        """
        Handle layout application. Connected to ``MainTab.layout_applied``
        in :meth:`_create_main_tab` — the canonical signal source. The
        inner :class:`LayoutsTab` (now hosted inside the LAYOUTS IA
        container) intentionally does NOT connect here to avoid double-
        logging.

        Args:
            preset_name: Layout preset name
        """
        self.logger.info(f"Layout applied: {preset_name}")

    def show_layout_chooser(self) -> None:
        """Open a modal dialog listing all saved layout presets.

        This is the operationally correct entry point for the Command
        Center's ``Layout ▾`` button and any peer subsystem that wants
        to surface a preset picker. The dialog is built from
        :meth:`LayoutManager.get_all_presets` so it stays in sync with
        whatever the user has saved.
        """
        from argus_overview.core.layout_manager import LayoutPreset

        presets: list[LayoutPreset] = list(self.layout_manager.get_all_presets())
        presets.sort(key=lambda p: p.name.lower())

        dialog = QDialog(self)
        dialog.setWindowTitle("Layout Presets")
        dialog.setMinimumSize(420, 360)
        layout = QVBoxLayout(dialog)

        intro = QLabel(
            f"Select a layout preset to apply. {len(presets)} saved.",
            dialog,
        )
        layout.addWidget(intro)

        list_widget = QListWidget(dialog)
        for preset in presets:
            item = QListWidgetItem(preset.name)
            if preset.description:
                item.setToolTip(preset.description)
            item.setData(Qt.ItemDataRole.UserRole, preset.name)
            list_widget.addItem(item)
        if presets:
            list_widget.setCurrentRow(0)
        layout.addWidget(list_widget, 1)

        button_box = QDialogButtonBox(dialog)
        apply_btn = QPushButton("Apply", dialog)
        button_box.addButton(apply_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(QDialogButtonBox.StandardButton.Close)
        layout.addWidget(button_box)

        def _apply_selected() -> None:
            current = list_widget.currentItem()
            if current is None:
                return
            preset_name = current.data(Qt.ItemDataRole.UserRole)
            try:
                preset = self.layout_manager.get_preset(preset_name)
                if preset is not None:
                    self.logger.info(f"Applying layout preset: {preset_name}")
                    self._on_layout_applied(preset_name)
                dialog.accept()
            except (OSError, RuntimeError, ValueError) as exc:
                self.logger.error(f"Failed to apply preset {preset_name}: {exc}")

        apply_btn.clicked.connect(_apply_selected)
        list_widget.itemDoubleClicked.connect(lambda _item: _apply_selected())
        button_box.rejected.connect(dialog.reject)

        dialog.exec()

    @Slot(str)
    def _handle_hotkey(self, hotkey_name: str):
        """
        Handle hotkey trigger

        Args:
            hotkey_name: Name of triggered hotkey
        """
        self.logger.info(f"Hotkey triggered: {hotkey_name}")

        # Route to appropriate action
        # Will be implemented as tabs are completed

    def closeEvent(self, event: QCloseEvent):
        """Handle application close - v2.2 minimize to tray support"""
        # Check if we should minimize to tray instead of closing
        if not self._is_quitting and self.settings_manager.get("general.minimize_to_tray", True):
            if hasattr(self, "system_tray") and self.system_tray.is_visible():
                self.logger.info("Minimizing to system tray")
                self.hide()
                self.system_tray.show_notification(
                    "Still Running",
                    "Argus Overview is still running in the system tray",
                )
                event.ignore()
                return

        # Actually closing the application
        self.logger.info(f"Shutting down Argus Overview v{__version__}...")
        if hasattr(self, "_discovery_notification_timer"):
            self._discovery_notification_timer.stop()
        if hasattr(self, "_status_refresh_timer"):
            self._status_refresh_timer.stop()
        self._pending_discovery_names.clear()
        self._disconnect_auto_discovery()

        # Disconnect signals to break reference cycles
        self._disconnect_signals()

        # Stop capture timer in main_tab
        if hasattr(self, "main_tab"):
            self.main_tab.stop_capture_loop()

        # Stop intel monitoring
        if hasattr(self, "intel_tab"):
            self.intel_tab.stop()

        # Stop systems
        if hasattr(self, "auto_discovery"):
            self.auto_discovery.stop()

        location_tracker = getattr(self, "location_tracker", None)
        if location_tracker is not None:
            try:
                location_tracker.character_system_changed.disconnect(
                    self._on_character_system_changed
                )
            except (RuntimeError, TypeError):
                pass
            location_tracker.stop()

        if hasattr(self, "capture_system"):
            self.capture_system.stop()

        if hasattr(self, "hotkey_manager"):
            self.hotkey_manager.stop()

        # Hide tray icon
        if hasattr(self, "system_tray"):
            self.system_tray.hide()

        # Save settings
        if hasattr(self, "settings_manager"):
            self.settings_manager.save_settings()

        # Save character/team data
        if hasattr(self, "character_manager"):
            self.character_manager.save_data()

        self.logger.info("Shutdown complete")
        event.accept()
