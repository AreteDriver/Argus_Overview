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
from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget

# Import core modules
from argus_overview.core.character_manager import CharacterManager
from argus_overview.core.discovery import AutoDiscovery
from argus_overview.core.eve_settings_sync import EVESettingsSync
from argus_overview.core.hotkey_manager import HotkeyManager
from argus_overview.core.layout_manager import LayoutManager
from argus_overview.core.window_capture_threaded import WindowCaptureThreaded
from argus_overview.ui.action_registry import ActionRegistry
from argus_overview.ui.menu_builder import MenuBuilder
from argus_overview.ui.settings_manager import SettingsManager
from argus_overview.ui.themes import get_theme_manager
from argus_overview.ui.tray import SystemTray


class MainWindowV21(QMainWindow):
    """Main application window with tabbed interface v2.2"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("Argus Overview v2.4")
        self.setMinimumSize(1000, 700)

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
        capture_workers = self.settings_manager.get("performance.capture_workers", 1)
        self.capture_system = WindowCaptureThreaded(max_workers=capture_workers)

        # v2.2: Auto-discovery
        self.auto_discovery = AutoDiscovery(
            interval_seconds=self.settings_manager.get("general.auto_discovery_interval", 5)
        )

        # v2.2: Window cycling state
        self.cycling_index = 0  # Current position in cycling group
        self.current_cycling_group = "Default"  # Active cycling group name

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
        layout.addWidget(self.tabs)

        # Create tabs
        self._create_main_tab()
        self._create_hotkeys_tab()
        self._create_characters_tab()
        self._create_intel_tab()
        self._create_settings_sync_tab()
        self._create_settings_tab()

        # Connect cross-tab signals
        self._connect_signals()

        # v2.2: Create system tray
        self._create_system_tray()

        # v2.2: Register hotkeys
        self._register_hotkeys()

        # Start systems
        self.logger.info("Starting capture system, hotkey manager, and auto-discovery...")
        self.capture_system.start()
        self.hotkey_manager.start()

        # v2.2: Start auto-discovery if enabled
        if self.settings_manager.get("general.auto_discovery", True):
            self.auto_discovery.new_character_found.connect(self._on_new_character_discovered)
            self.auto_discovery.character_gone.connect(self._on_character_gone)
            self.auto_discovery.start()

        self.logger.info("Main window v2.2 initialized successfully")

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

    def _get_window_id_for_character(self, char_name: str) -> Optional[str]:
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
        if not members:
            self.logger.warning("No members in cycling group")
            return

        # Try each member at most once to avoid infinite loop
        for _ in range(len(members)):
            self.cycling_index = (self.cycling_index + direction) % len(members)
            char_name = members[self.cycling_index]

            window_id = self._get_window_id_for_character(char_name)
            if window_id:
                self._activate_window(window_id)
                self.logger.info(
                    f"Cycled to: {char_name} ({self.cycling_index + 1}/{len(members)})"
                )
                return

            self.logger.warning(f"Character '{char_name}' not found in active windows, skipping")

        self.logger.warning("No active windows found in cycling group")

    @Slot()
    def _cycle_next(self):
        """Cycle to next window in group"""
        self._cycle_window(direction=1)

    @Slot()
    def _cycle_prev(self):
        """Cycle to previous window in group"""
        self._cycle_window(direction=-1)

    def _activate_window(self, window_id: str):
        """Activate a window by ID using xdotool, optionally minimizing previous EVE window"""
        import re
        import subprocess

        # Validate window ID format (X11: 0x followed by hex digits)
        if not window_id or not re.match(r"^0x[0-9a-fA-F]+$", window_id):
            self.logger.warning(f"Invalid window ID format: {window_id}")
            return

        try:
            # Check if auto-minimize is enabled
            auto_minimize = self.settings_manager.get("performance.auto_minimize_inactive", False)

            if auto_minimize:
                # Get the last activated EVE window
                last_eve_window = self.settings_manager.get_last_activated_window()

                if (
                    last_eve_window
                    and last_eve_window != window_id
                    and re.match(r"^0x[0-9a-fA-F]+$", last_eve_window)
                ):
                    # Minimize the previous EVE window
                    subprocess.run(
                        ["xdotool", "windowminimize", last_eve_window],
                        capture_output=True,
                        timeout=2,
                    )
                    self.logger.info(f"Auto-minimized previous EVE window: {last_eve_window}")

            # Track this as the last activated EVE window
            self.settings_manager.set_last_activated_window(window_id)

            # Activate the new window
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", window_id], capture_output=True, timeout=2
            )
        except Exception as e:
            self.logger.error(f"Failed to activate window {window_id}: {e}")

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
        """Show settings tab"""
        self.show()
        self.raise_()
        self.tabs.setCurrentIndex(
            4
        )  # Settings tab (Overview=0, Cycle Control=1, Roster=2, Sync=3, Settings=4)

    @Slot()
    def _reload_config(self):
        """Reload configuration (v2.2 hot reload)"""
        self.logger.info("Reloading configuration...")
        self.settings_manager.load_settings()
        self._apply_initial_settings()

        # Re-apply theme
        theme = self.settings_manager.get("appearance.theme", "dark")
        self.theme_manager.apply_theme(theme)

        # Update auto-discovery
        if self.settings_manager.get("general.auto_discovery", True):
            self.auto_discovery.set_interval(
                self.settings_manager.get("general.auto_discovery_interval", 5)
            )
            if not self.auto_discovery.scan_timer.isActive():
                self.auto_discovery.start()
        else:
            self.auto_discovery.stop()

        self.system_tray.show_notification("Config Reloaded", "Settings have been reloaded")
        self.logger.info("Configuration reloaded successfully")

    @Slot()
    def _quit_application(self):
        """Quit the application"""
        self.logger.info("Quit requested from tray")
        QApplication.quit()

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
        if hasattr(self, "main_tab"):
            for window_id, frame in self.main_tab.window_manager.preview_frames.items():
                if frame.character_name == char_name:
                    # Use _activate_window which has auto-minimize logic
                    self._activate_window(window_id)
                    self.logger.info(f"Activated character: {char_name}")
                    return
        self.logger.warning(f"Character not found: {char_name}")

    @Slot(str, str, str)
    def _on_new_character_discovered(self, char_name: str, window_id: str, window_title: str):
        """Handle new character discovered by auto-discovery (v2.2)"""
        self.logger.info(f"Auto-discovered new character: {char_name}")

        # Add to main tab if not already there
        if hasattr(self, "main_tab"):
            if window_id not in self.main_tab.window_manager.preview_frames:
                frame = self.main_tab.window_manager.add_window(window_id, char_name)
                if frame:
                    frame.window_activated.connect(
                        self.main_tab._on_window_activated,
                        Qt.ConnectionType.UniqueConnection,
                    )
                    frame.window_removed.connect(
                        self.main_tab._on_window_removed,
                        Qt.ConnectionType.UniqueConnection,
                    )
                    self.main_tab.preview_layout.addWidget(frame)
                    self.main_tab._update_status()

                    # Show notification
                    if self.settings_manager.get("general.show_notifications", True):
                        self.system_tray.show_notification(
                            "New Character Detected", f"Added: {char_name}"
                        )

    def _create_menu_bar(self):
        """Create menu bar with Help menu (v2.4 - uses ActionRegistry)"""
        menubar = self.menuBar()

        # Build Help menu using MenuBuilder (actions from ActionRegistry)
        registry = ActionRegistry.get_instance()
        menu_builder = MenuBuilder(registry)

        # Handler map for Help menu actions
        handlers = {
            "about": self._show_about_dialog,
            "donate": self._open_donation_link,
            "documentation": lambda: self._open_url(
                "https://github.com/AreteDriver/Argus_Overview#readme"
            ),
            "report_issue": lambda: self._open_url(
                "https://github.com/AreteDriver/Argus_Overview/issues"
            ),
        }

        help_menu = menu_builder.build_help_menu(parent=self, handlers=handlers)
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

    def _create_main_tab(self):
        """Create Overview tab (window preview management) - formerly 'Main'"""
        from argus_overview.ui.main_tab import MainTab

        self.main_tab = MainTab(
            self.capture_system,
            self.character_manager,
            settings_manager=self.settings_manager,
        )
        self.tabs.addTab(self.main_tab, "Overview")

        # Connect signals
        self.main_tab.character_detected.connect(self._on_character_detected)
        self.main_tab.layout_applied.connect(self._on_layout_applied)

    def _create_characters_tab(self):
        """Create Roster tab (character & team management) - formerly 'Characters & Teams'"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        self.characters_tab = CharactersTeamsTab(
            self.character_manager,
            self.layout_manager,
            settings_sync=self.settings_sync,  # v2.2: Enable EVE folder scanning
        )
        self.tabs.addTab(self.characters_tab, "Roster")

        # Connect signals
        self.characters_tab.team_selected.connect(self._on_team_selected)

    def _create_hotkeys_tab(self):
        """Create Cycle Control tab (hotkeys, cycling, alerts)"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        self.hotkeys_tab = HotkeysTab(
            self.character_manager, self.settings_manager, main_tab=self.main_tab
        )
        self.tabs.addTab(self.hotkeys_tab, "Cycle Control")

        # Connect group changes to refresh layout sources in overview tab
        self.hotkeys_tab.group_changed.connect(self.main_tab.refresh_layout_groups)

        # Pause/resume hotkey listeners during key recording to avoid X11 conflicts
        self.hotkeys_tab.cycle_forward_edit.recordingStarted.connect(self.hotkey_manager.pause)
        self.hotkeys_tab.cycle_forward_edit.recordingStopped.connect(self.hotkey_manager.resume)
        self.hotkeys_tab.cycle_backward_edit.recordingStarted.connect(self.hotkey_manager.pause)
        self.hotkeys_tab.cycle_backward_edit.recordingStopped.connect(self.hotkey_manager.resume)

    def _create_intel_tab(self):
        """Create Intel tab (chat log monitoring and alerts)"""
        from argus_overview.ui.intel_tab import IntelTab

        self.intel_tab = IntelTab(self.settings_manager)
        self.tabs.addTab(self.intel_tab, "Intel")

        # Connect alert signals to main window for visual feedback
        self.intel_tab.alert_triggered.connect(self._on_intel_alert)
        self.intel_tab.intel_received.connect(self._on_intel_received)

        # Connect alert dispatcher border flash to main tab
        alert_dispatcher = self.intel_tab.get_alert_dispatcher()
        alert_dispatcher.border_flash_requested.connect(self._flash_preview_borders)

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
        from argus_overview.intel.parser import IntelReport

        if not isinstance(report, IntelReport):
            return

        # Show tray notification for critical alerts
        if report.threat_level.value == "critical":
            if hasattr(self, "system_tray"):
                self.system_tray.show_notification(
                    f"CRITICAL: {report.system or 'Unknown'}",
                    f"{report.hostile_count or '?'} hostiles - {', '.join(report.ship_types[:2]) or 'unknown ships'}",
                )

    @Slot(object)
    def _on_intel_received(self, report):
        """Handle intel received from intel tab."""
        # Could update status bar or other UI elements
        pass

    def _create_settings_sync_tab(self):
        """Create Sync tab (EVE settings sync) - formerly 'Settings Sync'"""
        from argus_overview.ui.settings_sync_tab import SettingsSyncTab

        self.settings_sync_tab = SettingsSyncTab(self.settings_sync, self.character_manager)
        self.tabs.addTab(self.settings_sync_tab, "Sync")

    def _create_settings_tab(self):
        """Create Settings tab (application settings)"""
        from argus_overview.ui.settings_tab import SettingsTab

        self.settings_tab = SettingsTab(self.settings_manager, self.hotkey_manager)
        self.tabs.addTab(self.settings_tab, "Settings")

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
            # auto_discovery signals
            (
                self,
                "auto_discovery",
                [
                    ("new_character_found", self._on_new_character_discovered),
                    ("character_gone", self._on_character_gone),
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

        # Assign window in character manager
        self.character_manager.assign_window(char_name, window_id)

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

        # Update characters tab if it exists and has the method
        if hasattr(self, "characters_tab") and hasattr(
            self.characters_tab, "update_character_status"
        ):
            self.characters_tab.update_character_status(char_name, None)

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
        Handle layout application from Layouts Tab

        Args:
            preset_name: Layout preset name
        """
        self.logger.info(f"Layout applied: {preset_name}")

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
        if self.settings_manager.get("general.minimize_to_tray", True):
            if hasattr(self, "system_tray") and self.system_tray.is_visible():
                self.logger.info("Minimizing to system tray")
                self.hide()
                self.system_tray.show_notification(
                    "Still Running", "Argus Overview is still running in the system tray"
                )
                event.ignore()
                return

        # Actually closing the application
        self.logger.info("Shutting down Argus Overview v2.4...")

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
