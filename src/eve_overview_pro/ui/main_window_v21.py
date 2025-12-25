"""
Main Window v2.1 with Tabbed Interface
Production implementation with all core modules integrated
"""
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Slot
import logging

# Import core modules
from eve_overview_pro.core.character_manager import CharacterManager
from eve_overview_pro.core.layout_manager import LayoutManager
from eve_overview_pro.core.alert_detector import AlertDetector
from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded
from eve_overview_pro.core.hotkey_manager import HotkeyManager
from eve_overview_pro.core.eve_settings_sync import EVESettingsSync
from eve_overview_pro.ui.settings_manager import SettingsManager


class MainWindowV21(QMainWindow):
    """Main application window with tabbed interface"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("EVE Veles Eyes v2.1 Ultimate Edition")
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

        # Validate and apply settings
        self.settings_manager.validate()
        self._apply_initial_settings()

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

        # Create tabs (will be implemented progressively)
        self._create_main_tab()
        self._create_characters_tab()
        self._create_layouts_tab()
        self._create_settings_sync_tab()
        self._create_settings_tab()

        # Connect cross-tab signals
        self._connect_signals()

        # Start systems
        self.logger.info("Starting capture system and hotkey manager...")
        self.capture_system.start()
        self.hotkey_manager.start()

        self.logger.info("Main window v2.1 initialized successfully")

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
            self.alert_detector
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

    def closeEvent(self, event):
        """Handle application close"""
        self.logger.info("Shutting down EVE Overview Pro...")

        # Stop systems
        if hasattr(self, 'capture_system'):
            self.capture_system.stop()
        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.stop()

        # Save settings
        if hasattr(self, 'settings_manager'):
            self.settings_manager.save_settings()

        # Save character/team data
        if hasattr(self, 'character_manager'):
            self.character_manager.save_data()

        self.logger.info("Shutdown complete")
        event.accept()
