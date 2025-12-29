"""
Config Watcher - Hot reload configuration file changes
v2.2 Feature: Automatically detect and apply config changes without restart
"""
import logging
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, Signal

try:
    from watchdog.events import FileModifiedEvent, FileSystemEventHandler
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class ConfigFileHandler(FileSystemEventHandler):
    """Handler for config file changes"""

    def __init__(self, callback: Callable):
        super().__init__()
        self.callback = callback
        self.logger = logging.getLogger(__name__)

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            self.logger.debug(f"Config file modified: {event.src_path}")
            self.callback()


class ConfigWatcher(QObject):
    """
    Watches configuration files for changes and triggers reload.

    Features:
    - Uses watchdog for efficient file monitoring
    - Debounces rapid changes to prevent spam
    - Emits signal when config changes
    - Falls back to polling if watchdog unavailable
    """

    config_changed = Signal()

    def __init__(self, config_path: Path, debounce_ms: int = 500, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.debounce_ms = debounce_ms

        # Debounce timer
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_change)

        # Watchdog observer
        self._observer: Optional[Observer] = None
        self._running = False

        # Fallback polling timer
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._check_file)
        self._last_mtime: Optional[float] = None

    def start(self):
        """Start watching for config changes"""
        if self._running:
            return

        if WATCHDOG_AVAILABLE:
            self._start_watchdog()
        else:
            self._start_polling()

        self._running = True
        self.logger.info(f"Config watcher started for {self.config_path}")

    def stop(self):
        """Stop watching for config changes"""
        if not self._running:
            return

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=1.0)
            self._observer = None

        self._poll_timer.stop()
        self._debounce_timer.stop()
        self._running = False
        self.logger.info("Config watcher stopped")

    def _start_watchdog(self):
        """Start watchdog file monitoring"""
        try:
            handler = ConfigFileHandler(self._on_file_changed)
            self._observer = Observer()
            self._observer.schedule(
                handler,
                str(self.config_path.parent),
                recursive=False
            )
            self._observer.start()
            self.logger.info("Using watchdog for config monitoring")
        except Exception as e:
            self.logger.warning(f"Watchdog failed, falling back to polling: {e}")
            self._start_polling()

    def _start_polling(self):
        """Start fallback polling for config changes"""
        self._update_mtime()
        self._poll_timer.start(2000)  # Check every 2 seconds
        self.logger.info("Using polling for config monitoring")

    def _update_mtime(self):
        """Update stored modification time"""
        try:
            if self.config_path.exists():
                self._last_mtime = self.config_path.stat().st_mtime
        except Exception:
            pass

    def _check_file(self):
        """Polling check for file changes"""
        try:
            if self.config_path.exists():
                current_mtime = self.config_path.stat().st_mtime
                if self._last_mtime and current_mtime > self._last_mtime:
                    self._on_file_changed()
                self._last_mtime = current_mtime
        except Exception as e:
            self.logger.debug(f"Error checking config file: {e}")

    def _on_file_changed(self):
        """Handle file change - debounced"""
        # Reset debounce timer
        self._debounce_timer.stop()
        self._debounce_timer.start(self.debounce_ms)

    def _emit_change(self):
        """Emit the config changed signal after debounce"""
        self.logger.info("Config file changed, emitting reload signal")
        self.config_changed.emit()

    def is_running(self) -> bool:
        """Check if watcher is running"""
        return self._running
