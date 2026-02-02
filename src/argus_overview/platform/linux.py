"""Linux platform implementations using X11 tools.

Uses wmctrl, xdotool, xrandr, and ImageMagick for window management
and screen capture operations.
"""

import io
import logging
import re
import subprocess
import threading
import time
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

# X11 window ID pattern: 0x followed by hex digits
WINDOW_ID_PATTERN = re.compile(r"^0x[0-9a-fA-F]+$")

# EVE window title patterns
EVE_TITLE_PATTERNS = [
    re.compile(r"^EVE - (.+)$"),
    re.compile(r"^EVE Online - (.+)$"),
]

# Retry defaults for X11 subprocess operations
_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BACKOFF_SECONDS = 0.15
_DEFAULT_TIMEOUT = 2.0

# Module-level cache for wmctrl results
_wmctrl_cache: dict = {"result": None, "timestamp": 0.0}
_WMCTRL_CACHE_TTL = 1.0


def _clear_wmctrl_cache() -> None:
    """Clear wmctrl cache (for testing)."""
    _wmctrl_cache["result"] = None
    _wmctrl_cache["timestamp"] = 0.0


def _get_wmctrl_window_list() -> str:
    """Get wmctrl -l output with caching (1 second TTL)."""
    now = time.monotonic()
    if _wmctrl_cache["result"] is not None and now - _wmctrl_cache["timestamp"] < _WMCTRL_CACHE_TTL:
        return _wmctrl_cache["result"]

    try:
        result = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            _wmctrl_cache["result"] = result.stdout
            _wmctrl_cache["timestamp"] = now
            return result.stdout
    except (subprocess.TimeoutExpired, OSError):
        pass

    return _wmctrl_cache["result"] or ""


def run_x11_subprocess(
    cmd: List[str],
    timeout: float = _DEFAULT_TIMEOUT,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    backoff: float = _DEFAULT_BACKOFF_SECONDS,
    check_returncode: bool = True,
) -> subprocess.CompletedProcess:
    """Run an X11 subprocess command with retry and logging.

    Retries on failure with exponential backoff. Logs warnings on
    transient failures and errors on final failure.

    Args:
        cmd: Command and arguments (e.g. ["xdotool", "windowmove", ...])
        timeout: Per-attempt timeout in seconds
        max_attempts: Number of attempts before giving up (1-5)
        backoff: Initial backoff between retries in seconds (doubles each retry)
        check_returncode: If True, treat non-zero return codes as failures

    Returns:
        CompletedProcess from the successful attempt

    Raises:
        subprocess.SubprocessError: If all attempts fail
    """
    max_attempts = max(1, min(5, max_attempts))
    last_error: Optional[Exception] = None
    cmd_str = " ".join(cmd)

    for attempt in range(1, max_attempts + 1):
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout)
            if check_returncode and result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, result.stdout, result.stderr
                )
            return result
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            last_error = e
            if attempt < max_attempts:
                sleep_time = backoff * (2 ** (attempt - 1))
                logger.warning(
                    "X11 command failed (attempt %d/%d): %s — %s. Retrying in %.2fs",
                    attempt,
                    max_attempts,
                    cmd_str,
                    e,
                    sleep_time,
                )
                time.sleep(sleep_time)

    logger.warning(
        "X11 command failed after %d attempts: %s — %s",
        max_attempts,
        cmd_str,
        last_error,
    )
    raise last_error  # type: ignore[misc]


class WindowManagerLinux(WindowManager):
    """Linux window management using wmctrl and xdotool."""

    def get_window_list(self) -> List[Tuple[str, str]]:
        """Get list of all windows using wmctrl."""
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
            logger.warning(f"Failed to get window list: {e}")
            return []

    def get_eve_windows(self) -> List[Tuple[str, str]]:
        """Get list of EVE Online windows."""
        eve_windows = []
        output = _get_wmctrl_window_list()

        for line in output.strip().split("\n"):
            if not line:
                continue

            parts = line.split(None, 3)
            if len(parts) >= 4:
                window_id = parts[0]
                window_title = parts[3]

                for pattern in EVE_TITLE_PATTERNS:
                    if pattern.match(window_title):
                        eve_windows.append((window_id, window_title))
                        break

        return eve_windows

    def move_window(
        self, window_id: str, x: int, y: int, w: int, h: int, timeout: float = 2.0
    ) -> bool:
        """Move and resize a window using xdotool."""
        if not self.is_valid_window_id(window_id):
            logger.warning("Invalid window ID format for move: %s", window_id)
            return False

        try:
            # Try with --sync first, fallback for Wine/Proton windows
            try:
                run_x11_subprocess(
                    ["xdotool", "windowmove", "--sync", window_id, str(x), str(y)],
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                run_x11_subprocess(
                    ["xdotool", "windowmove", window_id, str(x), str(y)],
                    timeout=timeout,
                )
                time.sleep(0.1)

            try:
                run_x11_subprocess(
                    ["xdotool", "windowsize", "--sync", window_id, str(w), str(h)],
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                run_x11_subprocess(
                    ["xdotool", "windowsize", window_id, str(w), str(h)],
                    timeout=timeout,
                )
                time.sleep(0.1)

            return True

        except Exception as e:
            logger.warning("Failed to move window %s after retries: %s", window_id, e)
            return False

    def activate_window(self, window_id: str, timeout: float = 2.0) -> bool:
        """Activate/focus a window using wmctrl."""
        if not self.is_valid_window_id(window_id):
            logger.warning("Invalid window ID format: %s", window_id)
            return False
        try:
            run_x11_subprocess(["wmctrl", "-i", "-a", window_id], timeout=timeout)
            return True
        except Exception as e:
            logger.warning("Failed to activate window %s: %s", window_id, e)
            return False

    def minimize_window(self, window_id: str) -> bool:
        """Minimize a window using xdotool."""
        if not self.is_valid_window_id(window_id):
            logger.warning("Invalid window ID format: %s", window_id)
            return False
        try:
            run_x11_subprocess(["xdotool", "windowminimize", window_id], timeout=2)
            return True
        except Exception as e:
            logger.warning("Failed to minimize window %s: %s", window_id, e)
            return False

    def restore_window(self, window_id: str) -> bool:
        """Restore a minimized window using xdotool."""
        if not self.is_valid_window_id(window_id):
            logger.warning("Invalid window ID format: %s", window_id)
            return False
        try:
            run_x11_subprocess(["xdotool", "windowactivate", window_id], timeout=2)
            return True
        except Exception as e:
            logger.warning("Failed to restore window %s: %s", window_id, e)
            return False

    def get_focused_window(self) -> Optional[str]:
        """Get the currently focused window ID."""
        try:
            result = run_x11_subprocess(
                ["xdotool", "getwindowfocus"],
                timeout=2,
                max_attempts=2,
            )
            window_id = result.stdout.decode("utf-8", errors="replace").strip()
            # xdotool getwindowfocus returns decimal, convert to hex
            try:
                return hex(int(window_id))
            except ValueError:
                return window_id if self.is_valid_window_id(window_id) else None
        except Exception as e:
            logger.debug("Failed to get focused window: %s", e)
        return None

    def is_valid_window_id(self, window_id: str) -> bool:
        """Validate X11 window ID format (0x followed by hex digits)."""
        if not window_id or not isinstance(window_id, str):
            return False
        return bool(WINDOW_ID_PATTERN.match(window_id))

    def get_window_title(self, window_id: str) -> str:
        """Get window title using xdotool."""
        try:
            result = run_x11_subprocess(
                ["xdotool", "getwindowname", window_id], timeout=2, max_attempts=2
            )
            return result.stdout.decode("utf-8", errors="replace").strip()
        except Exception:
            return "Unknown"


class WindowCaptureLinux(WindowCapture):
    """Linux window capture using ImageMagick."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.capture_queue: Queue[Any] = Queue()
        self.result_queue: Queue[Any] = Queue()
        self.workers: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._stop_event.set()  # Start in stopped state
        self._window_mgr = WindowManagerLinux()

    @property
    def running(self) -> bool:
        """Check if workers are running."""
        return not self._stop_event.is_set()

    def start(self):
        """Start capture worker threads."""
        self._stop_event.clear()
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {self.max_workers} capture workers")

    def stop(self):
        """Stop worker threads."""
        self._stop_event.set()
        for _ in self.workers:
            self.capture_queue.put(None)
        for worker in self.workers:
            worker.join(timeout=1.0)
        self.workers.clear()

    def _worker(self):
        """Worker thread for capturing windows."""
        while self.running:
            try:
                task = self.capture_queue.get(timeout=0.5)
                if task is None:
                    break

                window_id, scale, request_id = task
                image = self.capture_window_sync(window_id, scale)
                self.result_queue.put((request_id, window_id, image))

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")

    def capture_window_async(self, window_id: str, scale: float = 1.0) -> str:
        """Request async window capture."""
        if not self._window_mgr.is_valid_window_id(window_id):
            logger.warning(f"Invalid window ID format for capture: {window_id}")
            return ""
        request_id = str(uuid.uuid4())
        self.capture_queue.put((window_id, scale, request_id))
        return request_id

    def get_result(self, timeout: float = 0.1) -> Optional[Tuple[str, str, Image.Image]]:
        """Get capture result if available."""
        try:
            return self.result_queue.get(timeout=timeout)
        except Empty:
            return None

    def capture_window_sync(self, window_id: str, scale: float = 1.0) -> Optional[Image.Image]:
        """Synchronous window capture using ImageMagick."""
        try:
            result = subprocess.run(
                ["import", "-window", window_id, "-silent", "png:-"],
                capture_output=True,
                timeout=2,
            )

            if result.returncode == 0 and result.stdout:
                img: Image.Image = Image.open(io.BytesIO(result.stdout))

                if scale != 1.0:
                    new_size = (int(img.width * scale), int(img.height * scale))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                return img
        except Exception as e:
            logger.debug(f"Capture failed for {window_id}: {e}")

        return None


class ScreenManagerLinux(ScreenManager):
    """Linux screen management using xrandr."""

    def get_screen_geometry(self, monitor: int = 0) -> ScreenGeometry:
        """Get screen geometry using xrandr."""
        try:
            result = subprocess.run(
                ["xrandr", "--query"], capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                logger.error("xrandr failed")
                return ScreenGeometry(0, 0, 1920, 1080, True)

            monitors = self._parse_xrandr_output(result.stdout)

            if monitor < len(monitors):
                return monitors[monitor]
            elif monitors:
                return monitors[0]

            logger.warning("Could not parse xrandr output, using default geometry")
            return ScreenGeometry(0, 0, 1920, 1080, True)

        except Exception as e:
            logger.error(f"Failed to get screen geometry: {e}")
            return ScreenGeometry(0, 0, 1920, 1080, True)

    def get_all_monitors(self) -> List[ScreenGeometry]:
        """Get geometry for all connected monitors."""
        try:
            result = subprocess.run(
                ["xrandr", "--query"], capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                return [ScreenGeometry(0, 0, 1920, 1080, True)]

            monitors = self._parse_xrandr_output(result.stdout)
            return monitors if monitors else [ScreenGeometry(0, 0, 1920, 1080, True)]

        except Exception as e:
            logger.error(f"Failed to get monitors: {e}")
            return [ScreenGeometry(0, 0, 1920, 1080, True)]

    def _parse_xrandr_output(self, output: str) -> List[ScreenGeometry]:
        """Parse xrandr output to extract monitor geometries."""
        monitors: List[ScreenGeometry] = []
        for line in output.split("\n"):
            if " connected" in line:
                match = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
                if match:
                    w, h, x, y = map(int, match.groups())
                    is_primary = "primary" in line
                    monitors.append(ScreenGeometry(x, y, w, h, is_primary))
        return monitors


class EVEPathResolverLinux(EVEPathResolver):
    """Linux EVE path resolution for Steam/Proton and Wine installations."""

    def get_eve_settings_paths(self) -> List[Path]:
        """Get candidate EVE settings paths for Linux."""
        home = Path.home()

        # Steam/Proton paths (most common)
        steam_base = home / ".steam" / "debian-installation" / "steamapps" / "compatdata"
        steam_alt = home / ".local" / "share" / "Steam" / "steamapps" / "compatdata"

        eve_steam_paths = [
            steam_base
            / "8500"
            / "pfx"
            / "drive_c"
            / "users"
            / "steamuser"
            / "AppData"
            / "Local"
            / "CCP"
            / "EVE",
            steam_alt
            / "8500"
            / "pfx"
            / "drive_c"
            / "users"
            / "steamuser"
            / "AppData"
            / "Local"
            / "CCP"
            / "EVE",
        ]

        # Legacy Wine/CrossOver paths
        legacy_paths = [
            home
            / ".eve"
            / "wineenv"
            / "drive_c"
            / "users"
            / "crossover"
            / "Local Settings"
            / "Application Data"
            / "CCP"
            / "EVE",
            home
            / ".wine"
            / "drive_c"
            / "users"
            / home.name
            / "Local Settings"
            / "Application Data"
            / "CCP"
            / "EVE",
            home / ".wine" / "drive_c" / "users" / home.name / "AppData" / "Local" / "CCP" / "EVE",
            home / "EVE" / "settings",
            home / ".local" / "share" / "CCP" / "EVE",
        ]

        return eve_steam_paths + legacy_paths

    def get_eve_logs_paths(self) -> List[Path]:
        """Get candidate EVE game logs paths for Linux."""
        home = Path.home()
        steam_base = home / ".steam" / "debian-installation" / "steamapps" / "compatdata"
        steam_alt = home / ".local" / "share" / "Steam" / "steamapps" / "compatdata"

        return [
            steam_base
            / "8500"
            / "pfx"
            / "drive_c"
            / "users"
            / "steamuser"
            / "Documents"
            / "EVE"
            / "logs"
            / "Gamelogs",
            steam_alt
            / "8500"
            / "pfx"
            / "drive_c"
            / "users"
            / "steamuser"
            / "Documents"
            / "EVE"
            / "logs"
            / "Gamelogs",
        ]

    def get_config_directory(self) -> Path:
        """Get application config directory (~/.config/argus-overview)."""
        return Path.home() / ".config" / "argus-overview"


class HotkeyHelperLinux(HotkeyHelper):
    """Linux hotkey normalization for pynput compatibility."""

    def normalize_combo(self, key_combo: str) -> str:
        """Normalize hotkey combo for pynput.

        Fixes common format issues:
        - <ctrl>+<v> -> <ctrl>+v (single keys shouldn't have angle brackets)
        - <R> -> r (lowercase for regular keys)
        """
        if not key_combo:
            return key_combo

        parts = key_combo.split("+")
        normalized_parts = []

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if it's a modifier key (should keep angle brackets)
            modifier_keys = {"ctrl", "alt", "shift", "super", "cmd", "win"}
            inner = part.strip("<>").lower()

            if inner in modifier_keys:
                # Keep modifiers as-is with angle brackets
                normalized_parts.append(f"<{inner}>")
            elif part.startswith("<") and part.endswith(">"):
                # Single character wrapped in brackets - remove them and lowercase
                inner_key = part[1:-1]
                if len(inner_key) == 1:
                    normalized_parts.append(inner_key.lower())
                else:
                    # Special keys like <space>, <enter> - keep them
                    normalized_parts.append(part.lower())
            else:
                # Regular key without brackets
                normalized_parts.append(part.lower())

        return "+".join(normalized_parts)

    def is_single_key(self, key_combo: str) -> bool:
        """Check if key combo is a single key (no modifiers)."""
        if not key_combo:
            return False
        return "+" not in key_combo
