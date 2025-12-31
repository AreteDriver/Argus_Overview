"""Window management utilities with validation."""

import logging
import re
import subprocess
import time
from typing import Optional

from .constants import TIMEOUT_MEDIUM

logger = logging.getLogger(__name__)

# X11 window ID pattern: 0x followed by hex digits
WINDOW_ID_PATTERN = re.compile(r'^0x[0-9a-fA-F]+$')


def is_valid_window_id(window_id: str) -> bool:
    """Validate that a string is a valid X11 window ID.

    Args:
        window_id: The window ID to validate

    Returns:
        True if valid X11 window ID format (0x followed by hex digits)
    """
    if not window_id or not isinstance(window_id, str):
        return False
    return bool(WINDOW_ID_PATTERN.match(window_id))


def move_window(window_id: str, x: int, y: int, w: int, h: int,
                timeout: float = TIMEOUT_MEDIUM) -> bool:
    """Move and resize a window safely with validation.

    Args:
        window_id: X11 window ID (e.g., "0x03800003")
        x: Target X position
        y: Target Y position
        w: Target width
        h: Target height
        timeout: Subprocess timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    if not is_valid_window_id(window_id):
        logger.warning(f"Invalid window ID format: {window_id}")
        return False

    try:
        # Try with --sync first, fallback for Wine/Proton windows
        try:
            subprocess.run(
                ['xdotool', 'windowmove', '--sync', window_id, str(x), str(y)],
                capture_output=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            # Wine windows don't respond to sync, retry without it
            subprocess.run(
                ['xdotool', 'windowmove', window_id, str(x), str(y)],
                capture_output=True, timeout=timeout
            )
            time.sleep(0.1)

        try:
            subprocess.run(
                ['xdotool', 'windowsize', '--sync', window_id, str(w), str(h)],
                capture_output=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            subprocess.run(
                ['xdotool', 'windowsize', window_id, str(w), str(h)],
                capture_output=True, timeout=timeout
            )
            time.sleep(0.1)

        return True

    except Exception as e:
        logger.error(f"Failed to move window {window_id}: {e}")
        return False


def activate_window(window_id: str, timeout: float = TIMEOUT_MEDIUM) -> bool:
    """Activate (focus) a window safely with validation.

    Args:
        window_id: X11 window ID
        timeout: Subprocess timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    if not is_valid_window_id(window_id):
        logger.warning(f"Invalid window ID format: {window_id}")
        return False

    try:
        try:
            subprocess.run(
                ['xdotool', 'windowactivate', '--sync', window_id],
                capture_output=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            subprocess.run(
                ['xdotool', 'windowactivate', window_id],
                capture_output=True, timeout=timeout
            )
        return True
    except Exception as e:
        logger.error(f"Failed to activate window {window_id}: {e}")
        return False


def get_focused_window() -> Optional[str]:
    """Get the currently focused window ID.

    Returns:
        Window ID string or None if unable to determine
    """
    try:
        result = subprocess.run(
            ['xdotool', 'getwindowfocus'],
            capture_output=True, text=True, timeout=1
        )
        if result.returncode == 0:
            window_id = result.stdout.strip()
            # xdotool getwindowfocus returns decimal, convert to hex
            try:
                return hex(int(window_id))
            except ValueError:
                return window_id if is_valid_window_id(window_id) else None
    except Exception as e:
        logger.debug(f"Failed to get focused window: {e}")
    return None
