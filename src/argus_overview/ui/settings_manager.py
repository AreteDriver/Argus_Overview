"""
Settings Manager - JSON-based configuration persistence
Handles all application settings with nested key support and auto-save
"""

import copy
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class SettingsManager:
    """
    Manages application settings with JSON persistence.
    Supports nested keys (e.g., "performance.capture_workers")
    """

    DEFAULT_SETTINGS = {
        "version": "2.3",
        "general": {
            "start_with_system": False,
            "minimize_to_tray": True,
            "show_notifications": True,
            "auto_save_interval": 5,  # minutes
            "auto_discovery": True,
            "auto_discovery_interval": 5,  # seconds
            "hot_reload": True,
        },
        "performance": {
            "low_power_mode": False,  # FPS=5, alerts off - for running with EVE clients
            "auto_minimize_inactive": False,  # Auto-minimize previous window when cycling
            "disable_previews": False,  # Disable all window captures (saves GPU/CPU)
            "default_refresh_rate": 1,  # FPS - 1 is efficient, increase if needed
            "capture_workers": 1,  # Single worker to reduce overhead
            "enable_caching": True,
            "cache_size_mb": 50,
            "capture_quality": "low",  # low, medium, high
        },
        "thumbnails": {
            "opacity_on_hover": 0.3,
            "zoom_on_hover": 1.5,
            "lock_positions": False,
            "show_labels": True,
            "show_session_timer": False,
            "show_activity_indicator": True,
            "default_width": 280,
            "default_height": 200,
        },
        "hotkeys": {
            "activate_window_1": "<ctrl>+<alt>+1",
            "activate_window_2": "<ctrl>+<alt>+2",
            "activate_window_3": "<ctrl>+<alt>+3",
            "activate_window_4": "<ctrl>+<alt>+4",
            "activate_window_5": "<ctrl>+<alt>+5",
            "activate_window_6": "<ctrl>+<alt>+6",
            "activate_window_7": "<ctrl>+<alt>+7",
            "activate_window_8": "<ctrl>+<alt>+8",
            "activate_window_9": "<ctrl>+<alt>+9",
            "minimize_all": "<ctrl>+<shift>+m",
            "restore_all": "<ctrl>+<shift>+r",
            "refresh_all": "<ctrl>+<alt>+f5",
            "next_layout": "<ctrl>+<alt>+]",
            "previous_layout": "<ctrl>+<alt>+[",
            "toggle_always_on_top": "<ctrl>+<alt>+t",
            "toggle_thumbnails": "<ctrl>+<shift>+t",
            "toggle_lock": "<ctrl>+<shift>+l",
            "cycle_next": "<ctrl>+<shift>+<]>",
            "cycle_prev": "<ctrl>+<shift>+<[>",
        },
        "character_hotkeys": {},
        "character_labels": {},
        "appearance": {
            "theme": "dark",
            "font_size": 10,
            "compact_mode": False,
            "accent_color": "#4287f5",
        },
        "advanced": {
            "log_level": "INFO",
            "config_directory": "~/.config/argus-overview",
            "enable_debug": False,
        },
        "intel": {
            "channels": ["Alliance", "Intel"],  # Default intel channels to monitor
            "alerts_enabled": True,
            "visual_border": True,
            "visual_overlay": True,
            "audio_enabled": True,
            "system_notification": False,
            "min_threat_level": "warning",  # info, warning, danger, critical
            "jumps_threshold": 5,  # Only alert if hostile within N jumps
            "cooldown_seconds": 5,  # Minimum time between alerts for same system
            "current_system": "",  # Player's current system for jump calculations
            "custom_log_path": "",  # Custom path to EVE chat logs
        },
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize SettingsManager

        Args:
            config_dir: Configuration directory path (default: ~/.config/argus-overview)
        """
        self.logger = logging.getLogger(__name__)

        if config_dir is None:
            config_dir = Path.home() / ".config" / "argus-overview"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.settings_file = self.config_dir / "settings.json"
        self.settings: Dict = {}

        # Runtime state (not persisted)
        self._last_activated_window: Optional[str] = None

        # Load settings or create defaults
        self.load_settings()

    def load_settings(self) -> Dict:
        """
        Load settings from JSON file

        Returns:
            dict: Loaded settings
        """
        if self.settings_file.exists():
            try:
                with open(self.settings_file) as f:
                    loaded = json.load(f)

                # Merge with defaults (add any new keys from updates)
                self.settings = self._merge_settings(copy.deepcopy(self.DEFAULT_SETTINGS), loaded)

                self.logger.info(f"Loaded settings from {self.settings_file}")
                return self.settings

            except Exception as e:
                self.logger.error(f"Failed to load settings: {e}")
                self.logger.info("Using default settings")

        # Use defaults if file doesn't exist or load failed
        self.settings = copy.deepcopy(self.DEFAULT_SETTINGS)
        self.save_settings(self.settings)
        return self.settings

    def save_settings(self, settings: Optional[Dict] = None) -> bool:
        """
        Save settings to JSON file

        Args:
            settings: Settings dict to save (default: current settings)

        Returns:
            bool: True if successful
        """
        if settings is not None:
            self.settings = settings

        try:
            # Atomic write: write to temp file, then rename
            temp_file = self.settings_file.with_suffix(".json.tmp")

            with open(temp_file, "w") as f:
                json.dump(self.settings, f, indent=2)

            # Rename (atomic on POSIX systems)
            temp_file.replace(self.settings_file)

            self.logger.debug("Settings saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get setting value by nested key

        Args:
            key: Setting key (e.g., "thumbnails.opacity_on_hover")
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        keys = key.split(".")
        value = self.settings

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """
        Set setting value by nested key

        Args:
            key: Setting key (e.g., "thumbnails.opacity_on_hover")
            value: Value to set
            auto_save: Save settings immediately (default: True)

        Returns:
            bool: True if successful
        """
        keys = key.split(".")

        # Navigate to parent dict
        current = self.settings
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set value
        current[keys[-1]] = value

        if auto_save:
            return self.save_settings()

        return True

    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to defaults

        Returns:
            bool: True if successful
        """
        self.logger.info("Resetting settings to defaults")
        self.settings = copy.deepcopy(self.DEFAULT_SETTINGS)
        return self.save_settings()

    def export_config(self, export_path: Path) -> bool:
        """
        Export settings to external file

        Args:
            export_path: Path to export to

        Returns:
            bool: True if successful
        """
        try:
            export_path = Path(export_path)

            # Add metadata
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "version": "2.1.0",
                "settings": self.settings,
            }

            with open(export_path, "w") as f:
                json.dump(export_data, f, indent=2)

            self.logger.info(f"Settings exported to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            return False

    def import_config(self, import_path: Path) -> bool:
        """
        Import settings from external file

        Args:
            import_path: Path to import from

        Returns:
            bool: True if successful
        """
        try:
            import_path = Path(import_path)

            with open(import_path) as f:
                import_data = json.load(f)

            # Extract settings (handle both old and new format)
            if "settings" in import_data:
                imported_settings = import_data["settings"]
            else:
                imported_settings = import_data

            # Merge with defaults (preserve structure)
            self.settings = self._merge_settings(
                copy.deepcopy(self.DEFAULT_SETTINGS), imported_settings
            )

            # Save
            if self.save_settings():
                self.logger.info(f"Settings imported from {import_path}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            return False

    def _merge_settings(self, base: Dict, overlay: Dict) -> Dict:
        """
        Recursively merge overlay settings into base settings
        Preserves structure from base, updates values from overlay

        Args:
            base: Base settings dict
            overlay: Overlay settings dict

        Returns:
            dict: Merged settings
        """
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._merge_settings(base[key], value)
            else:
                base[key] = value

        return base

    def get_all(self) -> Dict:
        """
        Get all settings

        Returns:
            dict: Complete settings dictionary
        """
        return self.settings.copy()

    def validate(self) -> bool:
        """
        Validate current settings

        Returns:
            bool: True if valid
        """
        try:
            # Check refresh rate is reasonable
            refresh_rate = self.get("performance.default_refresh_rate", 30)
            if not (1 <= refresh_rate <= 60):
                self.logger.warning(f"Invalid refresh rate: {refresh_rate}, resetting to 30")
                self.set("performance.default_refresh_rate", 30)

            # Check worker count is reasonable
            workers = self.get("performance.capture_workers", 4)
            if not (1 <= workers <= 16):
                self.logger.warning(f"Invalid worker count: {workers}, resetting to 4")
                self.set("performance.capture_workers", 4)

            return True

        except Exception as e:
            self.logger.error(f"Settings validation failed: {e}")
            return False

    def get_last_activated_window(self) -> Optional[str]:
        """Get the last activated EVE window ID (runtime state, not persisted)"""
        return self._last_activated_window

    def set_last_activated_window(self, window_id: Optional[str]) -> None:
        """Set the last activated EVE window ID (runtime state, not persisted)"""
        self._last_activated_window = window_id
