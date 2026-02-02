"""
Unit tests for the Window Capture Threaded module
Tests WindowCaptureThreaded class which wraps platform-specific capture implementations.

v3.0: Tests now mock the platform abstraction layer.
"""

from unittest.mock import MagicMock, patch


class TestWindowCaptureThreadedInit:
    """Tests for WindowCaptureThreaded initialization"""

    def test_init_default_workers(self):
        """Test initialization with default worker count"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()

                assert capture.max_workers == 4
                mock_get_capture.assert_called_once_with(max_workers=4)

    def test_init_custom_workers(self):
        """Test initialization with custom worker count"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded(max_workers=8)

                assert capture.max_workers == 8
                mock_get_capture.assert_called_once_with(max_workers=8)

    def test_init_single_worker(self):
        """Test initialization with single worker"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded(max_workers=1)

                assert capture.max_workers == 1


class TestStartStop:
    """Tests for start/stop functionality"""

    def test_start_delegates_to_capture(self):
        """Test that start delegates to platform capture"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded(max_workers=3)
                capture.start()

                mock_capture.start.assert_called_once()

    def test_stop_delegates_to_capture(self):
        """Test that stop delegates to platform capture"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded(max_workers=2)
                capture.stop()

                mock_capture.stop.assert_called_once()

    def test_running_property(self):
        """Test that running property delegates to platform capture"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_capture.running = True
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()

                assert capture.running is True

                mock_capture.running = False
                assert capture.running is False


class TestCaptureWindowAsync:
    """Tests for capture_window_async method"""

    def test_capture_window_async_delegates(self):
        """Test that capture_window_async delegates to platform capture"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_capture.capture_window_async.return_value = "test-uuid-123"
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                request_id = capture.capture_window_async("0x12345", scale=0.5)

                assert request_id == "test-uuid-123"
                mock_capture.capture_window_async.assert_called_once_with("0x12345", 0.5)

    def test_capture_window_async_default_scale(self):
        """Test capture with default scale of 1.0"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_capture.capture_window_async.return_value = "test-uuid"
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                capture.capture_window_async("0x12345")

                mock_capture.capture_window_async.assert_called_once_with("0x12345", 1.0)


class TestGetResult:
    """Tests for get_result method"""

    def test_get_result_delegates(self):
        """Test get_result delegates to platform capture"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_image = MagicMock()
                mock_capture.get_result.return_value = ("req_123", "0x12345", mock_image)
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.get_result(timeout=0.5)

                assert result is not None
                assert result[0] == "req_123"
                assert result[1] == "0x12345"
                assert result[2] is mock_image
                mock_capture.get_result.assert_called_once_with(0.5)

    def test_get_result_returns_none_when_empty(self):
        """Test get_result returns None when queue is empty"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager"):
                mock_capture = MagicMock()
                mock_capture.get_result.return_value = None
                mock_get_capture.return_value = mock_capture

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.get_result(timeout=0.01)

                assert result is None


class TestGetWindowList:
    """Tests for get_window_list method"""

    def test_get_window_list_delegates(self):
        """Test get_window_list delegates to platform window manager"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture"):
            with patch("argus_overview.core.window_capture_threaded.get_window_manager") as mock_get_wm:
                mock_wm = MagicMock()
                mock_wm.get_window_list.return_value = [
                    ("0x123", "Window 1"),
                    ("0x456", "Window 2"),
                ]
                mock_get_wm.return_value = mock_wm

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.get_window_list()

                assert len(result) == 2
                assert result[0] == ("0x123", "Window 1")
                assert result[1] == ("0x456", "Window 2")
                mock_wm.get_window_list.assert_called_once()

    def test_get_window_list_empty(self):
        """Test get_window_list returns empty list"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture"):
            with patch("argus_overview.core.window_capture_threaded.get_window_manager") as mock_get_wm:
                mock_wm = MagicMock()
                mock_wm.get_window_list.return_value = []
                mock_get_wm.return_value = mock_wm

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.get_window_list()

                assert result == []


class TestActivateWindow:
    """Tests for activate_window method"""

    def test_activate_window_delegates(self):
        """Test activate_window delegates to platform window manager"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture"):
            with patch("argus_overview.core.window_capture_threaded.get_window_manager") as mock_get_wm:
                mock_wm = MagicMock()
                mock_wm.activate_window.return_value = True
                mock_get_wm.return_value = mock_wm

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.activate_window("0x12345")

                assert result is True
                mock_wm.activate_window.assert_called_once_with("0x12345")

    def test_activate_window_failure(self):
        """Test activate_window returns False on failure"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture"):
            with patch("argus_overview.core.window_capture_threaded.get_window_manager") as mock_get_wm:
                mock_wm = MagicMock()
                mock_wm.activate_window.return_value = False
                mock_get_wm.return_value = mock_wm

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.activate_window("0x99999")

                assert result is False


class TestMinimizeWindow:
    """Tests for minimize_window method"""

    def test_minimize_window_delegates(self):
        """Test minimize_window delegates to platform window manager"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture"):
            with patch("argus_overview.core.window_capture_threaded.get_window_manager") as mock_get_wm:
                mock_wm = MagicMock()
                mock_wm.minimize_window.return_value = True
                mock_get_wm.return_value = mock_wm

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.minimize_window("0x12345")

                assert result is True
                mock_wm.minimize_window.assert_called_once_with("0x12345")

    def test_minimize_window_failure(self):
        """Test minimize_window returns False on failure"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture"):
            with patch("argus_overview.core.window_capture_threaded.get_window_manager") as mock_get_wm:
                mock_wm = MagicMock()
                mock_wm.minimize_window.return_value = False
                mock_get_wm.return_value = mock_wm

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.minimize_window("0x99999")

                assert result is False


class TestRestoreWindow:
    """Tests for restore_window method"""

    def test_restore_window_delegates(self):
        """Test restore_window delegates to platform window manager"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture"):
            with patch("argus_overview.core.window_capture_threaded.get_window_manager") as mock_get_wm:
                mock_wm = MagicMock()
                mock_wm.restore_window.return_value = True
                mock_get_wm.return_value = mock_wm

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.restore_window("0x12345")

                assert result is True
                mock_wm.restore_window.assert_called_once_with("0x12345")

    def test_restore_window_failure(self):
        """Test restore_window returns False on failure"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture"):
            with patch("argus_overview.core.window_capture_threaded.get_window_manager") as mock_get_wm:
                mock_wm = MagicMock()
                mock_wm.restore_window.return_value = False
                mock_get_wm.return_value = mock_wm

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()
                result = capture.restore_window("0x99999")

                assert result is False


class TestIntegration:
    """Integration tests for the WindowCaptureThreaded wrapper"""

    def test_full_workflow(self):
        """Test full capture workflow through wrapper"""
        with patch("argus_overview.core.window_capture_threaded.get_window_capture") as mock_get_capture:
            with patch("argus_overview.core.window_capture_threaded.get_window_manager") as mock_get_wm:
                mock_capture = MagicMock()
                mock_capture.running = False
                mock_capture.capture_window_async.return_value = "req-123"
                mock_image = MagicMock()
                mock_capture.get_result.return_value = ("req-123", "0x12345", mock_image)
                mock_get_capture.return_value = mock_capture

                mock_wm = MagicMock()
                mock_get_wm.return_value = mock_wm

                from argus_overview.core.window_capture_threaded import WindowCaptureThreaded

                capture = WindowCaptureThreaded()

                # Start capture
                capture.start()
                mock_capture.start.assert_called_once()

                # Request capture
                request_id = capture.capture_window_async("0x12345")
                assert request_id == "req-123"

                # Get result
                result = capture.get_result()
                assert result is not None
                assert result[0] == "req-123"

                # Stop capture
                capture.stop()
                mock_capture.stop.assert_called_once()
