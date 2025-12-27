#!/usr/bin/env python3
"""
EVE Veles Eyes v2.2 Ultimate Edition
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
"""
import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from eve_overview_pro.ui.main_window_v21 import MainWindowV21


def setup_logging():
    """Setup logging configuration"""
    log_dir = Path.home() / '.config' / 'eve-overview-pro'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / 'eve-overview-pro.log')
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
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("EVE Overview Pro")
    app.setOrganizationName("EVE Overview Pro")
    
    # Setup theme
    setup_dark_theme(app)
    
    # Create and show main window
    window = MainWindowV21()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
