"""Wayland platform implementations for wlroots-based compositors.

POC module targeting Sway and Hyprland. Uses subprocess calls to common
wlroots tools (swaymsg, hyprctl, wlr-randr, grim) rather than raw D-Bus
for pragmatism. Falls back gracefully when tools are unavailable.
"""

import io
import json
import logging
import re
import subprocess
import threading
import uuid
from pathlib import Path
from queue import Empty, Full, Queue
from typing import Any

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

# EVE window title patterns (shared with linux.py)
EVE_TITLE_PATTERNS = [
    re.compile(r"^EVE - (.+)$"),
    re.compile(r"^EVE Online - (.+)$"),
]

# Wayland window IDs are compositor-specific. Sway uses integer container IDs,
# Hyprland uses hex addresses. We accept both.
WAYLAND_WINDOW_ID_PATTERN = re.compile(r"^[0-9a-fA-Fx]+$")


def _detect_compositor() -> str:
    """Detect the active wlroots compositor.

    Returns:
        'sway', 'hyprland', or 'unknown'
    """
    # Check SWAYSOCK first (most reliable for Sway)
    import os

    if os.environ.get("SWAYSOCK"):
        return "sway"
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"

    # Fallback: check running processes
    try:
        result = subprocess.run(
            ["pgrep", "-x", "sway"],
            capture_output=True,
            timeout=2,
        )
        if result.returncode == 0:
            return "sway"
    except (OSError, subprocess.SubprocessError):
        pass

    try:
        result = subprocess.run(
            ["pgrep", "-x", "Hyprland"],
            capture_output=True,
            timeout=2,
        )
        if result.returncode == 0:
            return "hyprland"
    except (OSError, subprocess.SubprocessError):
        pass

    return "unknown"


def _run_swaymsg(args: list[str], timeout: float = 2.0) -> str | None:
    """Run swaymsg with arguments and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["swaymsg"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug("swaymsg %s failed: %s", args, e)
    return None


def _run_hyprctl(args: list[str], timeout: float = 2.0) -> str | None:
    """Run hyprctl with arguments and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["hyprctl"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug("hyprctl %s failed: %s", args, e)
    return None


def _get_sway_windows() -> list[dict[str, Any]]:
    """Get window list from Sway via swaymsg -t get_tree.

    Returns:
        List of dicts with 'id', 'name', 'app_id' keys.
    """
    output = _run_swaymsg(["-t", "get_tree"])
    if not output:
        return []

    try:
        tree = json.loads(output)
    except json.JSONDecodeError:
        logger.warning("Failed to parse swaymsg get_tree output")
        return []

    windows: list[dict[str, Any]] = []
    _walk_sway_tree(tree, windows)
    return windows


def _walk_sway_tree(node: dict, windows: list[dict[str, Any]]) -> None:
    """Recursively walk Sway tree to find window containers."""
    # A node with 'pid' and a name is a window (leaf container)
    if node.get("pid") and node.get("name") and node.get("type") == "con":
        windows.append(
            {
                "id": str(node["id"]),
                "name": node.get("name", ""),
                "app_id": node.get("app_id", ""),
                "focused": node.get("focused", False),
                "rect": node.get("rect", {}),
            }
        )
    # Recurse into child nodes
    for child in node.get("nodes", []):
        _walk_sway_tree(child, windows)
    for child in node.get("floating_nodes", []):
        _walk_sway_tree(child, windows)


def _get_hyprland_windows() -> list[dict[str, Any]]:
    """Get window list from Hyprland via hyprctl clients -j.

    Returns:
        List of dicts with 'address', 'title', 'class' keys.
    """
    output = _run_hyprctl(["clients", "-j"])
    if not output:
        return []

    try:
        clients = json.loads(output)
    except json.JSONDecodeError:
        logger.warning("Failed to parse hyprctl clients output")
        return []

    windows = []
    for client in clients:
        windows.append(
            {
                "id": client.get("address", ""),
                "name": client.get("title", ""),
                "app_id": client.get("class", ""),
                "focused": False,  # Hyprland tracks focus separately
                "rect": {
                    "x": client.get("at", [0, 0])[0],
                    "y": client.get("at", [0, 0])[1],
                    "width": client.get("size", [0, 0])[0],
                    "height": client.get("size", [0, 0])[1],
                },
            }
        )
    return windows


class WindowManagerWayland(WindowManager):
    """Wayland window management for wlroots compositors (Sway/Hyprland).

    Uses swaymsg or hyprctl subprocess calls for window enumeration and
    control. Falls back gracefully if compositor tools are unavailable.
    """

    def __init__(self) -> None:
        self._compositor = _detect_compositor()
        logger.info("Wayland compositor detected: %s", self._compositor)

    def get_window_list(self) -> list[tuple[str, str]]:
        """Get list of all visible windows."""
        windows = self._get_compositor_windows()
        return [(w["id"], w["name"]) for w in windows if w["name"]]

    def get_eve_windows(self) -> list[tuple[str, str]]:
        """Get list of EVE Online windows."""
        eve_windows = []
        for w in self._get_compositor_windows():
            title = w.get("name", "")
            for pattern in EVE_TITLE_PATTERNS:
                if pattern.match(title):
                    eve_windows.append((w["id"], title))
                    break
        return eve_windows

    def move_window(
        self, window_id: str, x: int, y: int, w: int, h: int, timeout: float = 2.0
    ) -> bool:
        """Move and resize a window."""
        if not self.is_valid_window_id(window_id):
            logger.warning("Invalid window ID format for move: %s", window_id)
            return False

        try:
            if self._compositor == "sway":
                # Sway: use criteria selector [con_id=<id>]
                cmd = f"[con_id={window_id}] move position {x} {y}"
                result = _run_swaymsg([cmd])
                if result is None:
                    return False
                if w > 0 and h > 0:
                    cmd = f"[con_id={window_id}] resize set {w} {h}"
                    _run_swaymsg([cmd])
                return True

            elif self._compositor == "hyprland":
                _run_hyprctl(
                    [
                        "dispatch",
                        "movewindowpixel",
                        f"exact {x} {y},address:{window_id}",
                    ]
                )
                if w > 0 and h > 0:
                    _run_hyprctl(
                        [
                            "dispatch",
                            "resizewindowpixel",
                            f"exact {w} {h},address:{window_id}",
                        ]
                    )
                return True

        except Exception as e:
            logger.warning("Failed to move window %s: %s", window_id, e)
        return False

    def activate_window(self, window_id: str, timeout: float = 2.0) -> bool:
        """Activate/focus a window."""
        if not self.is_valid_window_id(window_id):
            logger.warning("Invalid window ID format: %s", window_id)
            return False

        try:
            if self._compositor == "sway":
                result = _run_swaymsg([f"[con_id={window_id}] focus"])
                return result is not None
            elif self._compositor == "hyprland":
                result = _run_hyprctl(
                    ["dispatch", "focuswindow", f"address:{window_id}"]
                )
                return result is not None
        except Exception as e:
            logger.warning("Failed to activate window %s: %s", window_id, e)
        return False

    def minimize_window(self, window_id: str) -> bool:
        """Minimize a window (move to scratchpad on Sway)."""
        if not self.is_valid_window_id(window_id):
            return False

        try:
            if self._compositor == "sway":
                result = _run_swaymsg([f"[con_id={window_id}] move scratchpad"])
                return result is not None
            elif self._compositor == "hyprland":
                result = _run_hyprctl(
                    [
                        "dispatch",
                        "movetoworkspacesilent",
                        f"special,address:{window_id}",
                    ]
                )
                return result is not None
        except Exception as e:
            logger.warning("Failed to minimize window %s: %s", window_id, e)
        return False

    def restore_window(self, window_id: str) -> bool:
        """Restore a minimized window."""
        if not self.is_valid_window_id(window_id):
            return False

        try:
            if self._compositor == "sway":
                # Show from scratchpad and focus
                _run_swaymsg([f"[con_id={window_id}] scratchpad show"])
                result = _run_swaymsg([f"[con_id={window_id}] focus"])
                return result is not None
            elif self._compositor == "hyprland":
                result = _run_hyprctl(
                    ["dispatch", "movetoworkspace", f"e+0,address:{window_id}"]
                )
                return result is not None
        except Exception as e:
            logger.warning("Failed to restore window %s: %s", window_id, e)
        return False

    def get_focused_window(self) -> str | None:
        """Get the currently focused window ID."""
        try:
            if self._compositor == "sway":
                output = _run_swaymsg(["-t", "get_tree"])
                if not output:
                    return None
                tree = json.loads(output)
                focused = self._find_focused_sway(tree)
                return focused

            elif self._compositor == "hyprland":
                output = _run_hyprctl(["activewindow", "-j"])
                if not output:
                    return None
                data = json.loads(output)
                return data.get("address")

        except (json.JSONDecodeError, Exception) as e:
            logger.debug("Failed to get focused window: %s", e)
        return None

    def is_valid_window_id(self, window_id: str) -> bool:
        """Validate Wayland window ID format.

        Sway uses integer container IDs, Hyprland uses hex addresses.
        """
        if not window_id or not isinstance(window_id, str):
            return False
        return bool(WAYLAND_WINDOW_ID_PATTERN.match(window_id))

    def get_window_title(self, window_id: str) -> str:
        """Get the title of a window."""
        for w in self._get_compositor_windows():
            if w["id"] == window_id:
                return w.get("name", "Unknown")
        return "Unknown"

    def _get_compositor_windows(self) -> list[dict[str, Any]]:
        """Get windows from the detected compositor."""
        if self._compositor == "sway":
            return _get_sway_windows()
        elif self._compositor == "hyprland":
            return _get_hyprland_windows()
        else:
            logger.warning(
                "No supported Wayland compositor detected. Window management unavailable."
            )
            return []

    def _find_focused_sway(self, node: dict) -> str | None:
        """Find the focused window in a Sway tree."""
        if node.get("focused") and node.get("pid"):
            return str(node["id"])
        for child in node.get("nodes", []):
            result = self._find_focused_sway(child)
            if result:
                return result
        for child in node.get("floating_nodes", []):
            result = self._find_focused_sway(child)
            if result:
                return result
        return None


class WindowCaptureWayland(WindowCapture):
    """Wayland window capture using grim (wlroots screenshot tool).

    For POC, uses grim subprocess for capture. grim is widely available
    on wlroots compositors (Sway, Hyprland, river, etc.).

    Uses the same threaded worker pattern as the Linux/Windows implementations.
    """

    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max_workers
        self.capture_queue: Queue[Any] = Queue(maxsize=max_workers * 2)
        self.result_queue: Queue[Any] = Queue()
        self.workers: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self._stop_event.set()  # Start in stopped state
        self._window_mgr = WindowManagerWayland()

    @property
    def running(self) -> bool:
        """Check if workers are running."""
        return not self._stop_event.is_set()

    def start(self) -> None:
        """Start capture worker threads."""
        self._stop_event.clear()
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
        logger.info("Started %d Wayland capture workers", self.max_workers)

    def stop(self) -> None:
        """Stop worker threads."""
        self._stop_event.set()
        for _ in self.workers:
            try:
                self.capture_queue.put_nowait(None)
            except Full:
                pass
        for worker in self.workers:
            worker.join(timeout=1.0)
        self.workers.clear()

    def _worker(self) -> None:
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
                logger.error("Wayland capture worker error: %s", e)

    def capture_window_async(self, window_id: str, scale: float = 1.0) -> str:
        """Request async window capture."""
        if not self._window_mgr.is_valid_window_id(window_id):
            logger.warning("Invalid window ID format for capture: %s", window_id)
            return ""
        request_id = str(uuid.uuid4())
        try:
            self.capture_queue.put_nowait((window_id, scale, request_id))
        except Full:
            logger.debug("Capture queue full, dropping request for %s", window_id)
            return ""
        return request_id

    def get_result(self, timeout: float = 0.1) -> tuple[str, str, Image.Image] | None:
        """Get capture result if available."""
        try:
            return self.result_queue.get(timeout=timeout)
        except Empty:
            return None

    def capture_window_sync(
        self, window_id: str, scale: float = 1.0
    ) -> Image.Image | None:
        """Synchronous window capture using grim.

        On Sway, captures the window's geometry region using grim -g.
        On Hyprland, uses hyprctl to get window geometry then grim -g.

        Args:
            window_id: Compositor-specific window ID.
            scale: Deprecated, ignored. Scaling is done in Qt.

        Returns:
            PIL Image or None if capture failed.
        """
        geometry = self._get_window_geometry(window_id)
        if not geometry:
            logger.debug("Cannot determine geometry for window %s", window_id)
            return None

        return self._capture_grim(geometry)

    def _get_window_geometry(self, window_id: str) -> str | None:
        """Get window geometry string 'x,y widthxheight' for grim -g.

        Returns:
            Geometry string or None if window not found.
        """
        compositor = self._window_mgr._compositor

        if compositor == "sway":
            output = _run_swaymsg(["-t", "get_tree"])
            if not output:
                return None
            try:
                tree = json.loads(output)
                return self._find_sway_window_geometry(tree, window_id)
            except json.JSONDecodeError:
                return None

        elif compositor == "hyprland":
            output = _run_hyprctl(["clients", "-j"])
            if not output:
                return None
            try:
                clients = json.loads(output)
                for client in clients:
                    if client.get("address") == window_id:
                        at = client.get("at", [0, 0])
                        size = client.get("size", [0, 0])
                        return f"{at[0]},{at[1]} {size[0]}x{size[1]}"
            except json.JSONDecodeError:
                return None

        return None

    def _find_sway_window_geometry(self, node: dict, window_id: str) -> str | None:
        """Find window geometry in Sway tree by container ID."""
        if str(node.get("id")) == window_id and node.get("pid"):
            rect = node.get("rect", {})
            x = rect.get("x", 0)
            y = rect.get("y", 0)
            w = rect.get("width", 0)
            h = rect.get("height", 0)
            if w > 0 and h > 0:
                return f"{x},{y} {w}x{h}"
            return None

        for child in node.get("nodes", []):
            result = self._find_sway_window_geometry(child, window_id)
            if result:
                return result
        for child in node.get("floating_nodes", []):
            result = self._find_sway_window_geometry(child, window_id)
            if result:
                return result
        return None

    def _capture_grim(self, geometry: str) -> Image.Image | None:
        """Capture a screen region using grim.

        Args:
            geometry: Region in 'x,y widthxheight' format.

        Returns:
            PIL Image or None on failure.
        """
        try:
            result = subprocess.run(
                ["grim", "-g", geometry, "-t", "png", "-"],
                capture_output=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout:
                return Image.open(io.BytesIO(result.stdout))
        except (OSError, subprocess.SubprocessError) as e:
            logger.debug("grim capture failed for region %s: %s", geometry, e)
        return None


class ScreenManagerWayland(ScreenManager):
    """Wayland screen management using wlr-randr.

    Falls back to 1920x1080 default if wlr-randr is unavailable.
    """

    def get_screen_geometry(self, monitor: int = 0) -> ScreenGeometry:
        """Get screen geometry for a specific monitor."""
        monitors = self._query_monitors()
        if monitor < len(monitors):
            return monitors[monitor]
        elif monitors:
            return monitors[0]
        return ScreenGeometry(0, 0, 1920, 1080, True)

    def get_all_monitors(self) -> list[ScreenGeometry]:
        """Get geometry for all connected monitors."""
        monitors = self._query_monitors()
        return monitors if monitors else [ScreenGeometry(0, 0, 1920, 1080, True)]

    def _query_monitors(self) -> list[ScreenGeometry]:
        """Query monitor info from wlr-randr.

        Returns:
            List of ScreenGeometry, empty if wlr-randr unavailable.
        """
        try:
            result = subprocess.run(
                ["wlr-randr"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                logger.debug("wlr-randr returned non-zero exit code")
                return []
            return self._parse_wlr_randr_output(result.stdout)
        except (OSError, subprocess.SubprocessError) as e:
            logger.debug("wlr-randr failed: %s", e)
            return []

    def _parse_wlr_randr_output(self, output: str) -> list[ScreenGeometry]:
        """Parse wlr-randr output to extract monitor geometries.

        wlr-randr output format example:
            DP-1 "Dell Inc. ..." (DP-1)
              Enabled: yes
              ...
              Position: 0,0
              ...
              current 2560x1440@143.998001 Hz
                ...

        Args:
            output: Raw wlr-randr stdout.

        Returns:
            List of ScreenGeometry objects.
        """
        monitors: list[ScreenGeometry] = []
        current_enabled = False
        current_pos_x = 0
        current_pos_y = 0
        current_width = 0
        current_height = 0
        in_output_block = False

        for line in output.split("\n"):
            stripped = line.strip()

            # New output block (line starts without whitespace and isn't empty)
            if line and not line[0].isspace() and stripped:
                # Save previous monitor if we had one
                if in_output_block and current_enabled and current_width > 0:
                    is_primary = len(monitors) == 0
                    monitors.append(
                        ScreenGeometry(
                            current_pos_x,
                            current_pos_y,
                            current_width,
                            current_height,
                            is_primary,
                        )
                    )
                in_output_block = True
                current_enabled = False
                current_pos_x = 0
                current_pos_y = 0
                current_width = 0
                current_height = 0
                continue

            if not in_output_block:
                continue

            if "Enabled: yes" in stripped:
                current_enabled = True

            # Position: 0,0
            pos_match = re.match(r"Position:\s*(\d+),(\d+)", stripped)
            if pos_match:
                current_pos_x = int(pos_match.group(1))
                current_pos_y = int(pos_match.group(2))

            # current 2560x1440@143.998001 Hz
            # Also matches: current 1920x1080@60.000000 Hz (preferred)
            mode_match = re.match(r"current\s+(\d+)x(\d+)@", stripped)
            if mode_match:
                current_width = int(mode_match.group(1))
                current_height = int(mode_match.group(2))

        # Don't forget the last output block
        if in_output_block and current_enabled and current_width > 0:
            is_primary = len(monitors) == 0
            monitors.append(
                ScreenGeometry(
                    current_pos_x,
                    current_pos_y,
                    current_width,
                    current_height,
                    is_primary,
                )
            )

        return monitors


class EVEPathResolverWayland(EVEPathResolver):
    """Wayland EVE path resolution.

    Delegates to Linux paths since EVE runs under Proton regardless of
    display server.
    """

    def __init__(self) -> None:
        # Import here to avoid circular dependency at module level
        from .linux import EVEPathResolverLinux

        self._linux_resolver = EVEPathResolverLinux()

    def get_eve_settings_paths(self) -> list[Path]:
        """Get candidate EVE settings paths (same as Linux)."""
        return self._linux_resolver.get_eve_settings_paths()

    def get_eve_logs_paths(self) -> list[Path]:
        """Get candidate EVE game logs paths (same as Linux)."""
        return self._linux_resolver.get_eve_logs_paths()

    def get_config_directory(self) -> Path:
        """Get application config directory (same as Linux)."""
        return self._linux_resolver.get_config_directory()


class HotkeyHelperWayland(HotkeyHelper):
    """Wayland hotkey normalization.

    Delegates to Linux implementation since pynput normalization
    is identical regardless of display server.
    """

    def __init__(self) -> None:
        from .linux import HotkeyHelperLinux

        self._linux_helper = HotkeyHelperLinux()

    def normalize_combo(self, key_combo: str) -> str:
        """Normalize hotkey combo for pynput (same as Linux)."""
        return self._linux_helper.normalize_combo(key_combo)

    def is_single_key(self, key_combo: str) -> bool:
        """Check if key combo is a single key (same as Linux)."""
        return self._linux_helper.is_single_key(key_combo)
