#!/usr/bin/env python3
"""
EVE Veles Eyes v2.2 Ultimate Edition - Windows
Main entry point with professional UI and all features

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
import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QMessageBox

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from eve_overview_pro.ui.main_window_v21 import MainWindowV21


class SingleInstance:
    """
    Ensures only one instance of the application can run at a time.
    Uses Windows mutex for reliable single-instance detection.
    """

    def __init__(self, app_name: str = "EVE-Veles-Eyes"):
        self.app_name = app_name
        self.mutex = None
        self.mutex_name = f"Global\\{app_name}-Mutex"

    def try_lock(self) -> bool:
        """
        Try to acquire the mutex.
        Returns True if successful (first instance), False if already running.
        """
        try:
            import win32api
            import win32event
            import winerror

            self.mutex = win32event.CreateMutex(None, False, self.mutex_name)
            last_error = win32api.GetLastError()

            if last_error == winerror.ERROR_ALREADY_EXISTS:
                # Another instance is running
                win32api.CloseHandle(self.mutex)
                self.mutex = None
                return False

            return True

        except ImportError:
            # win32 not available, use file lock fallback
            return self._file_lock_fallback()
        except Exception:
            # If mutex fails, allow running (graceful fallback)
            return True

    def _file_lock_fallback(self) -> bool:
        """Fallback file-based locking if win32 not available"""
        try:
            import msvcrt
            lock_path = Path(os.environ.get('LOCALAPPDATA', '.')) / 'eve-veles-eyes' / 'app.lock'
            lock_path.parent.mkdir(parents=True, exist_ok=True)

            self.lock_file = open(lock_path, 'w')
            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except:
            return False

    def release(self):
        """Release the mutex"""
        if self.mutex:
            try:
                import win32api
                win32api.CloseHandle(self.mutex)
            except:
                pass
            self.mutex = None

    def __enter__(self):
        return self.try_lock()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def setup_logging():
    """Setup logging configuration"""
    # Use LOCALAPPDATA on Windows
    log_dir = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'eve-veles-eyes'
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / 'eve-veles-eyes.log')
        ]
    )


def setup_dark_theme(app):
    """Setup professional dark theme"""
    app.setStyle('Fusion')

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


def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting EVE Veles Eyes v2.2 Ultimate Edition")

    # Single instance check
    single_instance = SingleInstance()
    if not single_instance.try_lock():
        logger.warning("Another instance is already running")
        # Need QApplication to show message box
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "Already Running",
            "EVE Veles Eyes is already running.\n\n"
            "Check your system tray for the existing instance."
        )
        sys.exit(1)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("EVE Veles Eyes")
    app.setOrganizationName("EVE Veles Eyes")

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


if __name__ == '__main__':
    main()
