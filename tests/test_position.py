"""
Unit tests for the Position module.

Tests cover:
- ThumbnailPosition dataclass
- PositionManager initialization
- Position CRUD operations
- Locking functionality
- Grid snapping
- Next position calculation
- Grid layout calculation
"""
from unittest.mock import patch

import pytest
from PySide6.QtCore import QRect

from eve_overview_pro.core.position import (
    PositionManager,
    ThumbnailPosition,
)


class TestThumbnailPosition:
    """Tests for ThumbnailPosition dataclass"""

    def test_create_position(self):
        """ThumbnailPosition can be created"""
        pos = ThumbnailPosition(x=100, y=200, width=400, height=300)
        assert pos.x == 100
        assert pos.y == 200
        assert pos.width == 400
        assert pos.height == 300

    def test_to_rect(self):
        """ThumbnailPosition can convert to QRect"""
        pos = ThumbnailPosition(x=50, y=75, width=200, height=150)
        rect = pos.to_rect()

        assert isinstance(rect, QRect)
        assert rect.x() == 50
        assert rect.y() == 75
        assert rect.width() == 200
        assert rect.height() == 150

    def test_from_rect(self):
        """ThumbnailPosition can be created from QRect"""
        rect = QRect(10, 20, 300, 250)
        pos = ThumbnailPosition.from_rect(rect)

        assert pos.x == 10
        assert pos.y == 20
        assert pos.width == 300
        assert pos.height == 250

    def test_roundtrip_rect(self):
        """ThumbnailPosition survives QRect roundtrip"""
        original = ThumbnailPosition(x=123, y=456, width=789, height=321)
        rect = original.to_rect()
        restored = ThumbnailPosition.from_rect(rect)

        assert restored.x == original.x
        assert restored.y == original.y
        assert restored.width == original.width
        assert restored.height == original.height


class TestPositionManagerInit:
    """Tests for PositionManager initialization"""

    def test_default_values(self):
        """PositionManager has correct default values"""
        manager = PositionManager()

        assert manager.DEFAULT_WIDTH == 280
        assert manager.DEFAULT_HEIGHT == 200
        assert manager.MARGIN == 20
        assert manager.SPACING == 10
        assert manager.GRID_SIZE == 10

    def test_initial_state(self):
        """PositionManager starts with correct state"""
        manager = PositionManager()

        assert manager.positions == {}
        assert manager.snap_to_grid is True
        assert manager.locked is False


class TestPositionCRUD:
    """Tests for position CRUD operations"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test"""
        return PositionManager()

    def test_register_position(self, manager):
        """Can register a position"""
        pos = ThumbnailPosition(100, 200, 400, 300)
        manager.register_position("window1", pos)

        assert "window1" in manager.positions
        assert manager.positions["window1"] == pos

    def test_register_multiple_positions(self, manager):
        """Can register multiple positions"""
        pos1 = ThumbnailPosition(100, 100, 280, 200)
        pos2 = ThumbnailPosition(400, 100, 280, 200)

        manager.register_position("win1", pos1)
        manager.register_position("win2", pos2)

        assert len(manager.positions) == 2
        assert manager.positions["win1"] == pos1
        assert manager.positions["win2"] == pos2

    def test_update_position(self, manager):
        """Can update a position"""
        pos1 = ThumbnailPosition(100, 100, 280, 200)
        pos2 = ThumbnailPosition(200, 200, 280, 200)

        manager.register_position("win", pos1)
        result = manager.update_position("win", pos2)

        assert result is True
        assert manager.positions["win"] == pos2

    def test_update_position_when_locked(self, manager):
        """Update blocked when locked"""
        pos1 = ThumbnailPosition(100, 100, 280, 200)
        pos2 = ThumbnailPosition(200, 200, 280, 200)

        manager.register_position("win", pos1)
        manager.set_locked(True)
        result = manager.update_position("win", pos2)

        assert result is False
        assert manager.positions["win"] == pos1  # Unchanged

    def test_remove_position(self, manager):
        """Can remove a position"""
        pos = ThumbnailPosition(100, 100, 280, 200)
        manager.register_position("win", pos)
        manager.remove_position("win")

        assert "win" not in manager.positions

    def test_remove_nonexistent_position(self, manager):
        """Removing nonexistent position doesn't error"""
        manager.remove_position("nonexistent")  # Should not raise

    def test_get_all_positions(self, manager):
        """Can get all positions as copy"""
        pos1 = ThumbnailPosition(100, 100, 280, 200)
        pos2 = ThumbnailPosition(400, 100, 280, 200)

        manager.register_position("win1", pos1)
        manager.register_position("win2", pos2)

        all_pos = manager.get_all_positions()

        assert len(all_pos) == 2
        # Verify it's a copy
        all_pos["new"] = ThumbnailPosition(0, 0, 100, 100)
        assert "new" not in manager.positions

    def test_clear(self, manager):
        """Can clear all positions"""
        manager.register_position("win1", ThumbnailPosition(0, 0, 100, 100))
        manager.register_position("win2", ThumbnailPosition(100, 0, 100, 100))

        manager.clear()

        assert len(manager.positions) == 0


class TestLocking:
    """Tests for position locking"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        return PositionManager()

    def test_default_unlocked(self, manager):
        """Manager starts unlocked"""
        assert manager.is_locked() is False

    def test_set_locked(self, manager):
        """Can lock positions"""
        manager.set_locked(True)
        assert manager.is_locked() is True

    def test_set_unlocked(self, manager):
        """Can unlock positions"""
        manager.set_locked(True)
        manager.set_locked(False)
        assert manager.is_locked() is False


class TestGridSnapping:
    """Tests for grid snapping functionality"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        return PositionManager()

    def test_default_snap_enabled(self, manager):
        """Snap to grid enabled by default"""
        assert manager.snap_to_grid is True

    def test_disable_snap(self, manager):
        """Can disable grid snapping"""
        manager.set_snap_to_grid(False)
        assert manager.snap_to_grid is False

    def test_snap_rounds_to_grid(self, manager):
        """Snapping rounds to grid size"""
        pos = ThumbnailPosition(23, 47, 280, 200)
        snapped = manager._snap_position(pos)

        # Should round to nearest 10
        assert snapped.x == 20
        assert snapped.y == 50

    def test_snap_with_exact_grid(self, manager):
        """Snapping preserves exact grid positions"""
        pos = ThumbnailPosition(100, 200, 280, 200)
        snapped = manager._snap_position(pos)

        assert snapped.x == 100
        assert snapped.y == 200

    def test_snap_disabled_preserves_position(self, manager):
        """When disabled, snapping preserves original position"""
        manager.set_snap_to_grid(False)
        pos = ThumbnailPosition(23, 47, 280, 200)
        result = manager._snap_position(pos)

        assert result.x == 23
        assert result.y == 47


class TestGetNextPosition:
    """Tests for next position calculation"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        m = PositionManager()
        m.snap_to_grid = False  # Disable for predictable tests
        return m

    @pytest.fixture
    def mock_screen(self):
        """Mock screen geometry"""
        with patch.object(PositionManager, '_get_primary_screen') as mock:
            mock.return_value = QRect(0, 0, 1920, 1080)
            yield mock

    def test_first_position_at_margin(self, manager, mock_screen):
        """First thumbnail at margin position"""
        pos = manager.get_next_position("win1")

        assert pos.x == PositionManager.MARGIN
        assert pos.y == PositionManager.MARGIN

    def test_uses_preset_if_available(self, manager, mock_screen):
        """Uses preset position when provided"""
        preset = {"win1": ThumbnailPosition(500, 500, 300, 200)}
        pos = manager.get_next_position("win1", preset)

        assert pos.x == 500
        assert pos.y == 500

    def test_places_right_of_rightmost(self, manager, mock_screen):
        """Places new window right of rightmost existing"""
        existing = ThumbnailPosition(100, 100, 280, 200)
        manager.register_position("win1", existing)

        pos = manager.get_next_position("win2")

        expected_x = existing.x + existing.width + PositionManager.SPACING
        assert pos.x == expected_x
        assert pos.y == existing.y

    def test_wraps_to_new_row(self, manager, mock_screen):
        """Wraps to new row when right edge reached"""
        # Place window near right edge
        far_right = ThumbnailPosition(1800, 100, 280, 200)
        manager.register_position("win1", far_right)

        pos = manager.get_next_position("win2")

        # Should be on new row
        assert pos.x == PositionManager.MARGIN
        assert pos.y > far_right.y

    def test_default_dimensions(self, manager, mock_screen):
        """New positions use default dimensions"""
        pos = manager.get_next_position("win1")

        assert pos.width == PositionManager.DEFAULT_WIDTH
        assert pos.height == PositionManager.DEFAULT_HEIGHT


class TestRightmostBottommost:
    """Tests for finding extreme positions"""

    @pytest.fixture
    def manager(self):
        """Create manager with some positions"""
        m = PositionManager()
        m.register_position("left", ThumbnailPosition(50, 100, 200, 150))
        m.register_position("right", ThumbnailPosition(500, 100, 200, 150))
        m.register_position("bottom", ThumbnailPosition(200, 400, 200, 150))
        return m

    def test_get_rightmost(self, manager):
        """Finds rightmost position correctly"""
        rightmost = manager._get_rightmost()

        assert rightmost is not None
        assert rightmost.x == 500  # "right" position

    def test_get_bottommost(self, manager):
        """Finds bottommost position correctly"""
        bottommost = manager._get_bottommost()

        assert bottommost is not None
        assert bottommost.y == 400  # "bottom" position

    def test_rightmost_empty(self):
        """Returns None when no positions"""
        manager = PositionManager()
        assert manager._get_rightmost() is None

    def test_bottommost_empty(self):
        """Returns None when no positions"""
        manager = PositionManager()
        assert manager._get_bottommost() is None


class TestCalculateGridPositions:
    """Tests for grid position calculation"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        return PositionManager()

    def test_empty_list(self, manager):
        """Empty window list returns empty dict"""
        result = manager.calculate_grid_positions([])
        assert result == {}

    def test_single_window(self, manager):
        """Single window positioned at start"""
        result = manager.calculate_grid_positions(["win1"])

        assert len(result) == 1
        assert "win1" in result
        assert result["win1"].x == PositionManager.MARGIN
        assert result["win1"].y == PositionManager.MARGIN

    def test_three_columns_default(self, manager):
        """Default 3 columns layout"""
        windows = ["w1", "w2", "w3", "w4"]
        result = manager.calculate_grid_positions(windows)

        # w1, w2, w3 on row 0
        # w4 on row 1
        assert result["w1"].y == result["w2"].y == result["w3"].y
        assert result["w4"].y > result["w1"].y

    def test_custom_columns(self, manager):
        """Custom column count"""
        windows = ["w1", "w2", "w3", "w4"]
        result = manager.calculate_grid_positions(windows, columns=2)

        # w1, w2 on row 0
        # w3, w4 on row 1
        assert result["w1"].y == result["w2"].y
        assert result["w3"].y == result["w4"].y
        assert result["w3"].y > result["w1"].y

    def test_custom_start_position(self, manager):
        """Custom starting position"""
        windows = ["w1"]
        result = manager.calculate_grid_positions(windows, start_x=100, start_y=200)

        assert result["w1"].x == 100
        assert result["w1"].y == 200

    def test_spacing_between_windows(self, manager):
        """Windows have correct spacing"""
        windows = ["w1", "w2"]
        result = manager.calculate_grid_positions(windows, columns=2)

        expected_x2 = (PositionManager.MARGIN +
                       PositionManager.DEFAULT_WIDTH +
                       PositionManager.SPACING)
        assert result["w2"].x == expected_x2


class TestApplyLayoutPreset:
    """Tests for applying layout presets"""

    @pytest.fixture
    def manager(self):
        """Create manager with existing positions"""
        m = PositionManager()
        m.register_position("win1", ThumbnailPosition(0, 0, 100, 100))
        m.register_position("win2", ThumbnailPosition(100, 0, 100, 100))
        return m

    def test_applies_to_existing(self, manager):
        """Preset applied to existing windows"""
        preset = {
            "win1": ThumbnailPosition(500, 500, 200, 200),
            "win2": ThumbnailPosition(700, 500, 200, 200),
        }

        manager.apply_layout_preset(preset)

        assert manager.positions["win1"].x == 500
        assert manager.positions["win2"].x == 700

    def test_ignores_unknown_windows(self, manager):
        """Preset for unknown windows ignored"""
        preset = {
            "unknown": ThumbnailPosition(999, 999, 100, 100),
        }

        manager.apply_layout_preset(preset)

        assert "unknown" not in manager.positions
        assert len(manager.positions) == 2  # Original two still there

    def test_partial_preset(self, manager):
        """Partial preset only updates matching windows"""
        preset = {
            "win1": ThumbnailPosition(500, 500, 200, 200),
        }

        original_win2 = manager.positions["win2"]
        manager.apply_layout_preset(preset)

        assert manager.positions["win1"].x == 500
        assert manager.positions["win2"] == original_win2
