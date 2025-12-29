"""
Windows-specific Window Capture with threading
Uses Windows API (pywin32) for screen capture instead of ImageMagick
"""
import logging
import uuid
from ctypes import windll
from queue import Empty, Queue
from threading import Thread
from typing import Optional, Tuple

import win32con
import win32gui
import win32ui
from PIL import Image


class WindowCaptureThreaded:
    """
    Threaded window capture system for Windows
    Uses Windows GDI for efficient window capture
    """

    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.request_queue = Queue()
        self.result_queue = Queue()
        self.workers = []
        self.running = False

    def start(self):
        """Start worker threads"""
        if self.running:
            return

        self.running = True
        for i in range(self.max_workers):
            worker = Thread(target=self._worker, daemon=True, name=f"CaptureWorker-{i}")
            worker.start()
            self.workers.append(worker)

        self.logger.info(f"Started {self.max_workers} capture workers")

    def stop(self):
        """Stop worker threads"""
        self.running = False
        # Clear queues
        while not self.request_queue.empty():
            try:
                self.request_queue.get_nowait()
            except Empty:
                break

        self.logger.info("Stopped capture workers")

    def _worker(self):
        """Worker thread that processes capture requests"""
        while self.running:
            try:
                request = self.request_queue.get(timeout=0.1)
                if request is None:
                    break

                request_id, hwnd, scale = request
                image = self._capture_window(hwnd, scale)
                self.result_queue.put((request_id, hwnd, image))

            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {e}")

    def _capture_window(self, hwnd: int, scale: float = 1.0) -> Optional[Image.Image]:
        """
        Capture window using Windows GDI

        Args:
            hwnd: Window handle (HWND)
            scale: Scale factor (0.0-1.0)

        Returns:
            PIL Image or None if capture failed
        """
        try:
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

            # Copy window content to bitmap
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

            # Convert to PIL Image
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            image = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
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
            self.logger.error(f"Failed to capture window {hwnd}: {e}")
            return None

    def capture_window_async(self, hwnd: str, scale: float = 1.0) -> str:
        """
        Request async window capture

        Args:
            hwnd: Window handle as string (hex)
            scale: Scale factor

        Returns:
            Request ID (UUID)
        """
        request_id = str(uuid.uuid4())
        hwnd_int = int(hwnd, 16) if isinstance(hwnd, str) else hwnd
        self.request_queue.put((request_id, hwnd_int, scale))
        return request_id

    def get_result(self, timeout: float = 0.0) -> Optional[Tuple[str, str, Image.Image]]:
        """
        Get capture result (non-blocking)

        Args:
            timeout: Timeout in seconds

        Returns:
            Tuple of (request_id, hwnd, image) or None
        """
        try:
            request_id, hwnd, image = self.result_queue.get(timeout=timeout)
            hwnd_str = f"0x{hwnd:x}"
            return (request_id, hwnd_str, image)
        except Empty:
            return None

    def get_window_list(self) -> list:
        """
        Get list of all visible windows

        Returns:
            List of dicts with window info
        """
        windows = []

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 0:
                    # Check if it's a real application window
                    if win32gui.GetParent(hwnd) == 0:
                        class_name = win32gui.GetClassName(hwnd)
                        windows.append({
                            'id': f"0x{hwnd:x}",
                            'title': title,
                            'class': class_name
                        })
            return True

        win32gui.EnumWindows(enum_callback, None)
        return windows

    def get_window_title(self, hwnd: str) -> str:
        """
        Get window title

        Args:
            hwnd: Window handle as string

        Returns:
            Window title
        """
        try:
            hwnd_int = int(hwnd, 16)
            return win32gui.GetWindowText(hwnd_int)
        except:
            return "Unknown"

    def minimize_window(self, hwnd: str):
        """
        Minimize window

        Args:
            hwnd: Window handle as string
        """
        try:
            hwnd_int = int(hwnd, 16)
            win32gui.ShowWindow(hwnd_int, win32con.SW_MINIMIZE)
        except Exception as e:
            self.logger.error(f"Failed to minimize window: {e}")

    def restore_window(self, hwnd: str):
        """
        Restore window

        Args:
            hwnd: Window handle as string
        """
        try:
            hwnd_int = int(hwnd, 16)
            win32gui.ShowWindow(hwnd_int, win32con.SW_RESTORE)
        except Exception as e:
            self.logger.error(f"Failed to restore window: {e}")

    def activate_window(self, hwnd: str):
        """
        Activate (bring to front) window

        Args:
            hwnd: Window handle as string
        """
        try:
            hwnd_int = int(hwnd, 16)
            win32gui.SetForegroundWindow(hwnd_int)
        except Exception as e:
            self.logger.error(f"Failed to activate window: {e}")
