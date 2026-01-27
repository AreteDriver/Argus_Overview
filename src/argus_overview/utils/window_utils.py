"""Window management utilities with validation and retry logic."""

import logging
import re
import subprocess
import time
from typing import List, Optional

from .constants import TIMEOUT_MEDIUM

logger = logging.getLogger(__name__)

# X11 window ID pattern: 0x followed by hex digits
WINDOW_ID_PATTERN = re.compile(r"^0x[0-9a-fA-F]+$")

# Retry defaults
_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BACKOFF_SECONDS = 0.15


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


def run_x11_subprocess(
    cmd: List[str],
    timeout: float = TIMEOUT_MEDIUM,
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


def move_window(
    window_id: str, x: int, y: int, w: int, h: int, timeout: float = TIMEOUT_MEDIUM
) -> bool:
    """Move and resize a window safely with validation and retry.

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
            # Wine windows don't respond to sync, retry without it
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


def activate_window(window_id: str, timeout: float = TIMEOUT_MEDIUM) -> bool:
    """Activate (focus) a window safely with validation and retry.

    Args:
        window_id: X11 window ID
        timeout: Subprocess timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    if not is_valid_window_id(window_id):
        logger.warning("Invalid window ID format for activate: %s", window_id)
        return False

    try:
        try:
            run_x11_subprocess(
                ["xdotool", "windowactivate", "--sync", window_id],
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            run_x11_subprocess(
                ["xdotool", "windowactivate", window_id],
                timeout=timeout,
            )
        return True
    except Exception as e:
        logger.warning("Failed to activate window %s after retries: %s", window_id, e)
        return False


def get_focused_window() -> Optional[str]:
    """Get the currently focused window ID.

    Returns:
        Window ID string or None if unable to determine
    """
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
            return window_id if is_valid_window_id(window_id) else None
    except Exception as e:
        logger.debug("Failed to get focused window: %s", e)
    return None
