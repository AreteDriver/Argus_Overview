"""Pytest configuration and shared fixtures."""

import os
import sys

import pytest

# Set Qt platform plugin before importing PySide6
# When running under xvfb (DISPLAY is set), use xcb platform
# Otherwise use offscreen for headless testing
if "QT_QPA_PLATFORM" not in os.environ:
    if "DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    else:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

# Create QApplication at module load time to ensure it exists
# before any Qt widgets are imported by test files
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
