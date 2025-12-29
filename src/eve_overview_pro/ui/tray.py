"""
System Tray - Provides system tray icon with quick actions menu
v2.2 Feature: Minimize to tray, quick profile switching, toggle visibility
v2.4: Refactored to use ActionRegistry for menu construction
"""
import logging
from typing import List, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from eve_overview_pro.ui.action_registry import ActionRegistry
from eve_overview_pro.ui.menu_builder import MenuBuilder


class SystemTray(QObject):
    """
    System tray icon with menu for quick actions.

    Features:
    - Show/Hide main window
    - Toggle thumbnails visibility
    - Minimize/Restore all windows
    - Quick profile switching
    - Reload config
    - Quit application

    All actions are sourced from ActionRegistry (primary_home=TRAY_MENU).
    """

    # Signals - emitted when tray menu actions are triggered
    show_hide_requested = Signal()
    toggle_thumbnails_requested = Signal()
    minimize_all_requested = Signal()
    restore_all_requested = Signal()
    profile_selected = Signal(str)  # profile_name
    settings_requested = Signal()
    reload_config_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # State
        self._visible = True
        self._profiles: List[str] = []
        self._current_profile: Optional[str] = None

        # Action registry and menu builder
        self.registry = ActionRegistry.get_instance()
        self.menu_builder = MenuBuilder(self.registry)

        # Create tray icon
        self.tray_icon = QSystemTrayIcon(parent)
        self.tray_icon.setIcon(self._create_icon())
        self.tray_icon.setToolTip("Argus Overview v2.4")

        # Create context menu from registry
        self.menu = QMenu()
        self._setup_menu()
        self.tray_icon.setContextMenu(self.menu)

        # Connect signals
        self.tray_icon.activated.connect(self._on_tray_activated)

        self.logger.info("System tray initialized (using ActionRegistry)")

    def _create_icon(self) -> QIcon:
        """
        Create the tray icon from the app icon file.

        Returns:
            QIcon: The tray icon
        """
        from pathlib import Path

        # Try to load icon from assets (4 levels up from ui/tray.py to project root)
        icon_paths = [
            Path(__file__).parent.parent.parent.parent / "assets" / "icon_48.png",  # src/../assets
            Path(__file__).parent.parent.parent.parent / "assets" / "icon.png",
            Path.home() / ".local" / "share" / "icons" / "hicolor" / "48x48" / "apps" / "argus-overview.png",
            Path.home() / ".local" / "share" / "argus-overview" / "icon.png",
        ]

        for icon_path in icon_paths:
            if icon_path.exists():
                return QIcon(str(icon_path))

        # Fallback: Create programmatic icon
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(26, 10, 10))  # Dark red background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 68, 68))  # Veles red
        painter.drawText(pixmap.rect(), 0x0084, "V")
        painter.end()

        return QIcon(pixmap)

    def _setup_menu(self):
        """
        Setup the context menu using ActionRegistry.

        Menu structure:
        - Show/Hide Argus Overview
        - Toggle Thumbnails
        - [separator]
        - Minimize All
        - Restore All
        - [separator]
        - Profiles (submenu)
        - [separator]
        - Settings
        - Reload Config
        - [separator]
        - Quit

        This method rebuilds the entire menu. Call it when profiles change.
        """
        # Build handlers map - connects action IDs to signal emitters
        handlers = {
            "show_hide": self.show_hide_requested.emit,
            "toggle_thumbnails": self.toggle_thumbnails_requested.emit,
            "minimize_all": self.minimize_all_requested.emit,
            "restore_all": self.restore_all_requested.emit,
            "settings": self.settings_requested.emit,
            "reload_config": self.reload_config_requested.emit,
            "quit": self.quit_requested.emit,
        }

        # Build menu using MenuBuilder (creates new QMenu instance)
        self.menu = self.menu_builder.build_tray_menu(
            parent=None,
            handlers=handlers,
            profile_handler=self._on_profile_selected,
            profiles=self._profiles,
            current_profile=self._current_profile,
        )

        # Update the tray icon's context menu
        self.tray_icon.setContextMenu(self.menu)

    def _on_profile_selected(self, profile_name: str):
        """Handle profile selection from menu"""
        self.profile_selected.emit(profile_name)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """
        Handle tray icon activation

        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_hide_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click shows context menu (default behavior)
            pass

    def show(self):
        """Show the tray icon"""
        self.tray_icon.show()
        self.logger.debug("Tray icon shown")

    def hide(self):
        """Hide the tray icon"""
        self.tray_icon.hide()
        self.logger.debug("Tray icon hidden")

    def set_profiles(self, profiles: List[str], current: Optional[str] = None):
        """
        Update available profiles

        Args:
            profiles: List of profile names
            current: Currently active profile
        """
        self._profiles = profiles
        self._current_profile = current
        self._setup_menu()  # Rebuild menu with new profiles

    def set_current_profile(self, profile: str):
        """
        Set the current profile

        Args:
            profile: Profile name
        """
        self._current_profile = profile
        self._setup_menu()  # Rebuild menu with updated current profile

    def show_notification(self, title: str, message: str,
                          icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
                          duration: int = 3000):
        """
        Show a notification from the tray

        Args:
            title: Notification title
            message: Notification message
            icon: Message icon type
            duration: Duration in milliseconds
        """
        if self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(title, message, icon, duration)
            self.logger.debug(f"Notification shown: {title}")

    def update_tooltip(self, text: str):
        """
        Update the tray icon tooltip

        Args:
            text: New tooltip text
        """
        self.tray_icon.setToolTip(text)

    def is_visible(self) -> bool:
        """Check if tray icon is visible"""
        return self.tray_icon.isVisible()
