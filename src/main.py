#!/usr/bin/env python3
"""
Argus Overview v2.4 - ActionRegistry Edition
Main entry point with professional UI and all features

v2.4 Features:
- ActionRegistry: Single source of truth for all UI actions
- Centralized menu/toolbar building from registry
- Tab renames: Overview, Cycle Control, Roster, Sync
- ToolbarBuilder and ContextMenuBuilder classes
- CLI audit tool for redundancy checking

v2.2 Features:
- System tray with minimize-to-tray
- One-click EVE window import
- Auto-discovery of new EVE clients
- Per-character hotkeys
- Thumbnail hover effects (opacity/zoom)
- Activity indicators
- Session timers
- Custom labels for characters
- Themes (Dark, Light, EVE)
- Hot reload configuration
- Position lock for thumbnails
- Single instance enforcement
"""

import fcntl
import logging
import os
import sys
from pathlib import Path
from typing import Optional, TextIO

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QMessageBox

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# NOTE: MainWindowV21 is imported INSIDE main() AFTER single-instance check
# to prevent race conditions from early imports starting background threads


class SingleInstance:
    """
    Ensures only one instance of the application can run at a time.
    Uses a lock file with fcntl for reliable locking on Linux.
    """

    def __init__(self, app_name: str = "argus-overview"):
        self.app_name = app_name
        self.lock_file: Optional[TextIO] = None
        self.lock_path = Path.home() / ".config" / "argus-overview" / f"{app_name}.lock"

        # Ensure directory exists
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

    def try_lock(self) -> bool:
        """
        Try to acquire the lock.
        Returns True if successful (first instance), False if already running.
        """
        try:
            self.lock_file = open(self.lock_path, "w")
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Write PID to lock file
                self.lock_file.write(str(os.getpid()))
                self.lock_file.flush()
                return True
            except Exception:
                # Lock failed or other error - clean up file handle
                self.lock_file.close()
                self.lock_file = None
                raise
        except OSError:
            # Lock is held by another instance or file operation failed
            return False

    def release(self):
        """Release the lock"""
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
            except (OSError, ValueError):
                pass  # File already closed or released, safe to ignore
            self.lock_file = None

    def __enter__(self):
        return self.try_lock()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def setup_logging():
    """Setup logging configuration"""
    log_dir = Path.home() / ".config" / "argus-overview"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_dir / "argus-overview.log")],
    )


def setup_dark_theme(app):
    """Setup professional dark theme"""
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)


def check_wayland_compatibility() -> bool:
    """Check for Wayland compatibility and warn user if needed.

    Returns:
        True if should continue, False if user cancelled.
    """
    from argus_overview.utils.display_server import (
        DisplayServer,
        detect_display_server,
        get_wayland_limitation_message,
    )

    info = detect_display_server()

    if info.server == DisplayServer.WAYLAND and not info.has_x11_access:
        # Pure Wayland - show warning
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Wayland Detected")
        msg_box.setText("Pure Wayland session detected - limited functionality")
        msg_box.setInformativeText(get_wayland_limitation_message())
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)

        result = msg_box.exec()
        if result == QMessageBox.StandardButton.Cancel:
            return False

    elif info.server == DisplayServer.XWAYLAND:
        # XWayland - log info, should work
        logging.getLogger(__name__).info(
            "Running under XWayland - X11 tools available, full functionality expected"
        )

    return True


def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting Argus Overview v2.4")

    # Create QApplication early (needed for dialogs)
    app = QApplication(sys.argv)

    # Single instance check
    single_instance = SingleInstance()
    if not single_instance.try_lock():
        logger.warning("Another instance is already running")
        QMessageBox.warning(
            None,
            "Already Running",
            "Argus Overview is already running.\n\n"
            "Check your system tray for the existing instance.",
        )
        sys.exit(1)

    # Check Wayland compatibility before importing X11-dependent modules
    if not check_wayland_compatibility():
        logger.info("User cancelled due to Wayland limitations")
        single_instance.release()
        sys.exit(0)

    # Import main window AFTER lock acquired and Wayland check passed
    # (importing can start background threads/X11 hooks)
    from argus_overview.ui.main_window_v21 import MainWindowV21

    # Configure application (QApplication already created above)
    app.setApplicationName("Argus Overview")
    app.setOrganizationName("Argus Overview")
    app.setDesktopFileName("argus-overview")  # Matches .desktop file name

    # Setup theme
    setup_dark_theme(app)

    # Create and show main window
    window = MainWindowV21()
    window.show()

    # Run application
    exit_code = app.exec()

    # Release lock on exit
    single_instance.release()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
