"""
Main Window v2.2 with Tabbed Interface
Production implementation with all core modules integrated
v2.2: Added system tray, auto-discovery, themes, hotkey enhancements
"""
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QApplication
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QCloseEvent
import logging

# Import core modules
from eve_overview_pro.core.character_manager import CharacterManager
from eve_overview_pro.core.layout_manager import LayoutManager
from eve_overview_pro.core.alert_detector import AlertDetector
from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded
from eve_overview_pro.core.hotkey_manager import HotkeyManager
from eve_overview_pro.core.eve_settings_sync import EVESettingsSync
from eve_overview_pro.core.discovery import AutoDiscovery
from eve_overview_pro.ui.settings_manager import SettingsManager
from eve_overview_pro.ui.tray import SystemTray
from eve_overview_pro.ui.themes import get_theme_manager


class MainWindowV21(QMainWindow):
    """Main application window with tabbed interface v2.2"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("EVE Veles Eyes v2.2 Ultimate Edition")
        self.setMinimumSize(1000, 700)

        # Initialize core modules (singleton instances)
        self.logger.info("Initializing core modules...")
        self.character_manager = CharacterManager()
        self.layout_manager = LayoutManager()
        self.alert_detector = AlertDetector()
        self.capture_system = WindowCaptureThreaded()
        self.hotkey_manager = HotkeyManager()
        self.settings_sync = EVESettingsSync()
        self.settings_manager = SettingsManager()

        # v2.2: Auto-discovery
        self.auto_discovery = AutoDiscovery(
            interval_seconds=self.settings_manager.get("general.auto_discovery_interval", 5)
        )

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
        self._create_characters_tab()
        self._create_layouts_tab()
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
            self.auto_discovery.start()

        self.logger.info("Main window v2.2 initialized successfully")

    def _create_system_tray(self):
        """Create system tray icon (v2.2)"""
        self.system_tray = SystemTray(self)

        # Connect tray signals
        self.system_tray.show_hide_requested.connect(self._toggle_visibility)
        self.system_tray.toggle_thumbnails_requested.connect(self._toggle_thumbnails)
        self.system_tray.profile_selected.connect(self._on_profile_selected)
        self.system_tray.settings_requested.connect(self._show_settings)
        self.system_tray.reload_config_requested.connect(self._reload_config)
        self.system_tray.quit_requested.connect(self._quit_application)

        # Load saved profiles
        profiles = self.layout_manager.get_all_presets()
        self.system_tray.set_profiles(list(profiles.keys()))

        # Show tray icon
        self.system_tray.show()
        self.logger.info("System tray initialized")

    def _register_hotkeys(self):
        """Register global hotkeys (v2.2)"""
        # Minimize all
        minimize_combo = self.settings_manager.get("hotkeys.minimize_all", "<ctrl>+<shift>+m")
        self.hotkey_manager.register_hotkey("minimize_all", minimize_combo, self._minimize_all_windows)

        # Restore all
        restore_combo = self.settings_manager.get("hotkeys.restore_all", "<ctrl>+<shift>+r")
        self.hotkey_manager.register_hotkey("restore_all", restore_combo, self._restore_all_windows)

        # Toggle thumbnails
        toggle_combo = self.settings_manager.get("hotkeys.toggle_thumbnails", "<ctrl>+<shift>+t")
        self.hotkey_manager.register_hotkey("toggle_thumbnails", toggle_combo, self._toggle_thumbnails)

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
        if hasattr(self, 'main_tab'):
            self.main_tab.toggle_thumbnails_visibility()

    @Slot()
    def _toggle_lock(self):
        """Toggle position lock"""
        if hasattr(self, 'main_tab') and hasattr(self.main_tab, 'lock_btn'):
            self.main_tab.lock_btn.click()

    @Slot(str)
    def _on_profile_selected(self, profile_name: str):
        """Handle profile selection from tray"""
        self.logger.info(f"Profile selected from tray: {profile_name}")
        preset = self.layout_manager.load_preset(profile_name)
        if preset:
            self.system_tray.set_current_profile(profile_name)
            self.system_tray.show_notification("Profile Loaded", f"Loaded: {profile_name}")

    @Slot()
    def _show_settings(self):
        """Show settings tab"""
        self.show()
        self.raise_()
        self.tabs.setCurrentIndex(4)  # Settings tab

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

    @Slot()
    def _minimize_all_windows(self):
        """Minimize all EVE windows (v2.2)"""
        if hasattr(self, 'main_tab'):
            count = 0
            for window_id in self.main_tab.window_manager.preview_frames.keys():
                if self.capture_system.minimize_window(window_id):
                    count += 1
            self.logger.info(f"Minimized {count} EVE windows")
            self.system_tray.show_notification("Windows Minimized", f"Minimized {count} windows")

    @Slot()
    def _restore_all_windows(self):
        """Restore all EVE windows (v2.2)"""
        if hasattr(self, 'main_tab'):
            count = 0
            for window_id in self.main_tab.window_manager.preview_frames.keys():
                if self.capture_system.restore_window(window_id):
                    count += 1
            self.logger.info(f"Restored {count} EVE windows")
            self.system_tray.show_notification("Windows Restored", f"Restored {count} windows")

    def _activate_character(self, char_name: str):
        """Activate window for a specific character (v2.2 per-character hotkeys)"""
        if hasattr(self, 'main_tab'):
            for window_id, frame in self.main_tab.window_manager.preview_frames.items():
                if frame.character_name == char_name:
                    self.capture_system.activate_window(window_id)
                    self.logger.info(f"Activated character: {char_name}")
                    return
        self.logger.warning(f"Character not found: {char_name}")

    @Slot(str, str, str)
    def _on_new_character_discovered(self, char_name: str, window_id: str, window_title: str):
        """Handle new character discovered by auto-discovery (v2.2)"""
        self.logger.info(f"Auto-discovered new character: {char_name}")

        # Add to main tab if not already there
        if hasattr(self, 'main_tab'):
            if window_id not in self.main_tab.window_manager.preview_frames:
                frame = self.main_tab.window_manager.add_window(window_id, char_name)
                if frame:
                    frame.window_activated.connect(self.main_tab._on_window_activated)
                    frame.window_removed.connect(self.main_tab._on_window_removed)
                    self.main_tab.preview_layout.addWidget(frame)
                    self.main_tab._update_status()

                    # Show notification
                    if self.settings_manager.get("general.show_notifications", True):
                        self.system_tray.show_notification(
                            "New Character Detected",
                            f"Added: {char_name}"
                        )

    def _create_menu_bar(self):
        """Create menu bar with Help menu"""
        menubar = self.menuBar()

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = help_menu.addAction("&About EVE Veles Eyes")
        about_action.triggered.connect(self._show_about_dialog)

        help_menu.addSeparator()

        # Donate action
        donate_action = help_menu.addAction("☕ &Support Development (Buy Me a Coffee)")
        donate_action.triggered.connect(self._open_donation_link)

        help_menu.addSeparator()

        # Documentation
        docs_action = help_menu.addAction("&Documentation")
        docs_action.triggered.connect(lambda: self._open_url("https://github.com/AreteDriver/EVE_VelesEyes#readme"))

        # Report Issue
        issue_action = help_menu.addAction("&Report Issue")
        issue_action.triggered.connect(lambda: self._open_url("https://github.com/AreteDriver/EVE_VelesEyes/issues"))

    def _show_about_dialog(self):
        """Show About dialog"""
        from eve_overview_pro.ui.about_dialog import AboutDialog
        dialog = AboutDialog(self)
        dialog.exec()

    def _open_donation_link(self):
        """Open Buy Me a Coffee link"""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/aretedriver"))

    def _open_url(self, url: str):
        """Open URL in browser"""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))

    def _apply_initial_settings(self):
        """Apply settings loaded from config"""
        # Apply performance settings
        workers = self.settings_manager.get("performance.capture_workers", 4)
        self.capture_system.max_workers = workers

        # Apply alert settings
        from eve_overview_pro.core.alert_detector import AlertConfig
        alert_config = AlertConfig(
            enabled=self.settings_manager.get("alerts.enabled", True),
            red_flash_threshold=self.settings_manager.get("alerts.red_flash.threshold", 0.7),
            change_threshold=self.settings_manager.get("alerts.screen_change.threshold", 0.3),
            sound_enabled=self.settings_manager.get("alerts.red_flash.sound_alert", False),
            visual_border=self.settings_manager.get("alerts.red_flash.visual_border", True),
            alert_cooldown=self.settings_manager.get("alerts.red_flash.cooldown", 5)
        )
        self.alert_detector.set_config(alert_config)

        self.logger.info("Initial settings applied")

    def _create_main_tab(self):
        """Create main preview management tab"""
        from eve_overview_pro.ui.main_tab import MainTab

        self.main_tab = MainTab(
            self.capture_system,
            self.character_manager,
            self.alert_detector,
            settings_manager=self.settings_manager
        )
        self.tabs.addTab(self.main_tab, "Main")

        # Connect signals
        self.main_tab.character_detected.connect(self._on_character_detected)

    def _create_characters_tab(self):
        """Create character & team management tab"""
        from eve_overview_pro.ui.characters_teams_tab import CharactersTeamsTab

        self.characters_tab = CharactersTeamsTab(
            self.character_manager,
            self.layout_manager
        )
        self.tabs.addTab(self.characters_tab, "Characters & Teams")

        # Connect signals
        self.characters_tab.team_selected.connect(self._on_team_selected)

    def _create_layouts_tab(self):
        """Create layout presets tab"""
        from eve_overview_pro.ui.layouts_tab import LayoutsTab

        self.layouts_tab = LayoutsTab(
            self.layout_manager,
            self.main_tab
        )
        self.tabs.addTab(self.layouts_tab, "Layouts")

        # Connect signals
        self.layouts_tab.layout_applied.connect(self._on_layout_applied)

    def _create_settings_sync_tab(self):
        """Create EVE settings sync tab"""
        from eve_overview_pro.ui.settings_sync_tab import SettingsSyncTab

        self.settings_sync_tab = SettingsSyncTab(
            self.settings_sync,
            self.character_manager
        )
        self.tabs.addTab(self.settings_sync_tab, "Settings Sync")

    def _create_settings_tab(self):
        """Create application settings tab"""
        from eve_overview_pro.ui.settings_tab import SettingsTab

        self.settings_tab = SettingsTab(
            self.settings_manager,
            self.hotkey_manager,
            self.alert_detector
        )
        self.tabs.addTab(self.settings_tab, "Settings")

        # Connect signals
        self.settings_tab.settings_changed.connect(self._apply_setting)

    def _connect_signals(self):
        """Connect cross-tab signals for integration"""
        # Will be implemented as tabs are completed
        self.logger.debug("Signal connections ready")

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
            if key == "performance.capture_workers":
                # This requires restart of capture system
                self.logger.warning("Capture worker count change requires restart")
            elif key == "performance.default_refresh_rate":
                # Apply to main tab if it exists
                pass

        elif key.startswith("alerts"):
            # Update alert detector config
            self._apply_initial_settings()

        elif key.startswith("hotkeys"):
            # Update hotkey manager
            # Will be implemented with hotkey functionality
            pass

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
        if hasattr(self, 'characters_tab') and hasattr(self.characters_tab, 'update_character_status'):
            self.characters_tab.update_character_status(char_name, window_id)

    @Slot(object)
    def _on_team_selected(self, team):
        """
        Handle team selection from Characters Tab

        Args:
            team: Team object
        """
        self.logger.info(f"Team selected: {team.name}")

        # Load associated layout if it exists
        if hasattr(self, 'layouts_tab') and hasattr(self.layouts_tab, 'load_layout'):
            self.layouts_tab.load_layout(team.layout_name)

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
            if hasattr(self, 'system_tray') and self.system_tray.is_visible():
                self.logger.info("Minimizing to system tray")
                self.hide()
                self.system_tray.show_notification(
                    "Still Running",
                    "EVE Veles Eyes is still running in the system tray"
                )
                event.ignore()
                return

        # Actually closing the application
        self.logger.info("Shutting down EVE Veles Eyes v2.2...")

        # Stop systems
        if hasattr(self, 'auto_discovery'):
            self.auto_discovery.stop()

        if hasattr(self, 'capture_system'):
            self.capture_system.stop()

        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.stop()

        # Hide tray icon
        if hasattr(self, 'system_tray'):
            self.system_tray.hide()

        # Save settings
        if hasattr(self, 'settings_manager'):
            self.settings_manager.save_settings()

        # Save character/team data
        if hasattr(self, 'character_manager'):
            self.character_manager.save_data()

        self.logger.info("Shutdown complete")
        event.accept()
