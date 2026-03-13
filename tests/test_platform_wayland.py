"""Tests for Wayland platform module.

All subprocess calls and D-Bus interactions are mocked.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from argus_overview.platform.base import ScreenGeometry
from argus_overview.platform.wayland import (
    EVEPathResolverWayland,
    HotkeyHelperWayland,
    ScreenManagerWayland,
    WindowCaptureWayland,
    WindowManagerWayland,
    _detect_compositor,
    _get_hyprland_windows,
    _get_sway_windows,
    _run_hyprctl,
    _run_swaymsg,
)

# --- Fixtures ---

SWAY_TREE = {
    "id": 1,
    "type": "root",
    "name": "root",
    "nodes": [
        {
            "id": 2,
            "type": "output",
            "name": "__i3",
            "nodes": [],
            "floating_nodes": [],
        },
        {
            "id": 3,
            "type": "output",
            "name": "DP-1",
            "nodes": [
                {
                    "id": 4,
                    "type": "workspace",
                    "name": "1",
                    "nodes": [
                        {
                            "id": 100,
                            "type": "con",
                            "name": "EVE - Pilot One",
                            "pid": 12345,
                            "app_id": "wine",
                            "focused": True,
                            "rect": {
                                "x": 0,
                                "y": 0,
                                "width": 1920,
                                "height": 1080,
                            },
                        },
                        {
                            "id": 101,
                            "type": "con",
                            "name": "Firefox",
                            "pid": 12346,
                            "app_id": "firefox",
                            "focused": False,
                            "rect": {
                                "x": 100,
                                "y": 100,
                                "width": 800,
                                "height": 600,
                            },
                        },
                    ],
                    "floating_nodes": [
                        {
                            "id": 102,
                            "type": "con",
                            "name": "EVE Online - Pilot Two",
                            "pid": 12347,
                            "app_id": "wine",
                            "focused": False,
                            "rect": {
                                "x": 200,
                                "y": 200,
                                "width": 1280,
                                "height": 720,
                            },
                        }
                    ],
                }
            ],
            "floating_nodes": [],
        },
    ],
    "floating_nodes": [],
}

HYPRLAND_CLIENTS = [
    {
        "address": "0x55a1b2c3d4e5",
        "title": "EVE - Pilot One",
        "class": "wine",
        "at": [0, 0],
        "size": [1920, 1080],
    },
    {
        "address": "0x55a1b2c3d4e6",
        "title": "Firefox",
        "class": "firefox",
        "at": [100, 100],
        "size": [800, 600],
    },
]

WLR_RANDR_OUTPUT = """\
DP-1 "Dell Inc. U2720Q" (DP-1)
  Enabled: yes
  Modes:
    2560x1440@59.951000 Hz
    current 2560x1440@143.998001 Hz (preferred)
  Position: 0,0
  Transform: normal
  Scale: 1.000000
HDMI-A-1 "Samsung Electric Company" (HDMI-A-1)
  Enabled: yes
  Modes:
    1920x1080@60.000000 Hz
    current 1920x1080@60.000000 Hz (preferred)
  Position: 2560,0
  Transform: normal
  Scale: 1.000000
"""

WLR_RANDR_DISABLED = """\
DP-1 "Dell Inc. U2720Q" (DP-1)
  Enabled: no
  Modes:
    2560x1440@59.951000 Hz
  Position: 0,0
"""


# --- Compositor Detection ---


class TestDetectCompositor:
    """Tests for _detect_compositor."""

    @patch.dict("os.environ", {"SWAYSOCK": "/run/user/1000/sway-ipc.sock"})
    def test_detects_sway_via_env(self):
        assert _detect_compositor() == "sway"

    @patch.dict(
        "os.environ",
        {"HYPRLAND_INSTANCE_SIGNATURE": "abc123"},
        clear=False,
    )
    def test_detects_hyprland_via_env(self):
        # Remove SWAYSOCK if present to avoid false match
        import os

        os.environ.pop("SWAYSOCK", None)
        assert _detect_compositor() == "hyprland"

    @patch.dict("os.environ", {}, clear=True)
    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_detects_sway_via_pgrep(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert _detect_compositor() == "sway"

    @patch.dict("os.environ", {}, clear=True)
    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_detects_hyprland_via_pgrep(self, mock_run):
        # pgrep sway fails, pgrep Hyprland succeeds
        def side_effect(cmd, **kwargs):
            if "sway" in cmd:
                return MagicMock(returncode=1)
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect
        assert _detect_compositor() == "hyprland"

    @patch.dict("os.environ", {}, clear=True)
    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_returns_unknown_when_nothing_detected(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        assert _detect_compositor() == "unknown"

    @patch.dict("os.environ", {}, clear=True)
    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_handles_pgrep_oserror(self, mock_run):
        mock_run.side_effect = OSError("not found")
        assert _detect_compositor() == "unknown"


# --- Subprocess Helpers ---


class TestRunSwaymsg:
    """Tests for _run_swaymsg."""

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        assert _run_swaymsg(["-t", "get_tree"]) == "ok"

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_failure_returns_none(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert _run_swaymsg(["-t", "get_tree"]) is None

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_oserror_returns_none(self, mock_run):
        mock_run.side_effect = OSError("swaymsg not found")
        assert _run_swaymsg(["-t", "get_tree"]) is None

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_timeout_returns_none(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired("swaymsg", 2)
        assert _run_swaymsg(["-t", "get_tree"]) is None


class TestRunHyprctl:
    """Tests for _run_hyprctl."""

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        assert _run_hyprctl(["clients", "-j"]) == "ok"

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_failure_returns_none(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        assert _run_hyprctl(["clients", "-j"]) is None


# --- Sway/Hyprland Window Enumeration ---


class TestGetSwayWindows:
    """Tests for _get_sway_windows."""

    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_parses_sway_tree(self, mock_swaymsg):
        mock_swaymsg.return_value = json.dumps(SWAY_TREE)
        windows = _get_sway_windows()
        assert len(windows) == 3
        titles = [w["name"] for w in windows]
        assert "EVE - Pilot One" in titles
        assert "Firefox" in titles
        assert "EVE Online - Pilot Two" in titles

    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_returns_empty_on_failure(self, mock_swaymsg):
        mock_swaymsg.return_value = None
        assert _get_sway_windows() == []

    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_returns_empty_on_bad_json(self, mock_swaymsg):
        mock_swaymsg.return_value = "not json"
        assert _get_sway_windows() == []


class TestGetHyprlandWindows:
    """Tests for _get_hyprland_windows."""

    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_parses_hyprland_clients(self, mock_hyprctl):
        mock_hyprctl.return_value = json.dumps(HYPRLAND_CLIENTS)
        windows = _get_hyprland_windows()
        assert len(windows) == 2
        assert windows[0]["id"] == "0x55a1b2c3d4e5"
        assert windows[0]["name"] == "EVE - Pilot One"

    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_returns_empty_on_failure(self, mock_hyprctl):
        mock_hyprctl.return_value = None
        assert _get_hyprland_windows() == []

    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_returns_empty_on_bad_json(self, mock_hyprctl):
        mock_hyprctl.return_value = "{invalid"
        assert _get_hyprland_windows() == []


# --- WindowManagerWayland ---


class TestWindowManagerWayland:
    """Tests for WindowManagerWayland."""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._get_sway_windows")
    def test_get_window_list_sway(self, mock_windows, _mock_comp):
        mock_windows.return_value = [
            {"id": "100", "name": "EVE - Pilot One", "app_id": "wine"},
            {"id": "101", "name": "Firefox", "app_id": "firefox"},
        ]
        wm = WindowManagerWayland()
        windows = wm.get_window_list()
        assert len(windows) == 2
        assert ("100", "EVE - Pilot One") in windows

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._get_sway_windows")
    def test_get_eve_windows_sway(self, mock_windows, _mock_comp):
        mock_windows.return_value = [
            {"id": "100", "name": "EVE - Pilot One", "app_id": "wine"},
            {"id": "101", "name": "Firefox", "app_id": "firefox"},
            {"id": "102", "name": "EVE Online - Pilot Two", "app_id": "wine"},
        ]
        wm = WindowManagerWayland()
        eve = wm.get_eve_windows()
        assert len(eve) == 2
        assert ("100", "EVE - Pilot One") in eve
        assert ("102", "EVE Online - Pilot Two") in eve

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._get_hyprland_windows")
    def test_get_window_list_hyprland(self, mock_windows, _mock_comp):
        mock_windows.return_value = [
            {"id": "0x55a1b2c3d4e5", "name": "EVE - Pilot One"},
        ]
        wm = WindowManagerWayland()
        windows = wm.get_window_list()
        assert len(windows) == 1

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="unknown")
    def test_get_window_list_unknown_compositor(self, _mock_comp):
        wm = WindowManagerWayland()
        assert wm.get_window_list() == []

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_is_valid_window_id(self, _mock_comp):
        wm = WindowManagerWayland()
        assert wm.is_valid_window_id("100") is True
        assert wm.is_valid_window_id("0x55a1b2c3") is True
        assert wm.is_valid_window_id("abc") is True  # hex digits
        assert wm.is_valid_window_id("") is False
        assert wm.is_valid_window_id("not-valid!") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_move_window_sway(self, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = '{"success": true}'
        wm = WindowManagerWayland()
        assert wm.move_window("100", 0, 0, 1920, 1080) is True
        assert mock_swaymsg.call_count == 2  # move + resize

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_move_window_sway_no_resize(self, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = '{"success": true}'
        wm = WindowManagerWayland()
        assert wm.move_window("100", 0, 0, 0, 0) is True
        assert mock_swaymsg.call_count == 1  # move only

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_move_window_invalid_id(self, _mock_comp):
        wm = WindowManagerWayland()
        assert wm.move_window("", 0, 0, 100, 100) is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_move_window_hyprland(self, mock_hyprctl, _mock_comp):
        mock_hyprctl.return_value = "ok"
        wm = WindowManagerWayland()
        assert wm.move_window("0x55a1b2c3d4e5", 0, 0, 1920, 1080) is True

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_activate_window_sway(self, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = "ok"
        wm = WindowManagerWayland()
        assert wm.activate_window("100") is True

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_activate_window_sway_failure(self, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = None
        wm = WindowManagerWayland()
        assert wm.activate_window("100") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_activate_window_hyprland(self, mock_hyprctl, _mock_comp):
        mock_hyprctl.return_value = "ok"
        wm = WindowManagerWayland()
        assert wm.activate_window("0x55a1b2c3d4e5") is True

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_minimize_window_sway(self, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = "ok"
        wm = WindowManagerWayland()
        assert wm.minimize_window("100") is True

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_restore_window_sway(self, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = "ok"
        wm = WindowManagerWayland()
        assert wm.restore_window("100") is True

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_get_focused_window_sway(self, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = json.dumps(SWAY_TREE)
        wm = WindowManagerWayland()
        focused = wm.get_focused_window()
        assert focused == "100"  # ID of focused window in SWAY_TREE

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_get_focused_window_sway_none(self, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = None
        wm = WindowManagerWayland()
        assert wm.get_focused_window() is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_get_focused_window_hyprland(self, mock_hyprctl, _mock_comp):
        mock_hyprctl.return_value = json.dumps({"address": "0x55a1b2c3d4e5"})
        wm = WindowManagerWayland()
        assert wm.get_focused_window() == "0x55a1b2c3d4e5"

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._get_sway_windows")
    def test_get_window_title(self, mock_windows, _mock_comp):
        mock_windows.return_value = [
            {"id": "100", "name": "EVE - Pilot One"},
        ]
        wm = WindowManagerWayland()
        assert wm.get_window_title("100") == "EVE - Pilot One"
        assert wm.get_window_title("999") == "Unknown"

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._get_sway_windows")
    def test_filters_empty_titles(self, mock_windows, _mock_comp):
        mock_windows.return_value = [
            {"id": "100", "name": ""},
            {"id": "101", "name": "Real Window"},
        ]
        wm = WindowManagerWayland()
        windows = wm.get_window_list()
        assert len(windows) == 1
        assert windows[0] == ("101", "Real Window")


# --- WindowCaptureWayland ---


class TestWindowCaptureWayland:
    """Tests for WindowCaptureWayland."""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_start_stop(self, _mock_comp):
        capture = WindowCaptureWayland(max_workers=2)
        assert capture.running is False
        capture.start()
        assert capture.running is True
        assert len(capture.workers) == 2
        capture.stop()
        assert capture.running is False
        assert len(capture.workers) == 0

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_capture_async_invalid_id(self, _mock_comp):
        capture = WindowCaptureWayland(max_workers=1)
        assert capture.capture_window_async("invalid!") == ""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_capture_async_returns_request_id(self, _mock_comp):
        capture = WindowCaptureWayland(max_workers=1)
        req_id = capture.capture_window_async("100")
        assert req_id != ""
        assert len(req_id) == 36  # UUID format

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_get_result_empty(self, _mock_comp):
        capture = WindowCaptureWayland(max_workers=1)
        assert capture.get_result(timeout=0.01) is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_capture_sync_sway(self, mock_run, mock_swaymsg, _mock_comp):
        # Mock swaymsg get_tree to return window geometry
        mock_swaymsg.return_value = json.dumps(SWAY_TREE)

        # Mock grim to return a valid PNG
        img = Image.new("RGB", (100, 100), "red")
        import io

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        mock_run.return_value = MagicMock(returncode=0, stdout=buf.getvalue())

        capture = WindowCaptureWayland(max_workers=1)
        result = capture.capture_window_sync("100")
        assert result is not None
        assert result.size == (100, 100)

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_capture_sync_no_geometry(self, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = None
        capture = WindowCaptureWayland(max_workers=1)
        assert capture.capture_window_sync("100") is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_capture_grim_failure(self, mock_run, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = json.dumps(SWAY_TREE)
        mock_run.return_value = MagicMock(returncode=1, stdout=b"")
        capture = WindowCaptureWayland(max_workers=1)
        assert capture.capture_window_sync("100") is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_capture_grim_oserror(self, mock_run, mock_swaymsg, _mock_comp):
        mock_swaymsg.return_value = json.dumps(SWAY_TREE)
        mock_run.side_effect = OSError("grim not found")
        capture = WindowCaptureWayland(max_workers=1)
        assert capture.capture_window_sync("100") is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_capture_sync_hyprland(self, mock_run, mock_hyprctl, _mock_comp):
        mock_hyprctl.return_value = json.dumps(HYPRLAND_CLIENTS)

        img = Image.new("RGB", (50, 50), "blue")
        import io

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        mock_run.return_value = MagicMock(returncode=0, stdout=buf.getvalue())

        capture = WindowCaptureWayland(max_workers=1)
        result = capture.capture_window_sync("0x55a1b2c3d4e5")
        assert result is not None
        assert result.size == (50, 50)


# --- ScreenManagerWayland ---


class TestScreenManagerWayland:
    """Tests for ScreenManagerWayland."""

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_get_all_monitors(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=WLR_RANDR_OUTPUT)
        sm = ScreenManagerWayland()
        monitors = sm.get_all_monitors()
        assert len(monitors) == 2
        assert monitors[0].width == 2560
        assert monitors[0].height == 1440
        assert monitors[0].x == 0
        assert monitors[0].y == 0
        assert monitors[0].is_primary is True
        assert monitors[1].width == 1920
        assert monitors[1].height == 1080
        assert monitors[1].x == 2560
        assert monitors[1].y == 0
        assert monitors[1].is_primary is False

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_get_screen_geometry_specific_monitor(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=WLR_RANDR_OUTPUT)
        sm = ScreenManagerWayland()
        geom = sm.get_screen_geometry(1)
        assert geom.width == 1920
        assert geom.height == 1080

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_get_screen_geometry_out_of_range(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=WLR_RANDR_OUTPUT)
        sm = ScreenManagerWayland()
        geom = sm.get_screen_geometry(99)
        # Falls back to first monitor
        assert geom.width == 2560

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_get_screen_geometry_default_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        sm = ScreenManagerWayland()
        geom = sm.get_screen_geometry()
        assert geom == ScreenGeometry(0, 0, 1920, 1080, True)

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_get_all_monitors_default_on_oserror(self, mock_run):
        mock_run.side_effect = OSError("wlr-randr not found")
        sm = ScreenManagerWayland()
        monitors = sm.get_all_monitors()
        assert len(monitors) == 1
        assert monitors[0] == ScreenGeometry(0, 0, 1920, 1080, True)

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_disabled_output_skipped(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=WLR_RANDR_DISABLED)
        sm = ScreenManagerWayland()
        monitors = sm.get_all_monitors()
        # Disabled output should be skipped, fallback to default
        assert len(monitors) == 1
        assert monitors[0] == ScreenGeometry(0, 0, 1920, 1080, True)

    def test_parse_empty_output(self):
        sm = ScreenManagerWayland()
        monitors = sm._parse_wlr_randr_output("")
        assert monitors == []

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_timeout_returns_default(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired("wlr-randr", 5)
        sm = ScreenManagerWayland()
        monitors = sm.get_all_monitors()
        assert monitors == [ScreenGeometry(0, 0, 1920, 1080, True)]


# --- EVEPathResolverWayland ---


class TestEVEPathResolverWayland:
    """Tests for EVEPathResolverWayland (delegates to Linux)."""

    def test_get_eve_settings_paths(self):
        resolver = EVEPathResolverWayland()
        paths = resolver.get_eve_settings_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0
        assert all(isinstance(p, Path) for p in paths)

    def test_get_eve_logs_paths(self):
        resolver = EVEPathResolverWayland()
        paths = resolver.get_eve_logs_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0

    def test_get_config_directory(self):
        resolver = EVEPathResolverWayland()
        config_dir = resolver.get_config_directory()
        assert isinstance(config_dir, Path)
        assert "argus-overview" in str(config_dir)

    def test_paths_match_linux(self):
        """Wayland paths should be identical to Linux paths."""
        from argus_overview.platform.linux import EVEPathResolverLinux

        linux = EVEPathResolverLinux()
        wayland = EVEPathResolverWayland()
        assert linux.get_eve_settings_paths() == wayland.get_eve_settings_paths()
        assert linux.get_eve_logs_paths() == wayland.get_eve_logs_paths()
        assert linux.get_config_directory() == wayland.get_config_directory()


# --- HotkeyHelperWayland ---


class TestHotkeyHelperWayland:
    """Tests for HotkeyHelperWayland (delegates to Linux)."""

    def test_normalize_combo_modifier_plus_key(self):
        helper = HotkeyHelperWayland()
        assert helper.normalize_combo("<ctrl>+<v>") == "<ctrl>+v"

    def test_normalize_combo_single_key(self):
        helper = HotkeyHelperWayland()
        assert helper.normalize_combo("<R>") == "r"

    def test_normalize_combo_empty(self):
        helper = HotkeyHelperWayland()
        assert helper.normalize_combo("") == ""

    def test_normalize_combo_special_key(self):
        helper = HotkeyHelperWayland()
        assert helper.normalize_combo("<ctrl>+<space>") == "<ctrl>+<space>"

    def test_is_single_key_true(self):
        helper = HotkeyHelperWayland()
        assert helper.is_single_key("v") is True

    def test_is_single_key_false(self):
        helper = HotkeyHelperWayland()
        assert helper.is_single_key("<ctrl>+v") is False

    def test_is_single_key_empty(self):
        helper = HotkeyHelperWayland()
        assert helper.is_single_key("") is False

    def test_matches_linux_behavior(self):
        """Wayland hotkey normalization should match Linux exactly."""
        from argus_overview.platform.linux import HotkeyHelperLinux

        linux = HotkeyHelperLinux()
        wayland = HotkeyHelperWayland()

        test_combos = [
            "<ctrl>+<v>",
            "<alt>+<F4>",
            "<shift>+<ctrl>+<t>",
            "v",
            "",
            "<space>",
        ]
        for combo in test_combos:
            assert linux.normalize_combo(combo) == wayland.normalize_combo(combo)
            assert linux.is_single_key(combo) == wayland.is_single_key(combo)


# --- Factory Routing ---


class TestFactoryRouting:
    """Tests that factory functions route correctly based on display server."""

    def setup_method(self):
        """Clear singleton cache before each test."""
        from argus_overview.platform import _clear_singleton_cache

        _clear_singleton_cache()

    def teardown_method(self):
        """Clear singleton cache after each test."""
        from argus_overview.platform import _clear_singleton_cache

        _clear_singleton_cache()

    @patch("argus_overview.platform._is_pure_wayland", return_value=True)
    @patch("argus_overview.platform.get_platform_name", return_value="linux")
    @patch(
        "argus_overview.platform.wayland._detect_compositor",
        return_value="sway",
    )
    def test_wayland_routes_to_wayland_window_manager(self, _c, _p, _w):
        from argus_overview.platform import get_window_manager

        wm = get_window_manager()
        assert isinstance(wm, WindowManagerWayland)

    @patch("argus_overview.platform._is_pure_wayland", return_value=True)
    @patch("argus_overview.platform.get_platform_name", return_value="linux")
    @patch(
        "argus_overview.platform.wayland._detect_compositor",
        return_value="sway",
    )
    def test_wayland_routes_to_wayland_capture(self, _c, _p, _w):
        from argus_overview.platform import get_window_capture

        capture = get_window_capture()
        assert isinstance(capture, WindowCaptureWayland)

    @patch("argus_overview.platform._is_pure_wayland", return_value=True)
    @patch("argus_overview.platform.get_platform_name", return_value="linux")
    def test_wayland_routes_to_wayland_screen_manager(self, _p, _w):
        from argus_overview.platform import get_screen_manager

        sm = get_screen_manager()
        assert isinstance(sm, ScreenManagerWayland)

    @patch("argus_overview.platform._is_pure_wayland", return_value=True)
    @patch("argus_overview.platform.get_platform_name", return_value="linux")
    def test_wayland_routes_to_wayland_path_resolver(self, _p, _w):
        from argus_overview.platform import get_eve_path_resolver

        resolver = get_eve_path_resolver()
        assert isinstance(resolver, EVEPathResolverWayland)

    @patch("argus_overview.platform._is_pure_wayland", return_value=True)
    @patch("argus_overview.platform.get_platform_name", return_value="linux")
    def test_wayland_routes_to_wayland_hotkey_helper(self, _p, _w):
        from argus_overview.platform import get_hotkey_helper

        helper = get_hotkey_helper()
        assert isinstance(helper, HotkeyHelperWayland)

    @patch("argus_overview.platform._is_pure_wayland", return_value=False)
    @patch("argus_overview.platform.get_platform_name", return_value="linux")
    def test_xwayland_routes_to_linux_window_manager(self, _p, _w):
        from argus_overview.platform import get_window_manager
        from argus_overview.platform.linux import WindowManagerLinux

        wm = get_window_manager()
        assert isinstance(wm, WindowManagerLinux)

    @patch("argus_overview.platform._is_pure_wayland", return_value=False)
    @patch("argus_overview.platform.get_platform_name", return_value="linux")
    def test_xwayland_routes_to_linux_capture(self, _p, _w):
        from argus_overview.platform import get_window_capture
        from argus_overview.platform.linux import WindowCaptureLinux

        capture = get_window_capture()
        assert isinstance(capture, WindowCaptureLinux)

    @patch("argus_overview.platform._is_pure_wayland", return_value=False)
    @patch("argus_overview.platform.get_platform_name", return_value="linux")
    def test_xwayland_routes_to_linux_screen_manager(self, _p, _w):
        from argus_overview.platform import get_screen_manager
        from argus_overview.platform.linux import ScreenManagerLinux

        sm = get_screen_manager()
        assert isinstance(sm, ScreenManagerLinux)


# ---------------------------------------------------------------------------
# Coverage Push: _run_hyprctl exception path (lines 110-111)
# ---------------------------------------------------------------------------


class TestRunHyprctlExceptions:
    """Tests for _run_hyprctl error handling."""

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_oserror_returns_none(self, mock_run):
        """Lines 110-111: OSError from hyprctl is caught."""
        mock_run.side_effect = OSError("hyprctl not found")
        assert _run_hyprctl(["clients", "-j"]) is None

    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_timeout_returns_none(self, mock_run):
        """Lines 110-111: TimeoutExpired from hyprctl is caught."""
        import subprocess as sp

        mock_run.side_effect = sp.TimeoutExpired("hyprctl", 2)
        assert _run_hyprctl(["clients", "-j"]) is None


# ---------------------------------------------------------------------------
# Coverage Push: WindowManagerWayland move/activate/minimize/restore/focus
# exception paths and edge cases
# ---------------------------------------------------------------------------


class TestWindowManagerWaylandExceptions:
    """Tests for WindowManagerWayland exception handlers and edge cases."""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_move_window_sway_returns_false_when_swaymsg_fails(self, mock_swaymsg, _):
        """Line 232: move_window returns False when swaymsg returns None."""
        mock_swaymsg.return_value = None
        wm = WindowManagerWayland()
        assert wm.move_window("100", 0, 0, 1920, 1080) is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_move_window_exception_caught(self, mock_swaymsg, _):
        """Lines 246-248: Exception during move is caught, returns False."""
        mock_swaymsg.side_effect = Exception("Unexpected")
        wm = WindowManagerWayland()
        assert wm.move_window("100", 0, 0, 1920, 1080) is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_activate_window_invalid_id(self, _):
        """Lines 253-254: invalid ID returns False."""
        wm = WindowManagerWayland()
        assert wm.activate_window("") is False
        assert wm.activate_window("not-valid!") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_activate_window_exception_caught(self, mock_swaymsg, _):
        """Lines 263-265: Exception during activate is caught."""
        mock_swaymsg.side_effect = Exception("Unexpected")
        wm = WindowManagerWayland()
        assert wm.activate_window("100") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_minimize_window_invalid_id(self, _):
        """Line 270: invalid ID returns False."""
        wm = WindowManagerWayland()
        assert wm.minimize_window("") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_minimize_window_hyprland(self, mock_hyprctl, _):
        """Lines 276-280: Hyprland minimize path."""
        mock_hyprctl.return_value = "ok"
        wm = WindowManagerWayland()
        assert wm.minimize_window("0x55a1b2c3d4e5") is True

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_minimize_window_hyprland_failure(self, mock_hyprctl, _):
        """Lines 276-280: Hyprland minimize returns None."""
        mock_hyprctl.return_value = None
        wm = WindowManagerWayland()
        assert wm.minimize_window("0x55a1b2c3d4e5") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_minimize_window_exception_caught(self, mock_swaymsg, _):
        """Lines 281-283: Exception during minimize is caught."""
        mock_swaymsg.side_effect = Exception("Unexpected")
        wm = WindowManagerWayland()
        assert wm.minimize_window("100") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_restore_window_invalid_id(self, _):
        """Line 288: invalid ID returns False."""
        wm = WindowManagerWayland()
        assert wm.restore_window("") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_restore_window_hyprland(self, mock_hyprctl, _):
        """Lines 296-298: Hyprland restore path."""
        mock_hyprctl.return_value = "ok"
        wm = WindowManagerWayland()
        assert wm.restore_window("0x55a1b2c3d4e5") is True

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_restore_window_hyprland_failure(self, mock_hyprctl, _):
        """Lines 296-298: Hyprland restore returns None."""
        mock_hyprctl.return_value = None
        wm = WindowManagerWayland()
        assert wm.restore_window("0x55a1b2c3d4e5") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_restore_window_exception_caught(self, mock_swaymsg, _):
        """Lines 299-301: Exception during restore is caught."""
        mock_swaymsg.side_effect = Exception("Unexpected")
        wm = WindowManagerWayland()
        assert wm.restore_window("100") is False

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_get_focused_window_hyprland_none(self, mock_hyprctl, _):
        """Line 317: Hyprland focused window returns None when hyprctl fails."""
        mock_hyprctl.return_value = None
        wm = WindowManagerWayland()
        assert wm.get_focused_window() is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_get_focused_window_json_error(self, mock_swaymsg, _):
        """Lines 321-323: JSONDecodeError during get_focused is caught."""
        mock_swaymsg.return_value = "not json"
        wm = WindowManagerWayland()
        assert wm.get_focused_window() is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_get_focused_window_hyprland_json_error(self, mock_hyprctl, _):
        """Lines 321-323: JSONDecodeError from hyprland path is caught."""
        mock_hyprctl.return_value = "{bad json"
        wm = WindowManagerWayland()
        assert wm.get_focused_window() is None


class TestWindowManagerWaylandFindFocused:
    """Tests for _find_focused_sway with floating_nodes."""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_find_focused_in_floating_nodes(self, _):
        """Lines 362-364: focused window found in floating_nodes."""
        wm = WindowManagerWayland()
        tree = {
            "id": 1,
            "nodes": [],
            "floating_nodes": [
                {"id": 200, "pid": 999, "focused": True, "nodes": [], "floating_nodes": []},
            ],
        }
        assert wm._find_focused_sway(tree) == "200"

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_find_focused_nested_in_floating(self, _):
        """Lines 362-364: focused window nested inside floating_nodes."""
        wm = WindowManagerWayland()
        tree = {
            "id": 1,
            "nodes": [],
            "floating_nodes": [
                {
                    "id": 50,
                    "nodes": [
                        {"id": 300, "pid": 888, "focused": True, "nodes": [], "floating_nodes": []},
                    ],
                    "floating_nodes": [],
                },
            ],
        }
        assert wm._find_focused_sway(tree) == "300"


# ---------------------------------------------------------------------------
# Coverage Push: WindowCaptureWayland worker/async/geometry paths
# ---------------------------------------------------------------------------


class TestWindowCaptureWaylandWorker:
    """Tests for WindowCaptureWayland worker and async capture paths."""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    @patch("argus_overview.platform.wayland.subprocess.run")
    def test_worker_processes_task_and_puts_result(self, mock_run, mock_swaymsg, _):
        """Lines 419-421: worker processes task from queue."""
        mock_swaymsg.return_value = json.dumps(SWAY_TREE)

        img = Image.new("RGB", (50, 50), "green")
        import io

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        mock_run.return_value = MagicMock(returncode=0, stdout=buf.getvalue())

        capture = WindowCaptureWayland(max_workers=1)
        # Put a task and run worker iteration manually
        capture.capture_queue.put(("100", 1.0, "req-123"))
        capture._stop_event.clear()

        # Run worker in a thread that stops after one iteration

        def run_worker_once():
            capture._worker()

        # Worker will process one task then block on get; we stop it
        capture.start()
        import time

        time.sleep(0.3)
        capture.stop()

        # Check result was produced
        result = capture.get_result(timeout=0.5)
        if result:
            req_id, wid, image = result
            assert wid == "100"

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_worker_handles_exception(self, _):
        """Lines 424-425: worker catches exceptions during capture."""
        capture = WindowCaptureWayland(max_workers=1)

        # Put a malformed task (wrong number of values to unpack)
        capture.capture_queue.put(("bad_task",))
        capture._stop_event.clear()

        # Start and stop quickly
        capture.start()
        import time

        time.sleep(0.3)
        capture.stop()

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_capture_async_queue_full(self, _):
        """Lines 435-437: returns empty string when capture queue is full."""
        capture = WindowCaptureWayland(max_workers=1)
        # Fill the queue
        for i in range(capture.capture_queue.maxsize):
            capture.capture_queue.put(("dummy", 1.0, f"req-{i}"))

        result = capture.capture_window_async("100")
        assert result == ""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_capture_async_puts_valid_request(self, mock_swaymsg, _):
        """Capture queue receives valid request."""
        capture = WindowCaptureWayland(max_workers=1)
        req_id = capture.capture_window_async("100")
        assert req_id != ""
        # Verify it's in the queue
        task = capture.capture_queue.get_nowait()
        assert task[0] == "100"  # window_id
        assert task[2] == req_id  # request_id


class TestWindowCaptureWaylandStopFull:
    """Tests for stop() when capture_queue is full (lines 406-407)."""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_stop_handles_full_queue(self, _):
        """Lines 406-407: Full exception during stop is caught."""
        capture = WindowCaptureWayland(max_workers=2)
        # Fill the queue to capacity
        for i in range(capture.capture_queue.maxsize):
            capture.capture_queue.put(("dummy", 1.0, f"req-{i}"))

        # Add mock workers so the loop runs
        capture.workers = [MagicMock(), MagicMock()]
        capture._stop_event.clear()  # Pretend running

        # Stop should not raise despite full queue
        capture.stop()
        assert not capture.workers  # workers cleared


class TestWindowCaptureWaylandWorkerEmpty:
    """Tests for _worker Empty timeout path (line 423)."""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_worker_continues_on_empty_timeout(self, _):
        """Line 423: worker hits Empty timeout then exits when stopped."""

        capture = WindowCaptureWayland(max_workers=1)
        # Use a real queue with very short timeout - replace the queue's get
        # to use a very short timeout so the Empty is hit quickly
        original_get = capture.capture_queue.get

        call_count = 0

        def short_timeout_get(timeout=0.5):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                capture._stop_event.set()
            return original_get(timeout=0.01)  # Very short timeout

        capture.capture_queue.get = short_timeout_get
        capture._stop_event.clear()

        capture._worker()
        assert call_count >= 1


# ---------------------------------------------------------------------------
# Coverage Push: WindowCaptureWayland geometry paths
# ---------------------------------------------------------------------------


class TestWindowCaptureWaylandGeometry:
    """Tests for _get_window_geometry and _find_sway_window_geometry."""

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    @patch("argus_overview.platform.wayland._run_swaymsg")
    def test_sway_geometry_json_error(self, mock_swaymsg, _):
        """Lines 482-483: JSONDecodeError in sway geometry returns None."""
        mock_swaymsg.return_value = "not valid json"
        capture = WindowCaptureWayland(max_workers=1)
        assert capture._get_window_geometry("100") is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_hyprland_geometry_none_output(self, mock_hyprctl, _):
        """Line 488: hyprctl returns None for geometry."""
        mock_hyprctl.return_value = None
        capture = WindowCaptureWayland(max_workers=1)
        assert capture._get_window_geometry("0x55a1b2c3d4e5") is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_hyprland_geometry_json_error(self, mock_hyprctl, _):
        """Lines 496-497: JSONDecodeError in hyprland geometry."""
        mock_hyprctl.return_value = "bad json"
        capture = WindowCaptureWayland(max_workers=1)
        assert capture._get_window_geometry("0x55a1b2c3d4e5") is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="hyprland")
    @patch("argus_overview.platform.wayland._run_hyprctl")
    def test_hyprland_geometry_window_not_found(self, mock_hyprctl, _):
        """Lines 496-499: window not found in hyprland clients list."""
        mock_hyprctl.return_value = json.dumps(HYPRLAND_CLIENTS)
        capture = WindowCaptureWayland(max_workers=1)
        # Use an ID that doesn't match any client
        result = capture._get_window_geometry("0xDEADBEEF")
        assert result is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="unknown")
    def test_unknown_compositor_geometry(self, _):
        """Lines 498-499: unknown compositor returns None."""
        capture = WindowCaptureWayland(max_workers=1)
        assert capture._get_window_geometry("100") is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_find_sway_geometry_zero_size(self, _):
        """Line 511: window with zero size returns None."""
        capture = WindowCaptureWayland(max_workers=1)
        node = {
            "id": 100,
            "pid": 12345,
            "rect": {"x": 0, "y": 0, "width": 0, "height": 0},
            "nodes": [],
            "floating_nodes": [],
        }
        assert capture._find_sway_window_geometry(node, "100") is None

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_find_sway_geometry_in_floating_nodes(self, _):
        """Lines 518-520: geometry found in floating_nodes."""
        capture = WindowCaptureWayland(max_workers=1)
        tree = {
            "id": 1,
            "nodes": [],
            "floating_nodes": [
                {
                    "id": 200,
                    "pid": 999,
                    "rect": {"x": 10, "y": 20, "width": 800, "height": 600},
                    "nodes": [],
                    "floating_nodes": [],
                },
            ],
        }
        result = capture._find_sway_window_geometry(tree, "200")
        assert result == "10,20 800x600"

    @patch("argus_overview.platform.wayland._detect_compositor", return_value="sway")
    def test_find_sway_geometry_nested_floating(self, _):
        """Lines 517-520: geometry found nested in floating_nodes."""
        capture = WindowCaptureWayland(max_workers=1)
        tree = {
            "id": 1,
            "nodes": [],
            "floating_nodes": [
                {
                    "id": 50,
                    "nodes": [
                        {
                            "id": 300,
                            "pid": 888,
                            "rect": {"x": 5, "y": 10, "width": 1024, "height": 768},
                            "nodes": [],
                            "floating_nodes": [],
                        }
                    ],
                    "floating_nodes": [],
                },
            ],
        }
        result = capture._find_sway_window_geometry(tree, "300")
        assert result == "5,10 1024x768"
