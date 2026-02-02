"""Tests for platform abstraction layer.

v3.0: Tests for cross-platform window management, capture, and screen utilities.
"""

import subprocess
import sys
from pathlib import Path
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


class TestWmctrlCache:
    """Tests for wmctrl caching."""

    def test_cache_hit(self):
        """Test cache returns cached value within TTL."""
        from argus_overview.platform.linux import _clear_wmctrl_cache, _get_wmctrl_window_list

        _clear_wmctrl_cache()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "0x123 0 host Window1\n"

        with patch(
            "argus_overview.platform.linux.subprocess.run", return_value=mock_result
        ) as mock_run:
            result1 = _get_wmctrl_window_list()
            result2 = _get_wmctrl_window_list()

            assert result1 == result2
            assert mock_run.call_count == 1  # Only called once due to cache

    def test_cache_cleared(self):
        """Test clearing cache."""
        from argus_overview.platform.linux import (
            _clear_wmctrl_cache,
            _wmctrl_cache,
        )

        _wmctrl_cache["result"] = "cached"
        _wmctrl_cache["timestamp"] = 999999999999.0

        _clear_wmctrl_cache()

        assert _wmctrl_cache["result"] is None
        assert _wmctrl_cache["timestamp"] == 0.0

    def test_cache_timeout_returns_cached(self):
        """Test cache returns old value on subprocess failure."""
        from argus_overview.platform.linux import _clear_wmctrl_cache, _get_wmctrl_window_list

        _clear_wmctrl_cache()

        # First call succeeds
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "cached_value"

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            _get_wmctrl_window_list()

        # Force cache expiry and simulate failure
        from argus_overview.platform.linux import _wmctrl_cache

        _wmctrl_cache["timestamp"] = 0  # Force expiry

        with patch(
            "argus_overview.platform.linux.subprocess.run",
            side_effect=subprocess.TimeoutExpired("wmctrl", 2),
        ):
            result = _get_wmctrl_window_list()

        assert result == "cached_value"


class TestWindowManagerLinuxMoveWindow:
    """Tests for WindowManagerLinux.move_window."""

    def test_move_window_sync_timeout_fallback(self):
        """Test move_window falls back when --sync times out."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        call_count = 0

        def mock_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if "--sync" in cmd:
                raise subprocess.TimeoutExpired(" ".join(cmd), 2)
            result = MagicMock()
            result.returncode = 0
            return result

        with patch("argus_overview.platform.linux.subprocess.run", side_effect=mock_run):
            result = wm.move_window("0x12345", 100, 200, 800, 600, timeout=0.1)

        assert result is True
        assert call_count >= 2  # At least one retry

    def test_move_window_invalid_id(self):
        """Test move_window rejects invalid window ID."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()
        result = wm.move_window("invalid", 0, 0, 100, 100)
        assert result is False

    def test_move_window_complete_failure(self):
        """Test move_window returns False on complete failure."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        with patch(
            "argus_overview.platform.linux.subprocess.run",
            side_effect=subprocess.TimeoutExpired("cmd", 2),
        ):
            result = wm.move_window("0x12345", 0, 0, 100, 100, timeout=0.01)

        assert result is False


class TestWindowManagerLinuxFocusedWindow:
    """Tests for WindowManagerLinux.get_focused_window."""

    def test_decimal_to_hex_conversion(self):
        """Test decimal window ID is converted to hex."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"12345678"  # Decimal

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            result = wm.get_focused_window()

        assert result == "0xbc614e"  # hex(12345678)

    def test_already_hex_window_id(self):
        """Test hex window ID is validated."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"0x12345"  # Already hex

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            result = wm.get_focused_window()

        assert result == "0x12345"

    def test_invalid_window_id_returns_none(self):
        """Test invalid output returns None."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"not_a_number"

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            result = wm.get_focused_window()

        assert result is None

    def test_failure_returns_none(self):
        """Test failure returns None."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        with patch(
            "argus_overview.platform.linux.subprocess.run",
            side_effect=subprocess.TimeoutExpired("cmd", 2),
        ):
            result = wm.get_focused_window()

        assert result is None


class TestWindowManagerLinuxGetWindowTitle:
    """Tests for WindowManagerLinux.get_window_title."""

    def test_get_window_title_success(self):
        """Test getting window title."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"EVE - CharName\n"

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            result = wm.get_window_title("0x12345")

        assert result == "EVE - CharName"

    def test_get_window_title_failure(self):
        """Test getting window title on failure returns Unknown."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        with patch(
            "argus_overview.platform.linux.subprocess.run",
            side_effect=subprocess.TimeoutExpired("cmd", 2),
        ):
            result = wm.get_window_title("0x12345")

        assert result == "Unknown"


class TestWindowCaptureLinux:
    """Tests for WindowCaptureLinux."""

    def test_running_property(self):
        """Test running property reflects state."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        assert capture.running is False

        capture._stop_event.clear()
        assert capture.running is True

        capture._stop_event.set()
        assert capture.running is False

    def test_capture_window_async_invalid_id(self):
        """Test async capture rejects invalid window ID."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        result = capture.capture_window_async("invalid")
        assert result == ""

    def test_capture_window_async_valid_id(self):
        """Test async capture returns request ID."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        result = capture.capture_window_async("0x12345")
        assert result != ""
        assert len(result) > 0

    def test_capture_window_sync_failure(self):
        """Test sync capture returns None on failure."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        with patch(
            "argus_overview.platform.linux.subprocess.run",
            side_effect=subprocess.TimeoutExpired("cmd", 2),
        ):
            result = capture.capture_window_sync("0x12345")

        assert result is None

    def test_capture_window_sync_nonzero_returncode(self):
        """Test sync capture returns None on non-zero returncode."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b""

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            result = capture.capture_window_sync("0x12345")

        assert result is None

    def test_get_result_empty_queue(self):
        """Test get_result returns None when queue empty."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        result = capture.get_result(timeout=0.01)
        assert result is None


class TestEVEPathResolverLinux:
    """Tests for EVEPathResolverLinux."""

    def test_get_eve_settings_paths(self):
        """Test EVE settings paths are returned."""
        from argus_overview.platform.linux import EVEPathResolverLinux

        resolver = EVEPathResolverLinux()
        paths = resolver.get_eve_settings_paths()

        assert len(paths) > 0
        assert all(isinstance(p, Path) for p in paths)
        # Should include Steam paths
        steam_path_found = any("steamapps" in str(p) for p in paths)
        assert steam_path_found

    def test_get_eve_logs_paths(self):
        """Test EVE logs paths are returned."""
        from argus_overview.platform.linux import EVEPathResolverLinux

        resolver = EVEPathResolverLinux()
        paths = resolver.get_eve_logs_paths()

        assert len(paths) > 0
        assert all(isinstance(p, Path) for p in paths)
        assert all("Gamelogs" in str(p) for p in paths)

    def test_get_config_directory(self):
        """Test config directory path."""
        from argus_overview.platform.linux import EVEPathResolverLinux

        resolver = EVEPathResolverLinux()
        config_dir = resolver.get_config_directory()

        assert config_dir == Path.home() / ".config" / "argus-overview"


class TestHotkeyHelperLinux:
    """Tests for HotkeyHelperLinux."""

    def test_normalize_combo_modifier_keys(self):
        """Test modifier keys keep angle brackets."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()

        assert helper.normalize_combo("<ctrl>+a") == "<ctrl>+a"
        assert helper.normalize_combo("<alt>+b") == "<alt>+b"
        assert helper.normalize_combo("<shift>+c") == "<shift>+c"

    def test_normalize_combo_single_char_brackets(self):
        """Test single char brackets are removed."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()

        assert helper.normalize_combo("<ctrl>+<v>") == "<ctrl>+v"
        assert helper.normalize_combo("<alt>+<R>") == "<alt>+r"

    def test_normalize_combo_special_keys_kept(self):
        """Test special keys keep brackets."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()

        assert helper.normalize_combo("<ctrl>+<space>") == "<ctrl>+<space>"
        assert helper.normalize_combo("<alt>+<enter>") == "<alt>+<enter>"

    def test_normalize_combo_empty(self):
        """Test empty combo returns empty."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()
        assert helper.normalize_combo("") == ""

    def test_normalize_combo_uppercase_modifiers(self):
        """Test uppercase modifiers are lowercased."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()
        assert helper.normalize_combo("<CTRL>+a") == "<ctrl>+a"

    def test_is_single_key_true(self):
        """Test is_single_key returns True for single keys."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()

        assert helper.is_single_key("a") is True
        assert helper.is_single_key("<space>") is True
        assert helper.is_single_key("F1") is True

    def test_is_single_key_false(self):
        """Test is_single_key returns False for combos."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()

        assert helper.is_single_key("<ctrl>+a") is False
        assert helper.is_single_key("a+b") is False

    def test_is_single_key_empty(self):
        """Test is_single_key returns False for empty."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()
        assert helper.is_single_key("") is False


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

    def test_get_platform_name_macos(self):
        """Test get_platform_name returns macos on darwin."""
        from argus_overview.platform import get_platform_name

        with patch.object(sys, "platform", "darwin"):
            assert get_platform_name() == "macos"

    def test_get_platform_name_unknown(self):
        """Test get_platform_name returns unknown on unsupported platform."""
        from argus_overview.platform import get_platform_name

        with patch.object(sys, "platform", "freebsd"):
            assert get_platform_name() == "unknown"

    def test_get_window_manager_unsupported_platform(self):
        """Test get_window_manager raises on unsupported platform."""
        from argus_overview.platform import get_window_manager

        with patch("argus_overview.platform.get_platform_name", return_value="unknown"):
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                get_window_manager()

    def test_get_window_capture_unsupported_platform(self):
        """Test get_window_capture raises on unsupported platform."""
        from argus_overview.platform import get_window_capture

        with patch("argus_overview.platform.get_platform_name", return_value="unknown"):
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                get_window_capture()

    def test_get_screen_manager_unsupported_platform(self):
        """Test get_screen_manager raises on unsupported platform."""
        from argus_overview.platform import get_screen_manager

        with patch("argus_overview.platform.get_platform_name", return_value="unknown"):
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                get_screen_manager()

    def test_get_eve_path_resolver_linux(self):
        """Test get_eve_path_resolver returns Linux implementation."""
        from argus_overview.platform import get_eve_path_resolver
        from argus_overview.platform.linux import EVEPathResolverLinux

        with patch("argus_overview.platform.get_platform_name", return_value="linux"):
            resolver = get_eve_path_resolver()
            assert isinstance(resolver, EVEPathResolverLinux)

    def test_get_eve_path_resolver_unsupported_platform(self):
        """Test get_eve_path_resolver raises on unsupported platform."""
        from argus_overview.platform import get_eve_path_resolver

        with patch("argus_overview.platform.get_platform_name", return_value="unknown"):
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                get_eve_path_resolver()

    def test_get_hotkey_helper_linux(self):
        """Test get_hotkey_helper returns Linux implementation."""
        from argus_overview.platform import get_hotkey_helper
        from argus_overview.platform.linux import HotkeyHelperLinux

        with patch("argus_overview.platform.get_platform_name", return_value="linux"):
            helper = get_hotkey_helper()
            assert isinstance(helper, HotkeyHelperLinux)

    def test_get_hotkey_helper_unsupported_platform(self):
        """Test get_hotkey_helper raises on unsupported platform."""
        from argus_overview.platform import get_hotkey_helper

        with patch("argus_overview.platform.get_platform_name", return_value="unknown"):
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                get_hotkey_helper()
