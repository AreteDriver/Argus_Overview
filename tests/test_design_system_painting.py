"""Tests for design_system.painting helpers.

Verifies that draw_badge, draw_pill, draw_rounded_border, and
draw_status_dot do not crash and produce reasonable geometry.
"""

from __future__ import annotations

import pytest

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from argus_overview.ui.design_system import colors, metrics
from argus_overview.ui.design_system.painting import (
    draw_badge,
    draw_pill,
    draw_rounded_border,
    draw_solid_rounded_rect,
    draw_status_dot,
    widget_rect,
)


@pytest.fixture
def painter():
    """Yield a QPainter backed by a QPixmap."""
    pixmap = QPixmap(400, 300)
    pixmap.fill(QColor("transparent"))
    p = QPainter(pixmap)
    yield p
    p.end()


class TestDrawRoundedBorder:
    def test_does_not_crash(self, painter):
        rect = QRect(10, 10, 100, 80)
        draw_rounded_border(painter, rect, colors.HEALTHY, width=2, radius=6)

    def test_dashed_does_not_crash(self, painter):
        rect = QRect(10, 10, 100, 80)
        draw_rounded_border(painter, rect, colors.WARNING, dashed=True)


class TestDrawSolidRoundedRect:
    def test_does_not_crash(self, painter):
        rect = QRect(10, 10, 100, 80)
        draw_solid_rounded_rect(painter, rect, colors.SURFACE, alpha=180)


class TestDrawBadge:
    def test_returns_non_empty_rect(self, painter):
        rect = draw_badge(painter, 10, 10, "LIVE", fg_color=colors.HEALTHY)
        assert rect.width() > 0
        assert rect.height() > 0

    def test_accepts_rgb_tuple(self, painter):
        rect = draw_badge(painter, 10, 10, "TEST", fg_color=(255, 255, 255))
        assert rect.width() > 0


class TestDrawPill:
    def test_returns_non_empty_rect(self, painter):
        rect = draw_pill(painter, 10, 10, "+2j", fg_color=colors.WARNING)
        assert rect.width() > 0
        assert rect.height() > 0


class TestDrawStatusDot:
    def test_does_not_crash(self, painter):
        draw_status_dot(painter, 50, 50, colors.CRITICAL, radius=6)


class TestWidgetRect:
    def test_returns_correct_size(self, qapp):
        widget = QWidget()
        widget.resize(200, 150)
        r = widget_rect(widget)
        assert r.width() == 200
        assert r.height() == 150

    def test_margin_insets_correctly(self, qapp):
        widget = QWidget()
        widget.resize(200, 150)
        r = widget_rect(widget, margin=10)
        assert r.width() == 180
        assert r.height() == 130
        assert r.x() == 10
        assert r.y() == 10
