"""Tests for utility modules.

v3.0: Window utils tests now mock the platform abstraction layer.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestConstants:
    """Tests for constants module."""

    def test_timeout_values_are_positive(self):
        """Test timeout values are positive numbers."""
        from argus_overview.utils.constants import (
            TIMEOUT_LONG,
            TIMEOUT_MEDIUM,
            TIMEOUT_SHORT,
        )

        assert TIMEOUT_SHORT > 0
        assert TIMEOUT_MEDIUM > 0
        assert TIMEOUT_LONG > 0
        assert TIMEOUT_SHORT <= TIMEOUT_MEDIUM <= TIMEOUT_LONG

    def test_config_dir_default(self):
        """Test default config directory."""
        from argus_overview.utils.constants import CONFIG_DIR

        assert CONFIG_DIR is not None
        assert isinstance(CONFIG_DIR, Path)

    def test_config_dir_env_override(self):
        """Test config directory can be overridden via environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"ARGUS_CONFIG_DIR": tmpdir}):
                # Need to reimport to pick up env change
                import importlib

                from argus_overview.utils import constants

                importlib.reload(constants)

                assert constants.CONFIG_DIR == Path(tmpdir)

    def test_config_files_are_paths(self):
        """Test config file constants are Path objects."""
        from argus_overview.utils.constants import (
            CHARACTERS_FILE,
            LOG_FILE,
            SETTINGS_FILE,
            TEAMS_FILE,
        )

        assert isinstance(SETTINGS_FILE, Path)
        assert isinstance(CHARACTERS_FILE, Path)
        assert isinstance(TEAMS_FILE, Path)
        assert isinstance(LOG_FILE, Path)


class TestWindowUtils:
    """Tests for window utilities (now delegates to platform layer)."""

    def test_valid_window_id_hex_format(self):
        """Test valid window IDs in hex format."""
        import argus_overview.utils.window_utils as window_utils

        # Reset cached window manager and mock
        window_utils._window_mgr = None

        mock_wm = MagicMock()
        mock_wm.is_valid_window_id.side_effect = (
            lambda x: isinstance(x, str) and x.startswith("0x") and len(x) > 2
        )

        with patch.object(window_utils, "_get_window_mgr", return_value=mock_wm):
            assert window_utils.is_valid_window_id("0x03800003") is True
            assert window_utils.is_valid_window_id("0x1") is True
            assert window_utils.is_valid_window_id("0xABCDEF") is True

    def test_invalid_window_id_formats(self):
        """Test invalid window ID formats."""
        import argus_overview.utils.window_utils as window_utils

        window_utils._window_mgr = None

        mock_wm = MagicMock()
        mock_wm.is_valid_window_id.return_value = False

        with patch.object(window_utils, "_get_window_mgr", return_value=mock_wm):
            assert window_utils.is_valid_window_id("") is False
            assert window_utils.is_valid_window_id(None) is False
            assert window_utils.is_valid_window_id("12345") is False

    def test_move_window_validates_id(self):
        """Test move_window validates window ID via platform layer."""
        import argus_overview.utils.window_utils as window_utils

        window_utils._window_mgr = None

        mock_wm = MagicMock()
        mock_wm.move_window.return_value = False

        with patch.object(window_utils, "_get_window_mgr", return_value=mock_wm):
            result = window_utils.move_window("invalid", 0, 0, 100, 100)
            assert result is False
            mock_wm.move_window.assert_called_once_with("invalid", 0, 0, 100, 100, 2.0)

    def test_move_window_success(self):
        """Test move_window delegates to platform layer."""
        import argus_overview.utils.window_utils as window_utils

        window_utils._window_mgr = None

        mock_wm = MagicMock()
        mock_wm.move_window.return_value = True

        with patch.object(window_utils, "_get_window_mgr", return_value=mock_wm):
            result = window_utils.move_window("0x03800003", 100, 200, 800, 600)

            assert result is True
            mock_wm.move_window.assert_called_once_with("0x03800003", 100, 200, 800, 600, 2.0)

    def test_activate_window_validates_id(self):
        """Test activate_window validates window ID via platform layer."""
        import argus_overview.utils.window_utils as window_utils

        window_utils._window_mgr = None

        mock_wm = MagicMock()
        mock_wm.activate_window.return_value = False

        with patch.object(window_utils, "_get_window_mgr", return_value=mock_wm):
            result = window_utils.activate_window("invalid")
            assert result is False

    def test_activate_window_success(self):
        """Test activate_window delegates to platform layer."""
        import argus_overview.utils.window_utils as window_utils

        window_utils._window_mgr = None

        mock_wm = MagicMock()
        mock_wm.activate_window.return_value = True

        with patch.object(window_utils, "_get_window_mgr", return_value=mock_wm):
            result = window_utils.activate_window("0x03800003")

            assert result is True
            mock_wm.activate_window.assert_called_once_with("0x03800003", 2.0)

    def test_get_focused_window_success(self):
        """Test get_focused_window returns window ID from platform layer."""
        import argus_overview.utils.window_utils as window_utils

        window_utils._window_mgr = None

        mock_wm = MagicMock()
        mock_wm.get_focused_window.return_value = "0x3800003"

        with patch.object(window_utils, "_get_window_mgr", return_value=mock_wm):
            result = window_utils.get_focused_window()

            assert result == "0x3800003"

    def test_get_focused_window_failure(self):
        """Test get_focused_window handles errors."""
        import argus_overview.utils.window_utils as window_utils

        window_utils._window_mgr = None

        mock_wm = MagicMock()
        mock_wm.get_focused_window.return_value = None

        with patch.object(window_utils, "_get_window_mgr", return_value=mock_wm):
            result = window_utils.get_focused_window()

            assert result is None


class TestRunX11Subprocess:
    """Tests for run_x11_subprocess (Linux-only, re-exported from platform layer)."""

    def test_run_x11_subprocess_available_on_linux(self):
        """Test run_x11_subprocess is available on Linux."""
        from argus_overview.platform import is_linux

        if is_linux():
            from argus_overview.utils.window_utils import run_x11_subprocess

            assert callable(run_x11_subprocess)

    def test_run_x11_subprocess_success(self):
        """Test run_x11_subprocess success case (Linux only)."""
        from argus_overview.platform import is_linux

        if not is_linux():
            return  # Skip on non-Linux

        with patch("argus_overview.platform.linux.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            from argus_overview.platform.linux import run_x11_subprocess

            result = run_x11_subprocess(["xdotool", "getwindowfocus"], max_attempts=3)

            assert result.returncode == 0
            assert mock_run.call_count == 1

    def test_run_x11_subprocess_retries(self):
        """Test run_x11_subprocess retries on failure (Linux only)."""
        from argus_overview.platform import is_linux

        if not is_linux():
            return  # Skip on non-Linux

        import subprocess as sp

        with patch("argus_overview.platform.linux.subprocess.run") as mock_run:
            mock_run.side_effect = [
                sp.TimeoutExpired("xdotool", 2),
                MagicMock(returncode=0),
            ]

            from argus_overview.platform.linux import run_x11_subprocess

            result = run_x11_subprocess(["xdotool", "getwindowfocus"], max_attempts=3, backoff=0.01)

            assert result.returncode == 0
            assert mock_run.call_count == 2


class TestUtilsExports:
    """Test that utils module exports all expected symbols."""

    def test_all_exports_available(self):
        """Test all expected exports are available from utils."""
        from argus_overview import utils

        # Constants
        assert hasattr(utils, "CONFIG_DIR")
        assert hasattr(utils, "SETTINGS_FILE")
        assert hasattr(utils, "TIMEOUT_SHORT")
        assert hasattr(utils, "TIMEOUT_MEDIUM")
        assert hasattr(utils, "TIMEOUT_LONG")

        # Window utils
        assert hasattr(utils, "is_valid_window_id")
        assert hasattr(utils, "move_window")
        assert hasattr(utils, "activate_window")
        assert hasattr(utils, "get_focused_window")
