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
        from eve_overview_pro.ui.layouts_tab import ScreenGeometry

        screen = ScreenGeometry(0, 0, 1920, 1080)

        assert screen.x == 0
        assert screen.y == 0
        assert screen.width == 1920
        assert screen.height == 1080
        assert screen.is_primary is False

    def test_create_primary_screen(self):
        """Test creating primary screen"""
        from eve_overview_pro.ui.layouts_tab import ScreenGeometry

        screen = ScreenGeometry(0, 0, 2560, 1440, is_primary=True)

        assert screen.is_primary is True

    def test_multi_monitor_offset(self):
        """Test screen with offset for multi-monitor"""
        from eve_overview_pro.ui.layouts_tab import ScreenGeometry

        screen = ScreenGeometry(1920, 0, 1920, 1080)

        assert screen.x == 1920
        assert screen.y == 0


# Test helper functions
class TestHelperFunctions:
    """Tests for module helper functions"""

    def test_get_all_patterns(self):
        """Test get_all_patterns returns expected patterns"""
        from eve_overview_pro.ui.layouts_tab import get_all_patterns

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
        from eve_overview_pro.ui.layouts_tab import GridPattern, pattern_display_to_enum

        assert pattern_display_to_enum("2x2 Grid") == GridPattern.GRID_2X2
        assert pattern_display_to_enum("3x1 Row") == GridPattern.GRID_3X1
        assert pattern_display_to_enum("Cascade") == GridPattern.CASCADE

    def test_pattern_display_to_enum_unknown(self):
        """Test pattern_display_to_enum with unknown pattern"""
        from eve_overview_pro.ui.layouts_tab import GridPattern, pattern_display_to_enum

        result = pattern_display_to_enum("Unknown Pattern")

        assert result == GridPattern.CUSTOM


# Test DraggableTile
class TestDraggableTile:
    """Tests for DraggableTile widget"""

    @patch('eve_overview_pro.ui.layouts_tab.QFrame.__init__')
    @patch('eve_overview_pro.ui.layouts_tab.QVBoxLayout')
    @patch('eve_overview_pro.ui.layouts_tab.QLabel')
    @patch('eve_overview_pro.ui.layouts_tab.QColor')
    def test_init(self, mock_color, mock_label, mock_layout, mock_frame):
        """Test DraggableTile initialization"""
        mock_frame.return_value = None
        mock_color_instance = MagicMock()
        mock_color_instance.name.return_value = "#ff0000"
        mock_color_instance.darker.return_value = mock_color_instance

        from eve_overview_pro.ui.layouts_tab import DraggableTile

        with patch.object(DraggableTile, 'setFixedSize'):
            with patch.object(DraggableTile, 'setFrameStyle'):
                with patch.object(DraggableTile, 'setLineWidth'):
                    with patch.object(DraggableTile, 'setStyleSheet'):
                        with patch.object(DraggableTile, 'setLayout'):
                            tile = DraggableTile("TestChar", mock_color_instance)

                            assert tile.char_name == "TestChar"
                            assert tile.grid_row == 0
                            assert tile.grid_col == 0
                            assert tile.is_stacked is False

    @patch('eve_overview_pro.ui.layouts_tab.QFrame.__init__')
    @patch('eve_overview_pro.ui.layouts_tab.QVBoxLayout')
    @patch('eve_overview_pro.ui.layouts_tab.QLabel')
    @patch('eve_overview_pro.ui.layouts_tab.QColor')
    def test_set_position(self, mock_color, mock_label, mock_layout, mock_frame):
        """Test set_position method"""
        mock_frame.return_value = None
        mock_color_instance = MagicMock()
        mock_color_instance.name.return_value = "#ff0000"
        mock_color_instance.darker.return_value = mock_color_instance

        from eve_overview_pro.ui.layouts_tab import DraggableTile

        with patch.object(DraggableTile, 'setFixedSize'):
            with patch.object(DraggableTile, 'setFrameStyle'):
                with patch.object(DraggableTile, 'setLineWidth'):
                    with patch.object(DraggableTile, 'setStyleSheet'):
                        with patch.object(DraggableTile, 'setLayout'):
                            tile = DraggableTile("TestChar", mock_color_instance)

                            tile.set_position(2, 3)

                            assert tile.grid_row == 2
                            assert tile.grid_col == 3

    @patch('eve_overview_pro.ui.layouts_tab.QFrame.__init__')
    @patch('eve_overview_pro.ui.layouts_tab.QVBoxLayout')
    @patch('eve_overview_pro.ui.layouts_tab.QLabel')
    @patch('eve_overview_pro.ui.layouts_tab.QColor')
    def test_set_stacked(self, mock_color, mock_label, mock_layout, mock_frame):
        """Test set_stacked method"""
        mock_frame.return_value = None
        mock_color_instance = MagicMock()
        mock_color_instance.name.return_value = "#ff0000"
        mock_color_instance.darker.return_value = mock_color_instance

        from eve_overview_pro.ui.layouts_tab import DraggableTile

        with patch.object(DraggableTile, 'setFixedSize'):
            with patch.object(DraggableTile, 'setFrameStyle'):
                with patch.object(DraggableTile, 'setLineWidth'):
                    with patch.object(DraggableTile, 'setStyleSheet'):
                        with patch.object(DraggableTile, 'setLayout'):
                            tile = DraggableTile("TestChar", mock_color_instance)

                            tile.set_stacked(True)

                            assert tile.is_stacked is True

    def test_signal_exists(self):
        """Test that tile_moved signal exists"""
        from eve_overview_pro.ui.layouts_tab import DraggableTile

        assert hasattr(DraggableTile, 'tile_moved')


# Test ArrangementGrid
class TestArrangementGrid:
    """Tests for ArrangementGrid widget"""

    @patch('eve_overview_pro.ui.layouts_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.layouts_tab.QGridLayout')
    @patch('eve_overview_pro.ui.layouts_tab.QFrame')
    def test_init(self, mock_frame, mock_grid, mock_widget):
        """Test ArrangementGrid initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, 'setLayout'):
            grid = ArrangementGrid()

            assert grid.tiles == {}
            assert grid.grid_rows == 3
            assert grid.grid_cols == 4

    @patch('eve_overview_pro.ui.layouts_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.layouts_tab.QGridLayout')
    @patch('eve_overview_pro.ui.layouts_tab.QFrame')
    def test_clear_tiles(self, mock_frame, mock_grid, mock_widget):
        """Test clear_tiles method"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, 'setLayout'):
            grid = ArrangementGrid()
            grid.tiles = {"Char1": MagicMock(), "Char2": MagicMock()}

            grid.clear_tiles()

            assert grid.tiles == {}

    @patch('eve_overview_pro.ui.layouts_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.layouts_tab.QGridLayout')
    @patch('eve_overview_pro.ui.layouts_tab.QFrame')
    def test_get_arrangement_empty(self, mock_frame, mock_grid, mock_widget):
        """Test get_arrangement with no tiles"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, 'setLayout'):
            grid = ArrangementGrid()

            result = grid.get_arrangement()

            assert result == {}

    def test_signal_exists(self):
        """Test that arrangement_changed signal exists"""
        from eve_overview_pro.ui.layouts_tab import ArrangementGrid

        assert hasattr(ArrangementGrid, 'arrangement_changed')


# Test GridApplier
class TestGridApplier:
    """Tests for GridApplier class"""

    def test_init(self):
        """Test GridApplier initialization"""
        from eve_overview_pro.ui.layouts_tab import GridApplier

        mock_layout_manager = MagicMock()

        applier = GridApplier(mock_layout_manager)

        assert applier.layout_manager is mock_layout_manager

    @patch('eve_overview_pro.ui.layouts_tab.subprocess.run')
    def test_get_screen_geometry_success(self, mock_subprocess):
        """Test get_screen_geometry with successful xrandr"""
        from eve_overview_pro.ui.layouts_tab import GridApplier

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

    @patch('eve_overview_pro.ui.layouts_tab.subprocess.run')
    def test_get_screen_geometry_failure(self, mock_subprocess):
        """Test get_screen_geometry with xrandr failure"""
        from eve_overview_pro.ui.layouts_tab import GridApplier

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        result = applier.get_screen_geometry()

        # Should return default geometry on failure
        assert result is None

    @patch('eve_overview_pro.ui.layouts_tab.subprocess.run')
    def test_get_screen_geometry_exception(self, mock_subprocess):
        """Test get_screen_geometry with exception"""
        from eve_overview_pro.ui.layouts_tab import GridApplier

        mock_subprocess.side_effect = Exception("xrandr not found")

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        result = applier.get_screen_geometry()

        # Should return default geometry on exception
        assert result is not None
        assert result.width == 1920

    @patch('eve_overview_pro.ui.layouts_tab.subprocess.run')
    def test_apply_arrangement_stacked(self, mock_subprocess):
        """Test apply_arrangement with stacked mode"""
        from eve_overview_pro.ui.layouts_tab import GridApplier, ScreenGeometry

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
            stacked=True
        )

        assert result is True
        # Should have called xdotool for each window
        assert mock_subprocess.call_count >= 2

    @patch('eve_overview_pro.ui.layouts_tab.subprocess.run')
    def test_apply_arrangement_grid(self, mock_subprocess):
        """Test apply_arrangement with grid mode"""
        from eve_overview_pro.ui.layouts_tab import GridApplier, ScreenGeometry

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
            stacked=False
        )

        assert result is True

    @patch('eve_overview_pro.ui.layouts_tab.subprocess.run')
    def test_apply_arrangement_exception(self, mock_subprocess):
        """Test apply_arrangement handles exceptions"""
        from eve_overview_pro.ui.layouts_tab import GridApplier, ScreenGeometry

        mock_subprocess.side_effect = Exception("xdotool error")

        mock_layout_manager = MagicMock()
        applier = GridApplier(mock_layout_manager)

        screen = ScreenGeometry(0, 0, 1920, 1080)
        arrangement = {"Char1": (0, 0)}
        window_map = {"Char1": "0x12345"}

        result = applier.apply_arrangement(
            arrangement=arrangement,
            window_map=window_map,
            screen=screen,
            grid_rows=2,
            grid_cols=2
        )

        assert result is False


# Test LayoutsTab
class TestLayoutsTab:
    """Tests for LayoutsTab widget"""

    @patch('eve_overview_pro.ui.layouts_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test LayoutsTab initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(LayoutsTab, '_setup_ui'):
            with patch.object(LayoutsTab, '_load_groups'):
                tab = LayoutsTab(mock_layout_manager, mock_main_tab,
                                settings_manager=mock_settings_manager)

                assert tab.layout_manager is mock_layout_manager
                assert tab.main_tab is mock_main_tab

    @patch('eve_overview_pro.ui.layouts_tab.QWidget.__init__')
    def test_load_groups(self, mock_widget):
        """Test _load_groups creates Default if missing"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.layouts_tab import LayoutsTab

        mock_layout_manager = MagicMock()
        mock_main_tab = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {"TestGroup": ["A", "B"]}

        with patch.object(LayoutsTab, '_setup_ui'):
            tab = LayoutsTab(mock_layout_manager, mock_main_tab,
                            settings_manager=mock_settings_manager)

            assert "Default" in tab.cycling_groups
            assert "TestGroup" in tab.cycling_groups

    def test_signal_exists(self):
        """Test that layout_applied signal exists"""
        from eve_overview_pro.ui.layouts_tab import LayoutsTab

        assert hasattr(LayoutsTab, 'layout_applied')


# Test pattern grid calculations
class TestPatternCalculations:
    """Tests for pattern-based grid calculations"""

    @patch('eve_overview_pro.ui.layouts_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.layouts_tab.QGridLayout')
    @patch('eve_overview_pro.ui.layouts_tab.QFrame')
    def test_auto_arrange_2x2(self, mock_frame, mock_grid_layout, mock_widget):
        """Test auto_arrange_grid with 2x2 pattern"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, 'setLayout'):
            with patch.object(ArrangementGrid, 'arrangement_changed', MagicMock()):
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
                    "Char4": mock_tile4
                }

                grid.auto_arrange_grid("2x2 Grid")

                # Each tile should have set_position called
                mock_tile1.set_position.assert_called()
                mock_tile2.set_position.assert_called()

    @patch('eve_overview_pro.ui.layouts_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.layouts_tab.QGridLayout')
    @patch('eve_overview_pro.ui.layouts_tab.QFrame')
    def test_auto_arrange_stacked(self, mock_frame, mock_grid_layout, mock_widget):
        """Test auto_arrange_grid with stacked pattern"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.layouts_tab import ArrangementGrid

        with patch.object(ArrangementGrid, 'setLayout'):
            with patch.object(ArrangementGrid, 'arrangement_changed', MagicMock()):
                grid = ArrangementGrid()

                mock_tile1 = MagicMock()
                mock_tile2 = MagicMock()

                grid.tiles = {"Char1": mock_tile1, "Char2": mock_tile2}

                grid.auto_arrange_grid("Stacked (All Same Position)")

                # All tiles should be marked as stacked
                mock_tile1.set_stacked.assert_called_with(True)
                mock_tile2.set_stacked.assert_called_with(True)
