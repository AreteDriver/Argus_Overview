"""Tests for Windows platform module.

All Win32 APIs are mocked since tests run on Linux.
Covers WindowManagerWindows, WindowCaptureWindows, ScreenManagerWindows,
EVEPathResolverWindows, and HotkeyHelperWindows.
"""

from contextlib import ExitStack
from pathlib import Path
from queue import Empty
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

MODULE = "argus_overview.platform.windows"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_win32():
    """Provide mocked Win32 modules and set HAS_WIN32=True."""
    mock_gui = MagicMock(name="win32gui")
    mock_api = MagicMock(name="win32api")
    mock_con = MagicMock(name="win32con")
    mock_ui = MagicMock(name="win32ui")
    mock_windll = MagicMock(name="windll")
    mock_pywintypes = MagicMock(name="pywintypes")

    # win32con constants
    mock_con.SWP_NOZORDER = 0x0004
    mock_con.SWP_NOSIZE = 0x0001
    mock_con.SW_MINIMIZE = 6
    mock_con.SW_RESTORE = 9

    # pywintypes.error must be an exception type
    mock_pywintypes.error = type("pywintypes_error", (Exception,), {})

    error_tuple = (mock_pywintypes.error, ValueError, OSError)

    with ExitStack() as stack:
        stack.enter_context(patch(f"{MODULE}.HAS_WIN32", True))
        stack.enter_context(patch(f"{MODULE}.win32gui", mock_gui))
        stack.enter_context(patch(f"{MODULE}.win32api", mock_api))
        stack.enter_context(patch(f"{MODULE}.win32con", mock_con))
        stack.enter_context(patch(f"{MODULE}.win32ui", mock_ui))
        stack.enter_context(patch(f"{MODULE}.windll", mock_windll))
        stack.enter_context(patch(f"{MODULE}.pywintypes", mock_pywintypes))
        stack.enter_context(patch(f"{MODULE}._WIN32_CALL_ERRORS", error_tuple))
        yield {
            "gui": mock_gui,
            "api": mock_api,
            "con": mock_con,
            "ui": mock_ui,
            "windll": mock_windll,
            "pywintypes": mock_pywintypes,
        }


# ---------------------------------------------------------------------------
# _WIN32_CALL_ERRORS
# ---------------------------------------------------------------------------


class TestWin32CallErrors:
    """Tests for the _WIN32_CALL_ERRORS sentinel tuple."""

    def test_errors_without_win32(self):
        """When HAS_WIN32 is False, tuple should contain ValueError and OSError only."""
        from argus_overview.platform.windows import _WIN32_CALL_ERRORS, HAS_WIN32

        if not HAS_WIN32:
            assert _WIN32_CALL_ERRORS == (ValueError, OSError)

    def test_errors_with_win32(self, mock_win32):
        """When HAS_WIN32 is True, tuple should include pywintypes.error."""
        pywintypes_error = mock_win32["pywintypes"].error
        with patch(
            f"{MODULE}._WIN32_CALL_ERRORS",
            (pywintypes_error, ValueError, OSError),
        ):
            assert pywintypes_error in (pywintypes_error, ValueError, OSError)


# ---------------------------------------------------------------------------
# WindowManagerWindows
# ---------------------------------------------------------------------------


class TestWindowManagerWindows:
    """Tests for WindowManagerWindows."""

    # --- HAS_WIN32=False fallback ---

    def test_init_logs_warning_without_win32(self, caplog):
        """Constructor logs warning when Win32 unavailable."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowManagerWindows

            with caplog.at_level("WARNING"):
                WindowManagerWindows()
            assert "pywin32 not available" in caplog.text

    def test_get_window_list_no_win32(self):
        """Returns empty list without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowManagerWindows

            mgr = WindowManagerWindows()
            assert mgr.get_window_list() == []

    def test_get_eve_windows_no_win32(self):
        """Returns empty list without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowManagerWindows

            mgr = WindowManagerWindows()
            assert mgr.get_eve_windows() == []

    def test_move_window_no_win32(self):
        """Returns False without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowManagerWindows

            mgr = WindowManagerWindows()
            assert mgr.move_window("0x1", 0, 0, 100, 100) is False

    def test_activate_window_no_win32(self):
        """Returns False without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowManagerWindows

            mgr = WindowManagerWindows()
            assert mgr.activate_window("0x1") is False

    def test_minimize_window_no_win32(self):
        """Returns False without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowManagerWindows

            mgr = WindowManagerWindows()
            assert mgr.minimize_window("0x1") is False

    def test_restore_window_no_win32(self):
        """Returns False without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowManagerWindows

            mgr = WindowManagerWindows()
            assert mgr.restore_window("0x1") is False

    def test_get_focused_window_no_win32(self):
        """Returns None without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowManagerWindows

            mgr = WindowManagerWindows()
            assert mgr.get_focused_window() is None

    def test_get_window_title_no_win32(self):
        """Returns 'Unknown' without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowManagerWindows

            mgr = WindowManagerWindows()
            assert mgr.get_window_title("0x1") == "Unknown"

    # --- HAS_WIN32=True with mocked Win32 ---

    def test_get_window_list_enumerates(self, mock_win32):
        """EnumWindows callback collects visible, titled, top-level windows."""
        gui = mock_win32["gui"]

        def fake_enum(callback, _):
            # hwnd=100: visible, titled, top-level -> included
            gui.IsWindowVisible.return_value = True
            gui.GetWindowText.return_value = "Notepad"
            gui.GetParent.return_value = 0
            callback(100, None)

            # hwnd=200: not visible -> excluded
            gui.IsWindowVisible.return_value = False
            callback(200, None)

            # hwnd=300: visible, no title -> excluded
            gui.IsWindowVisible.return_value = True
            gui.GetWindowText.return_value = ""
            callback(300, None)

            # hwnd=400: visible, titled, has parent -> excluded
            gui.GetWindowText.return_value = "Child"
            gui.GetParent.return_value = 100
            callback(400, None)

        gui.EnumWindows.side_effect = fake_enum

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        result = mgr.get_window_list()

        assert len(result) == 1
        assert result[0] == ("0x64", "Notepad")

    def test_get_window_list_enum_error(self, mock_win32):
        """EnumWindows error returns empty list."""
        gui = mock_win32["gui"]
        gui.EnumWindows.side_effect = ValueError("enum failed")

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        result = mgr.get_window_list()
        assert result == []

    def test_get_eve_windows_matches_patterns(self, mock_win32):
        """EVE windows are found by title pattern matching."""
        gui = mock_win32["gui"]

        def fake_enum(callback, _):
            gui.IsWindowVisible.return_value = True
            # Match "EVE - CharName"
            gui.GetWindowText.return_value = "EVE - Aura"
            callback(0x10, None)
            # Match "EVE Online - CharName"
            gui.GetWindowText.return_value = "EVE Online - Pilot"
            callback(0x20, None)
            # No match
            gui.GetWindowText.return_value = "Discord"
            callback(0x30, None)

        gui.EnumWindows.side_effect = fake_enum

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        result = mgr.get_eve_windows()

        assert len(result) == 2
        assert result[0] == ("0x10", "EVE - Aura")
        assert result[1] == ("0x20", "EVE Online - Pilot")

    def test_get_eve_windows_skips_invisible(self, mock_win32):
        """Invisible windows are skipped in EVE enumeration."""
        gui = mock_win32["gui"]

        def fake_enum(callback, _):
            gui.IsWindowVisible.return_value = False
            gui.GetWindowText.return_value = "EVE - Hidden"
            callback(0x10, None)

        gui.EnumWindows.side_effect = fake_enum

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.get_eve_windows() == []

    def test_get_eve_windows_handles_getwindowtext_error(self, mock_win32):
        """GetWindowText error in callback is swallowed."""
        gui = mock_win32["gui"]

        def fake_enum(callback, _):
            gui.IsWindowVisible.return_value = True
            gui.GetWindowText.side_effect = ValueError("access denied")
            callback(0x10, None)

        gui.EnumWindows.side_effect = fake_enum

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.get_eve_windows() == []

    def test_get_eve_windows_enum_error(self, mock_win32):
        """EnumWindows error returns empty list."""
        gui = mock_win32["gui"]
        gui.EnumWindows.side_effect = OSError("failed")

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.get_eve_windows() == []

    def test_get_eve_windows_empty_title(self, mock_win32):
        """Empty title in EVE enum callback is skipped."""
        gui = mock_win32["gui"]

        def fake_enum(callback, _):
            gui.IsWindowVisible.return_value = True
            gui.GetWindowText.return_value = ""
            callback(0x10, None)

        gui.EnumWindows.side_effect = fake_enum

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.get_eve_windows() == []

    def test_move_window_success(self, mock_win32):
        """Successful window move with valid dimensions."""
        gui = mock_win32["gui"]
        con = mock_win32["con"]

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        result = mgr.move_window("0x64", 10, 20, 800, 600)

        assert result is True
        gui.SetWindowPos.assert_called_once_with(0x64, 0, 10, 20, 800, 600, con.SWP_NOZORDER)

    def test_move_window_nosize_flag_zero_dimensions(self, mock_win32):
        """SWP_NOSIZE added when w or h <= 0."""
        gui = mock_win32["gui"]
        con = mock_win32["con"]

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        mgr.move_window("0x64", 10, 20, 0, 0)

        expected_flags = con.SWP_NOZORDER | con.SWP_NOSIZE
        gui.SetWindowPos.assert_called_once_with(0x64, 0, 10, 20, 0, 0, expected_flags)

    def test_move_window_nosize_flag_negative_dimensions(self, mock_win32):
        """SWP_NOSIZE added when w or h are negative."""
        gui = mock_win32["gui"]
        con = mock_win32["con"]

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        mgr.move_window("0x64", 0, 0, -1, -1)

        expected_flags = con.SWP_NOZORDER | con.SWP_NOSIZE
        gui.SetWindowPos.assert_called_once_with(0x64, 0, 0, 0, -1, -1, expected_flags)

    def test_move_window_invalid_id(self, mock_win32):
        """Invalid window ID returns False."""
        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.move_window("not_hex", 0, 0, 100, 100) is False

    def test_move_window_api_error(self, mock_win32):
        """SetWindowPos error returns False."""
        gui = mock_win32["gui"]
        gui.SetWindowPos.side_effect = ValueError("move failed")

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.move_window("0x64", 0, 0, 100, 100) is False

    def test_activate_window_success(self, mock_win32):
        """Successful window activation."""
        gui = mock_win32["gui"]

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.activate_window("0xff") is True
        gui.SetForegroundWindow.assert_called_once_with(0xFF)

    def test_activate_window_invalid_id(self, mock_win32):
        """Invalid window ID returns False."""
        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.activate_window("zzz") is False

    def test_activate_window_api_error(self, mock_win32):
        """SetForegroundWindow error returns False."""
        gui = mock_win32["gui"]
        gui.SetForegroundWindow.side_effect = OSError("failed")

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.activate_window("0x1") is False

    def test_minimize_window_success(self, mock_win32):
        """Successful window minimization."""
        gui = mock_win32["gui"]
        con = mock_win32["con"]

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.minimize_window("0xa") is True
        gui.ShowWindow.assert_called_once_with(0xA, con.SW_MINIMIZE)

    def test_minimize_window_api_error(self, mock_win32):
        """ShowWindow error returns False."""
        gui = mock_win32["gui"]
        gui.ShowWindow.side_effect = ValueError("fail")

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.minimize_window("0xa") is False

    def test_restore_window_success(self, mock_win32):
        """Successful window restore."""
        gui = mock_win32["gui"]
        con = mock_win32["con"]

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.restore_window("0xb") is True
        gui.ShowWindow.assert_called_once_with(0xB, con.SW_RESTORE)

    def test_restore_window_api_error(self, mock_win32):
        """ShowWindow error on restore returns False."""
        gui = mock_win32["gui"]
        gui.ShowWindow.side_effect = OSError("fail")

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.restore_window("0xb") is False

    def test_get_focused_window_returns_hex(self, mock_win32):
        """Returns hex-formatted window ID."""
        gui = mock_win32["gui"]
        gui.GetForegroundWindow.return_value = 0xABC

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.get_focused_window() == "0xabc"

    def test_get_focused_window_returns_none_for_zero(self, mock_win32):
        """Returns None when no window focused (hwnd=0)."""
        gui = mock_win32["gui"]
        gui.GetForegroundWindow.return_value = 0

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.get_focused_window() is None

    def test_get_focused_window_api_error(self, mock_win32):
        """API error returns None."""
        gui = mock_win32["gui"]
        gui.GetForegroundWindow.side_effect = ValueError("fail")

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.get_focused_window() is None

    def test_get_window_title_success(self, mock_win32):
        """Returns window title string."""
        gui = mock_win32["gui"]
        gui.GetWindowText.return_value = "My App"

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.get_window_title("0x1") == "My App"

    def test_get_window_title_api_error(self, mock_win32):
        """API error returns 'Unknown'."""
        gui = mock_win32["gui"]
        gui.GetWindowText.side_effect = ValueError("fail")

        from argus_overview.platform.windows import WindowManagerWindows

        mgr = WindowManagerWindows()
        assert mgr.get_window_title("0x1") == "Unknown"

    # --- is_valid_window_id ---

    def test_is_valid_window_id_hex_with_prefix(self):
        """Hex with 0x prefix is valid."""
        from argus_overview.platform.windows import WindowManagerWindows

        with patch(f"{MODULE}.HAS_WIN32", False):
            mgr = WindowManagerWindows()
        assert mgr.is_valid_window_id("0x1a2b") is True

    def test_is_valid_window_id_hex_without_prefix(self):
        """Hex without 0x prefix is valid."""
        from argus_overview.platform.windows import WindowManagerWindows

        with patch(f"{MODULE}.HAS_WIN32", False):
            mgr = WindowManagerWindows()
        assert mgr.is_valid_window_id("1a2b") is True

    def test_is_valid_window_id_empty_string(self):
        """Empty string is invalid."""
        from argus_overview.platform.windows import WindowManagerWindows

        with patch(f"{MODULE}.HAS_WIN32", False):
            mgr = WindowManagerWindows()
        assert mgr.is_valid_window_id("") is False

    def test_is_valid_window_id_none(self):
        """None is invalid."""
        from argus_overview.platform.windows import WindowManagerWindows

        with patch(f"{MODULE}.HAS_WIN32", False):
            mgr = WindowManagerWindows()
        assert mgr.is_valid_window_id(None) is False

    def test_is_valid_window_id_non_hex(self):
        """Non-hex string is invalid."""
        from argus_overview.platform.windows import WindowManagerWindows

        with patch(f"{MODULE}.HAS_WIN32", False):
            mgr = WindowManagerWindows()
        assert mgr.is_valid_window_id("xyz") is False

    def test_is_valid_window_id_integer_type(self):
        """Non-string type is invalid."""
        from argus_overview.platform.windows import WindowManagerWindows

        with patch(f"{MODULE}.HAS_WIN32", False):
            mgr = WindowManagerWindows()
        assert mgr.is_valid_window_id(123) is False


# ---------------------------------------------------------------------------
# WindowCaptureWindows
# ---------------------------------------------------------------------------


class TestWindowCaptureWindows:
    """Tests for WindowCaptureWindows."""

    def _make_capture(self, mock_win32=None):
        """Create a capture instance (not started)."""
        from argus_overview.platform.windows import WindowCaptureWindows

        cap = WindowCaptureWindows(max_workers=2)
        return cap

    def _setup_gdi_mocks(self, mock_win32, width=100, height=80):
        """Set up the full GDI mock chain for capture_window_sync.

        Returns (mock_dc, mock_save_dc, mock_bitmap, mock_hwnd_dc).
        """
        gui = mock_win32["gui"]
        ui = mock_win32["ui"]

        # IsIconic must return False (0) so window is not skipped as minimized
        gui.IsIconic.return_value = 0

        gui.GetWindowRect.return_value = (0, 0, width, height)

        mock_hwnd_dc = MagicMock(name="hwnd_dc_handle")
        mock_dc = MagicMock(name="mfcDC")
        mock_save_dc = MagicMock(name="saveDC")
        mock_bitmap = MagicMock(name="saveBitMap")

        gui.GetWindowDC.return_value = mock_hwnd_dc
        ui.CreateDCFromHandle.return_value = mock_dc
        mock_dc.CreateCompatibleDC.return_value = mock_save_dc
        ui.CreateBitmap.return_value = mock_bitmap
        mock_bitmap.GetInfo.return_value = {"bmWidth": width, "bmHeight": height}
        mock_bitmap.GetBitmapBits.return_value = b"\x00" * (width * height * 4)
        mock_bitmap.GetHandle.return_value = 999

        return mock_dc, mock_save_dc, mock_bitmap, mock_hwnd_dc

    # --- Lifecycle ---

    def test_init_defaults(self, mock_win32):
        """Constructor sets defaults correctly."""
        cap = self._make_capture(mock_win32)
        assert cap.max_workers == 2
        assert cap.running is False
        assert cap.workers == []

    def test_start_creates_workers(self, mock_win32):
        """Start creates and starts worker threads."""
        cap = self._make_capture(mock_win32)
        cap.start()
        try:
            assert cap.running is True
            assert len(cap.workers) == 2
            for w in cap.workers:
                assert w.daemon is True
                assert w.is_alive()
        finally:
            cap.stop()

    def test_start_idempotent(self, mock_win32):
        """Calling start twice does not double workers."""
        cap = self._make_capture(mock_win32)
        cap.start()
        cap.start()
        try:
            assert len(cap.workers) == 2
        finally:
            cap.stop()

    def test_stop_clears_running(self, mock_win32):
        """Stop sets running to False."""
        cap = self._make_capture(mock_win32)
        cap.start()
        cap.stop()
        assert cap.running is False

    def test_stop_sets_stop_event(self, mock_win32):
        """Stop sets the stop event."""
        cap = self._make_capture(mock_win32)
        cap._stop_event.clear()  # Simulate running
        cap.stop()
        assert cap._stop_event.is_set()

    def test_stop_clears_request_queue(self, mock_win32):
        """Stop drains the request queue."""
        cap = self._make_capture(mock_win32)
        cap.request_queue.put(("id", 1, 1.0))
        cap.request_queue.put(("id2", 2, 1.0))
        cap.stop()
        assert cap.request_queue.empty()

    # --- capture_window_async ---

    def test_capture_window_async_returns_uuid(self, mock_win32):
        """Async capture returns a valid UUID request ID."""
        import uuid as uuid_mod

        cap = self._make_capture(mock_win32)
        req_id = cap.capture_window_async("0xff", 1.0)
        assert req_id != ""
        # Validate UUID format
        uuid_mod.UUID(req_id)

    def test_capture_window_async_queues_request(self, mock_win32):
        """Request is placed on the queue with int hwnd."""
        cap = self._make_capture(mock_win32)
        req_id = cap.capture_window_async("0xff", 0.5)
        item = cap.request_queue.get_nowait()
        assert item[0] == req_id
        assert item[1] == 0xFF
        assert item[2] == 0.5

    def test_capture_window_async_invalid_id(self, mock_win32):
        """Invalid window ID returns empty string."""
        cap = self._make_capture(mock_win32)
        result = cap.capture_window_async("not_hex", 1.0)
        assert result == ""

    def test_capture_window_async_empty_id(self, mock_win32):
        """Empty window ID returns empty string."""
        cap = self._make_capture(mock_win32)
        result = cap.capture_window_async("", 1.0)
        assert result == ""

    # --- get_result ---

    def test_get_result_returns_none_on_empty(self, mock_win32):
        """Returns None when result queue is empty."""
        cap = self._make_capture(mock_win32)
        assert cap.get_result(timeout=0.01) is None

    def test_get_result_returns_queued_item(self, mock_win32):
        """Returns item from result queue."""
        cap = self._make_capture(mock_win32)
        sentinel = ("req-1", "0xff", Image.new("RGB", (10, 10)))
        cap.result_queue.put(sentinel)
        result = cap.get_result(timeout=0.1)
        assert result[0] == "req-1"
        assert result[1] == "0xff"

    # --- _worker ---

    def test_worker_processes_request(self, mock_win32):
        """Worker processes a capture request and puts result."""
        cap = self._make_capture(mock_win32)
        fake_image = Image.new("RGB", (100, 100))

        with patch.object(type(cap), "capture_window_sync", return_value=fake_image):
            cap._stop_event.clear()  # Mark as running
            cap.request_queue.put(("req-1", 0xFF, 1.0))
            cap.request_queue.put(None)  # Sentinel to break inner loop
            cap._worker()

            result = cap.result_queue.get_nowait()
            assert result[0] == "req-1"
            assert result[1] == "0xff"
            assert result[2] is fake_image

    def test_worker_handles_none_sentinel(self, mock_win32):
        """Worker exits on None sentinel."""
        cap = self._make_capture(mock_win32)
        cap._stop_event.clear()  # Mark as running
        cap.request_queue.put(None)
        # Should return without hanging
        cap._worker()

    def test_worker_handles_empty_timeout(self, mock_win32):
        """Worker continues on Empty (queue timeout) then exits when stopped."""
        cap = self._make_capture(mock_win32)

        call_count = 0

        def fake_get(timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Empty()
            # Stop the worker
            cap._stop_event.set()
            raise Empty()

        cap._stop_event.clear()  # Mark as running
        with patch.object(cap.request_queue, "get", side_effect=fake_get):
            cap._worker()
        assert call_count >= 2

    def test_worker_handles_win32_error(self, mock_win32):
        """Worker logs and continues on Win32 errors."""
        cap = self._make_capture(mock_win32)

        call_count = 0

        def fake_get(timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ("req-1", 0xFF, 1.0)
            cap._stop_event.set()  # Stop the worker
            raise Empty()

        cap._stop_event.clear()  # Mark as running
        with ExitStack() as stack:
            stack.enter_context(patch.object(cap.request_queue, "get", side_effect=fake_get))
            stack.enter_context(
                patch.object(
                    type(cap),
                    "capture_window_sync",
                    side_effect=ValueError("gdi fail"),
                )
            )
            cap._worker()

        # Should not crash, result queue stays empty
        assert cap.result_queue.empty()

    def test_worker_string_hwnd_passthrough(self, mock_win32):
        """Worker converts int hwnd to hex string in result."""
        cap = self._make_capture(mock_win32)
        fake_image = Image.new("RGB", (50, 50))

        with patch.object(type(cap), "capture_window_sync", return_value=fake_image):
            cap._stop_event.clear()  # Mark as running
            cap.request_queue.put(("req-1", 256, 1.0))
            cap.request_queue.put(None)  # Sentinel to break
            cap._worker()

            result = cap.result_queue.get_nowait()
            assert result[1] == "0x100"

    # --- capture_window_sync ---

    def test_capture_sync_no_win32(self):
        """Returns None without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import WindowCaptureWindows

            cap = WindowCaptureWindows()
            assert cap.capture_window_sync("0x1") is None

    def test_capture_sync_string_window_id(self, mock_win32):
        """Handles string window ID and produces an Image."""
        self._setup_gdi_mocks(mock_win32, 100, 80)

        cap = self._make_capture(mock_win32)

        fake_img = Image.new("RGB", (100, 80))
        with patch(f"{MODULE}.Image") as mock_image_mod:
            mock_image_mod.frombuffer.return_value = fake_img
            mock_image_mod.LANCZOS = Image.LANCZOS
            result = cap.capture_window_sync("0x64", 1.0)

        assert result is not None
        assert result.size == (100, 80)

    def test_capture_sync_int_window_id(self, mock_win32):
        """Handles int window ID directly."""
        gui = mock_win32["gui"]
        self._setup_gdi_mocks(mock_win32, 200, 100)

        cap = self._make_capture(mock_win32)

        fake_img = Image.new("RGB", (200, 100))
        with patch(f"{MODULE}.Image") as mock_image_mod:
            mock_image_mod.frombuffer.return_value = fake_img
            mock_image_mod.LANCZOS = Image.LANCZOS
            result = cap.capture_window_sync(100, 1.0)

        assert result is not None
        gui.GetWindowRect.assert_called_once_with(100)

    def test_capture_sync_minimized_returns_none(self, mock_win32):
        """Returns None for minimized (iconic) windows."""
        gui = mock_win32["gui"]
        gui.IsIconic.return_value = 1  # Window is minimized

        cap = self._make_capture(mock_win32)
        assert cap.capture_window_sync("0x1") is None

    def test_capture_sync_zero_dimensions(self, mock_win32):
        """Returns None for zero-dimension windows."""
        gui = mock_win32["gui"]
        gui.IsIconic.return_value = 0
        gui.GetWindowRect.return_value = (100, 100, 100, 100)  # width=0, height=0

        cap = self._make_capture(mock_win32)
        assert cap.capture_window_sync("0x1") is None

    def test_capture_sync_negative_dimensions(self, mock_win32):
        """Returns None for negative-dimension windows."""
        gui = mock_win32["gui"]
        gui.IsIconic.return_value = 0
        gui.GetWindowRect.return_value = (200, 200, 100, 100)  # negative w/h

        cap = self._make_capture(mock_win32)
        assert cap.capture_window_sync("0x1") is None

    def test_capture_sync_with_scale(self, mock_win32):
        """Scale < 1.0 resizes the captured image."""
        self._setup_gdi_mocks(mock_win32, 200, 100)

        cap = self._make_capture(mock_win32)

        fake_img = MagicMock(spec=Image.Image)
        fake_img.size = (200, 100)
        resized_img = MagicMock(spec=Image.Image)
        resized_img.size = (100, 50)
        fake_img.resize.return_value = resized_img

        with patch(f"{MODULE}.Image") as mock_image_mod:
            mock_image_mod.frombuffer.return_value = fake_img
            mock_image_mod.Resampling.LANCZOS = Image.Resampling.LANCZOS
            result = cap.capture_window_sync("0x1", scale=0.5)

        assert result is resized_img
        fake_img.resize.assert_called_once_with((100, 50), Image.Resampling.LANCZOS)

    def test_capture_sync_scale_1_no_resize(self, mock_win32):
        """Scale = 1.0 does not resize."""
        self._setup_gdi_mocks(mock_win32, 150, 75)

        cap = self._make_capture(mock_win32)

        fake_img = Image.new("RGB", (150, 75))
        with patch(f"{MODULE}.Image") as mock_image_mod:
            mock_image_mod.frombuffer.return_value = fake_img
            mock_image_mod.LANCZOS = Image.LANCZOS
            result = cap.capture_window_sync("0x1", scale=1.0)

        assert result is not None
        assert result.size == (150, 75)

    def test_capture_sync_gdi_cleanup(self, mock_win32):
        """GDI resources are cleaned up after capture."""
        gui = mock_win32["gui"]
        mock_dc, mock_save_dc, mock_bitmap, mock_hwnd_dc = self._setup_gdi_mocks(
            mock_win32, 100, 50
        )

        cap = self._make_capture(mock_win32)

        fake_img = Image.new("RGB", (100, 50))
        with patch(f"{MODULE}.Image") as mock_image_mod:
            mock_image_mod.frombuffer.return_value = fake_img
            mock_image_mod.LANCZOS = Image.LANCZOS
            cap.capture_window_sync("0x1")

        gui.DeleteObject.assert_called_once_with(999)
        mock_save_dc.DeleteDC.assert_called_once()
        mock_dc.DeleteDC.assert_called_once()

    def test_capture_sync_gdi_cleanup_on_error(self, mock_win32):
        """GDI resources are cleaned up even when capture fails mid-way."""
        gui = mock_win32["gui"]
        ui = mock_win32["ui"]

        gui.IsIconic.return_value = 0
        gui.GetWindowRect.return_value = (0, 0, 100, 50)

        mock_hwnd_dc = MagicMock(name="hwnd_dc_handle")
        mock_dc = MagicMock(name="mfcDC")
        mock_save_dc = MagicMock(name="saveDC")
        mock_bitmap = MagicMock(name="saveBitMap")

        gui.GetWindowDC.return_value = mock_hwnd_dc
        ui.CreateDCFromHandle.return_value = mock_dc
        mock_dc.CreateCompatibleDC.return_value = mock_save_dc
        ui.CreateBitmap.return_value = mock_bitmap
        mock_bitmap.GetHandle.return_value = 888

        # Fail during bitmap operations
        mock_bitmap.CreateCompatibleBitmap.side_effect = ValueError("gdi error")

        cap = self._make_capture(mock_win32)
        result = cap.capture_window_sync("0x1")

        assert result is None
        # Cleanup should still happen for resources created before failure
        gui.DeleteObject.assert_called_once_with(888)
        mock_save_dc.DeleteDC.assert_called_once()
        mock_dc.DeleteDC.assert_called_once()

    def test_capture_sync_api_error(self, mock_win32):
        """Win32 error during capture returns None."""
        gui = mock_win32["gui"]
        gui.IsIconic.return_value = 0
        gui.GetWindowRect.side_effect = ValueError("access denied")

        cap = self._make_capture(mock_win32)
        assert cap.capture_window_sync("0x1") is None


# ---------------------------------------------------------------------------
# ScreenManagerWindows
# ---------------------------------------------------------------------------


class TestScreenManagerWindows:
    """Tests for ScreenManagerWindows."""

    def test_get_all_monitors_no_win32(self):
        """Returns default 1920x1080 without Win32."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import ScreenManagerWindows

            mgr = ScreenManagerWindows()
            monitors = mgr.get_all_monitors()
            assert len(monitors) == 1
            assert monitors[0].width == 1920
            assert monitors[0].height == 1080
            assert monitors[0].is_primary is True

    def test_get_all_monitors_enumerates(self, mock_win32):
        """EnumDisplayMonitors callback collects monitor geometries."""
        api = mock_win32["api"]

        def fake_enum(hdc, clip, callback, data):
            callback(None, None, (0, 0, 1920, 1080), None)
            callback(None, None, (1920, 0, 3840, 1080), None)

        api.EnumDisplayMonitors.side_effect = fake_enum

        from argus_overview.platform.windows import ScreenManagerWindows

        mgr = ScreenManagerWindows()
        monitors = mgr.get_all_monitors()

        assert len(monitors) == 2
        assert monitors[0].x == 0
        assert monitors[0].width == 1920
        assert monitors[0].is_primary is True
        assert monitors[1].x == 1920
        assert monitors[1].width == 1920
        assert monitors[1].is_primary is False

    def test_get_all_monitors_enum_error(self, mock_win32):
        """Error returns default monitor."""
        api = mock_win32["api"]
        api.EnumDisplayMonitors.side_effect = OSError("enum failed")

        from argus_overview.platform.windows import ScreenManagerWindows

        mgr = ScreenManagerWindows()
        monitors = mgr.get_all_monitors()

        assert len(monitors) == 1
        assert monitors[0].width == 1920

    def test_get_all_monitors_empty_returns_default(self, mock_win32):
        """No monitors enumerated returns default."""
        api = mock_win32["api"]

        def fake_enum(hdc, clip, callback, data):
            pass  # No callbacks

        api.EnumDisplayMonitors.side_effect = fake_enum

        from argus_overview.platform.windows import ScreenManagerWindows

        mgr = ScreenManagerWindows()
        monitors = mgr.get_all_monitors()

        assert len(monitors) == 1
        assert monitors[0].width == 1920

    def test_get_screen_geometry_first_monitor(self, mock_win32):
        """Index 0 returns first monitor."""
        api = mock_win32["api"]

        def fake_enum(hdc, clip, callback, data):
            callback(None, None, (0, 0, 2560, 1440), None)
            callback(None, None, (2560, 0, 4480, 1440), None)

        api.EnumDisplayMonitors.side_effect = fake_enum

        from argus_overview.platform.windows import ScreenManagerWindows

        mgr = ScreenManagerWindows()
        geom = mgr.get_screen_geometry(0)

        assert geom.width == 2560
        assert geom.height == 1440

    def test_get_screen_geometry_second_monitor(self, mock_win32):
        """Index 1 returns second monitor."""
        api = mock_win32["api"]

        def fake_enum(hdc, clip, callback, data):
            callback(None, None, (0, 0, 1920, 1080), None)
            callback(None, None, (1920, 0, 3840, 1080), None)

        api.EnumDisplayMonitors.side_effect = fake_enum

        from argus_overview.platform.windows import ScreenManagerWindows

        mgr = ScreenManagerWindows()
        geom = mgr.get_screen_geometry(1)

        assert geom.x == 1920
        assert geom.width == 1920

    def test_get_screen_geometry_invalid_index_falls_back(self, mock_win32):
        """Out-of-range index falls back to first monitor."""
        api = mock_win32["api"]

        def fake_enum(hdc, clip, callback, data):
            callback(None, None, (0, 0, 2560, 1440), None)

        api.EnumDisplayMonitors.side_effect = fake_enum

        from argus_overview.platform.windows import ScreenManagerWindows

        mgr = ScreenManagerWindows()
        geom = mgr.get_screen_geometry(99)

        assert geom.width == 2560

    def test_get_screen_geometry_no_monitors_default(self):
        """No monitors at all returns 1920x1080 default."""
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import ScreenManagerWindows

            mgr = ScreenManagerWindows()
            geom = mgr.get_screen_geometry(5)

            assert geom.width == 1920
            assert geom.height == 1080
            assert geom.is_primary is True


# ---------------------------------------------------------------------------
# EVEPathResolverWindows
# ---------------------------------------------------------------------------


class TestEVEPathResolverWindows:
    """Tests for EVEPathResolverWindows."""

    def test_get_eve_settings_paths_with_localappdata(self):
        """Uses LOCALAPPDATA env var."""
        with patch.dict("os.environ", {"LOCALAPPDATA": "C:\\Users\\Test\\AppData\\Local"}):
            from argus_overview.platform.windows import EVEPathResolverWindows

            resolver = EVEPathResolverWindows()
            paths = resolver.get_eve_settings_paths()

            assert len(paths) == 1
            assert paths[0] == Path("C:\\Users\\Test\\AppData\\Local") / "CCP" / "EVE"

    def test_get_eve_settings_paths_no_env(self):
        """Falls back to empty path when LOCALAPPDATA not set."""
        with patch.dict("os.environ", {}, clear=True):
            from argus_overview.platform.windows import EVEPathResolverWindows

            resolver = EVEPathResolverWindows()
            paths = resolver.get_eve_settings_paths()

            assert len(paths) == 1
            assert "CCP" in str(paths[0])

    def test_get_eve_logs_paths_with_userprofile(self):
        """Uses USERPROFILE env var."""
        with patch.dict("os.environ", {"USERPROFILE": "C:\\Users\\Test"}):
            from argus_overview.platform.windows import EVEPathResolverWindows

            resolver = EVEPathResolverWindows()
            paths = resolver.get_eve_logs_paths()

            assert len(paths) == 1
            expected = Path("C:\\Users\\Test") / "Documents" / "EVE" / "logs" / "Gamelogs"
            assert paths[0] == expected

    def test_get_eve_logs_paths_no_env(self):
        """Falls back to empty path when USERPROFILE not set."""
        with patch.dict("os.environ", {}, clear=True):
            from argus_overview.platform.windows import EVEPathResolverWindows

            resolver = EVEPathResolverWindows()
            paths = resolver.get_eve_logs_paths()

            assert len(paths) == 1
            assert "Gamelogs" in str(paths[0])

    def test_get_config_directory_with_localappdata(self):
        """Uses LOCALAPPDATA for config dir."""
        with patch.dict("os.environ", {"LOCALAPPDATA": "C:\\Users\\Test\\AppData\\Local"}):
            from argus_overview.platform.windows import EVEPathResolverWindows

            resolver = EVEPathResolverWindows()
            config_dir = resolver.get_config_directory()

            assert config_dir == Path("C:\\Users\\Test\\AppData\\Local") / "Argus-Overview"

    def test_get_config_directory_fallback_to_home(self):
        """Falls back to Path.home() when LOCALAPPDATA not set."""
        with patch.dict("os.environ", {}, clear=True):
            from argus_overview.platform.windows import EVEPathResolverWindows

            resolver = EVEPathResolverWindows()
            config_dir = resolver.get_config_directory()

            assert config_dir == Path.home() / "Argus-Overview"


# ---------------------------------------------------------------------------
# HotkeyHelperWindows
# ---------------------------------------------------------------------------


class TestHotkeyHelperWindows:
    """Tests for HotkeyHelperWindows."""

    @pytest.fixture
    def helper(self):
        with patch(f"{MODULE}.HAS_WIN32", False):
            from argus_overview.platform.windows import HotkeyHelperWindows

            return HotkeyHelperWindows()

    def test_normalize_combo_passthrough(self, helper):
        """Returns combo as-is (no normalization on Windows)."""
        assert helper.normalize_combo("ctrl+a") == "ctrl+a"

    def test_normalize_combo_empty(self, helper):
        """Empty string passed through."""
        assert helper.normalize_combo("") == ""

    def test_normalize_combo_complex(self, helper):
        """Complex combo passed through unchanged."""
        assert helper.normalize_combo("ctrl+shift+alt+f5") == "ctrl+shift+alt+f5"

    def test_is_single_key_true(self, helper):
        """Single key without + returns True."""
        assert helper.is_single_key("f1") is True

    def test_is_single_key_false_with_modifier(self, helper):
        """Key with + returns False."""
        assert helper.is_single_key("ctrl+a") is False

    def test_is_single_key_empty_string(self, helper):
        """Empty string returns False."""
        assert helper.is_single_key("") is False

    def test_is_single_key_single_char(self, helper):
        """Single character is a single key."""
        assert helper.is_single_key("a") is True

    def test_is_single_key_special(self, helper):
        """Special key name without + is single."""
        assert helper.is_single_key("escape") is True

    def test_is_single_key_multiple_modifiers(self, helper):
        """Multiple modifiers are not single key."""
        assert helper.is_single_key("ctrl+shift+a") is False


# ---------------------------------------------------------------------------
# EVE Title Patterns
# ---------------------------------------------------------------------------


class TestEVETitlePatterns:
    """Tests for EVE_TITLE_PATTERNS regex patterns."""

    def test_eve_dash_pattern(self):
        """Matches 'EVE - CharName'."""
        from argus_overview.platform.windows import EVE_TITLE_PATTERNS

        m = EVE_TITLE_PATTERNS[0].match("EVE - Aura")
        assert m is not None
        assert m.group(1) == "Aura"

    def test_eve_online_dash_pattern(self):
        """Matches 'EVE Online - CharName'."""
        from argus_overview.platform.windows import EVE_TITLE_PATTERNS

        m = EVE_TITLE_PATTERNS[1].match("EVE Online - Pilot")
        assert m is not None
        assert m.group(1) == "Pilot"

    def test_no_match_random_title(self):
        """Random title does not match."""
        from argus_overview.platform.windows import EVE_TITLE_PATTERNS

        for pattern in EVE_TITLE_PATTERNS:
            assert pattern.match("Discord") is None

    def test_no_match_partial(self):
        """Partial match (missing dash) does not match."""
        from argus_overview.platform.windows import EVE_TITLE_PATTERNS

        assert EVE_TITLE_PATTERNS[0].match("EVE Aura") is None

    def test_eve_class_name_constant(self):
        """EVE_CLASS_NAME is correct."""
        from argus_overview.platform.windows import EVE_CLASS_NAME

        assert EVE_CLASS_NAME == "triuiScreen"


# ---------------------------------------------------------------------------
# Coverage Push: WindowCaptureWindows.stop() Empty exception (lines 266-267)
# ---------------------------------------------------------------------------


class TestWindowCaptureStopEmptyException:
    """Tests for stop() when request_queue.get_nowait() raises Empty."""

    def test_stop_handles_empty_during_queue_drain(self, mock_win32):
        """Lines 266-267: Empty exception breaks the drain loop."""
        from argus_overview.platform.windows import WindowCaptureWindows

        cap = WindowCaptureWindows(max_workers=1)
        cap._stop_event.clear()  # Pretend running

        # Make the queue report non-empty but raise Empty on get
        with patch.object(cap.request_queue, "empty", return_value=False):
            with patch.object(cap.request_queue, "get_nowait", side_effect=Empty):
                cap.stop()

        assert cap._stop_event.is_set()


# ---------------------------------------------------------------------------
# Coverage Push: ScreenManagerWindows.get_screen_geometry empty monitors (line 399)
# ---------------------------------------------------------------------------


class TestScreenManagerWindowsEmptyMonitors:
    """Tests for get_screen_geometry when get_all_monitors returns empty."""

    def test_get_screen_geometry_empty_monitors_returns_default(self, mock_win32):
        """Line 399: returns 1920x1080 default when no monitors detected."""
        from argus_overview.platform.windows import ScreenManagerWindows

        mgr = ScreenManagerWindows()

        # Mock get_all_monitors to return empty list (simulating enumeration failure
        # where the callback finds zero monitors but no exception is raised)
        with patch.object(mgr, "get_all_monitors", return_value=[]):
            geom = mgr.get_screen_geometry(0)

        from argus_overview.platform.base import ScreenGeometry

        assert geom == ScreenGeometry(0, 0, 1920, 1080, True)
