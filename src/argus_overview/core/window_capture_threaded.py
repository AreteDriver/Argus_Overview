"""Threaded window capture system with cross-platform support.

Architecture role:
    Core capture engine used by the Overview tab to produce live window
    thumbnails. Sits beneath the UI layer and is owned by MainWindowV21,
    which starts/stops it during application lifecycle.

Threading model:
    A pool of daemon worker threads (default 4) consume capture requests
    from ``capture_queue`` and place results on ``result_queue``.  Both
    queues are stdlib ``queue.Queue`` (thread-safe).  The ``_stop_event``
    (``threading.Event``) coordinates graceful shutdown.

    Workers use platform-specific capture methods (ImageMagick on Linux,
    GDI on Windows).  These are blocking I/O calls isolated to worker
    threads; callers on the Qt main thread use ``capture_window_async``
    (non-blocking put) and poll ``get_result``.

Thread-safety guarantees:
    * ``capture_window_async`` and ``get_result`` are safe to call from
      any thread (queue operations are atomic).
    * ``start`` and ``stop`` should be called from a single owner thread
      (typically the Qt main thread).
    * ``get_window_list``, ``activate_window``, ``minimize_window``, and
      ``restore_window`` delegate to platform layer and are thread-safe.

v3.0: Cross-platform support via platform abstraction layer.
"""

import logging
from typing import List, Optional, Tuple

from PIL import Image

from argus_overview.platform import get_window_capture, get_window_manager


class WindowCaptureThreaded:
    """Thread-safe window capture system with cross-platform support.

    This class wraps the platform-specific WindowCapture and WindowManager
    implementations, providing a unified interface for window operations.
    """

    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers

        # Platform abstraction layer - lazy initialization
        self._capture = get_window_capture(max_workers=max_workers)
        self._window_mgr = get_window_manager()

    @property
    def running(self) -> bool:
        """Thread-safe check if workers are running."""
        return self._capture.running

    def start(self):
        """Start capture worker threads."""
        self._capture.start()
        self.logger.info(f"Started {self.max_workers} capture workers")

    def stop(self):
        """Stop worker threads."""
        self._capture.stop()

    def capture_window_async(self, window_id: str, scale: float = 1.0) -> str:
        """Request async window capture.

        Returns:
            request_id to retrieve result later (empty string if invalid window_id)
        """
        return self._capture.capture_window_async(window_id, scale)

    def get_result(self, timeout: float = 0.1) -> Optional[Tuple[str, str, Image.Image]]:
        """Get capture result if available.

        Returns:
            Tuple of (request_id, window_id, image) or None
        """
        return self._capture.get_result(timeout)

    def get_window_list(self) -> List[Tuple[str, str]]:
        """Get list of all windows."""
        return self._window_mgr.get_window_list()

    def activate_window(self, window_id: str) -> bool:
        """Activate/focus a window."""
        return self._window_mgr.activate_window(window_id)

    def minimize_window(self, window_id: str) -> bool:
        """Minimize a window."""
        return self._window_mgr.minimize_window(window_id)

    def restore_window(self, window_id: str) -> bool:
        """Restore a minimized window."""
        return self._window_mgr.restore_window(window_id)
