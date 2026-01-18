"""
Unit tests for the Layouts Tab module
Tests ScreenGeometry, DraggableTile, ArrangementGrid, GridApplier, LayoutsTab
"""

from unittest.mock import MagicMock, patch


# Test ScreenGeometry dataclass
class TestScreenGeometry:
    """Tests for ScreenGeometry dataclass"""

    def test_create_screen_geometry(self):
        """Test creating ScreenGeometry"""
        from argus_overview.ui.layouts_tab import ScreenGeometry

        screen = ScreenGeometry(0, 0, 1920, 1080)

        assert screen.x == 0
        assert screen.y == 0
        assert screen.width == 1920
        assert screen.height == 1080
        assert screen.is_primary is False

    def test_create_primary_screen(self):
        """Test creating primary screen"""
        from argus_overview.ui.layouts_tab import ScreenGeometry

        screen = ScreenGeometry(0, 0, 2560, 1440, is_primary=True)

        assert screen.is_primary is True

    def test_multi_monitor_offset(self):
        """Test screen with offset for multi-monitor"""
        from argus_overview.ui.layouts_tab import ScreenGeometry

        screen = ScreenGeometry(1920, 0, 1920, 1080)

        assert screen.x == 1920
        assert screen.y == 0


# Test helper functions
class TestHelperFunctions:
    """Tests for module helper functions"""

    def test_get_all_patterns(self):
        """Test get_all_patterns returns expected patterns"""
        from argus_overview.ui.layouts_tab import get_all_patterns

        patterns = get_all_patterns()

        assert "2x2 Grid" in patterns
        assert "3x1 Row" in patterns
        assert "1x3 Column" in patterns
        assert "4x1 Row" in patterns
        assert "Main + Sides" in patterns
        assert "Cascade" in patterns
        assert "Stacked (All Same Position)" in patterns
        assert "Custom" in patterns

    def test_pattern_display_to_enum(self):
        """Test pattern_display_to_enum conversion"""
        from argus_overview.ui.layouts_tab import GridPattern, pattern_display_to_enum

        assert pattern_display_to_enum("2x2 Grid") == GridPattern.GRID_2X2
        assert pattern_display_to_enum("3x1 Row") == GridPattern.GRID_3X1
        assert pattern_display_to_enum("Cascade") == GridPattern.CASCADE

    def test_pattern_display_to_enum_unknown(self):
        """Test pattern_display_to_enum with unknown pattern"""
        from argus_overview.ui.layouts_tab import GridPattern, pattern_display_to_enum

        result = pattern_display_to_enum("Unknown Pattern")

        assert result == GridPattern.CUSTOM


# Test DraggableTile
class TestDraggableTile:
    """Tests for DraggableTile widget"""

    @patch("argus_overview.ui.layouts_tab.QFrame.__init__")
    @patch("argus_overview.ui.layouts_tab.QVBoxLayout")
    @patch("argus_overview.ui.layouts_tab.QLabel")
    @patch("argus_overview.ui.layouts_tab.QColor")
    def test_init(self, mock_color, mock_label, mock_layout, mock_frame):
        """Test DraggableTile initialization"""
        mock_frame.return_value = None
        mock_color_instance = MagicMock()
        mock_color_instance.name.return_value = "#ff0000"
        mock_color_instance.darker.return_value = mock_color_instance

        from argus_overview.ui.layouts_tab import DraggableTile

        with patch.object(DraggableTile, "setFixedSize"):
            with patch.object(DraggableTile, "setFrameStyle"):
                with patch.object(DraggableTile, "setLineWidth"):
                    with patch.object(DraggableTile, "setStyleSheet"):
                        with patch.object(DraggableTile, "setLayout"):
                            tile = DraggableTile("TestChar", mock_color_instance)

                            assert tile.char_name == "TestChar"
                            assert tile.grid_row == 0
                            assert tile.grid_col == 0
                            assert tile.is_stacked is False

    @patch("argus_overview.ui.layouts_tab.QFrame.__init__")
    @patch("argus_overview.ui.layouts_tab.QVBoxLayout")
    @patch("argus_overview.ui.layouts_tab.QLabel")
    @patch("argus_overview.ui.layouts_tab.QColor")
    def test_set_position(self, mock_color, mock_label, mock_layout, mock_frame):
        """Test set_position method"""
        mock_frame.return_value = None
        mock_color_instance = MagicMock()
        mock_color_instance.name.return_value = "#ff0000"
        mock_color_instance.darker.return_value = mock_color_instance

        from argus_overview.ui.layouts_tab import DraggableTile

        with patch.object(DraggableTile, "setFixedSize"):
            with patch.object(DraggableTile, "setFrameStyle"):
                with patch.object(DraggableTile, "setLineWidth"):
                    with patch.object(DraggableTile, "setStyleSheet"):
                        with patch.object(DraggableTile, "setLayout"):
                            tile = DraggableTile("TestChar", mock_color_instance)

                            tile.set_position(2, 3)

                            assert tile.grid_row == 2
                            assert tile.grid_col == 3

    @patch("argus_overview.ui.layouts_tab.QFrame.__init__")
    @patch("argus_overview.ui.layouts_tab.QVBoxLayout")
    @patch("argus_overview.ui.layouts_tab.QLabel")
    @patch("argus_overview.ui.layouts_tab.QColor")
    def test_set_stacked(self, mock_color, mock_label, mock_layout, mock_frame):
        """Test set_stacked method"""
        mock_frame.return_value = None
        mock_color_instance = MagicMock()
        mock_color_instance.name.return_value = "#ff0000"
        mock_color_instance.darker.return_value = mock_color_instance

        from argus_overview.ui.layouts_tab import DraggableTile

        with patch.object(DraggableTile, "setFixedSize"):
            with patch.object(DraggableTile, "setFrameStyle"):
                with patch.object(DraggableTile, "setLineWidth"):
                    with patch.object(DraggableTile, "setStyleSheet"):
                        with patch.object(DraggableTile, "setLayout"):
                            tile = DraggableTile("TestChar", mock_color_instance)

                            tile.set_stacked(True)

                            assert tile.is_stacked is True

    def test_signal_exists(self):
        """Test that tile_moved signal exists"""
        from argus_overview.ui.layouts_tab import DraggableTile

        assert hasattr(DraggableTile, "tile_moved")


# Test ArrangementGrid
class TestArrangementGrid:
    """Tests for ArrangementGrid widget"""

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_init(self, mock_frame, mock_grid, mock_widget):
        """Test ArrangementGrid initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            grid = ArrangementGrid()

            assert grid.tiles == {}
            assert grid.grid_rows == 3
            assert grid.grid_cols == 4

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_clear_tiles(self, mock_frame, mock_grid, mock_widget):
        """Test clear_tiles method"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            grid = ArrangementGrid()
            grid.tiles = {"Char1": MagicMock(), "Char2": MagicMock()}

            grid.clear_tiles()

            assert grid.tiles == {}

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_get_arrangement_empty(self, mock_frame, mock_grid, mock_widget):
        """Test get_arrangement with no tiles"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            grid = ArrangementGrid()

            result = grid.get_arrangement()

            assert result == {}

    def test_signal_exists(self):
        """Test that arrangement_changed signal exists"""
        from argus_overview.ui.layouts_tab import ArrangementGrid

        assert hasattr(ArrangementGrid, "arrangement_changed")


# Test GridApplier
class TestGridApplier:
    """Tests for GridApplier class"""

    def test_init(self):
        """Test GridApplier initialization"""
        from argus_overview.ui.layouts_tab import GridApplier

        mock_layout_manager = MagicMock()

        applier = GridApplier(mock_layout_manager)

        assert applier.layout_manager is mock_layout_manager

    @patch("argus_overview.utils.screen.subprocess.run")
    def test_get_screen_geometry_success(self, mock_subprocess):
        """Test get_screen_geometry with successful xrandr"""
        from argus_overview.ui.layouts_tab import GridApplier

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "HDMI-1 connected primary 1920x1080+0+0"
        mock_subprocess.return_value = mock_result

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        result = applier.get_screen_geometry()

        assert result is not None
        assert result.width == 1920
        assert result.height == 1080
        assert result.is_primary is True

    @patch("argus_overview.utils.screen.subprocess.run")
    def test_get_screen_geometry_failure(self, mock_subprocess):
        """Test get_screen_geometry with xrandr failure"""
        from argus_overview.ui.layouts_tab import GridApplier

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        result = applier.get_screen_geometry()

        # Should return default geometry on failure
        assert result is not None
        assert result.width == 1920

    @patch("argus_overview.utils.screen.subprocess.run")
    def test_get_screen_geometry_exception(self, mock_subprocess):
        """Test get_screen_geometry with exception"""
        from argus_overview.ui.layouts_tab import GridApplier

        mock_subprocess.side_effect = Exception("xrandr not found")

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        result = applier.get_screen_geometry()

        # Should return default geometry on exception
        assert result is not None
        assert result.width == 1920

    @patch("argus_overview.ui.layouts_tab.subprocess.run")
    def test_apply_arrangement_stacked(self, mock_subprocess):
        """Test apply_arrangement with stacked mode"""
        from argus_overview.ui.layouts_tab import GridApplier, ScreenGeometry

        mock_subprocess.return_value = MagicMock()

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        screen = ScreenGeometry(0, 0, 1920, 1080)
        arrangement = {"Char1": (0, 0), "Char2": (0, 1)}
        window_map = {"Char1": "0x12345", "Char2": "0x67890"}

        result = applier.apply_arrangement(
            arrangement=arrangement,
            window_map=window_map,
            screen=screen,
            grid_rows=2,
            grid_cols=2,
            stacked=True,
        )

        assert result is True
        # Should have called xdotool for each window
        assert mock_subprocess.call_count >= 2

    @patch("argus_overview.ui.layouts_tab.subprocess.run")
    def test_apply_arrangement_grid(self, mock_subprocess):
        """Test apply_arrangement with grid mode"""
        from argus_overview.ui.layouts_tab import GridApplier, ScreenGeometry

        mock_subprocess.return_value = MagicMock()

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        screen = ScreenGeometry(0, 0, 1920, 1080)
        arrangement = {"Char1": (0, 0), "Char2": (0, 1)}
        window_map = {"Char1": "0x12345", "Char2": "0x67890"}

        result = applier.apply_arrangement(
            arrangement=arrangement,
            window_map=window_map,
            screen=screen,
            grid_rows=2,
            grid_cols=2,
            stacked=False,
        )

        assert result is True

    @patch("argus_overview.ui.layouts_tab.subprocess.run")
    def test_apply_arrangement_exception(self, mock_subprocess):
        """Test apply_arrangement handles exceptions"""
        from argus_overview.ui.layouts_tab import GridApplier, ScreenGeometry

        mock_subprocess.side_effect = Exception("xdotool error")

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        screen = ScreenGeometry(0, 0, 1920, 1080)
        arrangement = {"Char1": (0, 0)}
        window_map = {"Char1": "0x12345"}

        result = applier.apply_arrangement(
            arrangement=arrangement, window_map=window_map, screen=screen, grid_rows=2, grid_cols=2
        )

        assert result is False


# Test LayoutsTab
class TestLayoutsTab:
    """Tests for LayoutsTab widget"""

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test LayoutsTab initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                assert tab.layout_manager is mock_layout_manager
                assert tab.main_tab is mock_main_tab

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    def test_load_groups(self, mock_widget):
        """Test _load_groups creates Default if missing"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {"TestGroup": ["A", "B"]}

        with patch.object(LayoutsTab, "_setup_ui"):
            tab = LayoutsTab(
                mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
            )

            assert "Default" in tab.cycling_groups
            assert "TestGroup" in tab.cycling_groups

    def test_signal_exists(self):
        """Test that layout_applied signal exists"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        assert hasattr(LayoutsTab, "layout_applied")


# Test pattern grid calculations
class TestPatternCalculations:
    """Tests for pattern-based grid calculations"""

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_2x2(self, mock_frame, mock_grid_layout, mock_widget):
        """Test auto_arrange_grid with 2x2 pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                # Add mock tiles
                mock_tile1 = MagicMock()
                mock_tile2 = MagicMock()
                mock_tile3 = MagicMock()
                mock_tile4 = MagicMock()

                grid.tiles = {
                    "Char1": mock_tile1,
                    "Char2": mock_tile2,
                    "Char3": mock_tile3,
                    "Char4": mock_tile4,
                }

                grid.auto_arrange_grid("2x2 Grid")

                # Each tile should have set_position called
                mock_tile1.set_position.assert_called()
                mock_tile2.set_position.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_stacked(self, mock_frame, mock_grid_layout, mock_widget):
        """Test auto_arrange_grid with stacked pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                mock_tile1 = MagicMock()
                mock_tile2 = MagicMock()

                grid.tiles = {"Char1": mock_tile1, "Char2": mock_tile2}

                grid.auto_arrange_grid("Stacked (All Same Position)")

                # All tiles should be marked as stacked
                mock_tile1.set_stacked.assert_called_with(True)
                mock_tile2.set_stacked.assert_called_with(True)


# Test ArrangementGrid set_grid_size
class TestArrangementGridSetGridSize:
    """Tests for ArrangementGrid.set_grid_size method"""

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_set_grid_size(self, mock_frame, mock_grid, mock_widget):
        """Test set_grid_size resizes grid"""
        mock_widget.return_value = None
        mock_layout = MagicMock()
        mock_layout.count.return_value = 0
        mock_grid.return_value = mock_layout

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            grid = ArrangementGrid()
            grid.grid_layout = mock_layout

            grid.set_grid_size(4, 5)

            assert grid.grid_rows == 4
            assert grid.grid_cols == 5

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_set_grid_size_clears_existing(self, mock_frame, mock_grid, mock_widget):
        """Test set_grid_size clears existing cells"""
        mock_widget.return_value = None
        mock_layout = MagicMock()
        mock_layout.count.side_effect = [2, 1, 0]  # Simulate clearing items
        mock_item = MagicMock()
        mock_item.widget.return_value = MagicMock()
        mock_layout.takeAt.return_value = mock_item
        mock_grid.return_value = mock_layout

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            grid = ArrangementGrid()
            grid.grid_layout = mock_layout

            grid.set_grid_size(2, 2)

            # Should have called takeAt to remove items
            assert mock_layout.takeAt.called


# Test ArrangementGrid add_character
class TestArrangementGridAddCharacter:
    """Tests for ArrangementGrid.add_character method"""

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    @patch("argus_overview.ui.layouts_tab.DraggableTile")
    def test_add_character_new(self, mock_tile_class, mock_frame, mock_grid, mock_widget):
        """Test add_character adds new character"""
        mock_widget.return_value = None
        mock_tile = MagicMock()
        mock_tile_class.return_value = mock_tile

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            grid = ArrangementGrid()
            grid.grid_layout = MagicMock()

            grid.add_character("TestPilot", 1, 2)

            assert "TestPilot" in grid.tiles
            mock_tile.set_position.assert_called_with(1, 2)

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_add_character_duplicate_ignored(self, mock_frame, mock_grid, mock_widget):
        """Test add_character ignores duplicate"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            grid = ArrangementGrid()
            grid.tiles = {"TestPilot": MagicMock()}  # Already exists

            with patch("argus_overview.ui.layouts_tab.DraggableTile") as mock_tile:
                grid.add_character("TestPilot", 0, 0)

                # Should NOT create new tile
                mock_tile.assert_not_called()


# Test auto_arrange_grid more patterns
class TestAutoArrangeMorePatterns:
    """Tests for auto_arrange_grid with various patterns"""

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_3x1_row(self, mock_frame, mock_grid, mock_widget):
        """Test auto_arrange with 3x1 row pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                tiles = [MagicMock() for _ in range(3)]
                grid.tiles = {f"Char{i}": tiles[i] for i in range(3)}

                grid.auto_arrange_grid("3x1 Row")

                for tile in tiles:
                    tile.set_position.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_1x3_column(self, mock_frame, mock_grid, mock_widget):
        """Test auto_arrange with 1x3 column pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                tiles = [MagicMock() for _ in range(3)]
                grid.tiles = {f"Char{i}": tiles[i] for i in range(3)}

                grid.auto_arrange_grid("1x3 Column")

                for tile in tiles:
                    tile.set_position.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_4x1_row(self, mock_frame, mock_grid, mock_widget):
        """Test auto_arrange with 4x1 row pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                tiles = [MagicMock() for _ in range(4)]
                grid.tiles = {f"Char{i}": tiles[i] for i in range(4)}

                grid.auto_arrange_grid("4x1 Row")

                for tile in tiles:
                    tile.set_position.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_2x3_grid(self, mock_frame, mock_grid, mock_widget):
        """Test auto_arrange with 2x3 grid pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                tiles = [MagicMock() for _ in range(6)]
                grid.tiles = {f"Char{i}": tiles[i] for i in range(6)}

                grid.auto_arrange_grid("2x3 Grid")

                for tile in tiles:
                    tile.set_position.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_3x2_grid(self, mock_frame, mock_grid, mock_widget):
        """Test auto_arrange with 3x2 grid pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                tiles = [MagicMock() for _ in range(6)]
                grid.tiles = {f"Char{i}": tiles[i] for i in range(6)}

                grid.auto_arrange_grid("3x2 Grid")

                for tile in tiles:
                    tile.set_position.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_main_plus_sides(self, mock_frame, mock_grid, mock_widget):
        """Test auto_arrange with Main + Sides pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                tiles = [MagicMock() for _ in range(3)]
                grid.tiles = {f"Char{i}": tiles[i] for i in range(3)}

                grid.auto_arrange_grid("Main + Sides")

                for tile in tiles:
                    tile.set_position.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_cascade(self, mock_frame, mock_grid, mock_widget):
        """Test auto_arrange with Cascade pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                tiles = [MagicMock() for _ in range(3)]
                grid.tiles = {f"Char{i}": tiles[i] for i in range(3)}

                grid.auto_arrange_grid("Cascade")

                for tile in tiles:
                    tile.set_position.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_custom(self, mock_frame, mock_grid, mock_widget):
        """Test auto_arrange with Custom pattern (falls through to default sequential fill)"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()

                tiles = [MagicMock() for _ in range(2)]
                grid.tiles = {f"Char{i}": tiles[i] for i in range(2)}

                grid.auto_arrange_grid("Custom")

                # Custom pattern falls through to default sequential fill
                for tile in tiles:
                    tile.set_position.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_auto_arrange_empty_tiles(self, mock_frame, mock_grid, mock_widget):
        """Test auto_arrange with no tiles"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()
                grid.tiles = {}

                # Should not raise
                grid.auto_arrange_grid("2x2 Grid")


# Test LayoutsTab methods
class TestLayoutsTabMethods:
    """Tests for LayoutsTab methods"""

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    def test_refresh_groups(self, mock_widget):
        """Test _refresh_groups reloads groups"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {"Team1": ["A", "B"]}

        with patch.object(LayoutsTab, "_setup_ui"):
            # Don't patch _load_groups - let it call settings_manager.get
            tab = LayoutsTab(
                mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
            )

            tab.cycling_groups = {"Old": []}
            tab.group_combo = MagicMock()
            tab.group_combo.count.return_value = 0
            tab.logger = MagicMock()

            tab._refresh_groups()

            # Should have reloaded groups via _load_groups
            mock_settings_manager.get.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    def test_on_group_selected_all_active(self, mock_widget):
        """Test _on_group_selected with All Active Windows"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_frame = MagicMock()
        mock_frame.character_name = "TestPilot"
        mock_main_tab.window_manager = MagicMock()
        mock_main_tab.window_manager.preview_frames = {"0x123": mock_frame}

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.arrangement_grid = MagicMock()
                tab.info_label = MagicMock()
                tab.group_combo = MagicMock()
                tab.group_combo.currentText.return_value = "All Active Windows"
                tab.pattern_combo = MagicMock()
                tab.pattern_combo.currentText.return_value = "Custom"

                tab._on_group_selected()

                tab.arrangement_grid.clear_tiles.assert_called()
                tab.arrangement_grid.add_character.assert_called_with("TestPilot")

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    def test_on_group_selected_specific_group(self, mock_widget):
        """Test _on_group_selected with specific group"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {"PvP": ["Pilot1", "Pilot2"]}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.cycling_groups = {"PvP": ["Pilot1", "Pilot2"]}
                tab.arrangement_grid = MagicMock()
                tab.arrangement_grid.grid_cols = 4
                tab.info_label = MagicMock()
                tab.group_combo = MagicMock()
                tab.group_combo.currentText.return_value = "PvP"
                tab.pattern_combo = MagicMock()
                tab.pattern_combo.currentText.return_value = "Custom"

                tab._on_group_selected()

                assert tab.arrangement_grid.add_character.call_count == 2

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    def test_on_pattern_changed_stacked(self, mock_widget):
        """Test _on_pattern_changed with stacked pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.pattern_combo = MagicMock()
                tab.pattern_combo.currentText.return_value = "Stacked (All Same Position)"
                tab.stack_checkbox = MagicMock()
                tab.arrangement_grid = MagicMock()

                tab._on_pattern_changed()

                tab.stack_checkbox.setChecked.assert_called_with(True)

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    def test_on_pattern_changed_non_stacked(self, mock_widget):
        """Test _on_pattern_changed with non-stacked pattern"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.pattern_combo = MagicMock()
                tab.pattern_combo.currentText.return_value = "2x2 Grid"
                tab.stack_checkbox = MagicMock()
                tab.arrangement_grid = MagicMock()

                tab._on_pattern_changed()

                tab.stack_checkbox.setChecked.assert_called_with(False)

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    def test_update_grid_size(self, mock_widget):
        """Test _update_grid_size method"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.rows_spin = MagicMock()
                tab.rows_spin.value.return_value = 3
                tab.cols_spin = MagicMock()
                tab.cols_spin.value.return_value = 4
                tab.arrangement_grid = MagicMock()

                tab._update_grid_size()

                tab.arrangement_grid.set_grid_size.assert_called_with(3, 4)

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    def test_auto_arrange(self, mock_widget):
        """Test _auto_arrange method"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.pattern_combo = MagicMock()
                tab.pattern_combo.currentText.return_value = "2x2 Grid"
                tab.arrangement_grid = MagicMock()

                tab._auto_arrange()

                tab.arrangement_grid.auto_arrange_grid.assert_called_with("2x2 Grid")


# Test GridApplier more methods
class TestGridApplierMore:
    """More tests for GridApplier"""

    @patch("argus_overview.utils.screen.subprocess.run")
    def test_get_screen_geometry_with_monitor(self, mock_subprocess):
        """Test get_screen_geometry with specific monitor"""
        from argus_overview.ui.layouts_tab import GridApplier

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "HDMI-1 connected primary 1920x1080+0+0\nDP-1 connected 2560x1440+1920+0"
        )
        mock_subprocess.return_value = mock_result

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        result = applier.get_screen_geometry(monitor=1)

        assert result is not None

    @patch("argus_overview.ui.layouts_tab.subprocess.run")
    def test_apply_arrangement_empty(self, mock_subprocess):
        """Test apply_arrangement with empty arrangement"""
        from argus_overview.ui.layouts_tab import GridApplier, ScreenGeometry

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        screen = ScreenGeometry(0, 0, 1920, 1080)
        result = applier.apply_arrangement(
            arrangement={}, window_map={}, screen=screen, grid_rows=2, grid_cols=2
        )

        assert result is True  # No windows = success


# Test LayoutsTab apply_to_active_windows
class TestLayoutsTabApplyToActiveWindows:
    """Tests for LayoutsTab._apply_to_active_windows"""

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QMessageBox")
    def test_apply_no_main_tab(self, mock_msgbox, mock_widget):
        """Test _apply_to_active_windows with no main_tab"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        del mock_main_tab.window_manager  # No window_manager
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab._apply_to_active_windows()

                mock_msgbox.warning.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QMessageBox")
    def test_apply_no_arrangement(self, mock_msgbox, mock_widget):
        """Test _apply_to_active_windows with no arrangement"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_main_tab.window_manager = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.arrangement_grid = MagicMock()
                tab.arrangement_grid.get_arrangement.return_value = {}

                tab._apply_to_active_windows()

                mock_msgbox.warning.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QMessageBox")
    def test_apply_no_matching_windows(self, mock_msgbox, mock_widget):
        """Test _apply_to_active_windows with no matching windows"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_main_tab.window_manager = MagicMock()
        mock_main_tab.window_manager.preview_frames = {}  # No windows
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.arrangement_grid = MagicMock()
                tab.arrangement_grid.get_arrangement.return_value = {"Pilot1": (0, 0)}

                tab._apply_to_active_windows()

                mock_msgbox.warning.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QMessageBox")
    def test_apply_no_screen_geometry(self, mock_msgbox, mock_widget):
        """Test _apply_to_active_windows with no screen geometry"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_frame = MagicMock()
        mock_frame.character_name = "Pilot1"
        mock_main_tab.window_manager = MagicMock()
        mock_main_tab.window_manager.preview_frames = {"0x123": mock_frame}
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.arrangement_grid = MagicMock()
                tab.arrangement_grid.get_arrangement.return_value = {"Pilot1": (0, 0)}
                tab.monitor_spin = MagicMock()
                tab.monitor_spin.value.return_value = 0
                tab.grid_applier = MagicMock()
                tab.grid_applier.get_screen_geometry.return_value = None

                tab._apply_to_active_windows()

                mock_msgbox.warning.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QMessageBox")
    def test_apply_success(self, mock_msgbox, mock_widget):
        """Test _apply_to_active_windows success"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab, ScreenGeometry

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_frame = MagicMock()
        mock_frame.character_name = "Pilot1"
        mock_main_tab.window_manager = MagicMock()
        mock_main_tab.window_manager.preview_frames = {"0x123": mock_frame}
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.arrangement_grid = MagicMock()
                tab.arrangement_grid.get_arrangement.return_value = {"Pilot1": (0, 0)}
                tab.monitor_spin = MagicMock()
                tab.monitor_spin.value.return_value = 0
                tab.rows_spin = MagicMock()
                tab.rows_spin.value.return_value = 2
                tab.cols_spin = MagicMock()
                tab.cols_spin.value.return_value = 2
                tab.spacing_spin = MagicMock()
                tab.spacing_spin.value.return_value = 0
                tab.stack_checkbox = MagicMock()
                tab.stack_checkbox.isChecked.return_value = False
                tab.pattern_combo = MagicMock()
                tab.pattern_combo.currentText.return_value = "2x2 Grid"

                tab.grid_applier = MagicMock()
                tab.grid_applier.get_screen_geometry.return_value = ScreenGeometry(0, 0, 1920, 1080)
                tab.grid_applier.apply_arrangement.return_value = True

                tab.layout_applied = MagicMock()

                tab._apply_to_active_windows()

                mock_msgbox.information.assert_called()
                tab.layout_applied.emit.assert_called()

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QMessageBox")
    def test_apply_failure(self, mock_msgbox, mock_widget):
        """Test _apply_to_active_windows failure"""
        mock_widget.return_value = None

        from argus_overview.ui.layouts_tab import LayoutsTab, ScreenGeometry

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_frame = MagicMock()
        mock_frame.character_name = "Pilot1"
        mock_main_tab.window_manager = MagicMock()
        mock_main_tab.window_manager.preview_frames = {"0x123": mock_frame}
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, "_setup_ui"):
            with patch.object(LayoutsTab, "_load_groups"):
                tab = LayoutsTab(
                    mock_layout_manager, mock_main_tab, settings_manager=mock_settings_manager
                )

                tab.arrangement_grid = MagicMock()
                tab.arrangement_grid.get_arrangement.return_value = {"Pilot1": (0, 0)}
                tab.monitor_spin = MagicMock()
                tab.monitor_spin.value.return_value = 0
                tab.rows_spin = MagicMock()
                tab.rows_spin.value.return_value = 2
                tab.cols_spin = MagicMock()
                tab.cols_spin.value.return_value = 2
                tab.spacing_spin = MagicMock()
                tab.spacing_spin.value.return_value = 0
                tab.stack_checkbox = MagicMock()
                tab.stack_checkbox.isChecked.return_value = False

                tab.grid_applier = MagicMock()
                tab.grid_applier.get_screen_geometry.return_value = ScreenGeometry(0, 0, 1920, 1080)
                tab.grid_applier.apply_arrangement.return_value = False

                tab._apply_to_active_windows()

                mock_msgbox.warning.assert_called()


# Test edge cases for more coverage
class TestArrangementGridSetGridSizeWithTiles:
    """Tests for set_grid_size with existing tiles"""

    @patch("argus_overview.ui.layouts_tab.QWidget.__init__")
    @patch("argus_overview.ui.layouts_tab.QGridLayout")
    @patch("argus_overview.ui.layouts_tab.QFrame")
    def test_set_grid_size_repositions_existing_tiles(self, mock_frame, mock_grid, mock_widget):
        """Test set_grid_size repositions tiles that are out of bounds"""
        mock_widget.return_value = None
        mock_grid_instance = MagicMock()
        mock_grid_instance.count.return_value = 0  # No existing widgets to clear
        mock_grid.return_value = mock_grid_instance

        from argus_overview.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, "setLayout"):
            with patch.object(ArrangementGrid, "arrangement_changed", MagicMock()):
                grid = ArrangementGrid()
                grid.grid_layout = mock_grid_instance

                # Add tiles with positions beyond new grid size
                tile1 = MagicMock()
                tile1.grid_row = 5  # Will need repositioning if grid shrinks
                tile1.grid_col = 5
                tile2 = MagicMock()
                tile2.grid_row = 0
                tile2.grid_col = 0
                grid.tiles = {"Char1": tile1, "Char2": tile2}

                # Shrink grid - tiles should be repositioned
                grid.set_grid_size(2, 2)

                # Tile1 should be repositioned to (1, 1) (clamped from (5, 5))
                tile1.set_position.assert_called_with(1, 1)
                # Tile2 stays at (0, 0)
                tile2.set_position.assert_called_with(0, 0)


class TestGridApplierScreenGeometryEdgeCases:
    """Tests for GridApplier.get_screen_geometry edge cases"""

    @patch("argus_overview.utils.screen.subprocess.run")
    def test_get_screen_geometry_monitor_out_of_range(self, mock_subprocess):
        """Test get_screen_geometry falls back to first monitor when index out of range"""
        from argus_overview.ui.layouts_tab import GridApplier

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "HDMI-1 connected primary 1920x1080+0+0"  # Only 1 monitor
        mock_subprocess.return_value = mock_result

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        # Request monitor 5 but only 1 exists - should fall back to monitors[0]
        result = applier.get_screen_geometry(monitor=5)

        assert result is not None
        assert result.width == 1920
        assert result.height == 1080

    @patch("argus_overview.utils.screen.subprocess.run")
    @patch("argus_overview.utils.screen.logger")
    def test_get_screen_geometry_no_monitors_parsed(self, mock_logger, mock_subprocess):
        """Test get_screen_geometry returns default when no monitors parsed"""
        from argus_overview.ui.layouts_tab import GridApplier

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "some unrecognized output"  # No valid monitor lines
        mock_subprocess.return_value = mock_result

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        result = applier.get_screen_geometry(monitor=0)

        # Should return default geometry
        assert result is not None
        assert result.width == 1920
        assert result.height == 1080
        # Now logger is the module-level logger in utils.screen
        mock_logger.warning.assert_called()


class TestGridApplierApplyArrangementEdgeCases:
    """Tests for GridApplier.apply_arrangement edge cases"""

    @patch("argus_overview.ui.layouts_tab.subprocess.run")
    def test_apply_arrangement_char_not_in_window_map(self, mock_subprocess):
        """Test apply_arrangement skips chars not in window_map"""
        from argus_overview.ui.layouts_tab import GridApplier, ScreenGeometry

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        screen = ScreenGeometry(0, 0, 1920, 1080)

        # Arrangement has chars not in window_map
        result = applier.apply_arrangement(
            arrangement={"Pilot1": (0, 0), "Pilot2": (0, 1)},
            window_map={"Pilot1": "0x123"},  # Pilot2 not in map
            screen=screen,
            grid_rows=2,
            grid_cols=2,
        )

        # Should still succeed (only Pilot1 processed)
        assert result is True


class TestGridApplierMoveWindowTimeout:
    """Tests for GridApplier._move_window TimeoutExpired handling"""

    @patch("argus_overview.ui.layouts_tab.subprocess.run")
    @patch("time.sleep")  # Patch time.sleep at module level since it's imported locally
    def test_move_window_timeout_retry(self, mock_sleep, mock_subprocess):
        """Test _move_window retries without --sync on timeout"""
        import subprocess

        from argus_overview.ui.layouts_tab import GridApplier

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        # First call times out, second succeeds
        mock_subprocess.side_effect = [
            subprocess.TimeoutExpired("xdotool", 2),  # windowmove --sync times out
            MagicMock(),  # windowmove without --sync
            MagicMock(),  # windowsize --sync
        ]

        applier._move_window("0x123", 100, 200, 800, 600)

        # Should have called 3 times - timeout on first, then retry, then size
        assert mock_subprocess.call_count == 3
        mock_sleep.assert_called_once_with(0.1)

    @patch("argus_overview.ui.layouts_tab.subprocess.run")
    @patch("time.sleep")  # Patch time.sleep at module level since it's imported locally
    def test_move_window_windowsize_timeout_retry(self, mock_sleep, mock_subprocess):
        """Test _move_window retries windowsize without --sync on timeout"""
        import subprocess

        from argus_overview.ui.layouts_tab import GridApplier

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        # Move succeeds, size times out then succeeds
        mock_subprocess.side_effect = [
            MagicMock(),  # windowmove --sync succeeds
            subprocess.TimeoutExpired("xdotool", 2),  # windowsize --sync times out
            MagicMock(),  # windowsize without --sync
        ]

        applier._move_window("0x123", 100, 200, 800, 600)

        assert mock_subprocess.call_count == 3
        mock_sleep.assert_called_once_with(0.1)


# =============================================================================
# LayoutsTab UI Setup Tests
# =============================================================================


class TestLayoutsTabUISetup:
    """Tests for LayoutsTab UI setup methods"""

    def test_layouts_tab_has_setup_ui(self):
        """Test LayoutsTab has _setup_ui method"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        assert hasattr(LayoutsTab, "_setup_ui")

    def test_layouts_tab_has_create_top_section(self):
        """Test LayoutsTab has _create_top_section method"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        assert hasattr(LayoutsTab, "_create_top_section")

    def test_layouts_tab_has_create_grid_section(self):
        """Test LayoutsTab has _create_grid_section method"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        assert hasattr(LayoutsTab, "_create_grid_section")

    def test_layouts_tab_has_create_bottom_section(self):
        """Test LayoutsTab has _create_bottom_section method"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        assert hasattr(LayoutsTab, "_create_bottom_section")

    def test_layouts_tab_has_refresh_groups(self):
        """Test LayoutsTab has _refresh_groups method"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        assert hasattr(LayoutsTab, "_refresh_groups")

    def test_layouts_tab_has_on_group_selected(self):
        """Test LayoutsTab has _on_group_selected method"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        assert hasattr(LayoutsTab, "_on_group_selected")

    def test_layouts_tab_has_on_pattern_changed(self):
        """Test LayoutsTab has _on_pattern_changed method"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        assert hasattr(LayoutsTab, "_on_pattern_changed")


class TestLayoutsTabRefreshGroups:
    """Tests for LayoutsTab._refresh_groups method"""

    def test_refresh_groups_populates_combo(self):
        """Test _refresh_groups populates group combo"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab.cycling_groups = {"Default": [], "PvP": ["char1"]}
            tab.group_combo = MagicMock()
            tab.group_combo.count.return_value = 0  # Initially empty
            tab.settings_manager = MagicMock()
            tab.settings_manager.get.return_value = {"Default": [], "PvP": ["char1"]}
            tab.logger = MagicMock()

            tab._refresh_groups()

            # Should have cleared and added items
            tab.group_combo.clear.assert_called_once()
            assert tab.group_combo.addItem.call_count >= 2

    def test_refresh_groups_restores_selection(self):
        """Test _refresh_groups restores previous selection"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab.cycling_groups = {"Default": [], "PvP": []}
            tab.group_combo = MagicMock()
            tab.group_combo.count.return_value = 2  # Has items
            tab.group_combo.currentText.return_value = "PvP"
            tab.group_combo.findText.return_value = 1
            tab.settings_manager = MagicMock()
            tab.settings_manager.get.return_value = {"Default": [], "PvP": []}
            tab.logger = MagicMock()

            tab._refresh_groups()

            tab.group_combo.setCurrentIndex.assert_called_with(1)


class TestLayoutsTabOnGroupSelected:
    """Tests for LayoutsTab._on_group_selected method"""

    def test_on_group_selected_clears_tiles(self):
        """Test _on_group_selected clears arrangement grid"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab.group_combo = MagicMock()
            tab.group_combo.currentText.return_value = "Default"
            tab.arrangement_grid = MagicMock()
            tab.cycling_groups = {"Default": []}
            tab.info_label = MagicMock()
            tab.pattern_combo = MagicMock()
            tab.pattern_combo.currentText.return_value = "Custom"
            tab.logger = MagicMock()

            tab._on_group_selected()

            tab.arrangement_grid.clear_tiles.assert_called_once()

    def test_on_group_selected_adds_characters(self):
        """Test _on_group_selected adds group members"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab.group_combo = MagicMock()
            tab.group_combo.currentText.return_value = "PvP"
            tab.arrangement_grid = MagicMock()
            tab.arrangement_grid.grid_cols = 3
            tab.cycling_groups = {"PvP": ["Char1", "Char2"]}
            tab.info_label = MagicMock()
            tab.pattern_combo = MagicMock()
            tab.pattern_combo.currentText.return_value = "Custom"
            tab.logger = MagicMock()

            tab._on_group_selected()

            # Should add 2 characters
            assert tab.arrangement_grid.add_character.call_count == 2

    def test_on_group_selected_all_active_windows(self):
        """Test _on_group_selected with 'All Active Windows'"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab.group_combo = MagicMock()
            tab.group_combo.currentText.return_value = "All Active Windows"
            tab.arrangement_grid = MagicMock()
            tab.cycling_groups = {}
            tab.info_label = MagicMock()
            tab.pattern_combo = MagicMock()
            tab.pattern_combo.currentText.return_value = "Custom"
            tab.logger = MagicMock()

            # Mock main_tab with window manager
            tab.main_tab = MagicMock()
            mock_frame = MagicMock()
            mock_frame.character_name = "TestChar"
            tab.main_tab.window_manager.preview_frames = {"123": mock_frame}

            tab._on_group_selected()

            tab.arrangement_grid.add_character.assert_called_with("TestChar")

    def test_on_group_selected_auto_arranges(self):
        """Test _on_group_selected auto-arranges when pattern selected"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab.group_combo = MagicMock()
            tab.group_combo.currentText.return_value = "Default"
            tab.arrangement_grid = MagicMock()
            tab.cycling_groups = {"Default": []}
            tab.info_label = MagicMock()
            tab.pattern_combo = MagicMock()
            tab.pattern_combo.currentText.return_value = "2x2 Grid"
            tab._auto_arrange = MagicMock()
            tab.logger = MagicMock()

            tab._on_group_selected()

            tab._auto_arrange.assert_called_once()


class TestLayoutsTabOnPatternChanged:
    """Tests for LayoutsTab._on_pattern_changed method"""

    def test_on_pattern_changed_stacked(self):
        """Test _on_pattern_changed with Stacked pattern"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab.pattern_combo = MagicMock()
            tab.pattern_combo.currentText.return_value = "Stacked (All Same Position)"
            tab.stack_checkbox = MagicMock()
            tab.arrangement_grid = MagicMock()
            tab.logger = MagicMock()

            tab._on_pattern_changed()

            tab.stack_checkbox.setChecked.assert_called_with(True)

    def test_on_pattern_changed_grid(self):
        """Test _on_pattern_changed with Grid pattern"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab.pattern_combo = MagicMock()
            tab.pattern_combo.currentText.return_value = "2x2 Grid"
            tab.stack_checkbox = MagicMock()
            tab.arrangement_grid = MagicMock()
            tab.logger = MagicMock()

            tab._on_pattern_changed()

            tab.stack_checkbox.setChecked.assert_called_with(False)


class TestLayoutsTabRefreshFromSettings:
    """Tests for LayoutsTab.refresh_groups_from_settings method"""

    def test_refresh_groups_from_settings_calls_methods(self):
        """Test refresh_groups_from_settings calls internal methods"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab._refresh_groups = MagicMock()
            tab._on_group_selected = MagicMock()

            tab.refresh_groups_from_settings()

            tab._refresh_groups.assert_called_once()
            tab._on_group_selected.assert_called_once()


class TestLayoutsTabSetupUI:
    """Tests for LayoutsTab._setup_ui method"""

    def test_setup_ui_creates_layout(self):
        """Test _setup_ui creates vertical layout with sections"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)

            mock_top = MagicMock()
            mock_grid = MagicMock()
            mock_bottom = MagicMock()
            tab._create_top_section = MagicMock(return_value=mock_top)
            tab._create_grid_section = MagicMock(return_value=mock_grid)
            tab._create_bottom_section = MagicMock(return_value=mock_bottom)
            tab._on_group_selected = MagicMock()
            tab.setLayout = MagicMock()

            with patch("argus_overview.ui.layouts_tab.QVBoxLayout") as mock_layout_cls:
                mock_layout = MagicMock()
                mock_layout_cls.return_value = mock_layout

                tab._setup_ui()

                # Verify layout created
                mock_layout.setContentsMargins.assert_called_once_with(10, 10, 10, 10)
                tab.setLayout.assert_called_once_with(mock_layout)

                # Verify sections added
                assert mock_layout.addWidget.call_count == 3
                tab._on_group_selected.assert_called_once()


class TestLayoutsTabCreateTopSection:
    """Tests for LayoutsTab._create_top_section method"""

    def test_create_top_section_creates_group_selector(self):
        """Test _create_top_section creates group selector widgets"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab._refresh_groups = MagicMock()
            tab._on_group_selected = MagicMock()
            tab._on_pattern_changed = MagicMock()
            tab._auto_arrange = MagicMock()
            tab._update_grid_size = MagicMock()

            with patch("argus_overview.ui.layouts_tab.QGroupBox") as mock_groupbox_cls, patch(
                "argus_overview.ui.layouts_tab.QHBoxLayout"
            ) as mock_hlayout_cls, patch("argus_overview.ui.layouts_tab.QVBoxLayout"), patch(
                "argus_overview.ui.layouts_tab.QLabel"
            ), patch("argus_overview.ui.layouts_tab.QComboBox") as mock_combo_cls, patch(
                "argus_overview.ui.layouts_tab.QPushButton"
            ) as mock_btn_cls, patch(
                "argus_overview.ui.layouts_tab.QSpinBox"
            ) as mock_spin_cls, patch(
                "argus_overview.ui.layouts_tab.QCheckBox"
            ) as mock_checkbox_cls, patch(
                "argus_overview.ui.layouts_tab.get_all_patterns", return_value=["2x2", "3x1"]
            ):
                mock_section = MagicMock()
                mock_groupbox_cls.return_value = mock_section

                mock_hlayout = MagicMock()
                mock_hlayout_cls.return_value = mock_hlayout

                mock_combo = MagicMock()
                mock_combo_cls.return_value = mock_combo

                mock_btn = MagicMock()
                mock_btn_cls.return_value = mock_btn

                mock_spin = MagicMock()
                mock_spin_cls.return_value = mock_spin

                mock_checkbox = MagicMock()
                mock_checkbox_cls.return_value = mock_checkbox

                result = tab._create_top_section()

                # Verify section created
                mock_groupbox_cls.assert_called_with("Layout Configuration")
                assert result == mock_section

                # Verify combos created for group and pattern
                assert mock_combo_cls.call_count >= 2
                tab._refresh_groups.assert_called_once()

    def test_create_top_section_creates_grid_size_controls(self):
        """Test _create_top_section creates grid size spinboxes"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab._refresh_groups = MagicMock()
            tab._on_group_selected = MagicMock()
            tab._on_pattern_changed = MagicMock()
            tab._auto_arrange = MagicMock()
            tab._update_grid_size = MagicMock()

            with patch("argus_overview.ui.layouts_tab.QGroupBox"), patch(
                "argus_overview.ui.layouts_tab.QHBoxLayout"
            ), patch("argus_overview.ui.layouts_tab.QVBoxLayout"), patch(
                "argus_overview.ui.layouts_tab.QLabel"
            ), patch("argus_overview.ui.layouts_tab.QComboBox"), patch(
                "argus_overview.ui.layouts_tab.QPushButton"
            ), patch("argus_overview.ui.layouts_tab.QSpinBox") as mock_spin_cls, patch(
                "argus_overview.ui.layouts_tab.QCheckBox"
            ), patch("argus_overview.ui.layouts_tab.get_all_patterns", return_value=[]):
                mock_spin = MagicMock()
                mock_spin_cls.return_value = mock_spin

                tab._create_top_section()

                # Verify spinboxes created (rows, cols, spacing, monitor = 4)
                assert mock_spin_cls.call_count >= 4
                # Verify valueChanged connected
                mock_spin.valueChanged.connect.assert_called()


class TestLayoutsTabCreateGridSection:
    """Tests for LayoutsTab._create_grid_section method"""

    def test_create_grid_section_creates_scroll_area(self):
        """Test _create_grid_section creates scroll area with grid"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)

            with patch("argus_overview.ui.layouts_tab.QGroupBox") as mock_groupbox_cls, patch(
                "argus_overview.ui.layouts_tab.QVBoxLayout"
            ) as mock_vlayout_cls, patch("argus_overview.ui.layouts_tab.QLabel"), patch(
                "argus_overview.ui.layouts_tab.QScrollArea"
            ) as mock_scroll_cls, patch(
                "argus_overview.ui.layouts_tab.ArrangementGrid"
            ) as mock_grid_cls:
                mock_section = MagicMock()
                mock_groupbox_cls.return_value = mock_section

                mock_layout = MagicMock()
                mock_vlayout_cls.return_value = mock_layout

                mock_scroll = MagicMock()
                mock_scroll_cls.return_value = mock_scroll

                mock_grid = MagicMock()
                mock_grid_cls.return_value = mock_grid

                result = tab._create_grid_section()

                # Verify section created
                mock_groupbox_cls.assert_called_with("Window Arrangement")
                assert result == mock_section

                # Verify scroll area setup
                mock_scroll.setWidgetResizable.assert_called_with(True)
                mock_scroll.setMinimumHeight.assert_called_with(300)
                mock_scroll.setWidget.assert_called_with(mock_grid)

                # Verify arrangement_grid assigned
                assert tab.arrangement_grid == mock_grid

    def test_create_grid_section_creates_instructions_label(self):
        """Test _create_grid_section creates instructions label"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)

            with patch("argus_overview.ui.layouts_tab.QGroupBox"), patch(
                "argus_overview.ui.layouts_tab.QVBoxLayout"
            ), patch("argus_overview.ui.layouts_tab.QLabel") as mock_label_cls, patch(
                "argus_overview.ui.layouts_tab.QScrollArea"
            ), patch("argus_overview.ui.layouts_tab.ArrangementGrid"):
                mock_label = MagicMock()
                mock_label_cls.return_value = mock_label

                tab._create_grid_section()

                # Verify label created with instructions
                assert mock_label_cls.call_count >= 1
                mock_label.setWordWrap.assert_called_with(True)


class TestLayoutsTabCreateBottomSection:
    """Tests for LayoutsTab._create_bottom_section method"""

    def test_create_bottom_section_creates_apply_button(self):
        """Test _create_bottom_section creates apply button"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab._apply_to_active_windows = MagicMock()

            with patch("argus_overview.ui.layouts_tab.QWidget") as mock_widget_cls, patch(
                "argus_overview.ui.layouts_tab.QHBoxLayout"
            ) as mock_hlayout_cls, patch(
                "argus_overview.ui.layouts_tab.QLabel"
            ) as mock_label_cls, patch("argus_overview.ui.layouts_tab.QPushButton") as mock_btn_cls:
                mock_widget = MagicMock()
                mock_widget_cls.return_value = mock_widget

                mock_layout = MagicMock()
                mock_hlayout_cls.return_value = mock_layout

                mock_label = MagicMock()
                mock_label_cls.return_value = mock_label

                mock_btn = MagicMock()
                mock_btn_cls.return_value = mock_btn

                result = tab._create_bottom_section()

                # Verify widget created
                assert result == mock_widget
                mock_layout.setContentsMargins.assert_called_with(0, 0, 0, 0)

                # Verify apply button created
                mock_btn_cls.assert_called_with("Apply to Active Windows")
                mock_btn.clicked.connect.assert_called()

                # Verify info_label assigned
                assert tab.info_label == mock_label

    def test_create_bottom_section_creates_info_label(self):
        """Test _create_bottom_section creates info label"""
        from argus_overview.ui.layouts_tab import LayoutsTab

        with patch.object(LayoutsTab, "__init__", return_value=None):
            tab = LayoutsTab.__new__(LayoutsTab)
            tab._apply_to_active_windows = MagicMock()

            with patch("argus_overview.ui.layouts_tab.QWidget"), patch(
                "argus_overview.ui.layouts_tab.QHBoxLayout"
            ) as mock_hlayout_cls, patch(
                "argus_overview.ui.layouts_tab.QLabel"
            ) as mock_label_cls, patch("argus_overview.ui.layouts_tab.QPushButton"):
                mock_layout = MagicMock()
                mock_hlayout_cls.return_value = mock_layout

                mock_label = MagicMock()
                mock_label_cls.return_value = mock_label

                tab._create_bottom_section()

                # Verify label created
                mock_label_cls.assert_called_with("Select a group to begin")
                mock_layout.addStretch.assert_called_once()


class TestMoveWindowInvalidId:
    """Tests for _move_window with invalid window IDs"""

    @patch("argus_overview.ui.layouts_tab.subprocess.run")
    def test_move_window_invalid_id_returns_early(self, mock_subprocess):
        """Test _move_window returns early for invalid window ID"""
        from argus_overview.ui.layouts_tab import GridApplier

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        # Call with various invalid IDs
        applier._move_window("invalid", 100, 200, 800, 600)
        applier._move_window("", 100, 200, 800, 600)
        applier._move_window("12345", 100, 200, 800, 600)  # Missing 0x prefix

        # subprocess should never be called
        mock_subprocess.assert_not_called()

    @patch("argus_overview.ui.layouts_tab.subprocess.run")
    def test_move_window_valid_id_proceeds(self, mock_subprocess):
        """Test _move_window proceeds for valid window ID"""
        from argus_overview.ui.layouts_tab import GridApplier

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        applier._move_window("0x12345", 100, 200, 800, 600)

        # subprocess should be called
        assert mock_subprocess.called
