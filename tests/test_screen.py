"""
Unit tests for screen geometry utilities
Tests get_screen_geometry and get_all_monitors functions

v3.0: Tests now mock the platform abstraction layer.
"""

from unittest.mock import MagicMock, patch

from argus_overview.utils.screen import ScreenGeometry, get_all_monitors, get_screen_geometry


class TestScreenGeometry:
    """Tests for ScreenGeometry dataclass"""

    def test_screen_geometry_defaults(self):
        """Test ScreenGeometry with default is_primary"""
        geom = ScreenGeometry(0, 0, 1920, 1080)
        assert geom.x == 0
        assert geom.y == 0
        assert geom.width == 1920
        assert geom.height == 1080
        assert geom.is_primary is False

    def test_screen_geometry_with_primary(self):
        """Test ScreenGeometry with is_primary=True"""
        geom = ScreenGeometry(100, 200, 2560, 1440, True)
        assert geom.x == 100
        assert geom.y == 200
        assert geom.width == 2560
        assert geom.height == 1440
        assert geom.is_primary is True


class TestGetScreenGeometry:
    """Tests for get_screen_geometry function (delegates to platform layer)"""

    def test_get_screen_geometry_single_monitor(self):
        """Test with single monitor"""
        with patch("argus_overview.utils.screen.get_screen_manager") as mock_get_sm:
            mock_sm = MagicMock()
            mock_sm.get_screen_geometry.return_value = ScreenGeometry(0, 0, 1920, 1080, True)
            mock_get_sm.return_value = mock_sm

            geom = get_screen_geometry(0)

            assert geom.width == 1920
            assert geom.height == 1080
            assert geom.x == 0
            assert geom.y == 0
            assert geom.is_primary is True
            mock_sm.get_screen_geometry.assert_called_once_with(0)

    def test_get_screen_geometry_second_monitor(self):
        """Test requesting second monitor"""
        with patch("argus_overview.utils.screen.get_screen_manager") as mock_get_sm:
            mock_sm = MagicMock()
            mock_sm.get_screen_geometry.return_value = ScreenGeometry(1920, 0, 2560, 1440, False)
            mock_get_sm.return_value = mock_sm

            geom = get_screen_geometry(1)

            assert geom.width == 2560
            assert geom.height == 1440
            assert geom.x == 1920
            assert geom.is_primary is False
            mock_sm.get_screen_geometry.assert_called_once_with(1)

    def test_get_screen_geometry_default_monitor(self):
        """Test with default monitor index (0)"""
        with patch("argus_overview.utils.screen.get_screen_manager") as mock_get_sm:
            mock_sm = MagicMock()
            mock_sm.get_screen_geometry.return_value = ScreenGeometry(0, 0, 1920, 1080, True)
            mock_get_sm.return_value = mock_sm

            result = get_screen_geometry()

            mock_sm.get_screen_geometry.assert_called_once_with(0)
            assert result is not None

    def test_get_screen_geometry_fallback(self):
        """Test fallback when platform layer returns default"""
        with patch("argus_overview.utils.screen.get_screen_manager") as mock_get_sm:
            mock_sm = MagicMock()
            # Platform layer returns default on failure
            mock_sm.get_screen_geometry.return_value = ScreenGeometry(0, 0, 1920, 1080, True)
            mock_get_sm.return_value = mock_sm

            geom = get_screen_geometry(99)  # High index

            assert geom.width == 1920
            assert geom.height == 1080


class TestGetAllMonitors:
    """Tests for get_all_monitors function (delegates to platform layer)"""

    def test_get_all_monitors_single(self):
        """Test with single monitor"""
        with patch("argus_overview.utils.screen.get_screen_manager") as mock_get_sm:
            mock_sm = MagicMock()
            mock_sm.get_all_monitors.return_value = [ScreenGeometry(0, 0, 1920, 1080, True)]
            mock_get_sm.return_value = mock_sm

            monitors = get_all_monitors()

            assert len(monitors) == 1
            assert monitors[0].width == 1920
            assert monitors[0].height == 1080
            assert monitors[0].is_primary is True

    def test_get_all_monitors_multiple(self):
        """Test with multiple monitors"""
        with patch("argus_overview.utils.screen.get_screen_manager") as mock_get_sm:
            mock_sm = MagicMock()
            mock_sm.get_all_monitors.return_value = [
                ScreenGeometry(0, 0, 1920, 1080, True),
                ScreenGeometry(1920, 0, 2560, 1440, False),
                ScreenGeometry(4480, 0, 3840, 2160, False),
            ]
            mock_get_sm.return_value = mock_sm

            monitors = get_all_monitors()

            assert len(monitors) == 3
            assert monitors[0].width == 1920
            assert monitors[0].is_primary is True
            assert monitors[1].width == 2560
            assert monitors[1].x == 1920
            assert monitors[2].width == 3840
            assert monitors[2].x == 4480

    def test_get_all_monitors_empty_returns_default(self):
        """Test empty list from platform layer (should not happen in practice)"""
        with patch("argus_overview.utils.screen.get_screen_manager") as mock_get_sm:
            mock_sm = MagicMock()
            # Platform layer should always return at least one default
            mock_sm.get_all_monitors.return_value = [ScreenGeometry(0, 0, 1920, 1080, True)]
            mock_get_sm.return_value = mock_sm

            monitors = get_all_monitors()

            assert len(monitors) == 1
            assert monitors[0].width == 1920

    def test_get_all_monitors_vertical_stacking(self):
        """Test monitors stacked vertically"""
        with patch("argus_overview.utils.screen.get_screen_manager") as mock_get_sm:
            mock_sm = MagicMock()
            mock_sm.get_all_monitors.return_value = [
                ScreenGeometry(0, 0, 1920, 1080, True),
                ScreenGeometry(0, 1080, 1920, 1080, False),
            ]
            mock_get_sm.return_value = mock_sm

            monitors = get_all_monitors()

            assert len(monitors) == 2
            assert monitors[0].y == 0
            assert monitors[1].y == 1080
