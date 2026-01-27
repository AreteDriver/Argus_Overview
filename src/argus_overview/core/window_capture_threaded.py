"""Threaded window capture system for X11 windows.

Architecture role:
    Core capture engine used by the Overview tab to produce live window
    thumbnails. Sits beneath the UI layer and is owned by MainWindowV21,
    which starts/stops it during application lifecycle.

Threading model:
    A pool of daemon worker threads (default 4) consume capture requests
    from ``capture_queue`` and place results on ``result_queue``.  Both
    queues are stdlib ``queue.Queue`` (thread-safe).  The ``_stop_event``
    (``threading.Event``) coordinates graceful shutdown.

    Workers call ``subprocess.run`` to invoke ImageMagick ``import`` and
    ``wmctrl``/``xdotool`` for window management.  These are blocking I/O
    calls isolated to worker threads; callers on the Qt main thread use
    ``capture_window_async`` (non-blocking put) and poll ``get_result``.

Thread-safety guarantees:
    * ``capture_window_async`` and ``get_result`` are safe to call from
      any thread (queue operations are atomic).
    * ``start`` and ``stop`` should be called from a single owner thread
      (typically the Qt main thread).
    * ``get_window_list``, ``activate_window``, ``minimize_window``, and
      ``restore_window`` are stateless subprocess calls, safe from any
      thread but will block the caller until the subprocess completes.
"""

import io
import logging
import subprocess
import threading
import uuid
from queue import Empty, Queue
from typing import Any, List, Optional, Tuple

from PIL import Image

from argus_overview.utils.window_utils import is_valid_window_id, run_x11_subprocess


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
        if not is_valid_window_id(window_id):
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
                ["import", "-window", window_id, "-silent", "png:-"], capture_output=True, timeout=2
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
        """Get list of all windows (with retry)"""
        try:
            result = run_x11_subprocess(["wmctrl", "-l"], timeout=2)
            stdout = result.stdout.decode("utf-8", errors="replace")

            windows = []
            for line in stdout.strip().split("\n"):
                if line:
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        window_id = parts[0]
                        window_title = parts[3]
                        windows.append((window_id, window_title))

            return windows
        except Exception as e:
            self.logger.warning(f"Failed to get window list: {e}")
            return []

    def activate_window(self, window_id: str) -> bool:
        """Activate/focus a window (with retry)"""
        if not is_valid_window_id(window_id):
            self.logger.warning(f"Invalid window ID format: {window_id}")
            return False
        try:
            run_x11_subprocess(["wmctrl", "-i", "-a", window_id], timeout=2)
            return True
        except Exception as e:
            self.logger.warning(f"Failed to activate window {window_id}: {e}")
            return False

    def minimize_window(self, window_id: str) -> bool:
        """Minimize a window (with retry)"""
        if not is_valid_window_id(window_id):
            self.logger.warning(f"Invalid window ID format: {window_id}")
            return False
        try:
            run_x11_subprocess(["xdotool", "windowminimize", window_id], timeout=2)
            return True
        except Exception as e:
            self.logger.warning(f"Failed to minimize window {window_id}: {e}")
            return False

    def restore_window(self, window_id: str) -> bool:
        """Restore a minimized window (with retry)"""
        if not is_valid_window_id(window_id):
            self.logger.warning(f"Invalid window ID format: {window_id}")
            return False
        try:
            run_x11_subprocess(["xdotool", "windowactivate", window_id], timeout=2)
            return True
        except Exception as e:
            self.logger.warning(f"Failed to restore window {window_id}: {e}")
            return False
