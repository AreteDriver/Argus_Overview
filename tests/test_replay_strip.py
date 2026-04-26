"""Tests for ReplayStrip child widget (PR10)."""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent, QPixmap

from argus_overview.ui.replay_strip import ReplayStrip


def _pixmap(w: int = 50, h: int = 30, color: str = "#ff0000") -> QPixmap:
    pm = QPixmap(w, h)
    pm.fill(Qt.GlobalColor.red)
    return pm


def _move_event(x: int, y: int) -> QMouseEvent:
    return QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(float(x), float(y)),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )


class TestReplayStripInit:
    def test_default_state_empty(self, qapp):
        strip = ReplayStrip()
        try:
            assert strip.frame_count() == 0
            assert strip.hover_index() == -1
        finally:
            strip.deleteLater()

    def test_fixed_height(self, qapp):
        strip = ReplayStrip()
        try:
            assert strip.height() == ReplayStrip.STRIP_HEIGHT
        finally:
            strip.deleteLater()


class TestReplayStripSetFrames:
    def test_set_frames_stores_count(self, qapp):
        strip = ReplayStrip()
        try:
            strip.set_frames([_pixmap(), _pixmap(), _pixmap()])
            assert strip.frame_count() == 3
        finally:
            strip.deleteLater()

    def test_set_frames_replaces_previous(self, qapp):
        strip = ReplayStrip()
        try:
            strip.set_frames([_pixmap(), _pixmap()])
            strip.set_frames([_pixmap()])
            assert strip.frame_count() == 1
        finally:
            strip.deleteLater()

    def test_set_frames_clamps_stale_hover(self, qapp):
        strip = ReplayStrip()
        try:
            strip.set_frames([_pixmap(), _pixmap(), _pixmap()])
            strip.resize(300, ReplayStrip.STRIP_HEIGHT)
            # Force hover_index to position 2 by mouse-moving there.
            cell_w = (300 - ReplayStrip.CELL_PADDING * 2) // 3
            x = ReplayStrip.CELL_PADDING + 2 * cell_w + 1
            strip.mouseMoveEvent(_move_event(x, 10))
            assert strip.hover_index() == 2

            # Shrink the frame list — the stale hover should clamp to -1.
            strip.set_frames([_pixmap()])
            assert strip.hover_index() == -1
        finally:
            strip.deleteLater()


class TestReplayStripHover:
    def test_mouse_move_emits_index(self, qapp):
        strip = ReplayStrip()
        try:
            strip.set_frames([_pixmap(), _pixmap(), _pixmap()])
            strip.resize(300, ReplayStrip.STRIP_HEIGHT)
            received: list[int] = []
            strip.frame_hovered.connect(received.append)

            cell_w = (300 - ReplayStrip.CELL_PADDING * 2) // 3
            # Hover middle cell
            x = ReplayStrip.CELL_PADDING + cell_w + cell_w // 2
            strip.mouseMoveEvent(_move_event(x, 10))

            assert received == [1]
            assert strip.hover_index() == 1
        finally:
            strip.deleteLater()

    def test_mouse_move_outside_after_inside_emits_minus_one(self, qapp):
        strip = ReplayStrip()
        try:
            strip.set_frames([_pixmap(), _pixmap()])
            strip.resize(200, ReplayStrip.STRIP_HEIGHT)

            # First land on cell 0 so the hover index actually changes.
            cell_w = (200 - ReplayStrip.CELL_PADDING * 2) // 2
            strip.mouseMoveEvent(_move_event(ReplayStrip.CELL_PADDING + cell_w // 2, 10))
            assert strip.hover_index() == 0

            # Now connect listener and move past the right edge.
            received: list[int] = []
            strip.frame_hovered.connect(received.append)
            strip.mouseMoveEvent(_move_event(500, 10))

            assert received == [-1]
            assert strip.hover_index() == -1
        finally:
            strip.deleteLater()

    def test_mouse_move_dedupes_same_index(self, qapp):
        strip = ReplayStrip()
        try:
            strip.set_frames([_pixmap(), _pixmap()])
            strip.resize(200, ReplayStrip.STRIP_HEIGHT)
            received: list[int] = []
            strip.frame_hovered.connect(received.append)

            cell_w = (200 - ReplayStrip.CELL_PADDING * 2) // 2
            x1 = ReplayStrip.CELL_PADDING + cell_w // 2
            x2 = ReplayStrip.CELL_PADDING + cell_w // 4
            strip.mouseMoveEvent(_move_event(x1, 10))
            strip.mouseMoveEvent(_move_event(x2, 10))

            # Both x are inside cell 0 → only one emission
            assert received == [0]
        finally:
            strip.deleteLater()

    def test_leave_event_emits_minus_one(self, qapp):
        from PySide6.QtCore import QEvent

        strip = ReplayStrip()
        try:
            strip.set_frames([_pixmap(), _pixmap()])
            strip.resize(200, ReplayStrip.STRIP_HEIGHT)
            cell_w = (200 - ReplayStrip.CELL_PADDING * 2) // 2
            strip.mouseMoveEvent(_move_event(ReplayStrip.CELL_PADDING + cell_w // 2, 10))
            received: list[int] = []
            strip.frame_hovered.connect(received.append)

            strip.leaveEvent(QEvent(QEvent.Type.Leave))

            assert received == [-1]
            assert strip.hover_index() == -1
        finally:
            strip.deleteLater()


class TestReplayStripPaint:
    def test_paint_with_frames_does_not_crash(self, qapp):
        strip = ReplayStrip()
        try:
            strip.set_frames([_pixmap(), _pixmap()])
            strip.resize(200, ReplayStrip.STRIP_HEIGHT)
            strip.repaint()
        finally:
            strip.deleteLater()

    def test_paint_empty_does_not_crash(self, qapp):
        strip = ReplayStrip()
        try:
            strip.resize(200, ReplayStrip.STRIP_HEIGHT)
            strip.repaint()
        finally:
            strip.deleteLater()

    def test_paint_with_hover_highlight_does_not_crash(self, qapp):
        strip = ReplayStrip()
        try:
            strip.set_frames([_pixmap(), _pixmap(), _pixmap()])
            strip.resize(300, ReplayStrip.STRIP_HEIGHT)
            cell_w = (300 - ReplayStrip.CELL_PADDING * 2) // 3
            strip.mouseMoveEvent(_move_event(ReplayStrip.CELL_PADDING + cell_w // 2, 10))
            strip.repaint()
        finally:
            strip.deleteLater()
