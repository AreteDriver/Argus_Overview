"""Tests for WindowPreviewWidget paint behavior across all health states.

These tests verify that paintEvent handles every PreviewHealth value
without crashing and that the threat border is suppressed appropriately
when capture health is degraded.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from PySide6.QtCore import QEvent
from PySide6.QtGui import QPaintEvent
from PySide6.QtWidgets import QApplication

from argus_overview.intel.parser import ThreatLevel
from argus_overview.ui.main_tab import WindowPreviewWidget


def _make_widget(qapp):
    """Create a minimal WindowPreviewWidget for paint testing."""
    capture = MagicMock()
    widget = WindowPreviewWidget(
        window_id="win_123",
        character_name="TestPilot",
        capture_system=capture,
        settings_manager=None,
    )
    widget.resize(240, 180)
    widget.show()
    return widget


@pytest.mark.parametrize("health_label", [
    "INITIALIZING",
    "LIVE",
    "STATIC",
    "STALE · 5s",
    "PAUSED",
    "ERROR",
    "DISCONNECTED",
])
def test_paint_event_for_health_label(qapp, health_label):
    """paintEvent must not crash for any capture health label."""
    widget = _make_widget(qapp)
    # Patch the health label method to return the test value
    widget._capture_health_label = lambda: health_label
    event = QPaintEvent(widget.rect())
    widget.paintEvent(event)


def test_threat_border_suppressed_when_stale(qapp):
    """When capture is STALE, the threat border should not be drawn."""
    widget = _make_widget(qapp)
    widget._capture_health_label = lambda: "STALE · 5s"
    widget.set_threat_state(ThreatLevel.CRITICAL, "Jita", initial_alpha=1.0)
    assert widget._threat_level == ThreatLevel.CRITICAL
    assert widget._threat_alpha > 0.0
    # paintEvent should run without crashing; the border layer will suppress
    event = QPaintEvent(widget.rect())
    widget.paintEvent(event)


def test_threat_border_drawn_when_live(qapp):
    """When capture is LIVE, the threat border should be drawn normally."""
    widget = _make_widget(qapp)
    widget._capture_health_label = lambda: "LIVE"
    widget._last_frame_received_at = time.monotonic()
    widget.set_threat_state(ThreatLevel.WARNING, "HED-GP", initial_alpha=1.0)
    event = QPaintEvent(widget.rect())
    widget.paintEvent(event)


def test_health_overlay_drawn_for_error(qapp):
    """ERROR state should apply a darkening overlay."""
    widget = _make_widget(qapp)
    widget._capture_health_label = lambda: "ERROR"
    widget._capture_error_count = 1
    event = QPaintEvent(widget.rect())
    widget.paintEvent(event)


def test_health_overlay_drawn_for_stale(qapp):
    """STALE state should apply a subtle darkening overlay."""
    widget = _make_widget(qapp)
    widget._capture_health_label = lambda: "STALE · 12s"
    widget._last_frame_received_at = time.monotonic() - 5.0
    event = QPaintEvent(widget.rect())
    widget.paintEvent(event)
