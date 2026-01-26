"""
Threaded Window Capture System
High-performance capture with background threading
"""

import io
import logging
import re
import subprocess
import threading
import uuid
from queue import Empty, Queue
from typing import Any, List, Optional, Tuple

from PIL import Image

# X11 window ID pattern: 0x followed by hex digits
_WINDOW_ID_PATTERN = re.compile(r"^0x[0-9a-fA-F]+$")


def _is_valid_window_id(window_id: str) -> bool:
    """Validate X11 window ID format."""
    return bool(window_id and isinstance(window_id, str) and _WINDOW_ID_PATTERN.match(window_id))


class WindowCaptureThreaded:
    """Thread-safe window capture system"""

    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.capture_queue: Queue[Any] = Queue()
        self.result_queue: Queue[Any] = Queue()
        self.workers: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._stop_event.set()  # Start in stopped state

    @property
    def running(self) -> bool:
        """Thread-safe check if workers are running"""
        return not self._stop_event.is_set()

    def start(self):
        """Start capture worker threads"""
        self._stop_event.clear()
        for _i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
        self.logger.info(f"Started {self.max_workers} capture workers")

    def stop(self):
        """Stop worker threads"""
        self._stop_event.set()
        for _ in self.workers:
            self.capture_queue.put(None)
        for worker in self.workers:
            worker.join(timeout=1.0)
        self.workers.clear()

    def _worker(self):
        """Worker thread for capturing windows"""
        while self.running:
            try:
                task = self.capture_queue.get(timeout=0.5)
                if task is None:
                    break

                window_id, scale, request_id = task
                image = self._capture_window_sync(window_id, scale)
                self.result_queue.put((request_id, window_id, image))

            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {e}")

    def capture_window_async(self, window_id: str, scale: float = 1.0) -> str:
        """Request async window capture

        Returns:
            request_id to retrieve result later (empty string if invalid window_id)
        """
        if not _is_valid_window_id(window_id):
            self.logger.warning(f"Invalid window ID format for capture: {window_id}")
            return ""
        request_id = str(uuid.uuid4())
        self.capture_queue.put((window_id, scale, request_id))
        return request_id

    def get_result(self, timeout: float = 0.1) -> Optional[Tuple[str, str, Image.Image]]:
        """Get capture result if available

        Returns:
            Tuple of (request_id, window_id, image) or None
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except Empty:
            return None

    def _capture_window_sync(self, window_id: str, scale: float) -> Optional[Image.Image]:
        """Synchronous window capture"""
        try:
            result = subprocess.run(
                ["import", "-window", window_id, "-silent", "png:-"], capture_output=True, timeout=1
            )

            if result.returncode == 0 and result.stdout:
                img: Image.Image = Image.open(io.BytesIO(result.stdout))

                if scale != 1.0:
                    new_size = (int(img.width * scale), int(img.height * scale))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                return img
        except Exception as e:
            self.logger.debug(f"Capture failed for {window_id}: {e}")

        return None

    def get_window_list(self) -> List[Tuple[str, str]]:
        """Get list of all windows"""
        try:
            result = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=2)

            windows = []
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            window_id = parts[0]
                            window_title = parts[3]
                            windows.append((window_id, window_title))

            return windows
        except Exception as e:
            self.logger.error(f"Failed to get window list: {e}")
            return []

    def activate_window(self, window_id: str) -> bool:
        """Activate/focus a window"""
        if not _is_valid_window_id(window_id):
            self.logger.warning(f"Invalid window ID format: {window_id}")
            return False
        try:
            result = subprocess.run(
                ["wmctrl", "-i", "-a", window_id], capture_output=True, timeout=1
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.debug(f"Failed to activate window {window_id}: {e}")
            return False

    def minimize_window(self, window_id: str) -> bool:
        """Minimize a window"""
        if not _is_valid_window_id(window_id):
            self.logger.warning(f"Invalid window ID format: {window_id}")
            return False
        try:
            result = subprocess.run(
                ["xdotool", "windowminimize", window_id], capture_output=True, timeout=1
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.debug(f"Failed to minimize window {window_id}: {e}")
            return False

    def restore_window(self, window_id: str) -> bool:
        """Restore a minimized window"""
        if not _is_valid_window_id(window_id):
            self.logger.warning(f"Invalid window ID format: {window_id}")
            return False
        try:
            result = subprocess.run(
                ["xdotool", "windowactivate", window_id], capture_output=True, timeout=1
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.debug(f"Failed to restore window {window_id}: {e}")
            return False
