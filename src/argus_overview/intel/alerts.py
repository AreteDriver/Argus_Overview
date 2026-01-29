"""
Alert Dispatcher - Triggers visual and audio alerts for intel reports.

Supports:
- Visual border flash on preview windows
- Visual overlay notifications
- Audio alerts with configurable sounds
- Desktop notifications
"""

import logging
import subprocess
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal

from argus_overview.intel.parser import IntelReport, ThreatLevel


class AlertType(Enum):
    """Types of alerts that can be triggered."""

    VISUAL_BORDER = "border"  # Flash window border
    VISUAL_OVERLAY = "overlay"  # Show overlay on preview
    AUDIO = "audio"  # Play sound
    SYSTEM_NOTIFICATION = "notification"  # Desktop notification


@dataclass
class AlertConfig:
    """Configuration for alert behavior."""

    enabled: bool = True
    visual_border: bool = True
    visual_overlay: bool = True
    audio: bool = True
    audio_file: Optional[Path] = None
    system_notification: bool = False

    # Thresholds
    min_threat_level: str = "warning"  # Minimum level to alert on
    jumps_threshold: int = 5  # Only alert if hostile within N jumps

    # Visual settings
    border_color: str = "#FF0000"  # Red
    border_duration_ms: int = 2000  # 2 seconds
    overlay_duration_ms: int = 5000  # 5 seconds

    # Audio settings
    audio_volume: float = 1.0  # 0.0 to 1.0

    # Cooldown (prevent alert spam)
    cooldown_seconds: int = 5  # Minimum time between alerts for same system

    # Threat level colors
    threat_colors: dict = field(
        default_factory=lambda: {
            ThreatLevel.CLEAR: "#00FF00",  # Green
            ThreatLevel.INFO: "#00BFFF",  # Light blue
            ThreatLevel.WARNING: "#FFA500",  # Orange
            ThreatLevel.DANGER: "#FF4500",  # Red-orange
            ThreatLevel.CRITICAL: "#FF0000",  # Red
        }
    )


class AlertDispatcher(QObject):
    """
    Dispatches alerts to Argus Overview UI.

    Emits signals for UI components to react to intel alerts.
    Handles audio playback and desktop notifications directly.
    """

    # Signals for UI alerts
    border_flash_requested = Signal(str, int)  # color, duration_ms
    overlay_requested = Signal(object)  # IntelReport
    alert_triggered = Signal(object, object)  # IntelReport, AlertType

    def __init__(self, config: Optional[AlertConfig] = None, parent: Optional[QObject] = None):
        """
        Initialize the alert dispatcher.

        Args:
            config: Alert configuration
            parent: Parent QObject
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config = config or AlertConfig()

        # Cooldown tracking: {system_name: last_alert_timestamp}
        self._cooldowns: dict = {}

        # Sound directory
        self._sounds_dir = Path(__file__).parent / "sounds"

    def set_config(self, config: AlertConfig):
        """Update alert configuration."""
        self.config = config

    def dispatch(self, report: IntelReport):
        """
        Dispatch alerts for an intel report.

        Args:
            report: Intel report to alert on
        """
        if not self.config.enabled:
            return

        if not self._should_alert(report):
            return

        self.logger.info(f"Dispatching alert: {report.system} - {report.threat_level.value}")

        # Visual border flash
        if self.config.visual_border:
            color = self.config.threat_colors.get(report.threat_level, self.config.border_color)
            self.border_flash_requested.emit(color, self.config.border_duration_ms)
            self.alert_triggered.emit(report, AlertType.VISUAL_BORDER)

        # Visual overlay
        if self.config.visual_overlay:
            self.overlay_requested.emit(report)
            self.alert_triggered.emit(report, AlertType.VISUAL_OVERLAY)

        # Audio alert
        if self.config.audio:
            self._play_audio(report)
            self.alert_triggered.emit(report, AlertType.AUDIO)

        # Desktop notification
        if self.config.system_notification:
            self._send_notification(report)
            self.alert_triggered.emit(report, AlertType.SYSTEM_NOTIFICATION)

        # Update cooldown
        if report.system:
            import time

            self._cooldowns[report.system.lower()] = time.time()

    def _should_alert(self, report: IntelReport) -> bool:
        """
        Determine if alert should fire based on config.

        Args:
            report: Intel report

        Returns:
            True if alert should fire
        """
        # Check threat level threshold
        threat_order = ["clear", "info", "warning", "danger", "critical"]
        try:
            min_level = threat_order.index(self.config.min_threat_level.lower())
            report_level = threat_order.index(report.threat_level.value)
        except ValueError:
            min_level = 2  # Default to warning
            report_level = threat_order.index(report.threat_level.value)

        if report_level < min_level:
            self.logger.debug(
                f"Alert suppressed: {report.threat_level.value} < {self.config.min_threat_level}"
            )
            return False

        # Check jump distance if available
        if report.jumps_from_current is not None:
            if report.jumps_from_current > self.config.jumps_threshold:
                self.logger.debug(
                    f"Alert suppressed: {report.jumps_from_current} jumps > {self.config.jumps_threshold}"
                )
                return False

        # Check cooldown
        if report.system:
            import time

            last_alert = self._cooldowns.get(report.system.lower(), 0)
            if time.time() - last_alert < self.config.cooldown_seconds:
                self.logger.debug(f"Alert suppressed: cooldown for {report.system}")
                return False

        return True

    def _play_audio(self, report: IntelReport):
        """
        Play alert sound in background thread.

        Args:
            report: Intel report
        """
        audio_file = self.config.audio_file or self._default_audio(report.threat_level)
        if audio_file and audio_file.exists():
            thread = threading.Thread(target=self._play_sound, args=(audio_file,), daemon=True)
            thread.start()
        else:
            self.logger.debug(f"No audio file found for {report.threat_level}")

    def _play_sound(self, filepath: Path):
        """
        Play sound file (runs in thread).

        Args:
            filepath: Path to audio file
        """
        try:
            # Try paplay (PulseAudio) first - most common on Linux
            result = subprocess.run(
                ["paplay", str(filepath)],
                capture_output=True,
                timeout=10,
            )
            if result.returncode == 0:
                return

            # Fallback to aplay (ALSA)
            subprocess.run(
                ["aplay", "-q", str(filepath)],
                capture_output=True,
                timeout=10,
            )

        except FileNotFoundError:
            self.logger.warning("No audio player found (paplay/aplay)")
        except subprocess.TimeoutExpired:
            self.logger.warning("Audio playback timed out")
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")

    def _default_audio(self, threat_level: ThreatLevel) -> Optional[Path]:
        """
        Get default audio file for threat level.

        Args:
            threat_level: Threat level

        Returns:
            Path to audio file, or None
        """
        files = {
            ThreatLevel.INFO: self._sounds_dir / "info.wav",
            ThreatLevel.WARNING: self._sounds_dir / "warning.wav",
            ThreatLevel.DANGER: self._sounds_dir / "danger.wav",
            ThreatLevel.CRITICAL: self._sounds_dir / "critical.wav",
        }
        return files.get(threat_level)

    def _send_notification(self, report: IntelReport):
        """
        Send desktop notification.

        Args:
            report: Intel report
        """
        try:
            title = f"Intel Alert: {report.system or 'Unknown System'}"
            body = f"{report.threat_level.value.upper()}"

            if report.hostile_count:
                body += f" - {report.hostile_count} hostile(s)"

            if report.ship_types:
                ships = ", ".join(report.ship_types[:3])
                body += f" - {ships}"
                if len(report.ship_types) > 3:
                    body += f" +{len(report.ship_types) - 3} more"

            if report.jumps_from_current is not None:
                body += f" ({report.jumps_from_current} jumps)"

            urgency = "critical" if report.threat_level == ThreatLevel.CRITICAL else "normal"

            subprocess.run(
                [
                    "notify-send",
                    f"--urgency={urgency}",
                    "--app-name=Argus Overview",
                    title,
                    body,
                ],
                capture_output=True,
                timeout=5,
            )

        except FileNotFoundError:
            self.logger.warning("notify-send not found")
        except subprocess.TimeoutExpired:
            self.logger.warning("Notification timed out")
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")

    def test_alert(self, threat_level: ThreatLevel = ThreatLevel.WARNING):
        """
        Trigger a test alert.

        Args:
            threat_level: Threat level for test
        """
        from datetime import datetime

        test_report = IntelReport(
            system="TEST-01",
            threat_level=threat_level,
            hostile_count=5,
            ship_types=["loki", "sabre"],
            player_names=[],
            raw_message="TEST-01 hostile Loki Sabre +5",
            timestamp=datetime.now(),
            channel="Test",
            reporter="Test Reporter",
        )
        self.dispatch(test_report)

    def clear_cooldowns(self):
        """Clear all alert cooldowns."""
        self._cooldowns.clear()
