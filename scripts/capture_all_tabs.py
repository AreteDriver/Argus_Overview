"""Capture screenshots of every tab in Argus Overview.

Usage:
    QT_QPA_PLATFORM=xcb python scripts/capture_all_tabs.py docs/screenshots/tabs/
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

sys.path.insert(0, "src")

# Neutralise hotkey manager so pynput doesn't try to grab X11 in headless mode
import argus_overview.core.hotkey_manager as _hm

_hm.HotkeyManager.start = lambda self: None
_hm.HotkeyManager.stop = lambda self: None
_hm.HotkeyManager.register_hotkey = lambda *a, **k: None
_hm.HotkeyManager.unregister_hotkey = lambda *a, **k: None
_hm.HotkeyManager.pause = lambda self: None
_hm.HotkeyManager.resume = lambda self: None
_hm.HotkeyManager.get_health = lambda self: ("unknown", "")

# Import after the monkey patches so MainWindowV21 picks them up.
from argus_overview.ui.main_window_v21 import MainWindowV21  # noqa: E402


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/screenshots/tabs")
    out_dir.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    window = MainWindowV21()
    window.resize(1440, 900)
    window.show()

    tabs = [
        (0, "overview"),
        (1, "cycle_control"),
        (2, "roster"),
        (3, "intel"),
        (4, "sync"),
        (5, "settings"),
    ]

    idx = 0

    def _capture_next():
        nonlocal idx
        if idx >= len(tabs):
            print("All tabs captured.")
            app.quit()
            return
        tab_index, tab_name = tabs[idx]
        window.tabs.setCurrentIndex(tab_index)
        window.repaint()
        QApplication.processEvents()
        QTimer.singleShot(500, lambda: _grab(tab_name))

    def _grab(tab_name: str):
        nonlocal idx
        pixmap = window.grab()
        path = out_dir / f"{tab_name}_1440.png"
        pixmap.save(str(path))
        print(f"  {tab_name}: {pixmap.width()}x{pixmap.height()} → {path}")
        idx += 1
        QTimer.singleShot(200, _capture_next)

    QTimer.singleShot(2000, _capture_next)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
