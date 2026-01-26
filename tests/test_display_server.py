"""Tests for display server detection module."""

import subprocess
from unittest.mock import patch

from argus_overview.utils.display_server import (
    DisplayInfo,
    DisplayServer,
    _check_x11_tools_work,
    detect_display_server,
    get_wayland_limitation_message,
    is_pure_wayland,
)


class TestDisplayServer:
    """Tests for DisplayServer enum."""

    def test_all_values_exist(self):
        assert DisplayServer.X11.value == "x11"
        assert DisplayServer.WAYLAND.value == "wayland"
        assert DisplayServer.XWAYLAND.value == "xwayland"
        assert DisplayServer.UNKNOWN.value == "unknown"

    def test_value_count(self):
        assert len(DisplayServer) == 4


class TestDisplayInfo:
    """Tests for DisplayInfo dataclass."""

    def test_create_display_info(self):
        info = DisplayInfo(
            server=DisplayServer.X11,
            has_x11_access=True,
            session_type="x11",
            wayland_display=None,
            x11_display=":0",
        )
        assert info.server == DisplayServer.X11
        assert info.has_x11_access is True
        assert info.session_type == "x11"
        assert info.wayland_display is None
        assert info.x11_display == ":0"

    def test_wayland_info(self):
        info = DisplayInfo(
            server=DisplayServer.WAYLAND,
            has_x11_access=False,
            session_type="wayland",
            wayland_display="wayland-0",
            x11_display=None,
        )
        assert info.server == DisplayServer.WAYLAND
        assert info.has_x11_access is False


class TestCheckX11ToolsWork:
    """Tests for _check_x11_tools_work function."""

    def test_wmctrl_success(self):
        mock_result = subprocess.CompletedProcess(
            args=["wmctrl", "-l"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with patch("subprocess.run", return_value=mock_result):
            assert _check_x11_tools_work() is True

    def test_wmctrl_failure(self):
        mock_result = subprocess.CompletedProcess(
            args=["wmctrl", "-l"],
            returncode=1,
            stdout="",
            stderr="",
        )
        with patch("subprocess.run", return_value=mock_result):
            assert _check_x11_tools_work() is False

    def test_wmctrl_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert _check_x11_tools_work() is False

    def test_wmctrl_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("wmctrl", 2)):
            assert _check_x11_tools_work() is False


class TestDetectDisplayServer:
    """Tests for detect_display_server function."""

    def test_detect_x11_session(self):
        env = {
            "XDG_SESSION_TYPE": "x11",
            "DISPLAY": ":0",
        }
        with patch.dict("os.environ", env, clear=True):
            info = detect_display_server()
            assert info.server == DisplayServer.X11
            assert info.has_x11_access is True
            assert info.session_type == "x11"

    def test_detect_pure_wayland(self):
        env = {
            "XDG_SESSION_TYPE": "wayland",
            "WAYLAND_DISPLAY": "wayland-0",
        }
        with patch.dict("os.environ", env, clear=True):
            info = detect_display_server()
            assert info.server == DisplayServer.WAYLAND
            assert info.has_x11_access is False

    def test_detect_xwayland(self):
        env = {
            "XDG_SESSION_TYPE": "wayland",
            "WAYLAND_DISPLAY": "wayland-0",
            "DISPLAY": ":0",
        }
        with patch.dict("os.environ", env, clear=True):
            info = detect_display_server()
            assert info.server == DisplayServer.XWAYLAND
            assert info.has_x11_access is True

    def test_detect_unknown_with_working_x11(self):
        env = {}
        mock_result = subprocess.CompletedProcess(
            args=["wmctrl", "-l"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with patch.dict("os.environ", env, clear=True):
            with patch("subprocess.run", return_value=mock_result):
                info = detect_display_server()
                assert info.has_x11_access is True

    def test_detect_unknown_without_x11(self):
        env = {}
        with patch.dict("os.environ", env, clear=True):
            with patch("subprocess.run", side_effect=FileNotFoundError):
                info = detect_display_server()
                assert info.server == DisplayServer.UNKNOWN
                assert info.has_x11_access is False


class TestIsPureWayland:
    """Tests for is_pure_wayland function."""

    def test_pure_wayland_returns_true(self):
        env = {
            "XDG_SESSION_TYPE": "wayland",
            "WAYLAND_DISPLAY": "wayland-0",
        }
        with patch.dict("os.environ", env, clear=True):
            assert is_pure_wayland() is True

    def test_xwayland_returns_false(self):
        env = {
            "XDG_SESSION_TYPE": "wayland",
            "WAYLAND_DISPLAY": "wayland-0",
            "DISPLAY": ":0",
        }
        with patch.dict("os.environ", env, clear=True):
            assert is_pure_wayland() is False

    def test_x11_returns_false(self):
        env = {
            "XDG_SESSION_TYPE": "x11",
            "DISPLAY": ":0",
        }
        with patch.dict("os.environ", env, clear=True):
            assert is_pure_wayland() is False


class TestGetWaylandLimitationMessage:
    """Tests for get_wayland_limitation_message function."""

    def test_message_not_empty(self):
        msg = get_wayland_limitation_message()
        assert len(msg) > 100

    def test_message_contains_key_info(self):
        msg = get_wayland_limitation_message()
        assert "X11" in msg
        assert "Wayland" in msg
        assert "PROTON_ENABLE_WAYLAND" in msg
        assert "security" in msg.lower()

    def test_message_contains_solutions(self):
        msg = get_wayland_limitation_message()
        assert "XWayland" in msg or "X11 session" in msg
