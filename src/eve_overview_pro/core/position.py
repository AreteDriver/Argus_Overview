"""
Position Inheritance - Smart positioning for new thumbnail windows
v2.2 Feature: Automatically position new thumbnails relative to existing ones
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication


@dataclass
class ThumbnailPosition:
    """Position and size of a thumbnail"""
    x: int
    y: int
    width: int
    height: int

    def to_rect(self) -> QRect:
        return QRect(self.x, self.y, self.width, self.height)

    @classmethod
    def from_rect(cls, rect: QRect) -> 'ThumbnailPosition':
        return cls(rect.x(), rect.y(), rect.width(), rect.height())


class PositionManager:
    """
    Manages thumbnail positioning with smart inheritance.

    Features:
    - Places new thumbnails relative to existing ones
    - Respects screen boundaries
    - Supports grid snapping
    - Works with layout presets
    """

    # Default thumbnail size
    DEFAULT_WIDTH = 280
    DEFAULT_HEIGHT = 200

    # Margins and spacing
    MARGIN = 20
    SPACING = 10
    GRID_SIZE = 10

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Current positions of thumbnails
        self.positions: Dict[str, ThumbnailPosition] = {}

        # Grid snapping enabled
        self.snap_to_grid = True

        # Lock positions
        self.locked = False

    def get_next_position(self,
                          window_id: str,
                          preset_positions: Optional[Dict[str, ThumbnailPosition]] = None
                          ) -> ThumbnailPosition:
        """
        Calculate position for a new thumbnail.

        Args:
            window_id: Window ID for the new thumbnail
            preset_positions: Optional layout preset positions

        Returns:
            ThumbnailPosition for the new thumbnail
        """
        # If we have a preset position for this window, use it
        if preset_positions and window_id in preset_positions:
            pos = preset_positions[window_id]
            self.logger.debug(f"Using preset position for {window_id}: ({pos.x}, {pos.y})")
            return pos

        # Get screen geometry
        screen = self._get_primary_screen()

        # If no existing thumbnails, start at top-left with margin
        if not self.positions:
            pos = ThumbnailPosition(
                x=self.MARGIN,
                y=self.MARGIN,
                width=self.DEFAULT_WIDTH,
                height=self.DEFAULT_HEIGHT
            )
            self.logger.debug(f"First thumbnail position: ({pos.x}, {pos.y})")
            return self._snap_position(pos)

        # Try to place to the right of rightmost thumbnail
        rightmost = self._get_rightmost()
        if rightmost:
            new_x = rightmost.x + rightmost.width + self.SPACING
            new_y = rightmost.y

            # Check if it fits on screen
            if new_x + self.DEFAULT_WIDTH <= screen.width() - self.MARGIN:
                pos = ThumbnailPosition(
                    x=new_x,
                    y=new_y,
                    width=self.DEFAULT_WIDTH,
                    height=self.DEFAULT_HEIGHT
                )
                self.logger.debug(f"Placing to right of rightmost: ({pos.x}, {pos.y})")
                return self._snap_position(pos)

        # Try to place below bottommost thumbnail (new row)
        bottommost = self._get_bottommost()
        if bottommost:
            new_x = self.MARGIN
            new_y = bottommost.y + bottommost.height + self.SPACING

            # Check if it fits on screen
            if new_y + self.DEFAULT_HEIGHT <= screen.height() - self.MARGIN:
                pos = ThumbnailPosition(
                    x=new_x,
                    y=new_y,
                    width=self.DEFAULT_WIDTH,
                    height=self.DEFAULT_HEIGHT
                )
                self.logger.debug(f"Placing below bottommost (new row): ({pos.x}, {pos.y})")
                return self._snap_position(pos)

        # Fallback: stack with offset from first
        if self.positions:
            first = next(iter(self.positions.values()))
            offset = len(self.positions) * 30
            pos = ThumbnailPosition(
                x=first.x + offset,
                y=first.y + offset,
                width=self.DEFAULT_WIDTH,
                height=self.DEFAULT_HEIGHT
            )
            self.logger.debug(f"Fallback cascade position: ({pos.x}, {pos.y})")
            return self._snap_position(pos)

        # Ultimate fallback
        return ThumbnailPosition(
            x=self.MARGIN,
            y=self.MARGIN,
            width=self.DEFAULT_WIDTH,
            height=self.DEFAULT_HEIGHT
        )

    def register_position(self, window_id: str, position: ThumbnailPosition):
        """
        Register a thumbnail's current position.

        Args:
            window_id: Window ID
            position: Current position
        """
        self.positions[window_id] = position
        self.logger.debug(f"Registered position for {window_id}: ({position.x}, {position.y})")

    def update_position(self, window_id: str, position: ThumbnailPosition) -> bool:
        """
        Update a thumbnail's position.

        Args:
            window_id: Window ID
            position: New position

        Returns:
            True if updated (not locked)
        """
        if self.locked:
            self.logger.debug(f"Position update blocked (locked): {window_id}")
            return False

        self.positions[window_id] = position
        return True

    def remove_position(self, window_id: str):
        """
        Remove a thumbnail's position tracking.

        Args:
            window_id: Window ID to remove
        """
        if window_id in self.positions:
            del self.positions[window_id]
            self.logger.debug(f"Removed position for {window_id}")

    def set_locked(self, locked: bool):
        """
        Lock or unlock all positions.

        Args:
            locked: True to lock positions
        """
        self.locked = locked
        self.logger.info(f"Positions {'locked' if locked else 'unlocked'}")

    def is_locked(self) -> bool:
        """Check if positions are locked"""
        return self.locked

    def set_snap_to_grid(self, enabled: bool):
        """
        Enable or disable grid snapping.

        Args:
            enabled: True to enable snapping
        """
        self.snap_to_grid = enabled
        self.logger.info(f"Grid snapping {'enabled' if enabled else 'disabled'}")

    def _snap_position(self, position: ThumbnailPosition) -> ThumbnailPosition:
        """
        Snap position to grid if enabled.

        Args:
            position: Original position

        Returns:
            Snapped position
        """
        if not self.snap_to_grid:
            return position

        snapped_x = round(position.x / self.GRID_SIZE) * self.GRID_SIZE
        snapped_y = round(position.y / self.GRID_SIZE) * self.GRID_SIZE

        return ThumbnailPosition(
            x=snapped_x,
            y=snapped_y,
            width=position.width,
            height=position.height
        )

    def _get_rightmost(self) -> Optional[ThumbnailPosition]:
        """Get the rightmost thumbnail position"""
        if not self.positions:
            return None

        return max(self.positions.values(), key=lambda p: p.x + p.width)

    def _get_bottommost(self) -> Optional[ThumbnailPosition]:
        """Get the bottommost thumbnail position"""
        if not self.positions:
            return None

        return max(self.positions.values(), key=lambda p: p.y + p.height)

    def _get_primary_screen(self) -> QRect:
        """Get primary screen geometry"""
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                return screen.availableGeometry()

        # Fallback
        return QRect(0, 0, 1920, 1080)

    def get_all_positions(self) -> Dict[str, ThumbnailPosition]:
        """Get all current positions"""
        return self.positions.copy()

    def apply_layout_preset(self, positions: Dict[str, ThumbnailPosition]):
        """
        Apply a layout preset to current thumbnails.

        Args:
            positions: Dict mapping window_id to ThumbnailPosition
        """
        for window_id, position in positions.items():
            if window_id in self.positions:
                self.positions[window_id] = position

        self.logger.info(f"Applied layout preset with {len(positions)} positions")

    def calculate_grid_positions(self,
                                  window_ids: List[str],
                                  columns: int = 3,
                                  start_x: int = None,
                                  start_y: int = None
                                  ) -> Dict[str, ThumbnailPosition]:
        """
        Calculate grid positions for thumbnails.

        Args:
            window_ids: List of window IDs to position
            columns: Number of columns in grid
            start_x: Starting X position (default: MARGIN)
            start_y: Starting Y position (default: MARGIN)

        Returns:
            Dict mapping window_id to ThumbnailPosition
        """
        if start_x is None:
            start_x = self.MARGIN
        if start_y is None:
            start_y = self.MARGIN

        positions = {}

        for i, window_id in enumerate(window_ids):
            row = i // columns
            col = i % columns

            x = start_x + col * (self.DEFAULT_WIDTH + self.SPACING)
            y = start_y + row * (self.DEFAULT_HEIGHT + self.SPACING)

            positions[window_id] = ThumbnailPosition(
                x=x,
                y=y,
                width=self.DEFAULT_WIDTH,
                height=self.DEFAULT_HEIGHT
            )

        return positions

    def clear(self):
        """Clear all position tracking"""
        self.positions.clear()
        self.logger.debug("All positions cleared")
