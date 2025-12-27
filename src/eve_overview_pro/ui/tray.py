"""
System Tray - Provides system tray icon with quick actions menu
v2.2 Feature: Minimize to tray, quick profile switching, toggle visibility
"""
import logging
from pathlib import Path
from typing import Optional, Dict, List, Callable

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtCore import Signal, QObject


class SystemTray(QObject):
    """
    System tray icon with menu for quick actions.

    Features:
    - Show/Hide main window
    - Toggle thumbnails visibility
    - Quick profile switching
    - Settings access
    - Quit application
    """

    # Signals
    show_hide_requested = Signal()
    toggle_thumbnails_requested = Signal()
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

        # Create tray icon
        self.tray_icon = QSystemTrayIcon(parent)
        self.tray_icon.setIcon(self._create_icon())
        self.tray_icon.setToolTip("EVE Veles Eyes v2.2")

        # Create context menu
        self.menu = QMenu()
        self._setup_menu()
        self.tray_icon.setContextMenu(self.menu)

        # Connect signals
        self.tray_icon.activated.connect(self._on_tray_activated)

        self.logger.info("System tray initialized")

    def _create_icon(self) -> QIcon:
        """
        Create the tray icon - Orange 'V' on dark blue background

        Returns:
            QIcon: The tray icon
        """
        # Create 32x32 pixmap
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(26, 26, 46))  # Dark blue background

        # Draw orange 'V'
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set font
        font = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font)

        # Orange color
        painter.setPen(QColor(255, 140, 0))  # Orange

        # Draw centered 'V'
        painter.drawText(pixmap.rect(), 0x0084, "V")  # AlignCenter
        painter.end()

        return QIcon(pixmap)

    def _setup_menu(self):
        """Setup the context menu"""
        # Show/Hide action
        self.show_hide_action = QAction("Show/Hide Veles Eyes", self.menu)
        self.show_hide_action.triggered.connect(self.show_hide_requested.emit)
        self.menu.addAction(self.show_hide_action)

        # Toggle Thumbnails
        self.toggle_thumbnails_action = QAction("Toggle Thumbnails", self.menu)
        self.toggle_thumbnails_action.triggered.connect(self.toggle_thumbnails_requested.emit)
        self.menu.addAction(self.toggle_thumbnails_action)

        self.menu.addSeparator()

        # Profiles submenu
        self.profiles_menu = self.menu.addMenu("Profiles")
        self._update_profiles_menu()

        self.menu.addSeparator()

        # Settings
        settings_action = QAction("Settings", self.menu)
        settings_action.triggered.connect(self.settings_requested.emit)
        self.menu.addAction(settings_action)

        # Reload Config
        reload_action = QAction("Reload Config", self.menu)
        reload_action.triggered.connect(self.reload_config_requested.emit)
        self.menu.addAction(reload_action)

        self.menu.addSeparator()

        # Quit
        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)

    def _update_profiles_menu(self):
        """Update the profiles submenu"""
        self.profiles_menu.clear()

        if not self._profiles:
            no_profiles = QAction("(No profiles saved)", self.profiles_menu)
            no_profiles.setEnabled(False)
            self.profiles_menu.addAction(no_profiles)
            return

        for profile in self._profiles:
            action = QAction(profile, self.profiles_menu)
            action.setCheckable(True)
            action.setChecked(profile == self._current_profile)

            # Create closure to capture profile name
            def make_callback(p=profile):
                return lambda: self.profile_selected.emit(p)

            action.triggered.connect(make_callback())
            self.profiles_menu.addAction(action)

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
        self._update_profiles_menu()

    def set_current_profile(self, profile: str):
        """
        Set the current profile

        Args:
            profile: Profile name
        """
        self._current_profile = profile
        self._update_profiles_menu()

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
