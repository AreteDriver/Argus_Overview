"""Tests for SystemStatusBar (PR8 — custom paint, no rich-text labels).

Covers:
- 5 default indicators created on init, all showing unknown/grey.
- set_status updates dot colour and tooltip.
- get_status returns the stored (status, detail) tuple.
- paintEvent produces non-empty output so we know it renders.
"""

from __future__ import annotations

from unittest.mock import patch

from PySide6.QtGui import QPainter, QPaintEvent

from argus_overview.ui.system_status_bar import SystemStatusBar


class TestSystemStatusBarInit:
    def test_five_indicators_created(self, qapp):
        bar = SystemStatusBar()
        assert len(bar._indicators) == 5
        assert set(bar._indicators.keys()) == {
            "capture",
            "hotkeys",
            "discovery",
            "intel",
            "location",
        }

    def test_all_unknown_on_init(self, qapp):
        bar = SystemStatusBar()
        for key in bar._indicators:
            assert bar.get_status(key) == ("unknown", "")

    def test_tooltips_set_on_init(self, qapp):
        bar = SystemStatusBar()
        for key, label in (
            ("capture", "Capture"),
            ("hotkeys", "Hotkeys"),
            ("discovery", "Discovery"),
            ("intel", "Intel"),
            ("location", "Location"),
        ):
            tooltip = bar._indicators[key].toolTip()
            assert f"{label}: unknown" in tooltip


class TestSystemStatusBarSetStatus:
    def test_set_status_changes_tooltip(self, qapp):
        bar = SystemStatusBar()
        bar.set_status("capture", "healthy", "workers running")
        tooltip = bar._indicators["capture"].toolTip()
        assert "Capture: healthy" in tooltip
        assert "workers running" in tooltip

    def test_set_status_unknown_colour_fallback(self, qapp):
        bar = SystemStatusBar()
        bar.set_status("capture", "nonexistent_status")
        # Should fall back to unknown colour silently
        assert bar.get_status("capture") == ("nonexistent_status", "")

    def test_set_status_stores_detail(self, qapp):
        bar = SystemStatusBar()
        bar.set_status("intel", "degraded", "parser lag")
        assert bar.get_status("intel") == ("degraded", "parser lag")

    def test_set_status_ignores_invalid_subsystem(self, qapp):
        bar = SystemStatusBar()
        bar.set_status("not_real", "healthy")  # should not raise


class TestSystemStatusBarPaint:
    def test_indicator_paint_event_runs(self, qapp):
        """Ensure the custom paintEvent does not crash and renders something."""
        bar = SystemStatusBar()
        indicator = bar._indicators["capture"]

        # Trigger a paint by showing + repainting (best-effort in headless)
        indicator.show()
        indicator.repaint()

        # We can't easily assert pixel colours in CI, but we can verify
        # the widget has a minimum size and no RuntimeError was raised.
        assert indicator.width() > 0
        assert indicator.height() > 0

    def test_painter_called_in_paint_event(self, qapp):
        """Patch QPainter to confirm drawing primitives are invoked."""
        bar = SystemStatusBar()
        indicator = bar._indicators["capture"]

        with patch.object(QPainter, "drawText") as mock_draw_text, patch.object(
            QPainter, "drawEllipse"
        ) as mock_draw_ellipse:
            # Fake a paint event
            event = QPaintEvent(indicator.rect())
            indicator.paintEvent(event)
            # drawEllipse for the dot, drawText for the label
            assert mock_draw_ellipse.call_count >= 1
            assert mock_draw_text.call_count >= 1

    def test_all_status_colours_render(self, qapp):
        """Cycle through every known status and ensure paint succeeds."""
        bar = SystemStatusBar()
        for status in ("healthy", "degraded", "unavailable", "unknown"):
            bar.set_status("capture", status)
            indicator = bar._indicators["capture"]
            event = QPaintEvent(indicator.rect())
            indicator.paintEvent(event)  # should not raise
