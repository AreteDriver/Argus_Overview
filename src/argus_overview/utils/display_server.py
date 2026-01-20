"""Display server detection utilities.

Detects X11, Wayland, and XWayland sessions to provide appropriate
warnings and graceful degradation.
"""

import logging
import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DisplayServer(Enum):
    """Display server types."""

    X11 = "x11"
    WAYLAND = "wayland"
    XWAYLAND = "xwayland"
    UNKNOWN = "unknown"


@dataclass
class DisplayInfo:
    """Information about the current display environment."""

    server: DisplayServer
    has_x11_access: bool  # Can use X11 tools (wmctrl, xdotool, etc.)
    session_type: str  # Raw XDG_SESSION_TYPE value
    wayland_display: Optional[str]  # WAYLAND_DISPLAY if set
    x11_display: Optional[str]  # DISPLAY if set


def detect_display_server() -> DisplayInfo:
    """Detect the current display server environment.

    Returns:
        DisplayInfo with details about the display environment.

    Detection logic:
    - XDG_SESSION_TYPE=wayland + no DISPLAY = Pure Wayland (no X11 access)
    - XDG_SESSION_TYPE=wayland + DISPLAY set = XWayland (X11 tools work)
    - XDG_SESSION_TYPE=x11 = Native X11
    - Fallback: check if X11 tools work
    """
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY")
    x11_display = os.environ.get("DISPLAY")

    logger.info(
        f"Display detection: XDG_SESSION_TYPE={session_type}, "
        f"WAYLAND_DISPLAY={wayland_display}, DISPLAY={x11_display}"
    )

    # Determine server type
    if session_type == "wayland":
        if x11_display:
            # Wayland session but X11 DISPLAY is set - XWayland available
            server = DisplayServer.XWAYLAND
            has_x11 = True
        else:
            # Pure Wayland - no X11 access
            server = DisplayServer.WAYLAND
            has_x11 = False
    elif session_type == "x11":
        server = DisplayServer.X11
        has_x11 = True
    else:
        # Unknown session type - try to detect via tool availability
        has_x11 = _check_x11_tools_work()
        if has_x11:
            server = DisplayServer.X11 if not wayland_display else DisplayServer.XWAYLAND
        else:
            server = DisplayServer.WAYLAND if wayland_display else DisplayServer.UNKNOWN

    info = DisplayInfo(
        server=server,
        has_x11_access=has_x11,
        session_type=session_type or "unknown",
        wayland_display=wayland_display,
        x11_display=x11_display,
    )

    logger.info(f"Detected display server: {info.server.value}, X11 access: {info.has_x11_access}")
    return info


def _check_x11_tools_work() -> bool:
    """Check if X11 tools (wmctrl) are functional.

    Returns:
        True if wmctrl can list windows, False otherwise.
    """
    try:
        result = subprocess.run(
            ["wmctrl", "-l"],
            capture_output=True,
            timeout=2,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def is_pure_wayland() -> bool:
    """Check if running in pure Wayland (no X11 access).

    Returns:
        True if pure Wayland session without XWayland.
    """
    info = detect_display_server()
    return info.server == DisplayServer.WAYLAND and not info.has_x11_access


def get_wayland_limitation_message() -> str:
    """Get user-friendly message explaining Wayland limitations.

    Returns:
        Formatted message string for display in dialogs.
    """
    return """Argus Overview requires X11 to function.

Your system is running a pure Wayland session, which by design prevents
applications from:
  - Listing windows from other applications
  - Capturing window screenshots
  - Moving or focusing other windows
  - Sending keystrokes to other windows

This is a Wayland security feature, not a bug in Argus Overview.

To use Argus Overview with EVE Online:

1. Run EVE without PROTON_ENABLE_WAYLAND:
   Unset this environment variable to run EVE under XWayland.

2. Or switch to an X11 session:
   Log out and select "GNOME on Xorg" or similar at login.

3. Or use a compositor with XWayland:
   Most Wayland compositors provide XWayland automatically.
   Ensure DISPLAY environment variable is set.

For more information, see the README.md file."""
