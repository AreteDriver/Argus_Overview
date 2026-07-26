"""Capture Argus Overview screenshots at multiple resolutions and DPI scales.

Targets:
    1024×768, 1280×720, 1440×900, 1920×1080
    Plus 200% scaling at 960×600 (simulated high-DPI)

Usage:
    QT_QPA_PLATFORM=xcb python scripts/capture_screenshot_matrix.py docs/screenshots/matrix/
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
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

from argus_overview.ui.main_window_v21 import MainWindowV21


RESOLUTIONS = [
    (1024, 768),
    (1280, 720),
    (1440, 900),
    (1920, 1080),
]


def _grab(window, out_dir: Path, name: str) -> None:
    QApplication.processEvents()
    pixmap = window.grab()
    path = out_dir / f"{name}.png"
    pixmap.save(str(path))
    print(f"  {name}: {pixmap.width()}x{pixmap.height()} → {path}")


def _run_matrix(out_dir: Path) -> None:
    app = QApplication(sys.argv)
    window = MainWindowV21()
    window.show()

    def _capture_all():
        for w, h in RESOLUTIONS:
            window.resize(w, h)
            window.repaint()
            QApplication.processEvents()
            _grab(window, out_dir, f"review_{w}x{h}")

        # High-DPI simulation: 200% scale at 960×600 logical (1920×1200 physical)
        os.environ["QT_SCALE_FACTOR"] = "2"
        window.resize(960, 600)
        window.repaint()
        QApplication.processEvents()
        _grab(window, out_dir, "review_960x600_200pct")

        print("Matrix complete.")
        app.quit()

    QTimer.singleShot(2000, _capture_all)
    sys.exit(app.exec())


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/screenshots/matrix")
    out_dir.mkdir(parents=True, exist_ok=True)
    _run_matrix(out_dir)


if __name__ == "__main__":
    main()
