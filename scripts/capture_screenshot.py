"""Capture a screenshot of the Argus Overview main window for visual review.

Usage:
    QT_QPA_PLATFORM=xcb python scripts/capture_screenshot.py docs/screenshots/review_1920x1080.png
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

# Ensure src is on path
sys.path.insert(0, "src")

from argus_overview.ui.main_window_v21 import MainWindowV21


def main():
    app = QApplication(sys.argv)
    window = MainWindowV21()
    window.show()

    # Wait for widgets to render
    QTimer.singleShot(2000, lambda: _grab_and_exit(window, app))
    sys.exit(app.exec())


def _grab_and_exit(window, app):
    pixmap = window.grab()
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/screenshots/review.png"
    pixmap.save(path)
    print(f"Screenshot saved to {path} ({pixmap.width()}x{pixmap.height()})")
    app.quit()


if __name__ == "__main__":
    main()
