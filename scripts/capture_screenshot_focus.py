"""Capture a screenshot of the Argus Overview main window with focus ring visible.

Usage:
    QT_QPA_PLATFORM=xcb python scripts/capture_screenshot_focus.py docs/screenshots/review_focus_1920.png
"""

from __future__ import annotations

import sys
import time

from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

sys.path.insert(0, "src")

from argus_overview.ui.main_window_v21 import MainWindowV21


def main():
    app = QApplication(sys.argv)
    window = MainWindowV21()
    window.show()

    def _focus_and_grab():
        # Focus the first preview frame so the focus ring is drawn
        if hasattr(window, "main_tab") and hasattr(window.main_tab, "window_manager"):
            frames = window.main_tab.window_manager.preview_frames
            if frames:
                first_frame = next(iter(frames.values()))
                first_frame.setFocus()
                # Force an immediate repaint so the ring renders
                first_frame.repaint()
        # Brief delay for focus change to propagate
        QTimer.singleShot(200, lambda: _grab_and_exit(window, app))

    QTimer.singleShot(2000, _focus_and_grab)
    sys.exit(app.exec())


def _grab_and_exit(window, app):
    pixmap = window.grab()
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/screenshots/review_focus.png"
    pixmap.save(path)
    print(f"Screenshot saved to {path} ({pixmap.width()}x{pixmap.height()})")
    app.quit()


if __name__ == "__main__":
    main()
