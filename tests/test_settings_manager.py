"""
Unit tests for the Settings Manager module
Tests SettingsManager class with JSON persistence and nested key support
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestSettingsManagerInit:
    """Tests for SettingsManager initialization"""

    def test_init_creates_config_dir(self):
        """Test that init creates config directory if it doesn't exist"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "new_config_dir"
            assert not config_dir.exists()

            SettingsManager(config_dir=config_dir)

            assert config_dir.exists()
            assert config_dir.is_dir()

    def test_init_uses_default_config_dir(self):
        """Test that init uses default config dir when none specified"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = Path("/mock/home")
            with patch.object(Path, 'mkdir'):
                with patch.object(Path, 'exists', return_value=False):
                    with patch.object(SettingsManager, 'load_settings'):
                        manager = SettingsManager(config_dir=None)
                        # Check it would use default path
                        assert "argus-overview" in str(manager.config_dir)

    def test_init_loads_settings(self):
        """Test that init calls load_settings"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            manager = SettingsManager(config_dir=config_dir)

            # Settings should be loaded (defaults since no file exists)
            assert manager.settings is not None
            assert len(manager.settings) > 0

    def test_settings_file_path(self):
        """Test that settings_file path is set correctly"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            manager = SettingsManager(config_dir=config_dir)

            assert manager.settings_file == config_dir / "settings.json"


class TestDefaultSettings:
    """Tests for default settings structure"""

    def test_default_settings_has_version(self):
        """Test that DEFAULT_SETTINGS has version"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        assert "version" in SettingsManager.DEFAULT_SETTINGS

    def test_default_settings_has_general(self):
        """Test that DEFAULT_SETTINGS has general section"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        assert "general" in SettingsManager.DEFAULT_SETTINGS
        general = SettingsManager.DEFAULT_SETTINGS["general"]
        assert "start_with_system" in general
        assert "minimize_to_tray" in general
        assert "auto_discovery" in general

    def test_default_settings_has_performance(self):
        """Test that DEFAULT_SETTINGS has performance section"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        assert "performance" in SettingsManager.DEFAULT_SETTINGS
        perf = SettingsManager.DEFAULT_SETTINGS["performance"]
        assert "default_refresh_rate" in perf
        assert "capture_workers" in perf

    def test_default_settings_has_thumbnails(self):
        """Test that DEFAULT_SETTINGS has thumbnails section"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        assert "thumbnails" in SettingsManager.DEFAULT_SETTINGS
        thumbs = SettingsManager.DEFAULT_SETTINGS["thumbnails"]
        assert "opacity_on_hover" in thumbs
        assert "default_width" in thumbs

    def test_default_settings_has_alerts(self):
        """Test that DEFAULT_SETTINGS has alerts section"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        assert "alerts" in SettingsManager.DEFAULT_SETTINGS
        alerts = SettingsManager.DEFAULT_SETTINGS["alerts"]
        assert "enabled" in alerts
        assert "red_flash" in alerts
        assert "threshold" in alerts["red_flash"]

    def test_default_settings_has_hotkeys(self):
        """Test that DEFAULT_SETTINGS has hotkeys section"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        assert "hotkeys" in SettingsManager.DEFAULT_SETTINGS
        hotkeys = SettingsManager.DEFAULT_SETTINGS["hotkeys"]
        assert "activate_window_1" in hotkeys
        assert "minimize_all" in hotkeys

    def test_default_settings_has_appearance(self):
        """Test that DEFAULT_SETTINGS has appearance section"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        assert "appearance" in SettingsManager.DEFAULT_SETTINGS
        appearance = SettingsManager.DEFAULT_SETTINGS["appearance"]
        assert "theme" in appearance
        assert "font_size" in appearance


class TestLoadSettings:
    """Tests for load_settings functionality"""

    def test_load_settings_creates_defaults_when_no_file(self):
        """Test that load_settings creates defaults when no file exists"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            manager = SettingsManager(config_dir=config_dir)

            # Should have loaded defaults
            assert manager.settings == SettingsManager.DEFAULT_SETTINGS

    def test_load_settings_saves_defaults(self):
        """Test that load_settings saves default settings file"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            manager = SettingsManager(config_dir=config_dir)

            # Settings file should now exist
            assert manager.settings_file.exists()

    def test_load_settings_reads_existing_file(self):
        """Test that load_settings reads existing settings file"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            settings_file = config_dir / "settings.json"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create custom settings file
            custom_settings = {"version": "test", "custom_key": "custom_value"}
            with open(settings_file, 'w') as f:
                json.dump(custom_settings, f)

            manager = SettingsManager(config_dir=config_dir)

            # Should have loaded custom settings (merged with defaults)
            assert manager.settings["version"] == "test"
            assert manager.settings["custom_key"] == "custom_value"

    def test_load_settings_merges_with_defaults(self):
        """Test that load_settings merges loaded settings with defaults"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            settings_file = config_dir / "settings.json"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create partial settings file
            partial_settings = {"version": "partial", "general": {"start_with_system": True}}
            with open(settings_file, 'w') as f:
                json.dump(partial_settings, f)

            manager = SettingsManager(config_dir=config_dir)

            # Should have merged - custom value preserved
            assert manager.settings["general"]["start_with_system"] is True
            # Default values should be present
            assert "minimize_to_tray" in manager.settings["general"]

    def test_load_settings_handles_invalid_json(self):
        """Test that load_settings handles invalid JSON gracefully"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            settings_file = config_dir / "settings.json"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create invalid JSON file
            with open(settings_file, 'w') as f:
                f.write("{ invalid json }")

            manager = SettingsManager(config_dir=config_dir)

            # Should fall back to defaults
            assert manager.settings == SettingsManager.DEFAULT_SETTINGS


class TestSaveSettings:
    """Tests for save_settings functionality"""

    def test_save_settings_writes_file(self):
        """Test that save_settings writes to file"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            manager = SettingsManager(config_dir=config_dir)
            manager.settings["test_key"] = "test_value"

            result = manager.save_settings()

            assert result is True
            # Verify file contents
            with open(manager.settings_file) as f:
                saved = json.load(f)
            assert saved["test_key"] == "test_value"

    def test_save_settings_with_provided_settings(self):
        """Test save_settings with provided settings dict"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            manager = SettingsManager(config_dir=config_dir)

            new_settings = {"new": "settings", "version": "1.0"}
            result = manager.save_settings(new_settings)

            assert result is True
            assert manager.settings == new_settings

    def test_save_settings_atomic_write(self):
        """Test that save uses atomic write (temp file then rename)"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            manager = SettingsManager(config_dir=config_dir)

            # Save should succeed and temp file should not exist
            result = manager.save_settings()

            assert result is True
            temp_file = manager.settings_file.with_suffix('.json.tmp')
            assert not temp_file.exists()

    def test_save_settings_returns_false_on_error(self):
        """Test that save_settings returns False on error"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            manager = SettingsManager(config_dir=config_dir)

            # Make the file read-only by removing parent directory write permission
            with patch('builtins.open', side_effect=PermissionError("denied")):
                result = manager.save_settings()

            assert result is False


class TestGetSetting:
    """Tests for get() method with nested keys"""

    def test_get_simple_key(self):
        """Test getting a simple key"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            value = manager.get("version")

            assert value is not None
            assert isinstance(value, str)

    def test_get_nested_key(self):
        """Test getting a nested key"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            value = manager.get("general.minimize_to_tray")

            assert value is True  # Default value

    def test_get_deeply_nested_key(self):
        """Test getting a deeply nested key"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            value = manager.get("alerts.red_flash.threshold")

            assert value == 0.7  # Default value

    def test_get_nonexistent_key_returns_default(self):
        """Test that get returns default for nonexistent key"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            value = manager.get("nonexistent.key", default="fallback")

            assert value == "fallback"

    def test_get_nonexistent_key_returns_none(self):
        """Test that get returns None for nonexistent key without default"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            value = manager.get("nonexistent.key")

            assert value is None

    def test_get_partial_path(self):
        """Test getting a partial path returns dict"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            value = manager.get("general")

            assert isinstance(value, dict)
            assert "start_with_system" in value


class TestSetSetting:
    """Tests for set() method with nested keys"""

    def test_set_simple_key(self):
        """Test setting a simple key"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            result = manager.set("version", "new_version")

            assert result is True
            assert manager.settings["version"] == "new_version"

    def test_set_nested_key(self):
        """Test setting a nested key"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            result = manager.set("general.start_with_system", True)

            assert result is True
            assert manager.settings["general"]["start_with_system"] is True

    def test_set_deeply_nested_key(self):
        """Test setting a deeply nested key"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            result = manager.set("alerts.red_flash.threshold", 0.9)

            assert result is True
            assert manager.settings["alerts"]["red_flash"]["threshold"] == 0.9

    def test_set_creates_intermediate_keys(self):
        """Test that set creates intermediate keys if needed"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            result = manager.set("new.nested.deep.key", "value")

            assert result is True
            assert manager.settings["new"]["nested"]["deep"]["key"] == "value"

    def test_set_auto_saves_by_default(self):
        """Test that set auto-saves by default"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            manager.set("test_key", "test_value")

            # Reload and verify persisted
            with open(manager.settings_file) as f:
                saved = json.load(f)
            assert saved["test_key"] == "test_value"

    def test_set_without_auto_save(self):
        """Test set with auto_save=False"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            # Get initial file content
            with open(manager.settings_file) as f:
                json.load(f)

            result = manager.set("no_save_key", "value", auto_save=False)

            assert result is True
            assert manager.settings["no_save_key"] == "value"

            # File should not have changed
            with open(manager.settings_file) as f:
                current = json.load(f)
            assert "no_save_key" not in current


class TestResetToDefaults:
    """Tests for reset_to_defaults functionality"""

    def test_reset_to_defaults(self):
        """Test resetting all settings to defaults"""
        import copy

        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            # Store original default version
            original_version = copy.deepcopy(SettingsManager.DEFAULT_SETTINGS["version"])

            # Modify settings with top-level key (avoids shallow copy mutation issue)
            manager.settings["custom_key"] = "custom_value"
            manager.settings["version"] = "modified_version"

            result = manager.reset_to_defaults()

            assert result is True
            assert "custom_key" not in manager.settings
            # Version should be reset to default
            assert manager.settings["version"] == original_version

    def test_reset_saves_defaults(self):
        """Test that reset saves the default settings"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            manager.settings["custom"] = "value"
            manager.save_settings()

            manager.reset_to_defaults()

            # Verify file was updated
            with open(manager.settings_file) as f:
                saved = json.load(f)
            assert "custom" not in saved


class TestExportImport:
    """Tests for export_config and import_config"""

    def test_export_config(self):
        """Test exporting settings to external file"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            export_path = Path(tmpdir) / "export.json"

            manager = SettingsManager(config_dir=config_dir)
            manager.settings["test_export"] = "export_value"

            result = manager.export_config(export_path)

            assert result is True
            assert export_path.exists()

            with open(export_path) as f:
                exported = json.load(f)

            assert "exported_at" in exported
            assert "version" in exported
            assert "settings" in exported
            assert exported["settings"]["test_export"] == "export_value"

    def test_export_config_path_as_string(self):
        """Test export with path as string"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            export_path = str(Path(tmpdir) / "export.json")

            manager = SettingsManager(config_dir=config_dir)

            result = manager.export_config(export_path)

            assert result is True
            assert Path(export_path).exists()

    def test_import_config(self):
        """Test importing settings from external file"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            import_path = Path(tmpdir) / "import.json"

            # Create import file
            import_data = {
                "exported_at": "2025-01-01T00:00:00",
                "version": "2.0",
                "settings": {
                    "version": "imported",
                    "general": {"start_with_system": True},
                    "custom_imported": "value"
                }
            }
            with open(import_path, 'w') as f:
                json.dump(import_data, f)

            manager = SettingsManager(config_dir=config_dir)

            result = manager.import_config(import_path)

            assert result is True
            assert manager.settings["version"] == "imported"
            assert manager.settings["general"]["start_with_system"] is True
            assert manager.settings["custom_imported"] == "value"

    def test_import_config_old_format(self):
        """Test importing old format (settings at root level)"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            import_path = Path(tmpdir) / "old_format.json"

            # Create old format file (no wrapper)
            old_format = {
                "version": "old",
                "general": {"start_with_system": True}
            }
            with open(import_path, 'w') as f:
                json.dump(old_format, f)

            manager = SettingsManager(config_dir=config_dir)

            result = manager.import_config(import_path)

            assert result is True
            assert manager.settings["version"] == "old"

    def test_import_config_invalid_file(self):
        """Test import with invalid file"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            import_path = Path(tmpdir) / "invalid.json"

            with open(import_path, 'w') as f:
                f.write("not valid json")

            manager = SettingsManager(config_dir=config_dir)

            result = manager.import_config(import_path)

            assert result is False

    def test_import_config_nonexistent_file(self):
        """Test import with nonexistent file"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"

            manager = SettingsManager(config_dir=config_dir)

            result = manager.import_config(Path("/nonexistent/file.json"))

            assert result is False


class TestMergeSettings:
    """Tests for _merge_settings helper"""

    def test_merge_preserves_base_structure(self):
        """Test that merge preserves base structure"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            base = {"a": 1, "b": {"c": 2, "d": 3}}
            overlay = {"b": {"c": 99}}

            result = manager._merge_settings(base, overlay)

            assert result["a"] == 1
            assert result["b"]["c"] == 99
            assert result["b"]["d"] == 3

    def test_merge_adds_new_keys(self):
        """Test that merge adds new keys from overlay"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            base = {"a": 1}
            overlay = {"b": 2}

            result = manager._merge_settings(base, overlay)

            assert result["a"] == 1
            assert result["b"] == 2

    def test_merge_deep_nesting(self):
        """Test merge with deep nesting"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            base = {"l1": {"l2": {"l3": {"l4": "base"}}}}
            overlay = {"l1": {"l2": {"l3": {"l4": "overlay"}}}}

            result = manager._merge_settings(base, overlay)

            assert result["l1"]["l2"]["l3"]["l4"] == "overlay"


class TestGetAll:
    """Tests for get_all method"""

    def test_get_all_returns_copy(self):
        """Test that get_all returns a copy of settings"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            all_settings = manager.get_all()

            # Modifying returned dict should not affect internal settings
            all_settings["modified"] = True

            assert "modified" not in manager.settings

    def test_get_all_contains_all_keys(self):
        """Test that get_all returns all settings"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            all_settings = manager.get_all()

            assert "version" in all_settings
            assert "general" in all_settings
            assert "performance" in all_settings
            assert "hotkeys" in all_settings


class TestValidate:
    """Tests for validate method"""

    def test_validate_valid_settings(self):
        """Test validate with valid settings"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            result = manager.validate()

            assert result is True

    def test_validate_fixes_invalid_refresh_rate_low(self):
        """Test validate fixes refresh rate below minimum"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))
            manager.settings["performance"]["default_refresh_rate"] = 0

            result = manager.validate()

            assert result is True
            assert manager.settings["performance"]["default_refresh_rate"] == 30

    def test_validate_fixes_invalid_refresh_rate_high(self):
        """Test validate fixes refresh rate above maximum"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))
            manager.settings["performance"]["default_refresh_rate"] = 100

            result = manager.validate()

            assert result is True
            assert manager.settings["performance"]["default_refresh_rate"] == 30

    def test_validate_fixes_invalid_worker_count(self):
        """Test validate fixes invalid worker count"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))
            manager.settings["performance"]["capture_workers"] = 100

            result = manager.validate()

            assert result is True
            assert manager.settings["performance"]["capture_workers"] == 4

    def test_validate_fixes_invalid_threshold(self):
        """Test validate fixes invalid alert threshold"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))
            manager.settings["alerts"]["red_flash"]["threshold"] = 1.5

            result = manager.validate()

            assert result is True
            assert manager.settings["alerts"]["red_flash"]["threshold"] == 0.7


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_empty_key_string(self):
        """Test handling of empty key string"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            # Empty string key
            value = manager.get("", default="fallback")
            # Should return the whole settings dict since split("") = [""]
            # and settings[""] doesn't exist
            assert value == "fallback"

    def test_key_with_dots_only(self):
        """Test handling of key with only dots"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            value = manager.get("...", default="fallback")

            assert value == "fallback"

    def test_set_none_value(self):
        """Test setting None as value"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            result = manager.set("nullable_key", None)

            assert result is True
            assert manager.settings["nullable_key"] is None

    def test_set_complex_value(self):
        """Test setting complex nested value"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            complex_value = {
                "nested": {"deeply": {"value": [1, 2, 3]}},
                "list": ["a", "b", "c"]
            }

            result = manager.set("complex", complex_value)

            assert result is True
            assert manager.settings["complex"] == complex_value

    def test_unicode_in_settings(self):
        """Test Unicode characters in settings"""
        from eve_overview_pro.ui.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SettingsManager(config_dir=Path(tmpdir))

            unicode_value = "日本語テスト 🚀 émojis"

            result = manager.set("unicode_test", unicode_value)

            assert result is True
            assert manager.get("unicode_test") == unicode_value

            # Verify it persists correctly
            with open(manager.settings_file, encoding='utf-8') as f:
                saved = json.load(f)
            assert saved["unicode_test"] == unicode_value
