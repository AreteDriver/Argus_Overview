"""Pytest configuration and shared fixtures."""

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create a single QApplication instance for all tests.

    Session-scoped to avoid Qt abort when multiple modules try to
    create QApplication instances.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't destroy - let Python garbage collector handle it
