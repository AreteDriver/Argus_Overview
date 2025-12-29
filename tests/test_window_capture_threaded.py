"""
Unit tests for the Window Capture Threaded module
Tests WindowCaptureThreaded class with mocked subprocess and threading
"""
import pytest
import io
import threading
import time
from queue import Queue, Empty
from unittest.mock import Mock, patch, MagicMock, PropertyMock


class TestWindowCaptureThreadedInit:
    """Tests for WindowCaptureThreaded initialization"""

    def test_init_default_workers(self):
        """Test initialization with default worker count"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        assert capture.max_workers == 4
        assert isinstance(capture.capture_queue, Queue)
        assert isinstance(capture.result_queue, Queue)
        assert capture.workers == []
        assert capture.running is False

    def test_init_custom_workers(self):
        """Test initialization with custom worker count"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded(max_workers=8)

        assert capture.max_workers == 8

    def test_init_single_worker(self):
        """Test initialization with single worker"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded(max_workers=1)

        assert capture.max_workers == 1

    def test_init_queues_empty(self):
        """Test that queues are initially empty"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        assert capture.capture_queue.empty()
        assert capture.result_queue.empty()


class TestStartStop:
    """Tests for start/stop functionality"""

    @patch('eve_overview_pro.core.window_capture_threaded.threading.Thread')
    def test_start_creates_workers(self, mock_thread_class):
        """Test that start creates worker threads"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread

        capture = WindowCaptureThreaded(max_workers=3)
        capture.start()

        assert capture.running is True
        assert mock_thread_class.call_count == 3
        assert mock_thread.start.call_count == 3
        assert len(capture.workers) == 3

    @patch('eve_overview_pro.core.window_capture_threaded.threading.Thread')
    def test_start_sets_daemon_threads(self, mock_thread_class):
        """Test that worker threads are daemon threads"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread

        capture = WindowCaptureThreaded(max_workers=2)
        capture.start()

        # Verify daemon=True was passed
        for call in mock_thread_class.call_args_list:
            assert call[1]['daemon'] is True

    @patch('eve_overview_pro.core.window_capture_threaded.threading.Thread')
    def test_stop_sets_running_false(self, mock_thread_class):
        """Test that stop sets running to False"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread

        capture = WindowCaptureThreaded(max_workers=2)
        capture.start()
        capture.stop()

        assert capture.running is False

    @patch('eve_overview_pro.core.window_capture_threaded.threading.Thread')
    def test_stop_sends_none_to_queue(self, mock_thread_class):
        """Test that stop sends None to queue for each worker"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread

        capture = WindowCaptureThreaded(max_workers=3)
        capture.start()
        capture.stop()

        # Should have put 3 None values in queue
        none_count = 0
        while not capture.capture_queue.empty():
            item = capture.capture_queue.get_nowait()
            if item is None:
                none_count += 1

        assert none_count == 3

    @patch('eve_overview_pro.core.window_capture_threaded.threading.Thread')
    def test_stop_joins_workers(self, mock_thread_class):
        """Test that stop joins worker threads"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread

        capture = WindowCaptureThreaded(max_workers=2)
        capture.start()
        capture.stop()

        assert mock_thread.join.call_count == 2

    @patch('eve_overview_pro.core.window_capture_threaded.threading.Thread')
    def test_stop_clears_workers(self, mock_thread_class):
        """Test that stop clears the workers list"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread

        capture = WindowCaptureThreaded(max_workers=2)
        capture.start()
        assert len(capture.workers) == 2

        capture.stop()
        assert len(capture.workers) == 0


class TestCaptureWindowAsync:
    """Tests for capture_window_async method"""

    def test_capture_window_async_returns_request_id(self):
        """Test that capture_window_async returns a request ID"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        request_id = capture.capture_window_async("0x12345", scale=1.0)

        assert request_id is not None
        assert isinstance(request_id, str)
        # UUID format check
        assert len(request_id) == 36

    def test_capture_window_async_queues_task(self):
        """Test that capture_window_async puts task in queue"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        request_id = capture.capture_window_async("0x12345", scale=0.5)

        # Get the task from queue
        task = capture.capture_queue.get_nowait()

        assert task[0] == "0x12345"  # window_id
        assert task[1] == 0.5  # scale
        assert task[2] == request_id  # request_id

    def test_capture_window_async_multiple_requests(self):
        """Test multiple async capture requests"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        id1 = capture.capture_window_async("0x11111")
        id2 = capture.capture_window_async("0x22222")
        id3 = capture.capture_window_async("0x33333")

        # All IDs should be unique
        assert len({id1, id2, id3}) == 3

        # Queue should have 3 items
        assert capture.capture_queue.qsize() == 3

    def test_capture_window_async_default_scale(self):
        """Test capture with default scale of 1.0"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        capture.capture_window_async("0x12345")

        task = capture.capture_queue.get_nowait()
        assert task[1] == 1.0  # Default scale


class TestGetResult:
    """Tests for get_result method"""

    def test_get_result_returns_none_when_empty(self):
        """Test get_result returns None when queue is empty"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        result = capture.get_result(timeout=0.01)

        assert result is None

    def test_get_result_returns_tuple(self):
        """Test get_result returns tuple from queue"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        # Manually put a result in the queue
        mock_image = MagicMock()
        capture.result_queue.put(("req_123", "0x12345", mock_image))

        result = capture.get_result(timeout=0.1)

        assert result is not None
        assert result[0] == "req_123"
        assert result[1] == "0x12345"
        assert result[2] is mock_image

    def test_get_result_timeout_parameter(self):
        """Test get_result respects timeout parameter"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        start_time = time.time()
        result = capture.get_result(timeout=0.1)
        elapsed = time.time() - start_time

        assert result is None
        # Should have waited approximately 0.1 seconds
        assert elapsed >= 0.09
        assert elapsed < 0.5


class TestCaptureWindowSync:
    """Tests for _capture_window_sync method"""

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    @patch('eve_overview_pro.core.window_capture_threaded.Image')
    def test_capture_window_sync_success(self, mock_image_module, mock_subprocess):
        """Test successful synchronous window capture"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'fake png data'
        mock_subprocess.return_value = mock_result

        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.width = 800
        mock_img.height = 600
        mock_image_module.open.return_value = mock_img

        capture = WindowCaptureThreaded()
        result = capture._capture_window_sync("0x12345", scale=1.0)

        assert result is mock_img
        mock_subprocess.assert_called_once()
        mock_image_module.open.assert_called_once()

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_capture_window_sync_failure(self, mock_subprocess):
        """Test capture failure returns None"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b''
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        result = capture._capture_window_sync("0x12345", scale=1.0)

        assert result is None

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    @patch('eve_overview_pro.core.window_capture_threaded.Image')
    def test_capture_window_sync_with_scaling(self, mock_image_module, mock_subprocess):
        """Test capture with scaling"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'fake png data'
        mock_subprocess.return_value = mock_result

        mock_img = MagicMock()
        mock_img.width = 800
        mock_img.height = 600
        mock_scaled_img = MagicMock()
        mock_img.resize.return_value = mock_scaled_img
        mock_image_module.open.return_value = mock_img
        mock_image_module.Resampling.LANCZOS = "LANCZOS"

        capture = WindowCaptureThreaded()
        result = capture._capture_window_sync("0x12345", scale=0.5)

        # Should have called resize
        mock_img.resize.assert_called_once_with((400, 300), "LANCZOS")
        assert result is mock_scaled_img

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_capture_window_sync_timeout(self, mock_subprocess):
        """Test capture handles timeout"""
        import subprocess as subprocess_module
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_subprocess.side_effect = subprocess_module.TimeoutExpired("import", 1)

        capture = WindowCaptureThreaded()
        result = capture._capture_window_sync("0x12345", scale=1.0)

        assert result is None

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_capture_window_sync_exception(self, mock_subprocess):
        """Test capture handles exceptions"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_subprocess.side_effect = Exception("Unknown error")

        capture = WindowCaptureThreaded()
        result = capture._capture_window_sync("0x12345", scale=1.0)

        assert result is None

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_capture_window_sync_uses_import_command(self, mock_subprocess):
        """Test that capture uses ImageMagick import command"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b''
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        capture._capture_window_sync("0xABCD", scale=1.0)

        # Verify command
        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert cmd[0] == 'import'
        assert '-window' in cmd
        assert '0xABCD' in cmd
        assert '-silent' in cmd
        assert 'png:-' in cmd


class TestGetWindowList:
    """Tests for get_window_list method"""

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_get_window_list_success(self, mock_subprocess):
        """Test successful window list retrieval"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """0x12345 0 hostname Window Title 1
0x67890 0 hostname Window Title 2
0xABCDE 0 hostname EVE Online - Character Name"""
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        windows = capture.get_window_list()

        assert len(windows) == 3
        assert windows[0] == ("0x12345", "Window Title 1")
        assert windows[1] == ("0x67890", "Window Title 2")
        assert windows[2] == ("0xABCDE", "EVE Online - Character Name")

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_get_window_list_empty(self, mock_subprocess):
        """Test empty window list"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        windows = capture.get_window_list()

        assert windows == []

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_get_window_list_failure(self, mock_subprocess):
        """Test window list retrieval failure"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        windows = capture.get_window_list()

        assert windows == []

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_get_window_list_exception(self, mock_subprocess):
        """Test window list handles exceptions"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_subprocess.side_effect = Exception("wmctrl not found")

        capture = WindowCaptureThreaded()
        windows = capture.get_window_list()

        assert windows == []

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_get_window_list_uses_wmctrl(self, mock_subprocess):
        """Test that window list uses wmctrl command"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        capture.get_window_list()

        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert cmd == ['wmctrl', '-l']

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_get_window_list_handles_short_lines(self, mock_subprocess):
        """Test handling of malformed/short lines"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """0x12345 0 hostname Full Window Title
0x67890 short
0xABCDE 0 hostname Another Window"""
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        windows = capture.get_window_list()

        # Should skip short line
        assert len(windows) == 2


class TestActivateWindow:
    """Tests for activate_window method"""

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_activate_window_success(self, mock_subprocess):
        """Test successful window activation"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        result = capture.activate_window("0x12345")

        assert result is True

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_activate_window_failure(self, mock_subprocess):
        """Test window activation failure"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        result = capture.activate_window("0x12345")

        assert result is False

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_activate_window_exception(self, mock_subprocess):
        """Test window activation handles exceptions"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_subprocess.side_effect = Exception("wmctrl error")

        capture = WindowCaptureThreaded()
        result = capture.activate_window("0x12345")

        assert result is False

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_activate_window_uses_wmctrl(self, mock_subprocess):
        """Test that activate uses wmctrl command"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        capture.activate_window("0xABCD")

        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert cmd == ['wmctrl', '-i', '-a', '0xABCD']


class TestMinimizeWindow:
    """Tests for minimize_window method"""

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_minimize_window_success(self, mock_subprocess):
        """Test successful window minimization"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        result = capture.minimize_window("0x12345")

        assert result is True

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_minimize_window_failure(self, mock_subprocess):
        """Test window minimization failure"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        result = capture.minimize_window("0x12345")

        assert result is False

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_minimize_window_exception(self, mock_subprocess):
        """Test window minimization handles exceptions"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_subprocess.side_effect = Exception("xdotool error")

        capture = WindowCaptureThreaded()
        result = capture.minimize_window("0x12345")

        assert result is False

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_minimize_window_uses_xdotool(self, mock_subprocess):
        """Test that minimize uses xdotool command"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        capture.minimize_window("0xABCD")

        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert cmd == ['xdotool', 'windowminimize', '0xABCD']


class TestRestoreWindow:
    """Tests for restore_window method"""

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_restore_window_success(self, mock_subprocess):
        """Test successful window restoration"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        result = capture.restore_window("0x12345")

        assert result is True

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_restore_window_failure(self, mock_subprocess):
        """Test window restoration failure"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        result = capture.restore_window("0x12345")

        assert result is False

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_restore_window_exception(self, mock_subprocess):
        """Test window restoration handles exceptions"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_subprocess.side_effect = Exception("xdotool error")

        capture = WindowCaptureThreaded()
        result = capture.restore_window("0x12345")

        assert result is False

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_restore_window_uses_xdotool(self, mock_subprocess):
        """Test that restore uses xdotool command"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        capture.restore_window("0xABCD")

        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert cmd == ['xdotool', 'windowactivate', '0xABCD']


class TestWorkerThread:
    """Tests for worker thread functionality"""

    def test_worker_exits_on_none(self):
        """Test worker exits when it receives None"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded(max_workers=1)
        capture.running = True
        capture.capture_queue.put(None)

        # Run worker in thread
        worker_thread = threading.Thread(target=capture._worker)
        worker_thread.start()
        worker_thread.join(timeout=1.0)

        assert not worker_thread.is_alive()

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    @patch('eve_overview_pro.core.window_capture_threaded.Image')
    def test_worker_processes_task(self, mock_image, mock_subprocess):
        """Test worker processes capture tasks"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'fake png'
        mock_subprocess.return_value = mock_result

        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_image.open.return_value = mock_img

        capture = WindowCaptureThreaded(max_workers=1)
        capture.running = True

        # Queue a task then None to stop
        capture.capture_queue.put(("0x12345", 1.0, "request_123"))
        capture.capture_queue.put(None)

        # Run worker
        worker_thread = threading.Thread(target=capture._worker)
        worker_thread.start()
        worker_thread.join(timeout=2.0)

        # Check result was queued
        result = capture.result_queue.get(timeout=1.0)
        assert result[0] == "request_123"
        assert result[1] == "0x12345"

    def test_worker_continues_on_empty_queue(self):
        """Test worker continues when queue is empty"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded(max_workers=1)
        capture.running = True

        # Start worker, let it timeout on empty queue, then stop
        worker_thread = threading.Thread(target=capture._worker)
        worker_thread.start()

        # Give it time to iterate
        time.sleep(0.2)

        # Stop it
        capture.running = False
        capture.capture_queue.put(None)
        worker_thread.join(timeout=1.0)

        assert not worker_thread.is_alive()

    def test_worker_handles_capture_exception(self):
        """Test worker handles exception from _capture_window_sync"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded(max_workers=1)
        capture.running = True

        # Mock _capture_window_sync to raise an exception
        with patch.object(capture, '_capture_window_sync', side_effect=Exception("Test error")):
            # Queue a task then None to stop
            capture.capture_queue.put(("0x12345", 1.0, "request_123"))
            capture.capture_queue.put(None)

            # Run worker
            worker_thread = threading.Thread(target=capture._worker)
            worker_thread.start()
            worker_thread.join(timeout=2.0)

            # Worker should have handled exception and exited cleanly
            assert not worker_thread.is_alive()


class TestIntegration:
    """Integration tests for the capture system"""

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    @patch('eve_overview_pro.core.window_capture_threaded.Image')
    def test_full_capture_workflow(self, mock_image, mock_subprocess):
        """Test complete capture workflow: start -> capture -> get result -> stop"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'fake png data'
        mock_subprocess.return_value = mock_result

        mock_img = MagicMock()
        mock_img.width = 800
        mock_img.height = 600
        mock_image.open.return_value = mock_img

        capture = WindowCaptureThreaded(max_workers=2)

        # Start workers
        capture.start()
        assert capture.running is True

        # Request capture
        request_id = capture.capture_window_async("0x12345", scale=1.0)
        assert request_id is not None

        # Wait for result
        result = None
        for _ in range(50):  # Try for up to 5 seconds
            result = capture.get_result(timeout=0.1)
            if result is not None:
                break

        # Stop workers
        capture.stop()
        assert capture.running is False

        # Verify result
        assert result is not None
        assert result[0] == request_id
        assert result[1] == "0x12345"

    def test_multiple_workers_process_concurrently(self):
        """Test that multiple workers can process tasks"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded(max_workers=4)

        # Just verify workers start and stop correctly
        capture.start()
        assert len(capture.workers) == 4

        capture.stop()
        assert len(capture.workers) == 0


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_stop_without_start(self):
        """Test calling stop without start doesn't crash"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        # Should not raise
        capture.stop()
        assert capture.running is False

    def test_start_multiple_times(self):
        """Test calling start multiple times"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        with patch('eve_overview_pro.core.window_capture_threaded.threading.Thread') as mock_thread:
            mock_thread.return_value = MagicMock()

            capture = WindowCaptureThreaded(max_workers=2)

            capture.start()
            initial_workers = len(capture.workers)

            capture.start()  # Second start
            # Workers accumulate (may be a bug, but we test current behavior)

            capture.stop()

    @patch('eve_overview_pro.core.window_capture_threaded.subprocess.run')
    def test_capture_with_empty_stdout(self, mock_subprocess):
        """Test capture handles empty stdout"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b''  # Empty
        mock_subprocess.return_value = mock_result

        capture = WindowCaptureThreaded()
        result = capture._capture_window_sync("0x12345", 1.0)

        assert result is None

    def test_capture_async_with_zero_scale(self):
        """Test capture request with zero scale"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        # Should not raise
        request_id = capture.capture_window_async("0x12345", scale=0.0)
        assert request_id is not None

    def test_capture_async_with_negative_scale(self):
        """Test capture request with negative scale"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        capture = WindowCaptureThreaded()

        # Should not raise
        request_id = capture.capture_window_async("0x12345", scale=-1.0)
        assert request_id is not None

    def test_window_id_with_special_chars(self):
        """Test window operations with special window IDs"""
        from eve_overview_pro.core.window_capture_threaded import WindowCaptureThreaded

        with patch('eve_overview_pro.core.window_capture_threaded.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            capture = WindowCaptureThreaded()

            # Various window ID formats
            capture.activate_window("0x7c00001")
            capture.activate_window("0xFFFFFFFF")

            assert mock_run.call_count == 2
