"""Reusable painting helpers for custom widgets.

All helpers accept a ``QPainter`` and design-system tokens so that
custom-painted widgets stay consistent without hardcoding geometry or
 colors.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from argus_overview.ui.design_system import colors, metrics


def _qcolor(hex_or_rgb: str | tuple[int, int, int], alpha: int = 255) -> QColor:
    """Build a ``QColor`` from a hex string or RGB tuple with optional alpha."""
    if isinstance(hex_or_rgb, str):
        c = QColor(hex_or_rgb)
    else:
        c = QColor(*hex_or_rgb)
    c.setAlpha(alpha)
    return c


def draw_rounded_border(
    painter: QPainter,
    rect: QRect,
    color: str | tuple[int, int, int] | QColor,
    *,
    width: int = 2,
    radius: int = metrics.RADIUS_CARD,
    alpha: int = 255,
    dashed: bool = False,
) -> None:
    """Draw a rounded rectangle border.

    Args:
        painter: Active QPainter.
        rect: Bounding rectangle (inclusive).
        color: Border color (hex, rgb tuple, or QColor).
        width: Pen width in pixels.
        radius: Corner radius.
        alpha: Optional alpha override.
        dashed: Use dashed line style.
    """
    pen = QPen(_qcolor(color, alpha) if not isinstance(color, QColor) else color)
    pen.setWidth(width)
    if dashed:
        pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    inset = width // 2 + 1
    painter.drawRoundedRect(
        rect.x() + inset,
        rect.y() + inset,
        rect.width() - 2 * inset,
        rect.height() - 2 * inset,
        radius,
        radius,
    )


def draw_solid_rounded_rect(
    painter: QPainter,
    rect: QRect,
    color: str | tuple[int, int, int] | QColor,
    *,
    radius: int = metrics.RADIUS_CARD,
    alpha: int = 255,
) -> None:
    """Fill a rounded rectangle with a solid color."""
    c = _qcolor(color, alpha) if not isinstance(color, QColor) else color
    painter.setPen(QPen(Qt.PenStyle.NoPen))
    painter.setBrush(QBrush(c))
    painter.drawRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)


def draw_badge(
    painter: QPainter,
    x: int,
    y: int,
    text: str,
    *,
    fg_color: str | tuple[int, int, int] = colors.TEXT_PRIMARY,
    bg_color: str | tuple[int, int, int] = colors.SURFACE,
    bg_alpha: int = 180,
    font_size_pt: int = 9,
    pad: int = 4,
    radius: int = metrics.RADIUS_CONTROL,
) -> QRect:
    """Draw a text badge with rounded background.

    Returns the bounding rectangle of the badge for layout chaining.
    """
    font = QFont(painter.font())
    font.setPointSize(font_size_pt)
    painter.setFont(font)
    metrics = painter.fontMetrics()
    text_w = metrics.horizontalAdvance(text)
    badge_w = text_w + pad * 2
    badge_h = metrics.height() + pad
    badge_rect = QRect(x, y, badge_w, badge_h)

    # Background
    painter.setPen(QPen(Qt.PenStyle.NoPen))
    painter.setBrush(QBrush(_qcolor(bg_color, bg_alpha)))
    painter.drawRoundedRect(badge_rect.x(), badge_rect.y(), badge_w, badge_h, radius, radius)

    # Text
    painter.setPen(QPen(_qcolor(fg_color)))
    painter.drawText(
        badge_rect.x() + pad,
        badge_rect.y() + pad + metrics.ascent() - 2,
        text,
    )
    return badge_rect


def draw_pill(
    painter: QPainter,
    x: int,
    y: int,
    text: str,
    *,
    fg_color: str | tuple[int, int, int] = colors.TEXT_PRIMARY,
    bg_color: str | tuple[int, int, int] = colors.CANVAS,
    bg_alpha: int = 200,
    font_size_pt: int = 8,
    pad: int = 4,
    radius: int = metrics.RADIUS_CONTROL,
) -> QRect:
    """Draw a compact pill label (semantically a small badge).

    Returns the bounding rectangle.
    """
    return draw_badge(
        painter,
        x,
        y,
        text,
        fg_color=fg_color,
        bg_color=bg_color,
        bg_alpha=bg_alpha,
        font_size_pt=font_size_pt,
        pad=pad,
        radius=radius,
    )


def draw_status_dot(
    painter: QPainter,
    center_x: int,
    center_y: int,
    color: str | tuple[int, int, int],
    *,
    radius: int = 4,
    alpha: int = 255,
) -> None:
    """Draw a solid circle status indicator."""
    painter.setBrush(QBrush(_qcolor(color, alpha)))
    painter.setPen(QPen(Qt.PenStyle.NoPen))
    painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)


def widget_rect(widget: QWidget, margin: int = 0) -> QRect:
    """Return the client rectangle of a widget, optionally inset by margin."""
    return QRect(margin, margin, widget.width() - 2 * margin, widget.height() - 2 * margin)
