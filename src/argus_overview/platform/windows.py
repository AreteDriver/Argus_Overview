"""Windows platform implementations using Win32 API.

Uses pywin32 for window management and GDI-based screen capture.
"""

import logging
import os
import re
import threading
import uuid
from pathlib import Path
from queue import Empty, Queue
from typing import Any, List, Optional, Tuple

from PIL import Image

from .base import (
    EVEPathResolver,
    HotkeyHelper,
    ScreenGeometry,
    ScreenManager,
    WindowCapture,
    WindowManager,
)

logger = logging.getLogger(__name__)

# Check for Win32 availability
try:
    from ctypes import windll

    import win32api
    import win32con
    import win32gui
    import win32ui

    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    win32api = None
    win32con = None
    win32gui = None
    win32ui = None
    windll = None

# EVE window title patterns
EVE_TITLE_PATTERNS = [
    re.compile(r"^EVE - (.+)$"),
    re.compile(r"^EVE Online - (.+)$"),
]

# EVE window class name
EVE_CLASS_NAME = "triuiScreen"


class WindowManagerWindows(WindowManager):
    """Windows window management using Win32 API."""

    def __init__(self):
        if not HAS_WIN32:
            logger.warning("pywin32 not available - window management disabled")

    def get_window_list(self) -> List[Tuple[str, str]]:
        """Get list of all visible windows using EnumWindows."""
        if not HAS_WIN32:
            return []

        windows = []

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 0:
                    # Check if it's a top-level application window
                    if win32gui.GetParent(hwnd) == 0:
                        window_id = f"0x{hwnd:x}"
                        windows.append((window_id, title))
            return True

        try:
            win32gui.EnumWindows(enum_callback, None)
        except Exception as e:
            logger.error(f"Failed to enumerate windows: {e}")

        return windows

    def get_eve_windows(self) -> List[Tuple[str, str]]:
        """Get list of EVE Online windows."""
        if not HAS_WIN32:
            return []

        eve_windows = []

        def enum_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True

            try:
                title = win32gui.GetWindowText(hwnd)
                if title:
                    for pattern in EVE_TITLE_PATTERNS:
                        if pattern.match(title):
                            window_id = f"0x{hwnd:x}"
                            eve_windows.append((window_id, title))
                            break
            except Exception:
                pass

            return True

        try:
            win32gui.EnumWindows(enum_callback, None)
        except Exception as e:
            logger.error(f"Failed to enumerate EVE windows: {e}")

        return eve_windows

    def move_window(
        self, window_id: str, x: int, y: int, w: int, h: int, timeout: float = 2.0
    ) -> bool:
        """Move and resize a window using SetWindowPos."""
        if not HAS_WIN32:
            return False

        if not self.is_valid_window_id(window_id):
            logger.warning("Invalid window ID format for move: %s", window_id)
            return False

        try:
            hwnd = int(window_id, 16)
            flags = win32con.SWP_NOZORDER
            if w <= 0 or h <= 0:
                flags |= win32con.SWP_NOSIZE
            win32gui.SetWindowPos(hwnd, 0, x, y, w, h, flags)
            return True
        except Exception as e:
            logger.warning("Failed to move window %s: %s", window_id, e)
            return False

    def activate_window(self, window_id: str, timeout: float = 2.0) -> bool:
        """Activate/focus a window using SetForegroundWindow."""
        if not HAS_WIN32:
            return False

        if not self.is_valid_window_id(window_id):
            logger.warning("Invalid window ID format: %s", window_id)
            return False

        try:
            hwnd = int(window_id, 16)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.warning("Failed to activate window %s: %s", window_id, e)
            return False

    def minimize_window(self, window_id: str) -> bool:
        """Minimize a window using ShowWindow."""
        if not HAS_WIN32:
            return False

        try:
            hwnd = int(window_id, 16)
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except Exception as e:
            logger.warning("Failed to minimize window %s: %s", window_id, e)
            return False

    def restore_window(self, window_id: str) -> bool:
        """Restore a minimized window using ShowWindow."""
        if not HAS_WIN32:
            return False

        try:
            hwnd = int(window_id, 16)
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return True
        except Exception as e:
            logger.warning("Failed to restore window %s: %s", window_id, e)
            return False

    def get_focused_window(self) -> Optional[str]:
        """Get the currently focused window ID."""
        if not HAS_WIN32:
            return None

        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                return f"0x{hwnd:x}"
        except Exception as e:
            logger.debug("Failed to get focused window: %s", e)
        return None

    def is_valid_window_id(self, window_id: str) -> bool:
        """Validate Windows window ID format (hex string)."""
        if not window_id or not isinstance(window_id, str):
            return False
        try:
            # Must be valid hex, either with 0x prefix or without
            if window_id.startswith("0x"):
                int(window_id, 16)
            else:
                int(window_id, 16)
            return True
        except ValueError:
            return False

    def get_window_title(self, window_id: str) -> str:
        """Get window title using GetWindowText."""
        if not HAS_WIN32:
            return "Unknown"

        try:
            hwnd = int(window_id, 16)
            return win32gui.GetWindowText(hwnd)
        except Exception:
            return "Unknown"


class WindowCaptureWindows(WindowCapture):
    """Windows window capture using GDI."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.request_queue: Queue[Any] = Queue()
        self.result_queue: Queue[Any] = Queue()
        self.workers: List[threading.Thread] = []
        self._running = False
        self._window_mgr = WindowManagerWindows()

    @property
    def running(self) -> bool:
        """Check if workers are running."""
        return self._running

    def start(self):
        """Start worker threads."""
        if self._running:
            return

        self._running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True, name=f"CaptureWorker-{i}")
            worker.start()
            self.workers.append(worker)

        logger.info(f"Started {self.max_workers} capture workers")

    def stop(self):
        """Stop worker threads."""
        self._running = False
        # Clear queues
        while not self.request_queue.empty():
            try:
                self.request_queue.get_nowait()
            except Empty:
                break

        logger.info("Stopped capture workers")

    def _worker(self):
        """Worker thread that processes capture requests."""
        while self._running:
            try:
                request = self.request_queue.get(timeout=0.1)
                if request is None:
                    break

                request_id, hwnd, scale = request
                image = self.capture_window_sync(hwnd, scale)
                # Convert hwnd back to hex string for consistency
                hwnd_str = f"0x{hwnd:x}" if isinstance(hwnd, int) else hwnd
                self.result_queue.put((request_id, hwnd_str, image))

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")

    def capture_window_async(self, window_id: str, scale: float = 1.0) -> str:
        """Request async window capture."""
        request_id = str(uuid.uuid4())
        try:
            hwnd_int = int(window_id, 16)
            self.request_queue.put((request_id, hwnd_int, scale))
            return request_id
        except ValueError:
            logger.warning(f"Invalid window ID for capture: {window_id}")
            return ""

    def get_result(self, timeout: float = 0.1) -> Optional[Tuple[str, str, Image.Image]]:
        """Get capture result if available."""
        try:
            return self.result_queue.get(timeout=timeout)
        except Empty:
            return None

    def capture_window_sync(self, window_id: str, scale: float = 1.0) -> Optional[Image.Image]:
        """Synchronous window capture using Windows GDI."""
        if not HAS_WIN32:
            return None

        try:
            # Handle both string and int window IDs
            if isinstance(window_id, str):
                hwnd = int(window_id, 16)
            else:
                hwnd = window_id

            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                return None

            # Get window DC
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # Create bitmap
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            # Copy window content to bitmap (PW_RENDERFULLCONTENT = 3)
            windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

            # Convert to PIL Image
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            image = Image.frombuffer(
                "RGB",
                (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
                bmpstr,
                "raw",
                "BGRX",
                0,
                1,
            )

            # Scale if requested
            if scale < 1.0:
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.LANCZOS)

            # Cleanup
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            return image

        except Exception as e:
            logger.error(f"Failed to capture window {window_id}: {e}")
            return None


class ScreenManagerWindows(ScreenManager):
    """Windows screen management using EnumDisplayMonitors."""

    def get_screen_geometry(self, monitor: int = 0) -> ScreenGeometry:
        """Get screen geometry using Win32 API."""
        monitors = self.get_all_monitors()
        if monitor < len(monitors):
            return monitors[monitor]
        elif monitors:
            return monitors[0]
        return ScreenGeometry(0, 0, 1920, 1080, True)

    def get_all_monitors(self) -> List[ScreenGeometry]:
        """Get geometry for all connected monitors."""
        if not HAS_WIN32:
            return [ScreenGeometry(0, 0, 1920, 1080, True)]

        monitors: List[ScreenGeometry] = []

        def monitor_enum_callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            # lprcMonitor is a tuple (left, top, right, bottom)
            left, top, right, bottom = lprcMonitor
            width = right - left
            height = bottom - top
            # First monitor is typically primary
            is_primary = len(monitors) == 0
            monitors.append(ScreenGeometry(left, top, width, height, is_primary))
            return True

        try:
            win32api.EnumDisplayMonitors(None, None, monitor_enum_callback, None)
        except Exception as e:
            logger.error(f"Failed to enumerate monitors: {e}")

        return monitors if monitors else [ScreenGeometry(0, 0, 1920, 1080, True)]


class EVEPathResolverWindows(EVEPathResolver):
    """Windows EVE path resolution using LOCALAPPDATA."""

    def get_eve_settings_paths(self) -> List[Path]:
        """Get candidate EVE settings paths for Windows."""
        local_appdata = Path(os.environ.get("LOCALAPPDATA", ""))

        return [
            local_appdata / "CCP" / "EVE",
        ]

    def get_eve_logs_paths(self) -> List[Path]:
        """Get candidate EVE game logs paths for Windows."""
        documents = Path(os.environ.get("USERPROFILE", "")) / "Documents"

        return [
            documents / "EVE" / "logs" / "Gamelogs",
        ]

    def get_config_directory(self) -> Path:
        """Get application config directory (%LOCALAPPDATA%/Argus-Overview)."""
        local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        return local_appdata / "Argus-Overview"


class HotkeyHelperWindows(HotkeyHelper):
    """Windows hotkey handling (no normalization needed)."""

    def normalize_combo(self, key_combo: str) -> str:
        """Return combo as-is (Windows pynput doesn't need normalization)."""
        return key_combo

    def is_single_key(self, key_combo: str) -> bool:
        """Check if key combo is a single key (no modifiers)."""
        if not key_combo:
            return False
        return "+" not in key_combo
