"""
Unit tests for the ConfigWatcher module.

Tests cover:
- ConfigFileHandler callback invocation
- ConfigWatcher initialization
- Start/stop functionality
- Debounce behavior
- Polling fallback
- File change detection
"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from eve_overview_pro.core.config_watcher import (
    WATCHDOG_AVAILABLE,
    ConfigFileHandler,
    ConfigWatcher,
)


class TestConfigFileHandler:
    """Tests for ConfigFileHandler"""

    @pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not installed")
    def test_calls_callback_on_modified(self):
        """Calls callback on file modification"""
        from watchdog.events import FileModifiedEvent

        callback = MagicMock()
        handler = ConfigFileHandler(callback)

        # Create a real FileModifiedEvent
        event = FileModifiedEvent('/path/to/config.json')
        handler.on_modified(event)

        callback.assert_called_once()


class TestConfigWatcherInit:
    """Tests for ConfigWatcher initialization"""

    def test_stores_config_path(self):
        """Stores config path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            watcher = ConfigWatcher(config_path)

            assert watcher.config_path == config_path

    def test_default_debounce(self):
        """Default debounce is 500ms"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            watcher = ConfigWatcher(config_path)

            assert watcher.debounce_ms == 500

    def test_custom_debounce(self):
        """Can set custom debounce"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            watcher = ConfigWatcher(config_path, debounce_ms=1000)

            assert watcher.debounce_ms == 1000

    def test_initial_not_running(self):
        """Starts not running"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            watcher = ConfigWatcher(config_path)

            assert watcher.is_running() is False
            assert watcher._running is False


class TestIsRunning:
    """Tests for is_running method"""

    def test_returns_running_state(self):
        """Returns correct running state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            watcher = ConfigWatcher(config_path)

            assert watcher.is_running() is False
            watcher._running = True
            assert watcher.is_running() is True


class TestStartStop:
    """Tests for start/stop functionality"""

    @pytest.fixture
    def watcher(self):
        """Create watcher with temp config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{}")
            yield ConfigWatcher(config_path)

    def test_start_sets_running(self, watcher):
        """Start sets running flag"""
        with patch.object(watcher, '_start_watchdog'):
            with patch.object(watcher, '_start_polling'):
                watcher.start()
                assert watcher._running is True

    def test_start_only_once(self, watcher):
        """Start does nothing if already running"""
        watcher._running = True

        with patch.object(watcher, '_start_watchdog') as mock_watchdog:
            with patch.object(watcher, '_start_polling') as mock_polling:
                watcher.start()

                mock_watchdog.assert_not_called()
                mock_polling.assert_not_called()

    def test_stop_clears_running(self, watcher):
        """Stop clears running flag"""
        watcher._running = True
        watcher.stop()

        assert watcher._running is False

    def test_stop_does_nothing_if_not_running(self, watcher):
        """Stop does nothing if not running"""
        watcher._running = False
        watcher.stop()  # Should not raise

        assert watcher._running is False


class TestDebounce:
    """Tests for debounce functionality"""

    @pytest.fixture
    def watcher(self):
        """Create watcher"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            yield ConfigWatcher(config_path, debounce_ms=100)

    def test_on_file_changed_starts_debounce(self, watcher):
        """File change starts debounce timer"""
        with patch.object(watcher._debounce_timer, 'start') as mock_start:
            with patch.object(watcher._debounce_timer, 'stop'):
                watcher._on_file_changed()
                mock_start.assert_called_with(100)

    def test_on_file_changed_stops_existing_timer(self, watcher):
        """File change stops existing timer first"""
        with patch.object(watcher._debounce_timer, 'stop') as mock_stop:
            with patch.object(watcher._debounce_timer, 'start'):
                watcher._on_file_changed()
                mock_stop.assert_called()

    def test_emit_change_emits_signal(self, watcher):
        """_emit_change emits config_changed signal"""
        signal_received = []
        watcher.config_changed.connect(lambda: signal_received.append(True))

        watcher._emit_change()

        assert len(signal_received) == 1


class TestPollingFallback:
    """Tests for polling fallback mechanism"""

    @pytest.fixture
    def watcher(self):
        """Create watcher with config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{}")
            w = ConfigWatcher(config_path)
            yield w
            w.stop()

    def test_start_polling_starts_timer(self, watcher):
        """Polling starts timer"""
        with patch.object(watcher._poll_timer, 'start') as mock_start:
            watcher._start_polling()
            mock_start.assert_called_with(2000)

    def test_update_mtime_stores_mtime(self, watcher):
        """Updates stored modification time"""
        watcher._update_mtime()
        assert watcher._last_mtime is not None

    def test_check_file_detects_change(self, watcher):
        """Check file detects modification"""
        # Update mtime first to get real value
        watcher._update_mtime()
        current_mtime = watcher._last_mtime

        # Set old mtime to something less than current
        watcher._last_mtime = current_mtime - 1

        with patch.object(watcher, '_on_file_changed') as mock_change:
            watcher._check_file()
            mock_change.assert_called_once()

    def test_check_file_no_change(self, watcher):
        """Check file ignores if not changed"""
        watcher._update_mtime()

        with patch.object(watcher, '_on_file_changed') as mock_change:
            watcher._check_file()
            mock_change.assert_not_called()

    def test_check_file_handles_missing(self, watcher):
        """Check file handles missing file"""
        watcher.config_path = Path("/nonexistent/config.json")

        # Should not raise
        watcher._check_file()


class TestWatchdogIntegration:
    """Tests for watchdog integration"""

    def test_watchdog_available_flag(self):
        """WATCHDOG_AVAILABLE flag is set"""
        # This just verifies the constant exists
        assert isinstance(WATCHDOG_AVAILABLE, bool)

    @pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not installed")
    def test_start_uses_watchdog(self):
        """Start uses watchdog when available"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{}")
            watcher = ConfigWatcher(config_path)

            with patch.object(watcher, '_start_watchdog') as mock_watchdog:
                watcher.start()
                mock_watchdog.assert_called_once()

            watcher.stop()


class TestStopCleansUp:
    """Tests for cleanup on stop"""

    def test_stops_observer(self):
        """Stop cleans up observer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{}")
            watcher = ConfigWatcher(config_path)

            # Mock observer
            mock_observer = MagicMock()
            watcher._observer = mock_observer
            watcher._running = True

            watcher.stop()

            mock_observer.stop.assert_called_once()
            assert watcher._observer is None

    def test_stops_poll_timer(self):
        """Stop stops poll timer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            watcher = ConfigWatcher(config_path)
            watcher._running = True

            with patch.object(watcher._poll_timer, 'stop') as mock_stop:
                watcher.stop()
                mock_stop.assert_called()

    def test_stops_debounce_timer(self):
        """Stop stops debounce timer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            watcher = ConfigWatcher(config_path)
            watcher._running = True

            with patch.object(watcher._debounce_timer, 'stop') as mock_stop:
                watcher.stop()
                mock_stop.assert_called()
