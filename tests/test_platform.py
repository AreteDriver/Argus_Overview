"""Tests for platform abstraction layer.

v3.0: Tests for cross-platform window management, capture, and screen utilities.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestPlatformDetection:
    """Tests for platform detection and factory functions."""

    def test_is_linux_on_linux(self):
        """Test is_linux returns True on Linux."""
        from argus_overview.platform import is_linux

        with patch.object(sys, "platform", "linux"):
            assert is_linux() is True

    def test_is_linux_on_windows(self):
        """Test is_linux returns False on Windows."""
        from argus_overview.platform import is_linux

        with patch.object(sys, "platform", "win32"):
            assert is_linux() is False

    def test_is_windows_on_windows(self):
        """Test is_windows returns True on Windows."""
        from argus_overview.platform import is_windows

        with patch.object(sys, "platform", "win32"):
            assert is_windows() is True

    def test_is_windows_on_linux(self):
        """Test is_windows returns False on Linux."""
        from argus_overview.platform import is_windows

        with patch.object(sys, "platform", "linux"):
            assert is_windows() is False


class TestBaseClasses:
    """Tests for abstract base classes."""

    def test_screen_geometry_dataclass(self):
        """Test ScreenGeometry dataclass."""
        from argus_overview.platform.base import ScreenGeometry

        geom = ScreenGeometry(100, 200, 1920, 1080, True)
        assert geom.x == 100
        assert geom.y == 200
        assert geom.width == 1920
        assert geom.height == 1080
        assert geom.is_primary is True

    def test_screen_geometry_default_primary(self):
        """Test ScreenGeometry default is_primary."""
        from argus_overview.platform.base import ScreenGeometry

        geom = ScreenGeometry(0, 0, 1920, 1080)
        assert geom.is_primary is False

    def test_window_info_dataclass(self):
        """Test WindowInfo dataclass."""
        from argus_overview.platform.base import WindowInfo

        info = WindowInfo("0x12345", "EVE - CharName", "triuiScreen")
        assert info.window_id == "0x12345"
        assert info.title == "EVE - CharName"
        assert info.class_name == "triuiScreen"

    def test_window_manager_is_abstract(self):
        """Test WindowManager cannot be instantiated directly."""
        from argus_overview.platform.base import WindowManager

        with pytest.raises(TypeError):
            WindowManager()

    def test_window_capture_is_abstract(self):
        """Test WindowCapture cannot be instantiated directly."""
        from argus_overview.platform.base import WindowCapture

        with pytest.raises(TypeError):
            WindowCapture()

    def test_screen_manager_is_abstract(self):
        """Test ScreenManager cannot be instantiated directly."""
        from argus_overview.platform.base import ScreenManager

        with pytest.raises(TypeError):
            ScreenManager()


class TestLinuxWindowManager:
    """Tests for Linux WindowManager implementation."""

    def test_is_valid_window_id_valid_hex(self):
        """Test valid hex window IDs."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()
        assert wm.is_valid_window_id("0x12345") is True
        assert wm.is_valid_window_id("0xABCDEF") is True
        assert wm.is_valid_window_id("0x1") is True

    def test_is_valid_window_id_invalid(self):
        """Test invalid window IDs."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()
        assert wm.is_valid_window_id("") is False
        assert wm.is_valid_window_id(None) is False
        assert wm.is_valid_window_id("12345") is False
        assert wm.is_valid_window_id("0x") is False
        assert wm.is_valid_window_id("not_hex") is False

    def test_get_eve_windows_parses_wmctrl(self):
        """Test get_eve_windows parses wmctrl output correctly."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        wmctrl_output = (
            "0x03800003  0 hostname EVE - CharOne\n"
            "0x03800004  0 hostname EVE - CharTwo\n"
            "0x03800005  0 hostname Firefox\n"
        )

        with patch(
            "argus_overview.platform.linux._get_wmctrl_window_list", return_value=wmctrl_output
        ):
            windows = wm.get_eve_windows()

        assert len(windows) == 2
        assert windows[0] == ("0x03800003", "EVE - CharOne")
        assert windows[1] == ("0x03800004", "EVE - CharTwo")

    def test_get_eve_windows_empty(self):
        """Test get_eve_windows with no EVE windows."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        wmctrl_output = "0x03800005  0 hostname Firefox\n"

        with patch(
            "argus_overview.platform.linux._get_wmctrl_window_list", return_value=wmctrl_output
        ):
            windows = wm.get_eve_windows()

        assert len(windows) == 0

    def test_get_window_list(self):
        """Test get_window_list returns tuples."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            b"0x03800003  0 hostname EVE - CharOne\n0x03800004  0 hostname Firefox\n"
        )

        with patch("argus_overview.platform.linux.run_x11_subprocess", return_value=mock_result):
            windows = wm.get_window_list()

        assert len(windows) == 2
        assert windows[0] == ("0x03800003", "EVE - CharOne")
        assert windows[1] == ("0x03800004", "Firefox")


class TestLinuxScreenManager:
    """Tests for Linux ScreenManager implementation."""

    def test_get_screen_geometry_parses_xrandr(self):
        """Test get_screen_geometry parses xrandr output."""
        from argus_overview.platform.linux import ScreenManagerLinux

        sm = ScreenManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "DP-1 connected primary 1920x1080+0+0\nHDMI-1 connected 2560x1440+1920+0"
        )

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            geom = sm.get_screen_geometry(0)

        assert geom.width == 1920
        assert geom.height == 1080
        assert geom.x == 0
        assert geom.y == 0
        assert geom.is_primary is True

    def test_get_screen_geometry_second_monitor(self):
        """Test get_screen_geometry for second monitor."""
        from argus_overview.platform.linux import ScreenManagerLinux

        sm = ScreenManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "DP-1 connected primary 1920x1080+0+0\nHDMI-1 connected 2560x1440+1920+0"
        )

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            geom = sm.get_screen_geometry(1)

        assert geom.width == 2560
        assert geom.height == 1440
        assert geom.x == 1920
        assert geom.is_primary is False

    def test_get_screen_geometry_fallback(self):
        """Test get_screen_geometry returns default on failure."""
        from argus_overview.platform.linux import ScreenManagerLinux

        sm = ScreenManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            geom = sm.get_screen_geometry(0)

        assert geom.width == 1920
        assert geom.height == 1080

    def test_get_all_monitors(self):
        """Test get_all_monitors returns list."""
        from argus_overview.platform.linux import ScreenManagerLinux

        sm = ScreenManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "DP-1 connected primary 1920x1080+0+0\nHDMI-1 connected 2560x1440+1920+0"
        )

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            monitors = sm.get_all_monitors()

        assert len(monitors) == 2
        assert monitors[0].width == 1920
        assert monitors[1].width == 2560


class TestRunX11Subprocess:
    """Tests for run_x11_subprocess retry logic."""

    def test_success_first_attempt(self):
        """Test successful command on first attempt."""
        from argus_overview.platform.linux import run_x11_subprocess

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch(
            "argus_overview.platform.linux.subprocess.run", return_value=mock_result
        ) as mock_run:
            result = run_x11_subprocess(["echo", "test"], max_attempts=3)

        assert result.returncode == 0
        assert mock_run.call_count == 1

    def test_retry_on_timeout(self):
        """Test retry on TimeoutExpired."""
        import subprocess

        from argus_overview.platform.linux import run_x11_subprocess

        mock_success = MagicMock()
        mock_success.returncode = 0

        with patch("argus_overview.platform.linux.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.TimeoutExpired("cmd", 2),
                mock_success,
            ]

            result = run_x11_subprocess(["echo", "test"], max_attempts=3, backoff=0.01)

        assert result.returncode == 0
        assert mock_run.call_count == 2

    def test_max_retries_exceeded(self):
        """Test raises exception after max retries."""
        import subprocess

        from argus_overview.platform.linux import run_x11_subprocess

        with patch("argus_overview.platform.linux.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.TimeoutExpired("cmd", 2),
                subprocess.TimeoutExpired("cmd", 2),
                subprocess.TimeoutExpired("cmd", 2),
            ]

            with pytest.raises(subprocess.TimeoutExpired):
                run_x11_subprocess(["echo", "test"], max_attempts=3, backoff=0.01)

        assert mock_run.call_count == 3


class TestFactoryFunctions:
    """Tests for platform factory functions."""

    def test_get_window_manager_returns_linux_on_linux(self):
        """Test get_window_manager returns Linux implementation."""
        from argus_overview.platform import get_window_manager
        from argus_overview.platform.linux import WindowManagerLinux

        with patch("argus_overview.platform.is_linux", return_value=True):
            wm = get_window_manager()
            assert isinstance(wm, WindowManagerLinux)

    def test_get_screen_manager_returns_linux_on_linux(self):
        """Test get_screen_manager returns Linux implementation."""
        from argus_overview.platform import get_screen_manager
        from argus_overview.platform.linux import ScreenManagerLinux

        with patch("argus_overview.platform.is_linux", return_value=True):
            sm = get_screen_manager()
            assert isinstance(sm, ScreenManagerLinux)

    def test_get_window_capture_returns_linux_on_linux(self):
        """Test get_window_capture returns Linux implementation."""
        from argus_overview.platform import get_window_capture
        from argus_overview.platform.linux import WindowCaptureLinux

        with patch("argus_overview.platform.is_linux", return_value=True):
            wc = get_window_capture()
            assert isinstance(wc, WindowCaptureLinux)
