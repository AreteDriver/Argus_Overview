"""
Unit tests for the LayoutManager module.

Tests cover:
- GridPattern enum
- WindowLayout dataclass
- LayoutPreset serialization
- LayoutManager CRUD operations
- Grid layout calculations
- Auto-arrange functionality
"""
import json
import tempfile
from pathlib import Path

import pytest

from eve_overview_pro.core.layout_manager import (
    GridPattern,
    LayoutManager,
    LayoutPreset,
    WindowLayout,
)


class TestGridPattern:
    """Tests for GridPattern enum"""

    def test_all_patterns_exist(self):
        """All expected patterns exist"""
        assert GridPattern.GRID_2X2.value == "2x2"
        assert GridPattern.GRID_3X1.value == "3x1"
        assert GridPattern.GRID_1X3.value == "1x3"
        assert GridPattern.GRID_4X1.value == "4x1"
        assert GridPattern.MAIN_PLUS_SIDES.value == "main+sides"
        assert GridPattern.CASCADE.value == "cascade"
        assert GridPattern.CUSTOM.value == "custom"

    def test_pattern_count(self):
        """Correct number of patterns"""
        assert len(GridPattern) == 8  # Including 1x4


class TestWindowLayout:
    """Tests for WindowLayout dataclass"""

    def test_create_minimal_layout(self):
        """WindowLayout can be created with minimal args"""
        layout = WindowLayout(
            window_id="0x123",
            x=100,
            y=200,
            width=400,
            height=300
        )
        assert layout.window_id == "0x123"
        assert layout.x == 100
        assert layout.y == 200
        assert layout.width == 400
        assert layout.height == 300
        assert layout.monitor == 0
        assert layout.opacity == 1.0
        assert layout.zoom == 0.3
        assert layout.always_on_top is True

    def test_create_full_layout(self):
        """WindowLayout can be created with all args"""
        layout = WindowLayout(
            window_id="0x456",
            x=50,
            y=50,
            width=800,
            height=600,
            monitor=1,
            opacity=0.8,
            zoom=0.5,
            always_on_top=False
        )
        assert layout.monitor == 1
        assert layout.opacity == 0.8
        assert layout.zoom == 0.5
        assert layout.always_on_top is False


class TestLayoutPreset:
    """Tests for LayoutPreset dataclass"""

    def test_create_minimal_preset(self):
        """LayoutPreset can be created with just name"""
        preset = LayoutPreset(name="Test")
        assert preset.name == "Test"
        assert preset.description == ""
        assert preset.windows == []
        assert preset.refresh_rate == 30
        assert preset.grid_pattern == "custom"

    def test_create_full_preset(self):
        """LayoutPreset can be created with all fields"""
        window = WindowLayout("0x1", 0, 0, 400, 300)
        preset = LayoutPreset(
            name="Full",
            description="Full preset",
            windows=[window],
            refresh_rate=60,
            grid_pattern="2x2"
        )
        assert preset.name == "Full"
        assert len(preset.windows) == 1
        assert preset.refresh_rate == 60

    def test_to_dict(self):
        """LayoutPreset can be serialized to dict"""
        window = WindowLayout("0x1", 10, 20, 400, 300)
        preset = LayoutPreset(name="Serialize", windows=[window])
        data = preset.to_dict()

        assert isinstance(data, dict)
        assert data["name"] == "Serialize"
        assert len(data["windows"]) == 1
        assert data["windows"][0]["x"] == 10

    def test_from_dict(self):
        """LayoutPreset can be deserialized from dict"""
        data = {
            "name": "Loaded",
            "description": "From dict",
            "windows": [
                {"window_id": "0x1", "x": 0, "y": 0, "width": 400,
                 "height": 300, "monitor": 0, "opacity": 1.0,
                 "zoom": 0.3, "always_on_top": True}
            ],
            "refresh_rate": 30,
            "grid_pattern": "custom",
            "created_at": "2025-01-01",
            "modified_at": "2025-01-01"
        }
        preset = LayoutPreset.from_dict(data)
        assert preset.name == "Loaded"
        assert len(preset.windows) == 1
        assert preset.windows[0].window_id == "0x1"

    def test_roundtrip_serialization(self):
        """LayoutPreset survives to_dict -> from_dict roundtrip"""
        window = WindowLayout("0xABC", 100, 200, 500, 400, monitor=1)
        original = LayoutPreset(
            name="RoundTrip",
            description="Test",
            windows=[window],
            refresh_rate=45
        )
        data = original.to_dict()
        restored = LayoutPreset.from_dict(data)

        assert restored.name == original.name
        assert restored.refresh_rate == original.refresh_rate
        assert len(restored.windows) == 1
        assert restored.windows[0].x == 100


class TestLayoutManagerInit:
    """Tests for LayoutManager initialization"""

    def test_creates_directories(self):
        """Manager creates config and layouts directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "new_config"
            LayoutManager(config_dir=config_dir)
            assert config_dir.exists()
            assert (config_dir / "layouts").exists()

    def test_loads_empty_state(self):
        """Manager starts with empty presets"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LayoutManager(config_dir=Path(tmpdir))
            assert len(manager.presets) == 0

    def test_loads_existing_presets(self):
        """Manager loads existing preset files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)

            # Create a preset file
            preset_data = {
                "name": "Existing",
                "description": "",
                "windows": [],
                "refresh_rate": 30,
                "grid_pattern": "custom",
                "created_at": "2025-01-01",
                "modified_at": "2025-01-01"
            }
            (layouts_dir / "Existing.json").write_text(json.dumps(preset_data))

            manager = LayoutManager(config_dir=config_dir)
            assert len(manager.presets) == 1
            assert "Existing" in manager.presets


class TestLayoutManagerCRUD:
    """Tests for LayoutManager CRUD operations"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield LayoutManager(config_dir=Path(tmpdir))

    def test_save_preset(self, manager):
        """Can save a preset"""
        preset = LayoutPreset(name="NewPreset")
        result = manager.save_preset(preset)
        assert result is True
        assert "NewPreset" in manager.presets

        # Check file was created
        preset_file = manager.layouts_dir / "NewPreset.json"
        assert preset_file.exists()

    def test_save_preset_with_windows(self, manager):
        """Can save preset with windows"""
        window = WindowLayout("0x1", 100, 200, 400, 300)
        preset = LayoutPreset(name="WithWindows", windows=[window])
        result = manager.save_preset(preset)
        assert result is True

        # Reload and verify
        loaded = manager.get_preset("WithWindows")
        assert len(loaded.windows) == 1
        assert loaded.windows[0].x == 100

    def test_delete_preset(self, manager):
        """Can delete a preset"""
        preset = LayoutPreset(name="ToDelete")
        manager.save_preset(preset)

        result = manager.delete_preset("ToDelete")
        assert result is True
        assert "ToDelete" not in manager.presets
        assert not (manager.layouts_dir / "ToDelete.json").exists()

    def test_delete_nonexistent_preset(self, manager):
        """Deleting nonexistent preset returns False"""
        result = manager.delete_preset("DoesNotExist")
        assert result is False

    def test_get_preset(self, manager):
        """Can get preset by name"""
        preset = LayoutPreset(name="GetMe")
        manager.save_preset(preset)

        loaded = manager.get_preset("GetMe")
        assert loaded is not None
        assert loaded.name == "GetMe"

    def test_get_nonexistent_preset(self, manager):
        """Getting nonexistent preset returns None"""
        result = manager.get_preset("DoesNotExist")
        assert result is None

    def test_get_all_presets(self, manager):
        """Can get all presets"""
        manager.save_preset(LayoutPreset(name="A"))
        manager.save_preset(LayoutPreset(name="B"))
        manager.save_preset(LayoutPreset(name="C"))

        all_presets = manager.get_all_presets()
        assert len(all_presets) == 3

    def test_create_preset_from_current(self, manager):
        """Can create preset from current window positions"""
        current_windows = {
            "0x111": {"x": 0, "y": 0, "width": 400, "height": 300},
            "0x222": {"x": 410, "y": 0, "width": 400, "height": 300},
        }
        preset = manager.create_preset_from_current(
            name="FromCurrent",
            description="Created from current",
            current_windows=current_windows
        )
        assert preset.name == "FromCurrent"
        assert len(preset.windows) == 2


class TestGridLayoutCalculations:
    """Tests for grid layout calculations"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield LayoutManager(config_dir=Path(tmpdir))

    @pytest.fixture
    def screen(self):
        """Standard screen geometry"""
        return {"x": 0, "y": 0, "width": 1920, "height": 1080}

    def test_empty_windows(self, manager, screen):
        """Empty window list returns empty dict"""
        result = manager.calculate_grid_layout(
            GridPattern.GRID_2X2, [], screen
        )
        assert result == {}

    def test_grid_2x2(self, manager, screen):
        """2x2 grid calculates correct positions"""
        windows = ["w1", "w2", "w3", "w4"]
        result = manager.calculate_grid_layout(
            GridPattern.GRID_2X2, windows, screen, spacing=10
        )

        assert len(result) == 4
        # All windows should have positions
        for w in windows:
            assert w in result
            assert "x" in result[w]
            assert "y" in result[w]
            assert "width" in result[w]
            assert "height" in result[w]

        # Check first window is top-left
        assert result["w1"]["x"] == 10
        assert result["w1"]["y"] == 10

    def test_grid_2x2_limits_to_4(self, manager, screen):
        """2x2 grid only arranges first 4 windows"""
        windows = ["w1", "w2", "w3", "w4", "w5", "w6"]
        result = manager.calculate_grid_layout(
            GridPattern.GRID_2X2, windows, screen
        )
        assert len(result) == 4

    def test_grid_3x1(self, manager, screen):
        """3x1 grid calculates correct positions"""
        windows = ["w1", "w2", "w3"]
        result = manager.calculate_grid_layout(
            GridPattern.GRID_3X1, windows, screen, spacing=10
        )

        assert len(result) == 3
        # All on same row (same y)
        assert result["w1"]["y"] == result["w2"]["y"] == result["w3"]["y"]
        # Horizontally distributed
        assert result["w1"]["x"] < result["w2"]["x"] < result["w3"]["x"]

    def test_grid_1x3(self, manager, screen):
        """1x3 grid calculates correct positions"""
        windows = ["w1", "w2", "w3"]
        result = manager.calculate_grid_layout(
            GridPattern.GRID_1X3, windows, screen, spacing=10
        )

        assert len(result) == 3
        # All on same column (same x)
        assert result["w1"]["x"] == result["w2"]["x"] == result["w3"]["x"]
        # Vertically distributed
        assert result["w1"]["y"] < result["w2"]["y"] < result["w3"]["y"]

    def test_grid_4x1(self, manager, screen):
        """4x1 grid calculates correct positions"""
        windows = ["w1", "w2", "w3", "w4"]
        result = manager.calculate_grid_layout(
            GridPattern.GRID_4X1, windows, screen, spacing=10
        )

        assert len(result) == 4
        # All on same row
        y_values = [result[w]["y"] for w in windows]
        assert len(set(y_values)) == 1

    def test_main_plus_sides(self, manager, screen):
        """Main+sides pattern calculates correct positions"""
        windows = ["main", "side1", "side2", "side3"]
        result = manager.calculate_grid_layout(
            GridPattern.MAIN_PLUS_SIDES, windows, screen, spacing=10
        )

        assert len(result) == 4
        # Main window should be larger
        assert result["main"]["width"] > result["side1"]["width"]

    def test_cascade(self, manager, screen):
        """Cascade pattern calculates offset positions"""
        windows = ["w1", "w2", "w3"]
        result = manager.calculate_grid_layout(
            GridPattern.CASCADE, windows, screen, spacing=10
        )

        assert len(result) == 3
        # Each window offset from previous
        assert result["w1"]["x"] < result["w2"]["x"] < result["w3"]["x"]
        assert result["w1"]["y"] < result["w2"]["y"] < result["w3"]["y"]
        # All same size
        assert result["w1"]["width"] == result["w2"]["width"] == result["w3"]["width"]

    def test_respects_screen_offset(self, manager):
        """Layout respects screen x/y offset"""
        screen = {"x": 1920, "y": 0, "width": 1920, "height": 1080}
        windows = ["w1"]
        result = manager.calculate_grid_layout(
            GridPattern.CASCADE, windows, screen, spacing=10
        )

        # Window should be on second monitor (x >= 1920)
        assert result["w1"]["x"] >= 1920


class TestAutoArrange:
    """Tests for auto_arrange method"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield LayoutManager(config_dir=Path(tmpdir))

    def test_auto_arrange_delegates_to_calculate(self, manager):
        """auto_arrange delegates to calculate_grid_layout"""
        windows = ["w1", "w2"]
        screen = {"x": 0, "y": 0, "width": 1920, "height": 1080}

        result = manager.auto_arrange(
            windows, GridPattern.GRID_2X2, screen, spacing=20
        )

        assert len(result) == 2


class TestGetBestPattern:
    """Tests for get_best_pattern method"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield LayoutManager(config_dir=Path(tmpdir))

    def test_best_pattern_for_1_window(self, manager):
        """1-2 windows get 1x3 pattern"""
        assert manager.get_best_pattern(1) == GridPattern.GRID_1X3
        assert manager.get_best_pattern(2) == GridPattern.GRID_1X3

    def test_best_pattern_for_3_4_windows(self, manager):
        """3-4 windows get 2x2 pattern"""
        assert manager.get_best_pattern(3) == GridPattern.GRID_2X2
        assert manager.get_best_pattern(4) == GridPattern.GRID_2X2

    def test_best_pattern_for_5_6_windows(self, manager):
        """5-6 windows get 3x1 pattern"""
        assert manager.get_best_pattern(5) == GridPattern.GRID_3X1
        assert manager.get_best_pattern(6) == GridPattern.GRID_3X1

    def test_best_pattern_for_many_windows(self, manager):
        """7+ windows get main+sides pattern"""
        assert manager.get_best_pattern(7) == GridPattern.MAIN_PLUS_SIDES
        assert manager.get_best_pattern(10) == GridPattern.MAIN_PLUS_SIDES


class TestExceptionHandling:
    """Tests for exception handling in file operations"""

    def test_load_presets_handles_corrupted_file(self):
        """Manager handles corrupted preset files gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            layouts_dir = config_dir / "layouts"
            layouts_dir.mkdir(parents=True)

            # Create a corrupted preset file (invalid JSON)
            (layouts_dir / "corrupted.json").write_text("not valid json {{{")

            # Should not raise, just log error and skip
            manager = LayoutManager(config_dir=config_dir)
            assert "corrupted" not in manager.presets

    def test_save_preset_handles_write_error(self):
        """save_preset handles write errors gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LayoutManager(config_dir=Path(tmpdir))
            preset = LayoutPreset(name="Test")

            # Make layouts_dir read-only to cause write error
            manager.layouts_dir.chmod(0o444)

            try:
                result = manager.save_preset(preset)
                assert result is False
            finally:
                # Restore permissions for cleanup
                manager.layouts_dir.chmod(0o755)

    def test_delete_preset_handles_unlink_error(self):
        """delete_preset handles file deletion errors gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from unittest.mock import patch, MagicMock

            manager = LayoutManager(config_dir=Path(tmpdir))
            preset = LayoutPreset(name="ToDelete")
            manager.save_preset(preset)

            # Mock unlink to raise an exception
            with patch.object(Path, 'unlink', side_effect=OSError("Permission denied")):
                result = manager.delete_preset("ToDelete")
                assert result is False


class TestDefaultConfigDir:
    """Tests for default config directory behavior"""

    def test_uses_home_config_when_none_provided(self):
        """Manager uses ~/.config/eve-overview-pro when no config_dir provided"""
        from unittest.mock import patch

        # Mock Path.home() to use temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir)

            with patch.object(Path, 'home', return_value=mock_home):
                manager = LayoutManager(config_dir=None)

                expected_dir = mock_home / '.config' / 'eve-overview-pro'
                assert manager.config_dir == expected_dir
                assert expected_dir.exists()


class TestDataPersistence:
    """Tests for data persistence"""

    def test_preset_persists_across_instances(self):
        """Presets persist across manager instances"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create and save preset
            m1 = LayoutManager(config_dir=config_dir)
            window = WindowLayout("0x123", 100, 200, 400, 300)
            preset = LayoutPreset(
                name="Persistent",
                description="Should persist",
                windows=[window]
            )
            m1.save_preset(preset)

            # New manager should load it
            m2 = LayoutManager(config_dir=config_dir)
            assert "Persistent" in m2.presets
            loaded = m2.get_preset("Persistent")
            assert loaded.description == "Should persist"
            assert len(loaded.windows) == 1
            assert loaded.windows[0].x == 100
