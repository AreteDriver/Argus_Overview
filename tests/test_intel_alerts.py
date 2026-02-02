"""Tests for intel alerts module.

Tests AlertDispatcher, AlertConfig, and AlertType.
"""

from unittest.mock import MagicMock, patch

from argus_overview.intel.alerts import AlertConfig, AlertDispatcher, AlertType
from argus_overview.intel.parser import IntelReport, ThreatLevel


def make_report(
    system="HED-GP",
    threat_level=ThreatLevel.DANGER,
    raw_message="Test intel",
    jumps_from_current=None,
):
    """Helper to create IntelReport with defaults."""
    return IntelReport(
        system=system,
        threat_level=threat_level,
        hostile_count=None,
        ship_types=[],
        player_names=[],
        raw_message=raw_message,
        jumps_from_current=jumps_from_current,
    )


class TestAlertType:
    """Tests for AlertType enum."""

    def test_alert_types_exist(self):
        """Test all alert types are defined."""
        assert AlertType.VISUAL_BORDER.value == "border"
        assert AlertType.VISUAL_OVERLAY.value == "overlay"
        assert AlertType.AUDIO.value == "audio"
        assert AlertType.SYSTEM_NOTIFICATION.value == "notification"


class TestAlertConfig:
    """Tests for AlertConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AlertConfig()

        assert config.enabled is True
        assert config.visual_border is True
        assert config.visual_overlay is True
        assert config.audio is True
        assert config.audio_file is None
        assert config.system_notification is False
        assert config.min_threat_level == "warning"
        assert config.jumps_threshold == 5
        assert config.border_duration_ms == 2000
        assert config.overlay_duration_ms == 5000
        assert config.cooldown_seconds == 5

    def test_custom_config(self):
        """Test custom configuration values."""
        config = AlertConfig(
            enabled=False,
            min_threat_level="danger",
            jumps_threshold=3,
            cooldown_seconds=10,
        )

        assert config.enabled is False
        assert config.min_threat_level == "danger"
        assert config.jumps_threshold == 3
        assert config.cooldown_seconds == 10

    def test_threat_colors_default(self):
        """Test default threat level colors."""
        config = AlertConfig()

        assert ThreatLevel.CLEAR in config.threat_colors
        assert ThreatLevel.WARNING in config.threat_colors
        assert ThreatLevel.CRITICAL in config.threat_colors
        assert config.threat_colors[ThreatLevel.CRITICAL] == "#FF0000"


class TestAlertDispatcher:
    """Tests for AlertDispatcher class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        dispatcher = AlertDispatcher()

        assert dispatcher.config is not None
        assert dispatcher.config.enabled is True

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = AlertConfig(enabled=False)
        dispatcher = AlertDispatcher(config=config)

        assert dispatcher.config.enabled is False

    def test_set_config(self):
        """Test updating configuration."""
        dispatcher = AlertDispatcher()
        new_config = AlertConfig(enabled=False, min_threat_level="critical")

        dispatcher.set_config(new_config)

        assert dispatcher.config.enabled is False
        assert dispatcher.config.min_threat_level == "critical"

    def test_dispatch_disabled(self):
        """Test dispatch when alerts are disabled."""
        config = AlertConfig(enabled=False)
        dispatcher = AlertDispatcher(config=config)
        report = make_report(threat_level=ThreatLevel.CRITICAL)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        dispatcher.dispatch(report)

        signal_handler.assert_not_called()

    def test_dispatch_below_threshold(self):
        """Test dispatch when threat level below threshold."""
        config = AlertConfig(enabled=True, min_threat_level="danger")
        dispatcher = AlertDispatcher(config=config)
        report = make_report(threat_level=ThreatLevel.WARNING)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        dispatcher.dispatch(report)

        signal_handler.assert_not_called()

    def test_dispatch_above_threshold(self):
        """Test dispatch when threat level meets threshold."""
        config = AlertConfig(
            enabled=True,
            min_threat_level="warning",
            visual_border=True,
            visual_overlay=False,
            audio=False,
            system_notification=False,
        )
        dispatcher = AlertDispatcher(config=config)
        report = make_report(threat_level=ThreatLevel.DANGER)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        dispatcher.dispatch(report)

        assert signal_handler.call_count == 1
        call_args = signal_handler.call_args[0]
        assert call_args[1] == AlertType.VISUAL_BORDER

    def test_dispatch_cooldown(self):
        """Test cooldown prevents rapid alerts."""
        config = AlertConfig(
            enabled=True,
            min_threat_level="warning",
            cooldown_seconds=60,
            visual_border=True,
            visual_overlay=False,
            audio=False,
            system_notification=False,
        )
        dispatcher = AlertDispatcher(config=config)
        report = make_report(threat_level=ThreatLevel.DANGER)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        # First dispatch should work
        dispatcher.dispatch(report)
        assert signal_handler.call_count == 1

        # Second dispatch should be blocked by cooldown
        dispatcher.dispatch(report)
        assert signal_handler.call_count == 1  # Still 1

    def test_dispatch_different_systems_no_cooldown(self):
        """Test different systems don't share cooldown."""
        config = AlertConfig(
            enabled=True,
            min_threat_level="warning",
            cooldown_seconds=60,
            visual_border=True,
            visual_overlay=False,
            audio=False,
            system_notification=False,
        )
        dispatcher = AlertDispatcher(config=config)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        report1 = make_report(system="HED-GP", threat_level=ThreatLevel.DANGER)
        report2 = make_report(system="1DQ1-A", threat_level=ThreatLevel.DANGER)

        dispatcher.dispatch(report1)
        dispatcher.dispatch(report2)

        # Both should trigger
        assert signal_handler.call_count == 2

    def test_dispatch_jumps_threshold(self):
        """Test jumps threshold filtering."""
        config = AlertConfig(
            enabled=True,
            min_threat_level="warning",
            jumps_threshold=3,
            visual_border=True,
            visual_overlay=False,
            audio=False,
            system_notification=False,
        )
        dispatcher = AlertDispatcher(config=config)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        # Report too far away
        report_far = make_report(
            system="HED-GP",
            threat_level=ThreatLevel.DANGER,
            jumps_from_current=5,
        )

        dispatcher.dispatch(report_far)
        assert signal_handler.call_count == 0

        # Report within range
        report_close = make_report(
            system="1DQ1-A",
            threat_level=ThreatLevel.DANGER,
            jumps_from_current=2,
        )

        dispatcher.dispatch(report_close)
        assert signal_handler.call_count == 1

    def test_border_flash_signal(self):
        """Test border flash signal is emitted with correct params."""
        config = AlertConfig(
            enabled=True,
            min_threat_level="info",
            visual_border=True,
            visual_overlay=False,
            audio=False,
            system_notification=False,
            border_duration_ms=3000,
        )
        dispatcher = AlertDispatcher(config=config)

        signal_handler = MagicMock()
        dispatcher.border_flash_requested.connect(signal_handler)

        report = make_report(threat_level=ThreatLevel.CRITICAL)

        dispatcher.dispatch(report)

        signal_handler.assert_called_once()
        call_args = signal_handler.call_args[0]
        assert call_args[0] == config.threat_colors[ThreatLevel.CRITICAL]
        assert call_args[1] == 3000

    def test_overlay_signal(self):
        """Test overlay signal is emitted."""
        config = AlertConfig(
            enabled=True,
            min_threat_level="info",
            visual_border=False,
            visual_overlay=True,
            audio=False,
            system_notification=False,
        )
        dispatcher = AlertDispatcher(config=config)

        signal_handler = MagicMock()
        dispatcher.overlay_requested.connect(signal_handler)

        report = make_report(threat_level=ThreatLevel.WARNING)

        dispatcher.dispatch(report)

        signal_handler.assert_called_once_with(report)


class TestShouldAlert:
    """Tests for _should_alert method."""

    def test_should_alert_clear_level(self):
        """Test clear threat level doesn't alert by default."""
        config = AlertConfig(min_threat_level="warning")
        dispatcher = AlertDispatcher(config=config)

        report = make_report(threat_level=ThreatLevel.CLEAR)

        assert dispatcher._should_alert(report) is False

    def test_should_alert_info_level(self):
        """Test info level doesn't alert when threshold is warning."""
        config = AlertConfig(min_threat_level="warning")
        dispatcher = AlertDispatcher(config=config)

        report = make_report(threat_level=ThreatLevel.INFO)

        assert dispatcher._should_alert(report) is False

    def test_should_alert_critical_level(self):
        """Test critical level always alerts."""
        config = AlertConfig(min_threat_level="warning")
        dispatcher = AlertDispatcher(config=config)

        report = make_report(threat_level=ThreatLevel.CRITICAL)

        assert dispatcher._should_alert(report) is True

    def test_should_alert_invalid_threshold(self):
        """Test invalid threshold defaults to warning."""
        config = AlertConfig(min_threat_level="invalid")
        dispatcher = AlertDispatcher(config=config)

        report = make_report(threat_level=ThreatLevel.DANGER)

        # Should still alert since danger > warning (default)
        assert dispatcher._should_alert(report) is True


class TestAudioAlerts:
    """Tests for audio alert functionality."""

    def test_play_audio_no_file(self):
        """Test _play_audio handles missing audio file."""
        config = AlertConfig(audio=True, audio_file=None)
        dispatcher = AlertDispatcher(config=config)

        report = make_report(threat_level=ThreatLevel.WARNING)

        # Should not raise even without audio file
        dispatcher._play_audio(report)

    def test_play_sound_paplay_success(self):
        """Test _play_sound uses paplay successfully."""
        dispatcher = AlertDispatcher()

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch(
            "argus_overview.intel.alerts.subprocess.run", return_value=mock_result
        ) as mock_run:
            from pathlib import Path

            dispatcher._play_sound(Path("/fake/sound.wav"))

            mock_run.assert_called_once()
            assert "paplay" in mock_run.call_args[0][0]

    def test_play_sound_fallback_to_aplay(self):
        """Test _play_sound falls back to aplay."""
        dispatcher = AlertDispatcher()

        mock_paplay_fail = MagicMock()
        mock_paplay_fail.returncode = 1
        mock_aplay_success = MagicMock()
        mock_aplay_success.returncode = 0

        with patch(
            "argus_overview.intel.alerts.subprocess.run",
            side_effect=[mock_paplay_fail, mock_aplay_success],
        ) as mock_run:
            from pathlib import Path

            dispatcher._play_sound(Path("/fake/sound.wav"))

            assert mock_run.call_count == 2

    def test_play_sound_no_player_found(self):
        """Test _play_sound handles no audio player."""
        dispatcher = AlertDispatcher()

        with patch(
            "argus_overview.intel.alerts.subprocess.run",
            side_effect=FileNotFoundError("No paplay"),
        ):
            from pathlib import Path

            # Should not raise
            dispatcher._play_sound(Path("/fake/sound.wav"))

    def test_play_sound_timeout(self):
        """Test _play_sound handles timeout."""
        import subprocess

        dispatcher = AlertDispatcher()

        with patch(
            "argus_overview.intel.alerts.subprocess.run",
            side_effect=subprocess.TimeoutExpired("paplay", 10),
        ):
            from pathlib import Path

            # Should not raise
            dispatcher._play_sound(Path("/fake/sound.wav"))

    def test_default_audio_returns_path(self):
        """Test _default_audio returns correct paths."""
        dispatcher = AlertDispatcher()

        warning_path = dispatcher._default_audio(ThreatLevel.WARNING)
        danger_path = dispatcher._default_audio(ThreatLevel.DANGER)
        clear_path = dispatcher._default_audio(ThreatLevel.CLEAR)

        assert warning_path is not None
        assert "warning.wav" in str(warning_path)
        assert danger_path is not None
        assert "danger.wav" in str(danger_path)
        assert clear_path is None  # No sound for CLEAR


class TestNotifications:
    """Tests for desktop notification functionality."""

    def test_send_notification_success(self):
        """Test _send_notification sends notification."""
        dispatcher = AlertDispatcher()

        report = make_report(
            system="HED-GP",
            threat_level=ThreatLevel.DANGER,
        )

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch(
            "argus_overview.intel.alerts.subprocess.run", return_value=mock_result
        ) as mock_run:
            dispatcher._send_notification(report)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "notify-send" in call_args

    def test_send_notification_with_hostiles(self):
        """Test notification includes hostile count."""
        dispatcher = AlertDispatcher()

        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.DANGER,
            hostile_count=5,
            ship_types=["Sabre", "Loki", "Tengu", "Legion"],
            player_names=[],
            raw_message="test",
            jumps_from_current=3,
        )

        with patch("argus_overview.intel.alerts.subprocess.run") as mock_run:
            dispatcher._send_notification(report)

            mock_run.assert_called_once()

    def test_send_notification_no_notifysend(self):
        """Test notification handles missing notify-send."""
        dispatcher = AlertDispatcher()

        report = make_report()

        with patch(
            "argus_overview.intel.alerts.subprocess.run",
            side_effect=FileNotFoundError("No notify-send"),
        ):
            # Should not raise
            dispatcher._send_notification(report)

    def test_send_notification_timeout(self):
        """Test notification handles timeout."""
        import subprocess

        dispatcher = AlertDispatcher()

        report = make_report()

        with patch(
            "argus_overview.intel.alerts.subprocess.run",
            side_effect=subprocess.TimeoutExpired("notify-send", 5),
        ):
            # Should not raise
            dispatcher._send_notification(report)

    def test_send_notification_critical_urgency(self):
        """Test critical alerts have critical urgency."""
        dispatcher = AlertDispatcher()

        report = make_report(threat_level=ThreatLevel.CRITICAL)

        with patch("argus_overview.intel.alerts.subprocess.run") as mock_run:
            dispatcher._send_notification(report)

            call_args = mock_run.call_args[0][0]
            assert "--urgency=critical" in call_args


class TestTestAlert:
    """Tests for test_alert method."""

    def test_test_alert_triggers_dispatch(self):
        """Test test_alert creates and dispatches a test report."""
        config = AlertConfig(
            enabled=True,
            min_threat_level="info",
            visual_border=True,
            visual_overlay=False,
            audio=False,
            system_notification=False,
        )
        dispatcher = AlertDispatcher(config=config)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        dispatcher.test_alert(ThreatLevel.WARNING)

        assert signal_handler.call_count >= 1

    def test_test_alert_default_warning(self):
        """Test test_alert defaults to WARNING level."""
        config = AlertConfig(
            enabled=True,
            min_threat_level="info",
            visual_border=True,
            visual_overlay=False,
            audio=False,
            system_notification=False,
        )
        dispatcher = AlertDispatcher(config=config)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        dispatcher.test_alert()

        call_args = signal_handler.call_args[0]
        assert call_args[0].threat_level == ThreatLevel.WARNING


class TestClearCooldowns:
    """Tests for clear_cooldowns method."""

    def test_clear_cooldowns(self):
        """Test clear_cooldowns removes all cooldowns."""
        config = AlertConfig(
            enabled=True,
            min_threat_level="info",
            cooldown_seconds=60,
            visual_border=True,
            visual_overlay=False,
            audio=False,
            system_notification=False,
        )
        dispatcher = AlertDispatcher(config=config)

        # Trigger alert to set cooldown
        report = make_report(system="HED-GP")
        dispatcher.dispatch(report)

        assert len(dispatcher._cooldowns) > 0

        dispatcher.clear_cooldowns()

        assert len(dispatcher._cooldowns) == 0


class TestDispatchAudioEnabled:
    """Tests for dispatch with audio enabled (lines 134-135)."""

    def test_dispatch_with_audio_enabled(self):
        """Test dispatch triggers audio alert when enabled."""
        from unittest.mock import patch

        config = AlertConfig(
            enabled=True,
            min_threat_level="info",
            cooldown_seconds=0,
            visual_border=False,
            visual_overlay=False,
            audio=True,
            system_notification=False,
        )
        dispatcher = AlertDispatcher(config=config)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        report = make_report(system="TEST", threat_level=ThreatLevel.WARNING)

        with patch.object(dispatcher, "_play_audio"):
            dispatcher.dispatch(report)

        # Should emit AUDIO alert type
        calls = [call[0][1] for call in signal_handler.call_args_list]
        assert AlertType.AUDIO in calls


class TestDispatchNotificationEnabled:
    """Tests for dispatch with system notification enabled (lines 139-140)."""

    def test_dispatch_with_notification_enabled(self):
        """Test dispatch triggers notification when enabled."""
        from unittest.mock import patch

        config = AlertConfig(
            enabled=True,
            min_threat_level="info",
            cooldown_seconds=0,
            visual_border=False,
            visual_overlay=False,
            audio=False,
            system_notification=True,
        )
        dispatcher = AlertDispatcher(config=config)

        signal_handler = MagicMock()
        dispatcher.alert_triggered.connect(signal_handler)

        report = make_report(system="TEST", threat_level=ThreatLevel.WARNING)

        with patch.object(dispatcher, "_send_notification"):
            dispatcher.dispatch(report)

        # Should emit SYSTEM_NOTIFICATION alert type
        calls = [call[0][1] for call in signal_handler.call_args_list]
        assert AlertType.SYSTEM_NOTIFICATION in calls


class TestPlayAudioNoFile:
    """Tests for _play_audio when no file found (line 204)."""

    def test_play_audio_no_file_found(self):
        """Test _play_audio logs debug when no file found."""
        from unittest.mock import patch

        config = AlertConfig(enabled=True)
        dispatcher = AlertDispatcher(config=config)

        report = make_report(threat_level=ThreatLevel.INFO)

        # Mock _default_audio to return None
        with patch.object(dispatcher, "_default_audio", return_value=None):
            dispatcher._play_audio(report)

        # Should not crash, just log debug


class TestPlaySoundException:
    """Tests for _play_sound exception handling (lines 234-235)."""

    def test_play_sound_generic_exception(self):
        """Test _play_sound handles generic exceptions."""
        from pathlib import Path
        from unittest.mock import patch

        config = AlertConfig(enabled=True)
        dispatcher = AlertDispatcher(config=config)

        # Mock subprocess.run to raise generic exception
        with patch("subprocess.run", side_effect=OSError("Permission denied")):
            # Should not raise
            dispatcher._play_sound(Path("/fake/audio.wav"))


class TestSendNotificationException:
    """Tests for _send_notification exception handling (lines 296-297)."""

    def test_send_notification_generic_exception(self):
        """Test _send_notification handles generic exceptions."""
        from unittest.mock import patch

        config = AlertConfig(enabled=True)
        dispatcher = AlertDispatcher(config=config)

        report = make_report(threat_level=ThreatLevel.DANGER)

        # Mock subprocess.run to raise generic exception
        with patch("subprocess.run", side_effect=OSError("Permission denied")):
            # Should not raise
            dispatcher._send_notification(report)
