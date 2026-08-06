"""Tests for the Layouts-tab visual widgets (PR L1)."""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent

from argus_overview.ui.layout_widgets import (
    PATTERN_CELLS,
    MonitorCard,
    MonitorCardStrip,
    PatternThumbnail,
    PatternThumbStrip,
)


def _click(widget, x: int = 5, y: int = 5):
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(float(x), float(y)),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)


# =============================================================================
# PatternThumbnail
# =============================================================================


class TestPatternThumbnail:
    def test_default_state(self, qapp):
        thumb = PatternThumbnail("2x2 Grid")
        try:
            assert thumb.pattern_name == "2x2 Grid"
            assert thumb.is_selected() is False
        finally:
            thumb.deleteLater()

    def test_set_selected(self, qapp):
        thumb = PatternThumbnail("Cascade")
        try:
            thumb.set_selected(True)
            assert thumb.is_selected() is True
            thumb.set_selected(False)
            assert thumb.is_selected() is False
        finally:
            thumb.deleteLater()

    def test_set_selected_idempotent(self, qapp):
        thumb = PatternThumbnail("2x2 Grid")
        try:
            thumb.set_selected(True)
            thumb.set_selected(True)  # no-op
            assert thumb.is_selected() is True
        finally:
            thumb.deleteLater()

    def test_click_emits_pattern_name(self, qapp):
        thumb = PatternThumbnail("3x1 Row")
        try:
            received: list[str] = []
            thumb.clicked.connect(received.append)
            _click(thumb)
            assert received == ["3x1 Row"]
        finally:
            thumb.deleteLater()

    def test_paint_with_cells_does_not_crash(self, qapp):
        thumb = PatternThumbnail("Main + Sides")
        try:
            thumb.resize(thumb.THUMB_W, thumb.THUMB_H + thumb.LABEL_H)
            thumb.repaint()
        finally:
            thumb.deleteLater()

    def test_paint_custom_pattern_does_not_crash(self, qapp):
        thumb = PatternThumbnail("Custom")
        try:
            thumb.resize(thumb.THUMB_W, thumb.THUMB_H + thumb.LABEL_H)
            thumb.repaint()
        finally:
            thumb.deleteLater()

    def test_paint_stacked_pattern_does_not_crash(self, qapp):
        thumb = PatternThumbnail("Stacked (All Same Position)")
        try:
            thumb.resize(thumb.THUMB_W, thumb.THUMB_H + thumb.LABEL_H)
            thumb.repaint()
        finally:
            thumb.deleteLater()

    def test_every_documented_pattern_renders(self, qapp):
        # Sanity: each pattern in PATTERN_CELLS can construct + paint.
        for name in PATTERN_CELLS:
            thumb = PatternThumbnail(name)
            try:
                thumb.resize(thumb.THUMB_W, thumb.THUMB_H + thumb.LABEL_H)
                thumb.repaint()
            finally:
                thumb.deleteLater()


# =============================================================================
# PatternThumbStrip
# =============================================================================


class TestPatternThumbStrip:
    def test_default_no_selection(self, qapp):
        strip = PatternThumbStrip(["2x2 Grid", "3x1 Row"])
        try:
            assert strip.selected_pattern() is None
        finally:
            strip.deleteLater()

    def test_set_selected_changes_pattern(self, qapp):
        strip = PatternThumbStrip(["2x2 Grid", "3x1 Row"])
        try:
            received: list[str] = []
            strip.pattern_selected.connect(received.append)
            strip.set_selected("3x1 Row")
            assert strip.selected_pattern() == "3x1 Row"
            assert received == ["3x1 Row"]
        finally:
            strip.deleteLater()

    def test_set_selected_unknown_pattern_noop(self, qapp):
        strip = PatternThumbStrip(["2x2 Grid"])
        try:
            received: list[str] = []
            strip.pattern_selected.connect(received.append)
            strip.set_selected("DoesNotExist")
            assert strip.selected_pattern() is None
            assert received == []
        finally:
            strip.deleteLater()

    def test_set_selected_dedupes(self, qapp):
        strip = PatternThumbStrip(["2x2 Grid", "3x1 Row"])
        try:
            received: list[str] = []
            strip.pattern_selected.connect(received.append)
            strip.set_selected("2x2 Grid")
            strip.set_selected("2x2 Grid")  # no-op
            assert received == ["2x2 Grid"]
        finally:
            strip.deleteLater()

    def test_clicking_thumb_selects_strip_pattern(self, qapp):
        strip = PatternThumbStrip(["2x2 Grid", "3x1 Row", "Cascade"])
        try:
            received: list[str] = []
            strip.pattern_selected.connect(received.append)
            # Find the Cascade thumbnail and click it
            thumb = strip._thumbnails["Cascade"]
            _click(thumb)
            assert strip.selected_pattern() == "Cascade"
            assert received == ["Cascade"]
        finally:
            strip.deleteLater()

    def test_changing_selection_clears_previous(self, qapp):
        strip = PatternThumbStrip(["2x2 Grid", "3x1 Row"])
        try:
            strip.set_selected("2x2 Grid")
            strip.set_selected("3x1 Row")
            assert strip._thumbnails["2x2 Grid"].is_selected() is False
            assert strip._thumbnails["3x1 Row"].is_selected() is True
        finally:
            strip.deleteLater()


# =============================================================================
# MonitorCard
# =============================================================================


class TestMonitorCard:
    def test_default_state(self, qapp):
        card = MonitorCard(0, 1920, 1080, is_primary=True)
        try:
            assert card.index == 0
            assert card.width_px == 1920
            assert card.height_px == 1080
            assert card.is_primary is True
            assert card.is_selected() is False
        finally:
            card.deleteLater()

    def test_set_selected(self, qapp):
        card = MonitorCard(1, 2560, 1440)
        try:
            card.set_selected(True)
            assert card.is_selected() is True
            card.set_selected(False)
            assert card.is_selected() is False
        finally:
            card.deleteLater()

    def test_click_emits_index(self, qapp):
        card = MonitorCard(2, 3840, 2160, is_primary=False)
        try:
            received: list[int] = []
            card.clicked.connect(received.append)
            _click(card)
            assert received == [2]
        finally:
            card.deleteLater()


# =============================================================================
# MonitorCardStrip
# =============================================================================


class TestMonitorCardStrip:
    def test_default_empty(self, qapp):
        strip = MonitorCardStrip()
        try:
            assert strip.card_count() == 0
            assert strip.selected_index() is None
        finally:
            strip.deleteLater()

    def test_set_monitors_creates_cards(self, qapp):
        strip = MonitorCardStrip()
        try:
            strip.set_monitors(
                [
                    (0, 1920, 1080, True),
                    (1, 2560, 1440, False),
                ]
            )
            assert strip.card_count() == 2
        finally:
            strip.deleteLater()

    def test_set_monitors_replaces_previous(self, qapp):
        strip = MonitorCardStrip()
        try:
            strip.set_monitors([(0, 1920, 1080, True)])
            strip.set_monitors([(0, 2560, 1440, False), (1, 1920, 1080, True)])
            assert strip.card_count() == 2
            assert strip.selected_index() is None  # prior selection cleared
        finally:
            strip.deleteLater()

    def test_set_selected_emits(self, qapp):
        strip = MonitorCardStrip()
        try:
            strip.set_monitors([(0, 1920, 1080, True), (1, 2560, 1440, False)])
            received: list[int] = []
            strip.monitor_selected.connect(received.append)
            strip.set_selected(1)
            assert strip.selected_index() == 1
            assert received == [1]
        finally:
            strip.deleteLater()

    def test_set_selected_unknown_index_noop(self, qapp):
        strip = MonitorCardStrip()
        try:
            strip.set_monitors([(0, 1920, 1080, True)])
            received: list[int] = []
            strip.monitor_selected.connect(received.append)
            strip.set_selected(99)
            assert received == []
        finally:
            strip.deleteLater()

    def test_clicking_card_selects_strip(self, qapp):
        strip = MonitorCardStrip()
        try:
            strip.set_monitors([(0, 1920, 1080, True), (1, 2560, 1440, False)])
            received: list[int] = []
            strip.monitor_selected.connect(received.append)
            _click(strip._cards[1])
            assert strip.selected_index() == 1
            assert received == [1]
        finally:
            strip.deleteLater()
