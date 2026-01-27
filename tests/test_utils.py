"""Tests for utility modules."""

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
    """Tests for window utilities."""

    def test_valid_window_id_hex_format(self):
        """Test valid window IDs in hex format."""
        from argus_overview.utils.window_utils import is_valid_window_id

        assert is_valid_window_id("0x03800003") is True
        assert is_valid_window_id("0x1") is True
        assert is_valid_window_id("0xABCDEF") is True
        assert is_valid_window_id("0xabcdef") is True
        assert is_valid_window_id("0x0") is True

    def test_invalid_window_id_formats(self):
        """Test invalid window ID formats."""
        from argus_overview.utils.window_utils import is_valid_window_id

        assert is_valid_window_id("") is False
        assert is_valid_window_id(None) is False
        assert is_valid_window_id("12345") is False  # No 0x prefix
        assert is_valid_window_id("0x") is False  # No digits after 0x
        assert is_valid_window_id("0xGHIJKL") is False  # Invalid hex
        assert is_valid_window_id("window123") is False
        assert is_valid_window_id("0x123; rm -rf /") is False  # Injection attempt

    def test_invalid_window_id_types(self):
        """Test non-string types."""
        from argus_overview.utils.window_utils import is_valid_window_id

        assert is_valid_window_id(12345) is False
        assert is_valid_window_id([]) is False
        assert is_valid_window_id({}) is False

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_move_window_validates_id(self, mock_run):
        """Test move_window validates window ID before calling subprocess."""
        from argus_overview.utils.window_utils import move_window

        # Invalid ID should return False without calling subprocess
        result = move_window("invalid", 0, 0, 100, 100)
        assert result is False
        mock_run.assert_not_called()

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_move_window_calls_xdotool(self, mock_run):
        """Test move_window calls xdotool with correct args."""
        from argus_overview.utils.window_utils import move_window

        mock_run.return_value = MagicMock(returncode=0)

        result = move_window("0x03800003", 100, 200, 800, 600)

        assert result is True
        assert mock_run.call_count >= 2  # windowmove and windowsize

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_activate_window_validates_id(self, mock_run):
        """Test activate_window validates window ID."""
        from argus_overview.utils.window_utils import activate_window

        result = activate_window("invalid")
        assert result is False
        mock_run.assert_not_called()

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_activate_window_calls_xdotool(self, mock_run):
        """Test activate_window calls xdotool."""
        from argus_overview.utils.window_utils import activate_window

        mock_run.return_value = MagicMock(returncode=0)

        result = activate_window("0x03800003")

        assert result is True
        mock_run.assert_called()

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_get_focused_window_success(self, mock_run):
        """Test get_focused_window returns window ID."""
        from argus_overview.utils.window_utils import get_focused_window

        mock_run.return_value = MagicMock(returncode=0, stdout=b"58720259\n")

        result = get_focused_window()

        # 58720259 in hex is 0x3800003
        assert result == "0x3800003"

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_get_focused_window_failure(self, mock_run):
        """Test get_focused_window handles errors."""
        from argus_overview.utils.window_utils import get_focused_window

        mock_run.side_effect = Exception("xdotool not found")

        result = get_focused_window()

        assert result is None

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_get_focused_window_invalid_output(self, mock_run):
        """Test get_focused_window handles non-integer output."""
        from argus_overview.utils.window_utils import get_focused_window

        # xdotool returns something that can't be converted to int
        mock_run.return_value = MagicMock(returncode=0, stdout=b"not_a_number\n")

        result = get_focused_window()

        # Should return None since "not_a_number" isn't a valid window ID
        assert result is None

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_move_window_timeout_fallback(self, mock_run):
        """Test move_window falls back when --sync times out."""
        import subprocess

        from argus_overview.utils.window_utils import move_window

        # First call (with --sync) times out, second (without) succeeds
        mock_run.side_effect = [
            subprocess.TimeoutExpired("xdotool", 2),  # windowmove --sync timeout
            MagicMock(returncode=0),  # windowmove without --sync
            subprocess.TimeoutExpired("xdotool", 2),  # windowsize --sync timeout
            MagicMock(returncode=0),  # windowsize without --sync
        ]

        result = move_window("0x03800003", 100, 200, 800, 600)

        assert result is True
        assert mock_run.call_count == 4

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_move_window_exception(self, mock_run):
        """Test move_window handles unexpected exceptions."""
        from argus_overview.utils.window_utils import move_window

        mock_run.side_effect = OSError("xdotool crashed")

        result = move_window("0x03800003", 100, 200, 800, 600)

        assert result is False

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_activate_window_timeout_fallback(self, mock_run):
        """Test activate_window falls back when --sync times out."""
        import subprocess

        from argus_overview.utils.window_utils import activate_window

        mock_run.side_effect = [
            subprocess.TimeoutExpired("xdotool", 2),  # First call with --sync
            MagicMock(returncode=0),  # Fallback without --sync
        ]

        result = activate_window("0x03800003")

        assert result is True
        assert mock_run.call_count == 2

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_activate_window_exception(self, mock_run):
        """Test activate_window handles unexpected exceptions."""
        from argus_overview.utils.window_utils import activate_window

        mock_run.side_effect = OSError("xdotool crashed")

        result = activate_window("0x03800003")

        assert result is False


class TestRunX11Subprocess:
    """Tests for run_x11_subprocess retry helper."""

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_success_on_first_attempt(self, mock_run):
        """Test successful command on first try."""
        from argus_overview.utils.window_utils import run_x11_subprocess

        mock_run.return_value = MagicMock(returncode=0)

        result = run_x11_subprocess(["xdotool", "getwindowfocus"], max_attempts=3)

        assert result.returncode == 0
        assert mock_run.call_count == 1

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_retries_on_failure(self, mock_run):
        """Test retries on transient failure then succeeds."""
        import subprocess as sp

        from argus_overview.utils.window_utils import run_x11_subprocess

        mock_run.side_effect = [
            sp.TimeoutExpired("xdotool", 2),
            MagicMock(returncode=0),
        ]

        result = run_x11_subprocess(["xdotool", "getwindowfocus"], max_attempts=3, backoff=0.01)

        assert result.returncode == 0
        assert mock_run.call_count == 2

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_raises_after_all_attempts_exhausted(self, mock_run):
        """Test raises exception after all retries fail."""
        import subprocess as sp

        import pytest

        from argus_overview.utils.window_utils import run_x11_subprocess

        mock_run.side_effect = sp.TimeoutExpired("xdotool", 2)

        with pytest.raises(sp.TimeoutExpired):
            run_x11_subprocess(["xdotool", "getwindowfocus"], max_attempts=2, backoff=0.01)

        assert mock_run.call_count == 2

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_nonzero_returncode_triggers_retry(self, mock_run):
        """Test non-zero return code is treated as failure when check_returncode=True."""
        import subprocess as sp

        import pytest

        from argus_overview.utils.window_utils import run_x11_subprocess

        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"error")

        with pytest.raises(sp.CalledProcessError):
            run_x11_subprocess(
                ["wmctrl", "-l"], max_attempts=2, backoff=0.01, check_returncode=True
            )

        assert mock_run.call_count == 2

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_nonzero_returncode_ignored_when_unchecked(self, mock_run):
        """Test non-zero return code passes through when check_returncode=False."""
        from argus_overview.utils.window_utils import run_x11_subprocess

        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"err")

        result = run_x11_subprocess(
            ["wmctrl", "-l"], max_attempts=2, backoff=0.01, check_returncode=False
        )

        assert result.returncode == 1
        assert mock_run.call_count == 1

    @patch("argus_overview.utils.window_utils.subprocess.run")
    def test_max_attempts_clamped(self, mock_run):
        """Test max_attempts is clamped between 1 and 5."""
        import subprocess as sp

        import pytest

        from argus_overview.utils.window_utils import run_x11_subprocess

        mock_run.side_effect = sp.TimeoutExpired("cmd", 1)

        # max_attempts=0 should be clamped to 1
        with pytest.raises(sp.TimeoutExpired):
            run_x11_subprocess(["cmd"], max_attempts=0, backoff=0.01)
        assert mock_run.call_count == 1

        mock_run.reset_mock()
        mock_run.side_effect = sp.TimeoutExpired("cmd", 1)

        # max_attempts=10 should be clamped to 5
        with pytest.raises(sp.TimeoutExpired):
            run_x11_subprocess(["cmd"], max_attempts=10, backoff=0.01)
        assert mock_run.call_count == 5


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
        assert hasattr(utils, "run_x11_subprocess")
