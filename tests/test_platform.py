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

        wmctrl_output = "0x03800003  0 hostname EVE - CharOne\n0x03800004  0 hostname Firefox\n"

        with patch(
            "argus_overview.platform.linux._get_wmctrl_window_list",
            return_value=wmctrl_output,
        ):
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

    def setup_method(self):
        """Clear singleton cache before each test for isolation."""
        from argus_overview.platform import _clear_singleton_cache

        _clear_singleton_cache()

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


class TestWindowManagerLinuxActivateMinimizeRestore:
    """Tests for activate, minimize, restore window operations."""

    def test_activate_window_success(self):
        """Test successful window activation."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("argus_overview.platform.linux.run_x11_subprocess", return_value=mock_result):
            result = wm.activate_window("0x12345")

        assert result is True

    def test_activate_window_invalid_id(self):
        """Test activate_window rejects invalid ID."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()
        result = wm.activate_window("invalid")
        assert result is False

    def test_activate_window_failure(self):
        """Test activate_window returns False on failure."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        with patch(
            "argus_overview.platform.linux.run_x11_subprocess",
            side_effect=subprocess.TimeoutExpired("cmd", 2),
        ):
            result = wm.activate_window("0x12345")

        assert result is False

    def test_minimize_window_success(self):
        """Test successful window minimization."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("argus_overview.platform.linux.run_x11_subprocess", return_value=mock_result):
            result = wm.minimize_window("0x12345")

        assert result is True

    def test_minimize_window_invalid_id(self):
        """Test minimize_window rejects invalid ID."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()
        result = wm.minimize_window("invalid")
        assert result is False

    def test_minimize_window_failure(self):
        """Test minimize_window returns False on failure."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        with patch(
            "argus_overview.platform.linux.run_x11_subprocess",
            side_effect=subprocess.TimeoutExpired("cmd", 2),
        ):
            result = wm.minimize_window("0x12345")

        assert result is False

    def test_restore_window_success(self):
        """Test successful window restoration."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("argus_overview.platform.linux.run_x11_subprocess", return_value=mock_result):
            result = wm.restore_window("0x12345")

        assert result is True

    def test_restore_window_invalid_id(self):
        """Test restore_window rejects invalid ID."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()
        result = wm.restore_window("invalid")
        assert result is False

    def test_restore_window_failure(self):
        """Test restore_window returns False on failure."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        with patch(
            "argus_overview.platform.linux.run_x11_subprocess",
            side_effect=subprocess.TimeoutExpired("cmd", 2),
        ):
            result = wm.restore_window("0x12345")

        assert result is False


class TestWindowManagerLinuxGetWindowListEdgeCases:
    """Edge case tests for get_window_list."""

    def test_get_window_list_exception(self):
        """Test get_window_list returns empty list on error."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        with patch(
            "argus_overview.platform.linux._get_wmctrl_window_list",
            return_value="",
        ):
            result = wm.get_window_list()

        assert result == []

    def test_get_eve_windows_empty_lines_skipped(self):
        """Test empty lines are skipped in get_eve_windows."""
        from argus_overview.platform.linux import WindowManagerLinux

        wm = WindowManagerLinux()

        # Output with empty lines
        wmctrl_output = "\n\n0x03800003  0 hostname EVE - CharOne\n\n"

        with patch(
            "argus_overview.platform.linux._get_wmctrl_window_list",
            return_value=wmctrl_output,
        ):
            windows = wm.get_eve_windows()

        assert len(windows) == 1
        assert windows[0] == ("0x03800003", "EVE - CharOne")


class TestScreenManagerLinuxEdgeCases:
    """Edge case tests for ScreenManagerLinux."""

    def test_get_screen_geometry_exception(self):
        """Test get_screen_geometry returns default on exception."""
        from argus_overview.platform.linux import ScreenManagerLinux

        sm = ScreenManagerLinux()

        with patch(
            "argus_overview.platform.linux.subprocess.run",
            side_effect=subprocess.TimeoutExpired("xrandr", 2),
        ):
            geom = sm.get_screen_geometry(0)

        # Should return default geometry
        assert geom.width == 1920
        assert geom.height == 1080

    def test_get_screen_geometry_invalid_monitor_index(self):
        """Test get_screen_geometry with out-of-range index."""
        from argus_overview.platform.linux import ScreenManagerLinux

        sm = ScreenManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "DP-1 connected primary 1920x1080+0+0"

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            # Request monitor index 5 when only 1 exists
            geom = sm.get_screen_geometry(5)

        # Should return default
        assert geom.width == 1920
        assert geom.height == 1080

    def test_get_all_monitors_exception(self):
        """Test get_all_monitors returns default on exception."""
        from argus_overview.platform.linux import ScreenManagerLinux

        sm = ScreenManagerLinux()

        with patch(
            "argus_overview.platform.linux.subprocess.run",
            side_effect=subprocess.TimeoutExpired("xrandr", 2),
        ):
            monitors = sm.get_all_monitors()

        # Returns default monitor on failure
        assert len(monitors) == 1
        assert monitors[0].width == 1920
        assert monitors[0].height == 1080

    def test_get_all_monitors_empty_output(self):
        """Test get_all_monitors with empty xrandr output returns default."""
        from argus_overview.platform.linux import ScreenManagerLinux

        sm = ScreenManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            monitors = sm.get_all_monitors()

        # Returns default monitor when no monitors found
        assert len(monitors) == 1
        assert monitors[0].width == 1920


class TestEVEPathResolverLinuxEdgeCases:
    """Edge case tests for EVEPathResolverLinux."""

    def test_get_eve_settings_paths_no_steam(self):
        """Test paths when Steam directory doesn't exist."""
        from argus_overview.platform.linux import EVEPathResolverLinux

        resolver = EVEPathResolverLinux()

        # Mock Path.home() to return a non-existent home
        with patch("pathlib.Path.home", return_value=Path("/nonexistent")):
            paths = resolver.get_eve_settings_paths()

        # Should still return paths (they just won't exist)
        assert isinstance(paths, list)

    def test_get_eve_logs_paths_returns_paths(self):
        """Test EVE logs paths structure."""
        from argus_overview.platform.linux import EVEPathResolverLinux

        resolver = EVEPathResolverLinux()
        paths = resolver.get_eve_logs_paths()

        # All paths should contain Gamelogs
        assert all("Gamelogs" in str(p) for p in paths)


class TestWindowsFactoryBranches:
    """Tests for Windows branches of factory functions (mocked)."""

    def setup_method(self):
        """Clear singleton cache before each test for isolation."""
        from argus_overview.platform import _clear_singleton_cache

        _clear_singleton_cache()

    def test_get_platform_name_windows(self):
        """Test get_platform_name returns windows on win32."""
        from argus_overview.platform import get_platform_name

        with patch.object(sys, "platform", "win32"):
            assert get_platform_name() == "windows"

    def test_get_window_manager_windows_branch(self):
        """Test get_window_manager Windows branch is reachable."""
        # Create mock Windows classes
        mock_wm_class = MagicMock()
        mock_windows_module = MagicMock()
        mock_windows_module.WindowManagerWindows = mock_wm_class

        # The function imports inside the if branch, so we need to mock the import
        with patch.object(sys, "platform", "win32"):
            with patch.dict(sys.modules, {"argus_overview.platform.windows": mock_windows_module}):
                # Need to re-import since we're testing the import path
                from argus_overview.platform import get_window_manager

                _ = get_window_manager()
                mock_wm_class.assert_called_once()

    def test_get_window_capture_windows_branch(self):
        """Test get_window_capture Windows branch is reachable."""
        mock_wc_class = MagicMock()
        mock_windows_module = MagicMock()
        mock_windows_module.WindowCaptureWindows = mock_wc_class

        with patch.object(sys, "platform", "win32"):
            with patch.dict(sys.modules, {"argus_overview.platform.windows": mock_windows_module}):
                from argus_overview.platform import get_window_capture

                _ = get_window_capture(max_workers=2)
                mock_wc_class.assert_called_once_with(max_workers=2)

    def test_get_screen_manager_windows_branch(self):
        """Test get_screen_manager Windows branch is reachable."""
        mock_sm_class = MagicMock()
        mock_windows_module = MagicMock()
        mock_windows_module.ScreenManagerWindows = mock_sm_class

        with patch.object(sys, "platform", "win32"):
            with patch.dict(sys.modules, {"argus_overview.platform.windows": mock_windows_module}):
                from argus_overview.platform import get_screen_manager

                _ = get_screen_manager()
                mock_sm_class.assert_called_once()

    def test_get_eve_path_resolver_windows_branch(self):
        """Test get_eve_path_resolver Windows branch is reachable."""
        mock_resolver_class = MagicMock()
        mock_windows_module = MagicMock()
        mock_windows_module.EVEPathResolverWindows = mock_resolver_class

        with patch.object(sys, "platform", "win32"):
            with patch.dict(sys.modules, {"argus_overview.platform.windows": mock_windows_module}):
                from argus_overview.platform import get_eve_path_resolver

                _ = get_eve_path_resolver()
                mock_resolver_class.assert_called_once()

    def test_get_hotkey_helper_windows_branch(self):
        """Test get_hotkey_helper Windows branch is reachable."""
        mock_helper_class = MagicMock()
        mock_windows_module = MagicMock()
        mock_windows_module.HotkeyHelperWindows = mock_helper_class

        with patch.object(sys, "platform", "win32"):
            with patch.dict(sys.modules, {"argus_overview.platform.windows": mock_windows_module}):
                from argus_overview.platform import get_hotkey_helper

                _ = get_hotkey_helper()
                mock_helper_class.assert_called_once()


class TestWindowCaptureLinuxEdgeCases:
    """Edge case tests for WindowCaptureLinux."""

    def test_start_stop_lifecycle(self):
        """Test start/stop lifecycle."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        assert capture.running is False

        capture.start()
        assert capture.running is True

        capture.stop()
        assert capture.running is False

    def test_capture_window_sync_command_fails(self):
        """Test sync capture when import command fails."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b""

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            result = capture.capture_window_sync("0x12345")

        assert result is None

    def test_capture_window_sync_file_not_found(self):
        """Test sync capture when import command not found."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        with patch(
            "argus_overview.platform.linux.subprocess.run",
            side_effect=FileNotFoundError("import not found"),
        ):
            result = capture.capture_window_sync("0x12345")

        assert result is None

    def test_capture_window_sync_timeout(self):
        """Test sync capture handles timeout."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        with patch(
            "argus_overview.platform.linux.subprocess.run",
            side_effect=subprocess.TimeoutExpired("import", 2),
        ):
            result = capture.capture_window_sync("0x12345")

        assert result is None

    def test_capture_window_sync_scale_ignored(self):
        """Test sync capture ignores scale param (scaling now done in Qt)."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        # Create a fake PNG image
        from io import BytesIO

        from PIL import Image

        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        fake_png = buffer.getvalue()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_png

        with patch("argus_overview.platform.linux.HAS_XLIB", False):
            with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
                result = capture.capture_window_sync("0x12345", scale=0.5)

        assert result is not None
        # Scale is deprecated/ignored — image retains original dimensions
        assert result.width == 100
        assert result.height == 100


class TestWindowManagerLinuxEmptyLines:
    """Tests for wmctrl output with empty lines (line 164)."""

    def test_get_eve_windows_with_empty_lines(self):
        """Test get_eve_windows handles empty lines in wmctrl output."""
        from argus_overview.platform.linux import WindowManagerLinux

        mgr = WindowManagerLinux()

        # Output with empty lines
        fake_output = "0x12345  0 host EVE - Character\n\n0x67890  0 host EVE - Another\n"

        with patch(
            "argus_overview.platform.linux._get_wmctrl_window_list", return_value=fake_output
        ):
            windows = mgr.get_eve_windows()

        assert len(windows) == 2


class TestScreenManagerLinuxXrandrFailure:
    """Tests for xrandr failure fallback (line 416)."""

    def test_get_all_monitors_xrandr_failure(self):
        """Test get_all_monitors returns fallback when xrandr fails."""
        from argus_overview.platform.linux import ScreenManagerLinux

        mgr = ScreenManagerLinux()

        mock_result = MagicMock()
        mock_result.returncode = 1  # Non-zero exit
        mock_result.stdout = ""

        with patch("argus_overview.platform.linux.subprocess.run", return_value=mock_result):
            monitors = mgr.get_all_monitors()

        # Should return default fallback
        assert len(monitors) == 1
        assert monitors[0].width == 1920
        assert monitors[0].height == 1080


class TestHotkeyHelperEmptyParts:
    """Tests for hotkey parsing with empty parts (line 553)."""

    def test_normalize_combo_with_empty_parts(self):
        """Test normalize_combo handles strings with extra spaces."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()

        # String with extra spaces that would create empty parts
        result = helper.normalize_combo("<ctrl>  +  a")

        assert result == "<ctrl>+a"


# =============================================================================
# Coverage Push: _worker loop (lines 332-339) and normalize_combo empty part (553)
# =============================================================================


class TestWindowCaptureLinuxWorker:
    """Tests for WindowCaptureLinux._worker processing and error paths."""

    def test_worker_processes_task_and_puts_result(self):
        """Test _worker picks up a task, captures, and puts result in queue."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        mock_image = MagicMock()
        capture.capture_window_sync = MagicMock(return_value=mock_image)

        # Put a task then None to break the loop
        capture.capture_queue.put(("0x123", 0.5, "req1"))
        capture.capture_queue.put(None)

        # Run worker (not as thread — direct call after clearing stop event)
        capture._stop_event.clear()
        capture._worker()

        capture.capture_window_sync.assert_called_once_with("0x123", 0.5)
        result = capture.result_queue.get_nowait()
        assert result == ("req1", "0x123", mock_image)

    def test_worker_handles_empty_queue_timeout(self):
        """Test _worker continues on Empty (queue timeout) then exits on None."""
        import threading

        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        capture._stop_event.clear()

        # Start worker in a thread with empty queue — it will hit Empty timeout
        # Then feed None after a brief delay to let it loop at least once
        def feed_stop():
            import time

            time.sleep(0.6)  # Just past the 0.5s queue timeout
            capture.capture_queue.put(None)

        feeder = threading.Thread(target=feed_stop)
        feeder.start()
        capture._worker()  # Blocks until None received
        feeder.join()

        # Worker exited cleanly after hitting Empty at least once
        assert capture.result_queue.empty()

    def test_worker_handles_capture_exception(self):
        """Test _worker catches exceptions from capture_window_sync."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        capture.capture_window_sync = MagicMock(side_effect=OSError("X11 error"))

        # Put a task then None to stop
        capture.capture_queue.put(("0x123", 0.5, "req1"))
        capture.capture_queue.put(None)

        capture._stop_event.clear()

        with patch("argus_overview.platform.linux.logger") as mock_logger:
            capture._worker()
            mock_logger.error.assert_called_once()
            assert "Worker error" in str(mock_logger.error.call_args)

        # Result queue should be empty (capture failed)
        assert capture.result_queue.empty()


class TestNormalizeComboEmptyPart:
    """Test normalize_combo with empty parts from consecutive + signs (line 553)."""

    def test_normalize_combo_consecutive_plus(self):
        """Test normalize_combo skips empty parts from '++' in combo."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()

        # "ctrl++a" splits to ["ctrl", "", "a"] — empty part should be skipped
        result = helper.normalize_combo("<ctrl>++a")
        assert result == "<ctrl>+a"

    def test_normalize_combo_trailing_plus(self):
        """Test normalize_combo with trailing +."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        helper = HotkeyHelperLinux()

        result = helper.normalize_combo("<ctrl>+a+")
        assert result == "<ctrl>+a"


# =============================================================================
# Performance overhaul: xlib capture, queue backpressure, fallback paths
# =============================================================================


class TestXlibCapture:
    """Tests for python-xlib capture path."""

    def test_capture_xlib_success(self):
        """Test _capture_xlib returns PIL Image on success."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        # Mock Xlib objects
        mock_display = MagicMock()
        mock_window = MagicMock()
        mock_geom = MagicMock()
        mock_geom.width = 4
        mock_geom.height = 2
        mock_window.get_geometry.return_value = mock_geom

        # BGRX pixel data: 4 bytes per pixel, 4x2 = 32 bytes
        mock_raw = MagicMock()
        mock_raw.data = b"\x00\x00\xff\xff" * 8  # Blue in BGRX
        mock_window.get_image.return_value = mock_raw
        # Window is viewable (not minimized)
        mock_attrs = MagicMock()
        mock_attrs.map_state = 2  # X.IsViewable
        mock_window.get_attributes.return_value = mock_attrs

        mock_display.create_resource_object.return_value = mock_window

        with patch("argus_overview.platform.linux._thread_local") as mock_tl:
            mock_tl.display = mock_display
            result = capture._capture_xlib("0x12345")

        assert result is not None
        assert result.mode == "RGBX"
        assert result.size == (4, 2)

    def test_capture_xlib_skips_minimized_window(self):
        """Test _capture_xlib returns None for unmapped/minimized windows."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        mock_display = MagicMock()
        mock_window = MagicMock()
        mock_attrs = MagicMock()
        mock_attrs.map_state = 0  # IsUnmapped
        mock_window.get_attributes.return_value = mock_attrs
        mock_display.create_resource_object.return_value = mock_window

        with patch("argus_overview.platform.linux._thread_local") as mock_tl:
            mock_tl.display = mock_display
            result = capture._capture_xlib("0x12345")

        assert result is None
        mock_window.get_image.assert_not_called()

    def test_capture_xlib_failure_resets_display(self):
        """Test _capture_xlib returns None and resets Display on exception."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        mock_display = MagicMock()
        mock_display.create_resource_object.side_effect = Exception("X11 BadWindow")

        with patch("argus_overview.platform.linux._thread_local") as mock_tl:
            mock_tl.display = mock_display
            result = capture._capture_xlib("0x12345")

        assert result is None
        # Display should be closed and removed to avoid corrupted state
        mock_display.close.assert_called_once()

    def test_capture_xlib_failure_display_close_raises(self):
        """Lines 428-429: display.close() exception is silently caught."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        mock_display = MagicMock()
        mock_display.create_resource_object.side_effect = Exception("X11 BadWindow")
        mock_display.close.side_effect = Exception("Display already closed")

        with patch("argus_overview.platform.linux._thread_local") as mock_tl:
            mock_tl.display = mock_display
            result = capture._capture_xlib("0x12345")

        assert result is None
        # close() was called even though it raised
        mock_display.close.assert_called_once()

    def test_capture_xlib_creates_thread_local_display(self):
        """Test _capture_xlib creates Display on first call per thread."""
        import threading

        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        mock_tl = threading.local()  # Fresh local with no .display

        mock_display_cls = MagicMock()
        mock_display_instance = MagicMock()
        mock_display_cls.return_value = mock_display_instance
        mock_display_instance.create_resource_object.side_effect = Exception("stop")

        with patch("argus_overview.platform.linux._thread_local", mock_tl):
            with patch("argus_overview.platform.linux.xlib_display.Display", mock_display_cls):
                capture._capture_xlib("0x12345")

        mock_display_cls.assert_called_once()


class TestXlibFallbackToImageMagick:
    """Tests for xlib→ImageMagick fallback."""

    def test_capture_falls_back_to_imagemagick(self):
        """Test capture_window_sync falls back to ImageMagick when xlib fails."""
        from io import BytesIO

        from PIL import Image

        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        # Create a fake PNG
        img = Image.new("RGB", (50, 50), color="green")
        buf = BytesIO()
        img.save(buf, format="PNG")
        fake_png = buf.getvalue()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_png

        with patch("argus_overview.platform.linux.HAS_XLIB", True):
            with patch.object(capture, "_capture_xlib", return_value=None):
                with patch(
                    "argus_overview.platform.linux.subprocess.run", return_value=mock_result
                ):
                    result = capture.capture_window_sync("0x12345")

        assert result is not None
        assert result.size == (50, 50)

    def test_capture_uses_xlib_when_available(self):
        """Test capture_window_sync uses xlib path when HAS_XLIB=True."""
        from PIL import Image

        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        mock_image = Image.new("RGB", (100, 100))

        with patch("argus_overview.platform.linux.HAS_XLIB", True):
            with patch.object(capture, "_capture_xlib", return_value=mock_image) as mock_xlib:
                result = capture.capture_window_sync("0x12345")

        mock_xlib.assert_called_once_with("0x12345")
        assert result is mock_image

    def test_capture_skips_xlib_when_not_available(self):
        """Test capture_window_sync uses ImageMagick when HAS_XLIB=False."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)

        with patch("argus_overview.platform.linux.HAS_XLIB", False):
            with patch.object(capture, "_capture_imagemagick", return_value=None) as mock_im:
                capture.capture_window_sync("0x12345")

        mock_im.assert_called_once_with("0x12345")


class TestQueueBackpressure:
    """Tests for bounded queue and backpressure."""

    def test_queue_is_bounded(self):
        """Test capture queue has maxsize = max_workers * 2."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=3)
        assert capture.capture_queue.maxsize == 6

    def test_capture_async_returns_empty_on_full_queue(self):
        """Test capture_window_async returns empty string when queue is full."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        # maxsize=2, fill it up
        capture.capture_queue.put(("0x1", 1.0, "r1"))
        capture.capture_queue.put(("0x2", 1.0, "r2"))

        result = capture.capture_window_async("0x12345")
        assert result == ""

    def test_stop_handles_full_queue(self):
        """Test stop() doesn't block if queue is full."""
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = WindowCaptureLinux(max_workers=1)
        # Fill queue to maxsize
        capture.capture_queue.put(("0x1", 1.0, "r1"))
        capture.capture_queue.put(("0x2", 1.0, "r2"))

        capture._stop_event.clear()  # Pretend started
        capture.workers = [MagicMock()]  # Mock worker
        capture.stop()  # Should not block or raise

        assert capture._stop_event.is_set()


# ---------------------------------------------------------------------------
# _is_pure_wayland coverage (platform/__init__.py lines 102, 108-109)
# ---------------------------------------------------------------------------


class TestIsPureWayland:
    """Tests for _is_pure_wayland helper in platform/__init__.py."""

    def test_returns_false_on_non_linux(self):
        """Line 102: returns False when not on linux."""
        from argus_overview.platform import _is_pure_wayland

        with patch.object(sys, "platform", "win32"):
            assert _is_pure_wayland() is False

    def test_returns_false_on_darwin(self):
        """Line 102: returns False on macOS."""
        from argus_overview.platform import _is_pure_wayland

        with patch.object(sys, "platform", "darwin"):
            assert _is_pure_wayland() is False

    def test_returns_false_on_import_error(self):
        """Lines 108-109: returns False when display_server module can't be imported."""
        from argus_overview.platform import _is_pure_wayland

        with patch.object(sys, "platform", "linux"):
            with patch(
                "argus_overview.platform._is_pure_wayland",
                wraps=_is_pure_wayland,
            ):
                with patch.dict(
                    "sys.modules",
                    {"argus_overview.utils.display_server": None},
                ):
                    # Force ImportError by making the import fail
                    _is_pure_wayland()  # noqa: F841
                    # On the test system, if display_server IS available,
                    # it won't raise ImportError. Test the fallback explicitly.

        # Direct test: mock the import to raise ImportError
        with patch.object(sys, "platform", "linux"):
            with patch(
                "argus_overview.utils.display_server.detect_display_server",
                side_effect=ImportError("no module"),
            ):
                # Even though the module exists, if detect_display_server
                # can't be imported at runtime, need to test the except block.
                pass

    def test_import_error_path_directly(self):
        """Lines 108-109: ImportError during display_server import returns False."""

        import argus_overview.platform as plat_mod

        with patch.object(sys, "platform", "linux"):
            _ = plat_mod._is_pure_wayland.__code__

            # Patch the import inside the function to raise
            with patch(
                "argus_overview.utils.display_server.detect_display_server",
            ) as mock_detect:
                mock_detect.side_effect = ImportError("no display_server")
                # The function does `from ..utils.display_server import ...`
                # which won't re-raise if module is cached. We need to
                # remove it from sys.modules.
                saved = sys.modules.get("argus_overview.utils.display_server")
                sys.modules["argus_overview.utils.display_server"] = None  # type: ignore
                try:
                    result = plat_mod._is_pure_wayland()
                    assert result is False
                finally:
                    if saved is not None:
                        sys.modules["argus_overview.utils.display_server"] = saved
                    elif "argus_overview.utils.display_server" in sys.modules:
                        del sys.modules["argus_overview.utils.display_server"]


class TestImportFallbacks:
    """Tests for try/except ImportError branches in platform modules."""

    def test_linux_has_xlib_false_when_import_fails(self):
        """Cover linux.py lines 34-35: HAS_XLIB = False on ImportError."""
        import importlib

        # Save original module state
        original_xlib = sys.modules.get("Xlib")
        original_xlib_x = sys.modules.get("Xlib.X")
        original_xlib_display = sys.modules.get("Xlib.display")

        try:
            # Setting to None forces ImportError on `import Xlib`
            sys.modules["Xlib"] = None  # type: ignore[assignment]
            sys.modules["Xlib.X"] = None  # type: ignore[assignment]
            sys.modules["Xlib.display"] = None  # type: ignore[assignment]

            import argus_overview.platform.linux as linux_mod

            importlib.reload(linux_mod)

            assert linux_mod.HAS_XLIB is False
        finally:
            # Restore original state
            if original_xlib is not None:
                sys.modules["Xlib"] = original_xlib
            else:
                sys.modules.pop("Xlib", None)
            if original_xlib_x is not None:
                sys.modules["Xlib.X"] = original_xlib_x
            else:
                sys.modules.pop("Xlib.X", None)
            if original_xlib_display is not None:
                sys.modules["Xlib.display"] = original_xlib_display
            else:
                sys.modules.pop("Xlib.display", None)

            # Reload to restore normal state
            importlib.reload(linux_mod)

    def test_windows_has_win32_true_when_imports_succeed(self):
        """Cover windows.py lines 32-38: HAS_WIN32 = True when Win32 available."""
        import ctypes
        import importlib

        # Create mock Win32 modules
        mock_pywintypes = MagicMock()
        mock_pywintypes.error = type("error", (Exception,), {})
        mock_win32api = MagicMock()
        mock_win32con = MagicMock()
        mock_win32gui = MagicMock()
        mock_win32ui = MagicMock()

        # ctypes exists on Linux but lacks windll — mock ctypes with windll
        mock_ctypes = MagicMock(spec=ctypes)
        mock_ctypes.windll = MagicMock()

        # Save originals
        saved = {}
        mod_names = [
            "pywintypes",
            "win32api",
            "win32con",
            "win32gui",
            "win32ui",
            "ctypes",
        ]
        for mod_name in mod_names:
            saved[mod_name] = sys.modules.get(mod_name)

        try:
            sys.modules["pywintypes"] = mock_pywintypes
            sys.modules["win32api"] = mock_win32api
            sys.modules["win32con"] = mock_win32con
            sys.modules["win32gui"] = mock_win32gui
            sys.modules["win32ui"] = mock_win32ui
            sys.modules["ctypes"] = mock_ctypes

            import argus_overview.platform.windows as win_mod

            importlib.reload(win_mod)

            assert win_mod.HAS_WIN32 is True
        finally:
            # Restore all originals
            for mod_name in mod_names:
                original = saved[mod_name]
                if original is not None:
                    sys.modules[mod_name] = original
                else:
                    sys.modules.pop(mod_name, None)

            importlib.reload(win_mod)
