"""
Layout Manager - Presets and Auto-Grid System
Handles saving/loading window layouts and auto-tiling patterns
"""

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


def sanitize_filename(name: str) -> str:
    """Sanitize a name for safe use as a filename.

    Removes path separators, null bytes, and other dangerous characters.
    Returns a safe filename or raises ValueError if result is empty.
    """
    # Remove path separators and null bytes
    sanitized = re.sub(r"[/\\:\x00]", "", name)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")
    # Limit length
    sanitized = sanitized[:100]

    if not sanitized:
        raise ValueError(f"Invalid name: '{name}' produces empty filename")

    return sanitized


class GridPattern(Enum):
    """Available grid patterns"""

    GRID_2X2 = "2x2"
    GRID_3X1 = "3x1"
    GRID_1X3 = "1x3"
    GRID_4X1 = "4x1"
    GRID_1X4 = "1x4"
    MAIN_PLUS_SIDES = "main+sides"
    CASCADE = "cascade"
    CUSTOM = "custom"


@dataclass
class WindowLayout:
    """Layout for a single window"""

    window_id: str
    x: int
    y: int
    width: int
    height: int
    monitor: int = 0
    opacity: float = 1.0
    zoom: float = 0.3
    always_on_top: bool = True


@dataclass
class LayoutPreset:
    """Complete layout preset"""

    name: str
    description: str = ""
    windows: List[WindowLayout] = field(default_factory=list)
    refresh_rate: int = 30
    grid_pattern: str = "custom"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["windows"] = [asdict(w) for w in self.windows]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "LayoutPreset":
        """Create from dictionary"""
        windows_data = data.pop("windows", [])
        preset = cls(**data)
        preset.windows = [WindowLayout(**w) for w in windows_data]
        return preset


class LayoutManager:
    """Manages layout presets and grid patterns"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)

        if config_dir is None:
            config_dir = Path.home() / ".config" / "argus-overview"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.layouts_dir = self.config_dir / "layouts"
        self.layouts_dir.mkdir(exist_ok=True)

        self.presets: Dict[str, LayoutPreset] = {}
        self._load_presets()

    @staticmethod
    def _validate_preset_data(data) -> bool:
        """Validate preset dict has required fields with correct types."""
        if not isinstance(data, dict):
            return False
        if "name" not in data or not isinstance(data["name"], str) or not data["name"]:
            return False
        type_checks = {
            "description": str,
            "grid_pattern": str,
            "refresh_rate": int,
        }
        for key, expected_type in type_checks.items():
            if key in data and data[key] is not None:
                if not isinstance(data[key], expected_type):
                    return False
        if "windows" in data and not isinstance(data.get("windows"), list):
            return False
        # Validate each window entry
        for win in data.get("windows", []):
            if not isinstance(win, dict):
                return False
            for req_field in ("window_id", "x", "y", "width", "height"):
                if req_field not in win:
                    return False
        return True

    def _load_presets(self):
        """Load all layout presets"""
        for preset_file in self.layouts_dir.glob("*.json"):
            try:
                with open(preset_file) as f:
                    data = json.load(f)
                    if not self._validate_preset_data(data):
                        self.logger.warning(
                            f"Skipping invalid preset file '{preset_file.name}': "
                            "missing or malformed fields"
                        )
                        continue
                    preset = LayoutPreset.from_dict(data)
                    self.presets[preset.name] = preset
            except Exception as e:
                self.logger.error(f"Failed to load preset {preset_file}: {e}")

        self.logger.info(f"Loaded {len(self.presets)} layout presets")

    def save_preset(self, preset: LayoutPreset) -> bool:
        """Save a layout preset"""
        try:
            safe_name = sanitize_filename(preset.name)
            preset.modified_at = datetime.now().isoformat()
            preset_file = self.layouts_dir / f"{safe_name}.json"

            # Verify path is within layouts_dir (defense in depth)
            if not preset_file.resolve().is_relative_to(self.layouts_dir.resolve()):
                self.logger.error(f"Path traversal attempt blocked: {preset.name}")
                return False

            with open(preset_file, "w") as f:
                json.dump(preset.to_dict(), f, indent=2)

            self.presets[preset.name] = preset
            self.logger.info(f"Saved layout preset '{preset.name}'")
            return True
        except ValueError as e:
            self.logger.error(f"Invalid preset name '{preset.name}': {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to save preset '{preset.name}': {e}")
            return False

    def delete_preset(self, preset_name: str) -> bool:
        """Delete a layout preset"""
        if preset_name not in self.presets:
            return False

        try:
            safe_name = sanitize_filename(preset_name)
            preset_file = self.layouts_dir / f"{safe_name}.json"

            # Verify path is within layouts_dir
            if not preset_file.resolve().is_relative_to(self.layouts_dir.resolve()):
                self.logger.error(f"Path traversal attempt blocked: {preset_name}")
                return False

            if preset_file.exists():
                preset_file.unlink()
            del self.presets[preset_name]
            self.logger.info(f"Deleted preset '{preset_name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete preset '{preset_name}': {e}")
            return False

    def get_preset(self, preset_name: str) -> Optional[LayoutPreset]:
        """Get a layout preset by name"""
        return self.presets.get(preset_name)

    def get_all_presets(self) -> List[LayoutPreset]:
        """Get all layout presets"""
        return list(self.presets.values())

    def create_preset_from_current(
        self, name: str, description: str, current_windows: Dict
    ) -> LayoutPreset:
        """Create a preset from current window positions

        Args:
            name: Preset name
            description: Preset description
            current_windows: Dict mapping window_id to geometry dict

        Returns:
            Created LayoutPreset
        """
        windows = []
        for window_id, geom in current_windows.items():
            layout = WindowLayout(
                window_id=window_id,
                x=geom.get("x", 0),
                y=geom.get("y", 0),
                width=geom.get("width", 400),
                height=geom.get("height", 300),
                monitor=geom.get("monitor", 0),
                opacity=geom.get("opacity", 1.0),
                zoom=geom.get("zoom", 0.3),
                always_on_top=geom.get("always_on_top", True),
            )
            windows.append(layout)

        preset = LayoutPreset(name=name, description=description, windows=windows)

        return preset

    # Grid Pattern Calculations - Helper methods
    def _calc_uniform_grid(
        self,
        windows: List[str],
        cols: int,
        rows: int,
        max_windows: int,
        screen_x: int,
        screen_y: int,
        screen_width: int,
        screen_height: int,
        spacing: int,
    ) -> Dict[str, Dict]:
        """Calculate uniform grid layout (2x2, etc.)"""
        win_width = (screen_width - spacing * (cols + 1)) // cols
        win_height = (screen_height - spacing * (rows + 1)) // rows
        layouts = {}
        for i, window_id in enumerate(windows[:max_windows]):
            col, row = i % cols, i // cols
            layouts[window_id] = {
                "x": screen_x + spacing + col * (win_width + spacing),
                "y": screen_y + spacing + row * (win_height + spacing),
                "width": win_width,
                "height": win_height,
            }
        return layouts

    def _calc_horizontal_row(
        self,
        windows: List[str],
        count: int,
        screen_x: int,
        screen_y: int,
        screen_width: int,
        screen_height: int,
        spacing: int,
    ) -> Dict[str, Dict]:
        """Calculate horizontal row layout (3x1, 4x1)"""
        win_width = (screen_width - spacing * (count + 1)) // count
        win_height = screen_height - spacing * 2
        return {
            window_id: {
                "x": screen_x + spacing + i * (win_width + spacing),
                "y": screen_y + spacing,
                "width": win_width,
                "height": win_height,
            }
            for i, window_id in enumerate(windows[:count])
        }

    def _calc_vertical_column(
        self,
        windows: List[str],
        count: int,
        screen_x: int,
        screen_y: int,
        screen_width: int,
        screen_height: int,
        spacing: int,
    ) -> Dict[str, Dict]:
        """Calculate vertical column layout (1x3)"""
        win_width = screen_width - spacing * 2
        win_height = (screen_height - spacing * (count + 1)) // count
        return {
            window_id: {
                "x": screen_x + spacing,
                "y": screen_y + spacing + i * (win_height + spacing),
                "width": win_width,
                "height": win_height,
            }
            for i, window_id in enumerate(windows[:count])
        }

    def calculate_grid_layout(
        self, pattern: GridPattern, windows: List[str], screen_geometry: Dict, spacing: int = 10
    ) -> Dict[str, Dict]:
        """Calculate grid layout positions

        Args:
            pattern: Grid pattern to use
            windows: List of window IDs
            screen_geometry: Dict with screen x, y, width, height
            spacing: Spacing between windows in pixels

        Returns:
            Dict mapping window_id to geometry dict {x, y, width, height}
        """
        if not windows:
            return {}

        sx = screen_geometry.get("x", 0)
        sy = screen_geometry.get("y", 0)
        sw = screen_geometry.get("width", 1920)
        sh = screen_geometry.get("height", 1080)

        if pattern == GridPattern.GRID_2X2:
            return self._calc_uniform_grid(windows, 2, 2, 4, sx, sy, sw, sh, spacing)
        elif pattern == GridPattern.GRID_3X1:
            return self._calc_horizontal_row(windows, 3, sx, sy, sw, sh, spacing)
        elif pattern == GridPattern.GRID_1X3:
            return self._calc_vertical_column(windows, 3, sx, sy, sw, sh, spacing)
        elif pattern == GridPattern.GRID_4X1:
            return self._calc_horizontal_row(windows, 4, sx, sy, sw, sh, spacing)
        elif pattern == GridPattern.MAIN_PLUS_SIDES:
            return self._calc_main_plus_sides(windows, sx, sy, sw, sh, spacing)
        elif pattern == GridPattern.CASCADE:
            return self._calc_cascade(windows, sx, sy, spacing)
        return {}

    def _calc_main_plus_sides(
        self,
        windows: List[str],
        screen_x: int,
        screen_y: int,
        screen_width: int,
        screen_height: int,
        spacing: int,
    ) -> Dict[str, Dict]:
        """Calculate main + sides layout"""
        layouts = {}
        num_windows = len(windows)
        if num_windows >= 1:
            main_width = int(screen_width * 0.6) - spacing * 2
            layouts[windows[0]] = {
                "x": screen_x + spacing,
                "y": screen_y + spacing,
                "width": main_width,
                "height": screen_height - spacing * 2,
            }
            if num_windows > 1:
                side_width = screen_width - main_width - spacing * 3
                side_height = (screen_height - spacing * num_windows) // (num_windows - 1)
                side_x = screen_x + main_width + spacing * 2
                for i, window_id in enumerate(windows[1:4]):
                    layouts[window_id] = {
                        "x": side_x,
                        "y": screen_y + spacing + i * (side_height + spacing),
                        "width": side_width,
                        "height": side_height,
                    }
        return layouts

    def _calc_cascade(
        self, windows: List[str], screen_x: int, screen_y: int, spacing: int
    ) -> Dict[str, Dict]:
        """Calculate cascade layout"""
        return {
            window_id: {
                "x": screen_x + spacing + i * 30,
                "y": screen_y + spacing + i * 30,
                "width": 600,
                "height": 400,
            }
            for i, window_id in enumerate(windows)
        }

    def auto_arrange(
        self, windows: List[str], pattern: GridPattern, screen_geometry: Dict, spacing: int = 10
    ) -> Dict[str, Dict]:
        """Auto-arrange windows in a grid pattern

        Args:
            windows: List of window IDs to arrange
            pattern: Grid pattern to use
            screen_geometry: Screen geometry dict
            spacing: Spacing between windows

        Returns:
            Dict mapping window_id to geometry dict
        """
        return self.calculate_grid_layout(pattern, windows, screen_geometry, spacing)

    def get_best_pattern(self, num_windows: int) -> GridPattern:
        """Get best grid pattern for number of windows

        Args:
            num_windows: Number of windows to arrange

        Returns:
            Recommended GridPattern
        """
        if num_windows <= 2:
            return GridPattern.GRID_1X3
        elif num_windows <= 4:
            return GridPattern.GRID_2X2
        elif num_windows <= 6:
            return GridPattern.GRID_3X1
        else:
            return GridPattern.MAIN_PLUS_SIDES
