"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Enforce supported runtime before importing Qt to avoid hard aborts in old interpreters.
if sys.version_info < (3, 10):  # noqa: UP036
    raise RuntimeError(
        "Argus Overview tests require Python 3.10+. "
        "Recreate your test environment with Python 3.10+."
    )

from PySide6 import __file__ as pyside6_file

# Set Qt platform plugin before importing PySide6
# Use offscreen platform for CI environments (GitHub Actions sets CI=true)
# This avoids display server compatibility issues with PySide6
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

_pyside6_root = Path(pyside6_file).resolve().parent
_qt_plugins_dir = _pyside6_root / "Qt" / "plugins"
_qt_platforms_dir = _qt_plugins_dir / "platforms"
os.environ.setdefault("QT_PLUGIN_PATH", str(_qt_plugins_dir))
os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(_qt_platforms_dir))

from PySide6.QtCore import QCoreApplication  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

# Create QApplication at module load time to ensure it exists
# before any Qt widgets are imported by test files
QCoreApplication.setLibraryPaths([str(_qt_plugins_dir)])
_qapp_instance = QApplication.instance()
if _qapp_instance is None:
    _qapp_instance = QApplication(sys.argv[:1])


@pytest.fixture(scope="session")
def qapp():
    """Provide the QApplication instance for tests.

    The application is created at module load time to avoid
    issues with Qt initialization order in CI.
    """
    return _qapp_instance
