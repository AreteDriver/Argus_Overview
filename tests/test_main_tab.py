"""
Unit tests for the Main Tab module
Tests FlowLayout, DraggableTile, ArrangementGrid, GridApplier, WindowPreviewWidget, WindowManager, MainTab
"""
from unittest.mock import MagicMock, patch

from PIL import Image


# Test ScreenGeometry dataclass
class TestScreenGeometry:
    """Tests for ScreenGeometry dataclass"""

    def test_create_screen_geometry(self):
        """Test creating ScreenGeometry"""
        from eve_overview_pro.ui.main_tab import ScreenGeometry

        screen = ScreenGeometry(0, 0, 1920, 1080)

        assert screen.x == 0
        assert screen.y == 0
        assert screen.width == 1920
        assert screen.height == 1080
        assert screen.is_primary is False

    def test_create_primary_screen(self):
        """Test creating primary screen"""
        from eve_overview_pro.ui.main_tab import ScreenGeometry

        screen = ScreenGeometry(0, 0, 2560, 1440, is_primary=True)

        assert screen.is_primary is True


# Test FlowLayout
class TestFlowLayout:
    """Tests for FlowLayout widget"""

    @patch('eve_overview_pro.ui.main_tab.QLayout.__init__')
    def test_init(self, mock_layout):
        """Test FlowLayout initialization"""
        mock_layout.return_value = None

        from eve_overview_pro.ui.main_tab import FlowLayout

        layout = FlowLayout(margin=10, spacing=5)

        assert layout._margin == 10
        assert layout._spacing == 5
        assert layout._item_list == []

    @patch('eve_overview_pro.ui.main_tab.QLayout.__init__')
    def test_count_empty(self, mock_layout):
        """Test count with no items"""
        mock_layout.return_value = None

        from eve_overview_pro.ui.main_tab import FlowLayout

        layout = FlowLayout()

        assert layout.count() == 0

    @patch('eve_overview_pro.ui.main_tab.QLayout.__init__')
    def test_add_and_count(self, mock_layout):
        """Test adding items and counting"""
        mock_layout.return_value = None

        from eve_overview_pro.ui.main_tab import FlowLayout

        layout = FlowLayout()
        mock_item = MagicMock()

        layout.addItem(mock_item)

        assert layout.count() == 1

    @patch('eve_overview_pro.ui.main_tab.QLayout.__init__')
    def test_item_at_valid_index(self, mock_layout):
        """Test itemAt with valid index"""
        mock_layout.return_value = None

        from eve_overview_pro.ui.main_tab import FlowLayout

        layout = FlowLayout()
        mock_item = MagicMock()
        layout.addItem(mock_item)

        result = layout.itemAt(0)

        assert result is mock_item

    @patch('eve_overview_pro.ui.main_tab.QLayout.__init__')
    def test_item_at_invalid_index(self, mock_layout):
        """Test itemAt with invalid index"""
        mock_layout.return_value = None

        from eve_overview_pro.ui.main_tab import FlowLayout

        layout = FlowLayout()

        result = layout.itemAt(5)

        assert result is None

    @patch('eve_overview_pro.ui.main_tab.QLayout.__init__')
    def test_take_at_valid_index(self, mock_layout):
        """Test takeAt removes and returns item"""
        mock_layout.return_value = None

        from eve_overview_pro.ui.main_tab import FlowLayout

        layout = FlowLayout()
        mock_item = MagicMock()
        layout.addItem(mock_item)

        result = layout.takeAt(0)

        assert result is mock_item
        assert layout.count() == 0

    @patch('eve_overview_pro.ui.main_tab.QLayout.__init__')
    def test_has_height_for_width(self, mock_layout):
        """Test hasHeightForWidth returns True"""
        mock_layout.return_value = None

        from eve_overview_pro.ui.main_tab import FlowLayout

        layout = FlowLayout()

        assert layout.hasHeightForWidth() is True


# Test helper functions
class TestHelperFunctions:
    """Tests for module helper functions"""

    def test_get_all_layout_patterns(self):
        """Test get_all_layout_patterns returns expected patterns"""
        from eve_overview_pro.ui.main_tab import get_all_layout_patterns

        patterns = get_all_layout_patterns()

        assert "2x2 Grid" in patterns
        assert "3x1 Row" in patterns
        assert "1x3 Column" in patterns
        assert "4x1 Row" in patterns
        assert "Main + Sides" in patterns
        assert "Cascade" in patterns
        assert "Stacked (All Same Position)" in patterns


# Test pil_to_qimage
class TestPilToQImage:
    """Tests for pil_to_qimage function"""

    def test_none_input(self):
        """Test with None input"""
        from eve_overview_pro.ui.main_tab import pil_to_qimage

        result = pil_to_qimage(None)

        assert result is None

    def test_rgb_image(self):
        """Test with RGB image"""
        from eve_overview_pro.ui.main_tab import pil_to_qimage

        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        result = pil_to_qimage(img)

        assert result is not None
        assert result.width() == 100
        assert result.height() == 100

    def test_rgba_image(self):
        """Test with RGBA image"""
        from eve_overview_pro.ui.main_tab import pil_to_qimage

        img = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
        result = pil_to_qimage(img)

        assert result is not None
        assert result.width() == 50

    def test_grayscale_image(self):
        """Test with grayscale image"""
        from eve_overview_pro.ui.main_tab import pil_to_qimage

        img = Image.new("L", (80, 60), color=128)
        result = pil_to_qimage(img)

        assert result is not None
        assert result.width() == 80

    def test_unknown_mode_converts(self):
        """Test that unknown mode converts to RGB"""
        from eve_overview_pro.ui.main_tab import pil_to_qimage

        # P mode (palette) should be converted
        img = Image.new("P", (40, 40))
        result = pil_to_qimage(img)

        assert result is not None


# Test DraggableTile
class TestDraggableTile:
    """Tests for DraggableTile widget"""

    @patch('eve_overview_pro.ui.main_tab.QFrame.__init__')
    @patch('eve_overview_pro.ui.main_tab.QVBoxLayout')
    @patch('eve_overview_pro.ui.main_tab.QLabel')
    def test_init(self, mock_label, mock_layout, mock_frame):
        """Test DraggableTile initialization"""
        mock_frame.return_value = None

        from PySide6.QtGui import QColor

        from eve_overview_pro.ui.main_tab import DraggableTile

        mock_color = QColor(255, 100, 100)

        with patch.object(DraggableTile, 'setFixedSize'):
            with patch.object(DraggableTile, 'setFrameStyle'):
                with patch.object(DraggableTile, 'setLineWidth'):
                    with patch.object(DraggableTile, 'setStyleSheet'):
                        with patch.object(DraggableTile, 'setLayout'):
                            tile = DraggableTile("TestChar", mock_color)

                            assert tile.char_name == "TestChar"
                            assert tile.grid_row == 0
                            assert tile.grid_col == 0
                            assert tile.is_stacked is False

    @patch('eve_overview_pro.ui.main_tab.QFrame.__init__')
    @patch('eve_overview_pro.ui.main_tab.QVBoxLayout')
    @patch('eve_overview_pro.ui.main_tab.QLabel')
    def test_set_position(self, mock_label, mock_layout, mock_frame):
        """Test set_position method"""
        mock_frame.return_value = None

        from PySide6.QtGui import QColor

        from eve_overview_pro.ui.main_tab import DraggableTile

        mock_color = QColor(255, 100, 100)

        with patch.object(DraggableTile, 'setFixedSize'):
            with patch.object(DraggableTile, 'setFrameStyle'):
                with patch.object(DraggableTile, 'setLineWidth'):
                    with patch.object(DraggableTile, 'setStyleSheet'):
                        with patch.object(DraggableTile, 'setLayout'):
                            tile = DraggableTile("TestChar", mock_color)
                            tile.pos_label = MagicMock()

                            tile.set_position(2, 3)

                            assert tile.grid_row == 2
                            assert tile.grid_col == 3
                            tile.pos_label.setText.assert_called()

    @patch('eve_overview_pro.ui.main_tab.QFrame.__init__')
    @patch('eve_overview_pro.ui.main_tab.QVBoxLayout')
    @patch('eve_overview_pro.ui.main_tab.QLabel')
    def test_set_stacked(self, mock_label, mock_layout, mock_frame):
        """Test set_stacked method"""
        mock_frame.return_value = None

        from PySide6.QtGui import QColor

        from eve_overview_pro.ui.main_tab import DraggableTile

        mock_color = QColor(255, 100, 100)

        with patch.object(DraggableTile, 'setFixedSize'):
            with patch.object(DraggableTile, 'setFrameStyle'):
                with patch.object(DraggableTile, 'setLineWidth'):
                    with patch.object(DraggableTile, 'setStyleSheet'):
                        with patch.object(DraggableTile, 'setLayout'):
                            tile = DraggableTile("TestChar", mock_color)
                            tile.pos_label = MagicMock()

                            tile.set_stacked(True)

                            assert tile.is_stacked is True

    def test_signal_exists(self):
        """Test that tile_moved signal exists"""
        from eve_overview_pro.ui.main_tab import DraggableTile

        assert hasattr(DraggableTile, 'tile_moved')


# Test ArrangementGrid
class TestArrangementGrid:
    """Tests for ArrangementGrid widget"""

    @patch('eve_overview_pro.ui.main_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test ArrangementGrid initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.main_tab import ArrangementGrid

        with patch.object(ArrangementGrid, '_setup_ui'):
            grid = ArrangementGrid()

            assert grid.tiles == {}
            assert grid.grid_rows == 2
            assert grid.grid_cols == 3

    @patch('eve_overview_pro.ui.main_tab.QWidget.__init__')
    def test_clear_tiles(self, mock_widget):
        """Test clear_tiles method"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.main_tab import ArrangementGrid

        with patch.object(ArrangementGrid, '_setup_ui'):
            grid = ArrangementGrid()
            grid.grid_layout = MagicMock()

            mock_tile = MagicMock()
            grid.tiles = {"Char1": mock_tile}

            grid.clear_tiles()

            assert grid.tiles == {}
            grid.grid_layout.removeWidget.assert_called_with(mock_tile)

    @patch('eve_overview_pro.ui.main_tab.QWidget.__init__')
    def test_get_arrangement_empty(self, mock_widget):
        """Test get_arrangement with no tiles"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.main_tab import ArrangementGrid

        with patch.object(ArrangementGrid, '_setup_ui'):
            grid = ArrangementGrid()

            result = grid.get_arrangement()

            assert result == {}

    @patch('eve_overview_pro.ui.main_tab.QWidget.__init__')
    def test_get_arrangement_with_tiles(self, mock_widget):
        """Test get_arrangement with tiles"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.main_tab import ArrangementGrid

        with patch.object(ArrangementGrid, '_setup_ui'):
            grid = ArrangementGrid()

            mock_tile = MagicMock()
            mock_tile.grid_row = 1
            mock_tile.grid_col = 2
            grid.tiles = {"TestChar": mock_tile}

            result = grid.get_arrangement()

            assert result == {"TestChar": (1, 2)}

    def test_signal_exists(self):
        """Test that arrangement_changed signal exists"""
        from eve_overview_pro.ui.main_tab import ArrangementGrid

        assert hasattr(ArrangementGrid, 'arrangement_changed')


# Test GridApplier
class TestGridApplier:
    """Tests for GridApplier class"""

    def test_init(self):
        """Test GridApplier initialization"""
        from eve_overview_pro.ui.main_tab import GridApplier

        applier = GridApplier()

        assert applier.logger is not None

    @patch('eve_overview_pro.ui.main_tab.subprocess.run')
    def test_get_screen_geometry_success(self, mock_subprocess):
        """Test get_screen_geometry with successful xrandr"""
        from eve_overview_pro.ui.main_tab import GridApplier

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "HDMI-1 connected primary 1920x1080+0+0"
        mock_subprocess.return_value = mock_result

        applier = GridApplier()

        result = applier.get_screen_geometry()

        assert result is not None
        assert result.width == 1920
        assert result.height == 1080
        assert result.is_primary is True

    @patch('eve_overview_pro.ui.main_tab.subprocess.run')
    def test_get_screen_geometry_failure(self, mock_subprocess):
        """Test get_screen_geometry with xrandr failure"""
        from eve_overview_pro.ui.main_tab import GridApplier

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        applier = GridApplier()

        result = applier.get_screen_geometry()

        # Should return default geometry on failure
        assert result is not None
        assert result.width == 1920

    @patch('eve_overview_pro.ui.main_tab.subprocess.run')
    def test_get_screen_geometry_exception(self, mock_subprocess):
        """Test get_screen_geometry with exception"""
        from eve_overview_pro.ui.main_tab import GridApplier

        mock_subprocess.side_effect = Exception("xrandr not found")

        applier = GridApplier()

        result = applier.get_screen_geometry()

        # Should return default geometry on exception
        assert result is not None
        assert result.width == 1920

    @patch('eve_overview_pro.ui.main_tab.subprocess.run')
    def test_apply_arrangement_stacked(self, mock_subprocess):
        """Test apply_arrangement with stacked mode"""
        from eve_overview_pro.ui.main_tab import GridApplier, ScreenGeometry

        mock_subprocess.return_value = MagicMock()

        applier = GridApplier()

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

    @patch('eve_overview_pro.ui.main_tab.subprocess.run')
    def test_apply_arrangement_grid(self, mock_subprocess):
        """Test apply_arrangement with grid mode"""
        from eve_overview_pro.ui.main_tab import GridApplier, ScreenGeometry

        mock_subprocess.return_value = MagicMock()

        applier = GridApplier()

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

    @patch('eve_overview_pro.ui.main_tab.subprocess.run')
    def test_apply_arrangement_exception(self, mock_subprocess):
        """Test apply_arrangement handles exceptions"""
        from eve_overview_pro.ui.main_tab import GridApplier, ScreenGeometry

        mock_subprocess.side_effect = Exception("xdotool error")

        applier = GridApplier()

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


# Test WindowManager
class TestWindowManager:
    """Tests for WindowManager class"""

    def test_init(self):
        """Test WindowManager initialization"""
        from eve_overview_pro.ui.main_tab import WindowManager

        mock_char_manager = MagicMock()
        mock_capture_system = MagicMock()
        mock_alert_detector = MagicMock()
        mock_settings_manager = MagicMock()

        manager = WindowManager(
            mock_char_manager,
            mock_capture_system,
            mock_alert_detector,
            mock_settings_manager
        )

        assert manager.character_manager is mock_char_manager
        assert manager.capture_system is mock_capture_system
        assert manager.alert_detector is mock_alert_detector
        assert manager.settings_manager is mock_settings_manager
        assert manager.refresh_rate == 30
        assert manager.preview_frames == {}

    def test_set_refresh_rate(self):
        """Test set_refresh_rate method"""
        from eve_overview_pro.ui.main_tab import WindowManager

        mock_char_manager = MagicMock()
        mock_capture_system = MagicMock()
        mock_alert_detector = MagicMock()

        manager = WindowManager(mock_char_manager, mock_capture_system, mock_alert_detector)

        manager.set_refresh_rate(15)

        assert manager.refresh_rate == 15

    def test_set_refresh_rate_clamped(self):
        """Test set_refresh_rate clamps values"""
        from eve_overview_pro.ui.main_tab import WindowManager

        mock_char_manager = MagicMock()
        mock_capture_system = MagicMock()
        mock_alert_detector = MagicMock()

        manager = WindowManager(mock_char_manager, mock_capture_system, mock_alert_detector)

        manager.set_refresh_rate(100)  # Over max
        assert manager.refresh_rate == 60

        manager.set_refresh_rate(-5)  # Under min
        assert manager.refresh_rate == 1

    def test_get_active_window_count(self):
        """Test get_active_window_count method"""
        from eve_overview_pro.ui.main_tab import WindowManager

        mock_char_manager = MagicMock()
        mock_capture_system = MagicMock()
        mock_alert_detector = MagicMock()

        manager = WindowManager(mock_char_manager, mock_capture_system, mock_alert_detector)
        manager.preview_frames = {"win1": MagicMock(), "win2": MagicMock()}

        assert manager.get_active_window_count() == 2


# Test MainTab
class TestMainTab:
    """Tests for MainTab widget"""

    @patch('eve_overview_pro.ui.main_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test MainTab initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.main_tab import MainTab

        mock_capture_system = MagicMock()
        mock_char_manager = MagicMock()
        mock_alert_detector = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(MainTab, '_setup_ui'):
            with patch.object(MainTab, '_load_cycling_groups'):
                with patch('eve_overview_pro.ui.main_tab.WindowManager'):
                    with patch('eve_overview_pro.ui.main_tab.GridApplier'):
                        tab = MainTab(
                            mock_capture_system,
                            mock_char_manager,
                            mock_alert_detector,
                            mock_settings_manager
                        )

                        assert tab.capture_system is mock_capture_system
                        assert tab.character_manager is mock_char_manager
                        assert tab.alert_detector is mock_alert_detector
                        assert tab.settings_manager is mock_settings_manager

    @patch('eve_overview_pro.ui.main_tab.QWidget.__init__')
    def test_load_cycling_groups_creates_default(self, mock_widget):
        """Test _load_cycling_groups creates Default group"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.main_tab import MainTab

        mock_capture_system = MagicMock()
        mock_char_manager = MagicMock()
        mock_alert_detector = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(MainTab, '_setup_ui'):
            with patch('eve_overview_pro.ui.main_tab.WindowManager'):
                with patch('eve_overview_pro.ui.main_tab.GridApplier'):
                    tab = MainTab(
                        mock_capture_system,
                        mock_char_manager,
                        mock_alert_detector,
                        mock_settings_manager
                    )

                    assert "Default" in tab.cycling_groups

    def test_signals_exist(self):
        """Test that MainTab has expected signals"""
        from eve_overview_pro.ui.main_tab import MainTab

        assert hasattr(MainTab, 'character_detected')
        assert hasattr(MainTab, 'thumbnails_toggled')
        assert hasattr(MainTab, 'layout_applied')


# Test WindowPreviewWidget
class TestWindowPreviewWidget:
    """Tests for WindowPreviewWidget"""

    @patch('eve_overview_pro.ui.main_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.main_tab.QVBoxLayout')
    @patch('eve_overview_pro.ui.main_tab.QLabel')
    @patch('eve_overview_pro.ui.main_tab.QTimer')
    @patch('eve_overview_pro.ui.main_tab.QGraphicsOpacityEffect')
    def test_init(self, mock_effect, mock_timer, mock_label, mock_layout, mock_widget):
        """Test WindowPreviewWidget initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.main_tab import WindowPreviewWidget

        mock_capture_system = MagicMock()
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(WindowPreviewWidget, 'setMinimumSize'):
            with patch.object(WindowPreviewWidget, 'setMaximumSize'):
                with patch.object(WindowPreviewWidget, 'setToolTip'):
                    with patch.object(WindowPreviewWidget, 'setMouseTracking'):
                        with patch.object(WindowPreviewWidget, 'setLayout'):
                            with patch.object(WindowPreviewWidget, 'setGraphicsEffect'):
                                widget = WindowPreviewWidget(
                                    "0x12345",
                                    "TestPilot",
                                    mock_capture_system,
                                    mock_settings_manager
                                )

                                assert widget.window_id == "0x12345"
                                assert widget.character_name == "TestPilot"

    def test_signals_exist(self):
        """Test that WindowPreviewWidget has expected signals"""
        from eve_overview_pro.ui.main_tab import WindowPreviewWidget

        assert hasattr(WindowPreviewWidget, 'window_activated')
        assert hasattr(WindowPreviewWidget, 'window_removed')
        assert hasattr(WindowPreviewWidget, 'label_changed')
