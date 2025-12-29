"""
Visual Activity Alert Detector
Monitors windows for visual changes and triggers alerts
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import numpy as np
from PIL import Image


class AlertLevel(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AlertConfig:
    """Configuration for alert detection"""
    enabled: bool = True
    red_flash_threshold: float = 0.7  # Threshold for red flash detection
    change_threshold: float = 0.3  # Threshold for general screen change
    alert_cooldown: int = 5  # Seconds between same alerts
    sound_enabled: bool = False
    visual_border: bool = True
    border_color: str = "#ff0000"
    border_flash_duration: int = 3  # Seconds


class AlertDetector:
    """Detects visual activity in window captures"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = AlertConfig()
        self.previous_frames = {}  # window_id -> previous image
        self.last_alert_times = {}  # window_id -> timestamp
        self.alert_callbacks = {}  # window_id -> callback function

    def set_config(self, config: AlertConfig):
        """Update alert configuration"""
        self.config = config

    def register_callback(self, window_id: str, callback: Callable):
        """Register callback for window alerts

        Args:
            window_id: Window to monitor
            callback: Function to call on alert (receives AlertLevel)
        """
        self.alert_callbacks[window_id] = callback

    def unregister_callback(self, window_id: str):
        """Unregister alert callback"""
        if window_id in self.alert_callbacks:
            del self.alert_callbacks[window_id]
        if window_id in self.previous_frames:
            del self.previous_frames[window_id]

    def analyze_frame(self, window_id: str, image: Image.Image) -> Optional[AlertLevel]:
        """Analyze a frame for alert conditions

        Args:
            window_id: Window being analyzed
            image: Current frame

        Returns:
            AlertLevel if alert detected, None otherwise
        """
        if not self.config.enabled or image is None:
            return None

        alert_level = None

        # Check for red flash (damage indicator)
        if self._detect_red_flash(image):
            alert_level = AlertLevel.HIGH
            self.logger.info(f"RED FLASH detected in window {window_id}")

        # Check for significant screen change
        elif window_id in self.previous_frames:
            if self._detect_screen_change(image, self.previous_frames[window_id]):
                alert_level = AlertLevel.MEDIUM
                self.logger.debug(f"Screen change detected in window {window_id}")

        # Store frame for next comparison
        self.previous_frames[window_id] = image.copy()

        # Trigger callback if alert detected
        if alert_level and window_id in self.alert_callbacks:
            try:
                self.alert_callbacks[window_id](alert_level)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")

        return alert_level

    def _detect_red_flash(self, image: Image.Image) -> bool:
        """Detect red flash in image (damage indicator)

        Args:
            image: Image to analyze

        Returns:
            True if red flash detected
        """
        try:
            # Convert to RGB array
            img_array = np.array(image.convert('RGB'))

            # Extract color channels
            r = img_array[:, :, 0].astype(float)
            g = img_array[:, :, 1].astype(float)
            b = img_array[:, :, 2].astype(float)

            # Calculate red dominance
            # Red flash: R > G+B and R > threshold
            red_dominant = (r > (g + b)) & (r > 200)

            # Calculate percentage of red pixels
            total_pixels = r.size
            red_pixels = np.sum(red_dominant)
            red_percentage = red_pixels / total_pixels

            # Alert if significant portion is red
            return red_percentage > self.config.red_flash_threshold

        except Exception as e:
            self.logger.error(f"Red flash detection error: {e}")
            return False

    def _detect_screen_change(self, current: Image.Image,
                             previous: Image.Image) -> bool:
        """Detect significant change between frames

        Args:
            current: Current frame
            previous: Previous frame

        Returns:
            True if significant change detected
        """
        try:
            # Resize to common size for comparison
            size = (100, 100)
            current_resized = current.resize(size).convert('L')
            previous_resized = previous.resize(size).convert('L')

            # Convert to arrays
            current_array = np.array(current_resized).astype(float)
            previous_array = np.array(previous_resized).astype(float)

            # Calculate difference
            diff = np.abs(current_array - previous_array)

            # Calculate percentage of changed pixels
            total_pixels = diff.size
            changed_pixels = np.sum(diff > 30)  # Threshold for pixel change
            change_percentage = changed_pixels / total_pixels

            # Alert if significant change
            return change_percentage > self.config.change_threshold

        except Exception as e:
            self.logger.error(f"Screen change detection error: {e}")
            return False

    def clear_history(self, window_id: Optional[str] = None):
        """Clear frame history

        Args:
            window_id: Specific window to clear, or None for all
        """
        if window_id:
            if window_id in self.previous_frames:
                del self.previous_frames[window_id]
        else:
            self.previous_frames.clear()
