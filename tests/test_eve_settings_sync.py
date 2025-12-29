"""
Unit tests for the EVE Settings Sync module
Tests EVECharacterSettings, EVECharacterInfo, EVESettingsSync class
"""
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os


# Test EVECharacterSettings dataclass
class TestEVECharacterSettings:
    """Tests for the EVECharacterSettings dataclass"""

    def test_create_with_required_fields(self):
        """Test creating with required fields only"""
        from eve_overview_pro.core.eve_settings_sync import EVECharacterSettings

        settings = EVECharacterSettings(
            character_name="TestPilot",
            character_id="12345678",
            settings_dir=Path("/tmp/settings"),
            core_char_file=Path("/tmp/settings/core_char_12345678.dat")
        )

        assert settings.character_name == "TestPilot"
        assert settings.character_id == "12345678"
        assert settings.settings_dir == Path("/tmp/settings")
        assert settings.core_char_file == Path("/tmp/settings/core_char_12345678.dat")

    def test_optional_fields_default_values(self):
        """Test that optional fields have correct defaults"""
        from eve_overview_pro.core.eve_settings_sync import EVECharacterSettings

        settings = EVECharacterSettings(
            character_name="TestPilot",
            character_id="12345678",
            settings_dir=Path("/tmp/settings"),
            core_char_file=Path("/tmp/settings/core_char_12345678.dat")
        )

        assert settings.core_user_file is None
        assert settings.user_id is None
        assert settings.has_settings is False
        assert settings.last_login is None

    def test_all_fields(self):
        """Test creating with all fields"""
        from eve_overview_pro.core.eve_settings_sync import EVECharacterSettings

        now = datetime.now()
        settings = EVECharacterSettings(
            character_name="FullPilot",
            character_id="87654321",
            settings_dir=Path("/tmp/full"),
            core_char_file=Path("/tmp/full/core_char_87654321.dat"),
            core_user_file=Path("/tmp/full/core_user_123.dat"),
            user_id="123",
            has_settings=True,
            last_login=now
        )

        assert settings.character_name == "FullPilot"
        assert settings.core_user_file == Path("/tmp/full/core_user_123.dat")
        assert settings.user_id == "123"
        assert settings.has_settings is True
        assert settings.last_login == now


# Test EVECharacterInfo dataclass
class TestEVECharacterInfo:
    """Tests for the EVECharacterInfo dataclass"""

    def test_create_with_required_fields(self):
        """Test creating with required fields only"""
        from eve_overview_pro.core.eve_settings_sync import EVECharacterInfo

        info = EVECharacterInfo(
            character_id="12345678",
            character_name="TestPilot"
        )

        assert info.character_id == "12345678"
        assert info.character_name == "TestPilot"

    def test_optional_fields_default_values(self):
        """Test that optional fields have correct defaults"""
        from eve_overview_pro.core.eve_settings_sync import EVECharacterInfo

        info = EVECharacterInfo(
            character_id="12345678",
            character_name="TestPilot"
        )

        assert info.user_id is None
        assert info.settings_path is None
        assert info.last_seen is None
        assert info.has_settings is False

    def test_all_fields(self):
        """Test creating with all fields"""
        from eve_overview_pro.core.eve_settings_sync import EVECharacterInfo

        now = datetime.now()
        info = EVECharacterInfo(
            character_id="12345678",
            character_name="FullPilot",
            user_id="456",
            settings_path=Path("/tmp/settings"),
            last_seen=now,
            has_settings=True
        )

        assert info.character_id == "12345678"
        assert info.character_name == "FullPilot"
        assert info.user_id == "456"
        assert info.settings_path == Path("/tmp/settings")
        assert info.last_seen == now
        assert info.has_settings is True


# Test EVESettingsSync class
class TestEVESettingsSync:
    """Tests for the EVESettingsSync class"""

    def test_init(self):
        """Test EVESettingsSync initialization"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        assert sync.eve_paths is not None
        assert len(sync.eve_paths) > 0
        assert sync.custom_paths == []
        assert sync.character_settings == {}
        assert isinstance(sync.character_id_to_name, dict)

    def test_eve_paths_include_steam(self):
        """Test that EVE paths include Steam paths"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        # Check for Steam-related path components
        steam_paths = [p for p in sync.eve_paths if '8500' in str(p)]
        assert len(steam_paths) > 0

    def test_eve_logs_paths_exist(self):
        """Test that eve_logs_paths is defined"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        assert hasattr(sync, 'eve_logs_paths')
        assert len(sync.eve_logs_paths) > 0

    def test_add_custom_path_valid(self):
        """Test adding a valid custom path"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            sync.add_custom_path(path)

            assert path in sync.custom_paths

    def test_add_custom_path_invalid(self):
        """Test adding an invalid custom path"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        invalid_path = Path("/nonexistent/path/that/does/not/exist")
        sync.add_custom_path(invalid_path)

        assert invalid_path not in sync.custom_paths

    def test_add_custom_path_file_not_dir(self):
        """Test adding a file path instead of directory"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        with tempfile.NamedTemporaryFile() as tmpfile:
            path = Path(tmpfile.name)
            sync.add_custom_path(path)

            # Should not be added since it's not a directory
            assert path not in sync.custom_paths

    def test_get_character_name_found(self):
        """Test getting character name when ID is known"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()
        sync.character_id_to_name["12345678"] = "KnownPilot"

        name = sync.get_character_name("12345678")

        assert name == "KnownPilot"

    def test_get_character_name_not_found(self):
        """Test getting character name when ID is unknown"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        name = sync.get_character_name("99999999")

        assert name == "Character_99999999"

    def test_list_available_characters_empty(self):
        """Test listing characters when none available"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        characters = sync.list_available_characters()

        assert characters == []

    def test_list_available_characters_with_settings(self):
        """Test listing characters with settings"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync, EVECharacterSettings

        sync = EVESettingsSync()

        # Add some character settings
        sync.character_settings["Pilot1"] = EVECharacterSettings(
            character_name="Pilot1",
            character_id="111",
            settings_dir=Path("/tmp/1"),
            core_char_file=Path("/tmp/1/core_char_111.dat"),
            has_settings=True
        )
        sync.character_settings["Pilot2"] = EVECharacterSettings(
            character_name="Pilot2",
            character_id="222",
            settings_dir=Path("/tmp/2"),
            core_char_file=Path("/tmp/2/core_char_222.dat"),
            has_settings=False  # No settings
        )
        sync.character_settings["Pilot3"] = EVECharacterSettings(
            character_name="Pilot3",
            character_id="333",
            settings_dir=Path("/tmp/3"),
            core_char_file=Path("/tmp/3/core_char_333.dat"),
            has_settings=True
        )

        characters = sync.list_available_characters()

        assert "Pilot1" in characters
        assert "Pilot2" not in characters  # has_settings=False
        assert "Pilot3" in characters

    def test_get_settings_summary_not_found(self):
        """Test getting summary for unknown character"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        summary = sync.get_settings_summary("UnknownPilot")

        assert summary is None

    def test_get_settings_summary_found(self):
        """Test getting summary for known character"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync, EVECharacterSettings

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_dir = Path(tmpdir)
            # Create some settings files
            (settings_dir / "core_char_123.dat").touch()
            (settings_dir / "prefs.ini").touch()
            (settings_dir / "overview.yaml").touch()

            sync.character_settings["TestPilot"] = EVECharacterSettings(
                character_name="TestPilot",
                character_id="123",
                settings_dir=settings_dir,
                core_char_file=settings_dir / "core_char_123.dat",
                has_settings=True
            )

            summary = sync.get_settings_summary("TestPilot")

            assert summary is not None
            assert summary["character"] == "TestPilot"
            assert summary["has_settings"] is True
            assert summary["total_files"] == 3  # .dat, .ini, .yaml
            assert "settings_dir" in summary

    def test_sync_settings_source_not_found(self):
        """Test sync when source character not found"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        results = sync.sync_settings("NonexistentSource", ["Target1"])

        assert results == {}

    def test_sync_settings_target_not_found(self):
        """Test sync when target character not found"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync, EVECharacterSettings

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_dir = Path(tmpdir)

            sync.character_settings["Source"] = EVECharacterSettings(
                character_name="Source",
                character_id="123",
                settings_dir=settings_dir,
                core_char_file=settings_dir / "core_char_123.dat",
                has_settings=True
            )

            results = sync.sync_settings("Source", ["NonexistentTarget"])

            assert "NonexistentTarget" in results
            assert results["NonexistentTarget"] is False

    def test_sync_settings_source_no_settings(self):
        """Test sync when source has no settings"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync, EVECharacterSettings

        sync = EVESettingsSync()

        sync.character_settings["Source"] = EVECharacterSettings(
            character_name="Source",
            character_id="123",
            settings_dir=Path("/tmp"),
            core_char_file=Path("/tmp/core_char_123.dat"),
            has_settings=False
        )

        results = sync.sync_settings("Source", ["Target1"])

        assert results == {}


# Test file parsing
class TestFileParsing:
    """Tests for file parsing functionality"""

    def test_parse_char_file_valid(self):
        """Test parsing a valid core_char file"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()
        sync.character_id_to_name["12345678"] = "KnownPilot"

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_dir = Path(tmpdir)
            char_file = settings_dir / "core_char_12345678.dat"
            char_file.touch()

            result = sync._parse_char_file(char_file, settings_dir)

            assert result is not None
            assert result.character_id == "12345678"
            assert result.character_name == "KnownPilot"
            assert result.has_settings is True

    def test_parse_char_file_invalid_name(self):
        """Test parsing file with invalid name format"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_dir = Path(tmpdir)
            char_file = settings_dir / "invalid_file.dat"
            char_file.touch()

            result = sync._parse_char_file(char_file, settings_dir)

            assert result is None

    def test_parse_char_file_with_user_file(self):
        """Test parsing when user file exists"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_dir = Path(tmpdir)
            char_file = settings_dir / "core_char_12345678.dat"
            user_file = settings_dir / "core_user_999.dat"
            char_file.touch()
            user_file.touch()

            result = sync._parse_char_file(char_file, settings_dir)

            assert result is not None
            assert result.core_user_file == user_file


# Test directory scanning
class TestDirectoryScanning:
    """Tests for directory scanning functionality"""

    def test_scan_for_characters_no_paths_exist(self):
        """Test scan when no EVE paths exist"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()
        # Override with non-existent paths
        sync.eve_paths = [Path("/nonexistent/path1"), Path("/nonexistent/path2")]
        sync.custom_paths = []

        characters = sync.scan_for_characters()

        assert characters == []

    def test_scan_for_characters_valid_structure(self):
        """Test scan with valid EVE directory structure"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create EVE-like directory structure
            base = Path(tmpdir)
            server_dir = base / "tranquility_server"
            settings_dir = server_dir / "settings_Default"
            settings_dir.mkdir(parents=True)

            # Create character files
            (settings_dir / "core_char_11111111.dat").touch()
            (settings_dir / "core_char_22222222.dat").touch()

            # Override paths to use temp dir
            sync.eve_paths = [base]
            sync.custom_paths = []

            characters = sync.scan_for_characters()

            assert len(characters) == 2
            char_ids = {c.character_id for c in characters}
            assert "11111111" in char_ids
            assert "22222222" in char_ids

    def test_get_all_known_characters_empty(self):
        """Test getting all known characters when none exist"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()
        sync.eve_paths = [Path("/nonexistent")]
        sync.custom_paths = []

        characters = sync.get_all_known_characters()

        assert characters == []

    def test_get_all_known_characters_with_names(self):
        """Test getting characters with known names from logs"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()
        sync.character_id_to_name["11111111"] = "PilotOne"
        sync.character_id_to_name["22222222"] = "PilotTwo"

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            server_dir = base / "tranquility"
            settings_dir = server_dir / "settings_Default"
            settings_dir.mkdir(parents=True)

            (settings_dir / "core_char_11111111.dat").touch()
            (settings_dir / "core_char_22222222.dat").touch()

            sync.eve_paths = [base]
            sync.custom_paths = []

            characters = sync.get_all_known_characters()

            assert len(characters) == 2
            names = {c.character_name for c in characters}
            assert "PilotOne" in names
            assert "PilotTwo" in names


# Test log parsing
class TestLogParsing:
    """Tests for game log parsing"""

    def test_load_character_names_from_logs_no_logs(self):
        """Test loading names when no logs exist"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()
        sync.eve_logs_paths = [Path("/nonexistent/logs")]

        # Should not raise, just have empty mappings
        sync._load_character_names_from_logs()

        # May or may not have entries depending on real system

    def test_load_character_names_from_logs_valid(self):
        """Test loading names from valid log files"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir)

            # Create a log file with character info
            log_file = logs_dir / "20251208_053612_94468033.txt"
            log_file.write_text(
                "------------------------------------------------------------\n"
                "  Channel ID:    xxx\n"
                "  Listener:      TestPilotName\n"
                "  Session started: 2025.12.08\n"
                "------------------------------------------------------------\n"
            )

            sync = EVESettingsSync()
            sync.eve_logs_paths = [logs_dir]
            sync.character_id_to_name.clear()

            sync._load_character_names_from_logs()

            assert "94468033" in sync.character_id_to_name
            assert sync.character_id_to_name["94468033"] == "TestPilotName"

    def test_load_character_names_handles_encoding_errors(self):
        """Test that log parsing handles encoding errors gracefully"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir)

            # Create a log file with binary garbage
            log_file = logs_dir / "20251208_053612_12345678.txt"
            log_file.write_bytes(b"\xff\xfe\x00\x01Invalid\xffBytes")

            sync = EVESettingsSync()
            sync.eve_logs_paths = [logs_dir]

            # Should not raise
            sync._load_character_names_from_logs()


# Test settings backup and copy
class TestSettingsBackupCopy:
    """Tests for settings backup and copy functionality"""

    def test_backup_settings(self):
        """Test creating settings backup"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync, EVECharacterSettings

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            settings_dir = base / "settings_Default"
            settings_dir.mkdir()

            # Create some files
            (settings_dir / "core_char_123.dat").write_text("data")
            (settings_dir / "prefs.ini").write_text("prefs")

            char_settings = EVECharacterSettings(
                character_name="BackupTest",
                character_id="123",
                settings_dir=settings_dir,
                core_char_file=settings_dir / "core_char_123.dat",
                has_settings=True
            )

            sync._backup_settings(char_settings)

            # Check backup was created
            backups = list(base.glob("backup_BackupTest_*"))
            assert len(backups) == 1
            backup_dir = backups[0]
            assert (backup_dir / "core_char_123.dat").exists()
            assert (backup_dir / "prefs.ini").exists()

    def test_copy_settings(self):
        """Test copying settings between characters"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync, EVECharacterSettings

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Source settings
            source_dir = base / "source"
            source_dir.mkdir()
            (source_dir / "core_char_111.dat").write_text("source data")
            (source_dir / "prefs.ini").write_text("source prefs")
            (source_dir / "overview.yaml").write_text("overview: data")

            # Target settings
            target_dir = base / "target"
            target_dir.mkdir()

            source = EVECharacterSettings(
                character_name="SourcePilot",
                character_id="111",
                settings_dir=source_dir,
                core_char_file=source_dir / "core_char_111.dat",
                has_settings=True
            )

            target = EVECharacterSettings(
                character_name="TargetPilot",
                character_id="222",
                settings_dir=target_dir,
                core_char_file=target_dir / "core_char_222.dat",
                has_settings=True
            )

            result = sync._copy_settings(source, target)

            assert result is True
            # Check files were copied
            assert (target_dir / "core_char_111.dat").exists()
            assert (target_dir / "prefs.ini").exists()

    def test_copy_settings_empty_source(self):
        """Test copying from empty source directory"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync, EVECharacterSettings

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            source_dir = base / "empty_source"
            source_dir.mkdir()

            target_dir = base / "target"
            target_dir.mkdir()

            source = EVECharacterSettings(
                character_name="EmptySource",
                character_id="111",
                settings_dir=source_dir,
                core_char_file=source_dir / "core_char_111.dat",
                has_settings=True
            )

            target = EVECharacterSettings(
                character_name="Target",
                character_id="222",
                settings_dir=target_dir,
                core_char_file=target_dir / "core_char_222.dat",
                has_settings=True
            )

            result = sync._copy_settings(source, target)

            # Should return False since no files were copied
            assert result is False


# Test sync integration
class TestSyncIntegration:
    """Integration tests for full sync workflow"""

    def test_full_sync_workflow(self):
        """Test complete sync from source to target"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync, EVECharacterSettings

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Source settings
            source_dir = base / "source"
            source_dir.mkdir()
            (source_dir / "core_char_111.dat").write_text("source")
            (source_dir / "prefs.ini").write_text("prefs")

            # Target settings
            target_dir = base / "target"
            target_dir.mkdir()
            (target_dir / "core_char_222.dat").write_text("old target")

            sync.character_settings["SourcePilot"] = EVECharacterSettings(
                character_name="SourcePilot",
                character_id="111",
                settings_dir=source_dir,
                core_char_file=source_dir / "core_char_111.dat",
                has_settings=True
            )

            sync.character_settings["TargetPilot"] = EVECharacterSettings(
                character_name="TargetPilot",
                character_id="222",
                settings_dir=target_dir,
                core_char_file=target_dir / "core_char_222.dat",
                has_settings=True
            )

            results = sync.sync_settings("SourcePilot", ["TargetPilot"], backup=True)

            assert results["TargetPilot"] is True
            # Backup should exist
            backups = list(base.glob("backup_TargetPilot_*"))
            assert len(backups) == 1

    def test_sync_multiple_targets(self):
        """Test syncing to multiple targets"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync, EVECharacterSettings

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Source
            source_dir = base / "source"
            source_dir.mkdir()
            (source_dir / "core_char_111.dat").write_text("source")

            # Targets
            for i, name in enumerate(["Target1", "Target2", "Target3"], start=2):
                target_dir = base / f"target{i}"
                target_dir.mkdir()
                sync.character_settings[name] = EVECharacterSettings(
                    character_name=name,
                    character_id=str(i) * 3,
                    settings_dir=target_dir,
                    core_char_file=target_dir / f"core_char_{i}{i}{i}.dat",
                    has_settings=True
                )

            sync.character_settings["Source"] = EVECharacterSettings(
                character_name="Source",
                character_id="111",
                settings_dir=source_dir,
                core_char_file=source_dir / "core_char_111.dat",
                has_settings=True
            )

            results = sync.sync_settings("Source", ["Target1", "Target2", "Target3"], backup=False)

            assert results["Target1"] is True
            assert results["Target2"] is True
            assert results["Target3"] is True


# Test edge cases
class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_character_id_regex_matching(self):
        """Test character ID extraction from various filenames"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync
        import re

        sync = EVESettingsSync()

        test_cases = [
            ("core_char_12345678.dat", "12345678"),
            ("core_char_1.dat", "1"),
            ("core_char_99999999999.dat", "99999999999"),
        ]

        for filename, expected_id in test_cases:
            match = re.search(r'core_char_(\d+)\.dat$', filename)
            assert match is not None, f"Failed to match: {filename}"
            assert match.group(1) == expected_id

    def test_invalid_filenames_not_matched(self):
        """Test that invalid filenames are not matched"""
        import re

        invalid_names = [
            "core_char_.dat",
            "core_char_abc.dat",
            "core_char_123.txt",
            "char_12345678.dat",
            "core_user_12345678.dat",
        ]

        for filename in invalid_names:
            match = re.search(r'core_char_(\d+)\.dat$', filename)
            # Some may match (like core_char_123.txt won't), verify carefully
            if "core_char_" in filename and filename.endswith(".dat"):
                # Check if digits are present
                if not any(c.isdigit() for c in filename):
                    assert match is None

    def test_settings_dir_with_special_characters(self):
        """Test handling of paths with special characters"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create path with spaces and special chars
            # Structure: base_path/server_dir/settings_dir/core_char_*.dat
            base = Path(tmpdir) / "EVE Settings (1)"
            server_dir = base / "tranquility_server"
            settings_dir = server_dir / "settings_Default"
            settings_dir.mkdir(parents=True)

            (settings_dir / "core_char_12345678.dat").touch()

            sync.eve_paths = [base]

            characters = sync.scan_for_characters()

            assert len(characters) == 1
            assert characters[0].character_id == "12345678"

    def test_concurrent_character_discovery(self):
        """Test discovering characters from multiple server directories"""
        from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

        sync = EVESettingsSync()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create multiple server directories with numeric character IDs
            servers_with_ids = [
                ("tranquility", "11111111"),
                ("singularity", "22222222"),
                ("thunderdome", "33333333"),
            ]
            for server, char_id in servers_with_ids:
                server_dir = base / server
                settings_dir = server_dir / "settings_Default"
                settings_dir.mkdir(parents=True)
                (settings_dir / f"core_char_{char_id}.dat").touch()

            sync.eve_paths = [base]
            characters = sync.scan_for_characters()

            # Should find characters from all servers
            assert len(characters) == 3
            char_ids = {c.character_id for c in characters}
            assert "11111111" in char_ids
            assert "22222222" in char_ids
            assert "33333333" in char_ids
