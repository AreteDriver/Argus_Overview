"""
Windows-specific Layout Manager
Uses Windows API for window positioning instead of xdotool
"""
import json
import logging
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import win32api
import win32con
import win32gui


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


@dataclass
class LayoutPreset:
    """A saved layout preset"""
    name: str
    description: str
    windows: Dict[str, Dict]  # window_id -> geometry
    grid_pattern: Optional[GridPattern] = None
    refresh_rate: int = 30

    def to_dict(self) -> Dict:
        result = asdict(self)
        if self.grid_pattern:
            result['grid_pattern'] = self.grid_pattern.value
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'LayoutPreset':
        if 'grid_pattern' in data and data['grid_pattern']:
            data['grid_pattern'] = GridPattern(data['grid_pattern'])
        return cls(**data)


class LayoutManager:
    """
    Manages window layouts and presets
    Windows version using Windows API
    """

    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)

        if config_dir is None:
            config_dir = Path.home() / 'AppData' / 'Local' / 'eve-veles-eyes'

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.presets_file = self.config_dir / 'layout_presets.json'
        self.presets: List[LayoutPreset] = []

        self._load_presets()

    def _load_presets(self):
        """Load layout presets from JSON file"""
        if self.presets_file.exists():
            try:
                with open(self.presets_file) as f:
                    data = json.load(f)
                    self.presets = [LayoutPreset.from_dict(p) for p in data]
                self.logger.info(f"Loaded {len(self.presets)} layout presets")
            except Exception as e:
                self.logger.error(f"Failed to load presets: {e}")
                self.presets = []

    def save_preset(self, preset: LayoutPreset) -> bool:
        """Save or update a layout preset"""
        # Remove existing preset with same name
        self.presets = [p for p in self.presets if p.name != preset.name]
        self.presets.append(preset)

        try:
            with open(self.presets_file, 'w') as f:
                json.dump([p.to_dict() for p in self.presets], f, indent=2)
            self.logger.info(f"Saved preset: {preset.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save preset: {e}")
            return False

    def delete_preset(self, preset_name: str) -> bool:
        """Delete a layout preset"""
        self.presets = [p for p in self.presets if p.name != preset_name]

        try:
            with open(self.presets_file, 'w') as f:
                json.dump([p.to_dict() for p in self.presets], f, indent=2)
            self.logger.info(f"Deleted preset: {preset_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete preset: {e}")
            return False

    def get_preset(self, preset_name: str) -> Optional[LayoutPreset]:
        """Get a preset by name"""
        return next((p for p in self.presets if p.name == preset_name), None)

    def get_all_presets(self) -> List[LayoutPreset]:
        """Get all layout presets"""
        return self.presets

    def create_preset_from_current(self, name: str, description: str,
                                   windows: Dict[str, Dict],
                                   grid_pattern: GridPattern = None,
                                   refresh_rate: int = 30) -> LayoutPreset:
        """Create a new preset from current window positions"""
        preset = LayoutPreset(
            name=name,
            description=description,
            windows=windows,
            grid_pattern=grid_pattern,
            refresh_rate=refresh_rate
        )
        self.save_preset(preset)
        return preset

    def calculate_grid_layout(self, pattern: GridPattern, windows: List[str],
                             screen_geometry: Dict, spacing: int = 10) -> Dict[str, Dict]:
        """
        Calculate window positions for a grid pattern

        Args:
            pattern: Grid pattern to use
            windows: List of window IDs
            screen_geometry: Dict with x, y, width, height
            spacing: Spacing between windows

        Returns:
            Dict mapping window_id to geometry dict
        """
        result = {}
        x = screen_geometry.get('x', 0)
        y = screen_geometry.get('y', 0)
        width = screen_geometry.get('width', 1920)
        height = screen_geometry.get('height', 1080)

        if pattern == GridPattern.GRID_2X2:
            # 2x2 grid
            cols, rows = 2, 2
            w = (width - spacing * 3) // cols
            h = (height - spacing * 3) // rows

            for i, win_id in enumerate(windows[:4]):
                row = i // cols
                col = i % cols
                wx = x + spacing + col * (w + spacing)
                wy = y + spacing + row * (h + spacing)
                result[win_id] = {'x': wx, 'y': wy, 'width': w, 'height': h}

        elif pattern == GridPattern.GRID_3X1:
            # 3 windows in a row
            cols = 3
            w = (width - spacing * 4) // cols
            h = height - spacing * 2

            for i, win_id in enumerate(windows[:3]):
                wx = x + spacing + i * (w + spacing)
                wy = y + spacing
                result[win_id] = {'x': wx, 'y': wy, 'width': w, 'height': h}

        elif pattern == GridPattern.GRID_1X3:
            # 3 windows in a column
            rows = 3
            w = width - spacing * 2
            h = (height - spacing * 4) // rows

            for i, win_id in enumerate(windows[:3]):
                wx = x + spacing
                wy = y + spacing + i * (h + spacing)
                result[win_id] = {'x': wx, 'y': wy, 'width': w, 'height': h}

        elif pattern == GridPattern.GRID_4X1:
            # 4 windows in a row
            cols = 4
            w = (width - spacing * 5) // cols
            h = height - spacing * 2

            for i, win_id in enumerate(windows[:4]):
                wx = x + spacing + i * (w + spacing)
                wy = y + spacing
                result[win_id] = {'x': wx, 'y': wy, 'width': w, 'height': h}

        elif pattern == GridPattern.MAIN_PLUS_SIDES:
            # Large main window + smaller side windows
            if len(windows) >= 1:
                main_w = int((width - spacing * 3) * 0.7)
                main_h = height - spacing * 2
                result[windows[0]] = {'x': x + spacing, 'y': y + spacing, 'width': main_w, 'height': main_h}

            if len(windows) >= 2:
                side_w = width - main_w - spacing * 3
                side_h = (height - spacing * 3) // (len(windows) - 1)

                for i, win_id in enumerate(windows[1:]):
                    wx = x + main_w + spacing * 2
                    wy = y + spacing + i * (side_h + spacing)
                    result[win_id] = {'x': wx, 'y': wy, 'width': side_w, 'height': side_h}

        elif pattern == GridPattern.CASCADE:
            # Cascading windows
            offset = 40
            w = width - spacing * 2 - offset * (len(windows) - 1)
            h = height - spacing * 2 - offset * (len(windows) - 1)

            for i, win_id in enumerate(windows):
                wx = x + spacing + i * offset
                wy = y + spacing + i * offset
                result[win_id] = {'x': wx, 'y': wy, 'width': w, 'height': h}

        return result

    def apply_layout(self, geometry_dict: Dict[str, Dict]) -> bool:
        """
        Apply layout to windows using Windows API

        Args:
            geometry_dict: Dict mapping window_id to geometry

        Returns:
            bool: Success
        """
        try:
            for hwnd_str, geom in geometry_dict.items():
                hwnd = int(hwnd_str, 16)

                # Set window position and size
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOP,
                    geom['x'], geom['y'],
                    geom['width'], geom['height'],
                    win32con.SWP_SHOWWINDOW
                )

            self.logger.info(f"Applied layout to {len(geometry_dict)} windows")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply layout: {e}")
            return False

    def get_screen_geometry(self, monitor: int = 0) -> Dict:
        """
        Get screen geometry for specified monitor

        Args:
            monitor: Monitor index

        Returns:
            Dict with x, y, width, height
        """
        try:
            # Get all monitors
            monitors = []

            def enum_callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
                monitors.append(lprcMonitor)
                return True

            win32api.EnumDisplayMonitors(None, None, enum_callback, 0)

            if monitor < len(monitors):
                rect = monitors[monitor]
                return {
                    'x': rect[0],
                    'y': rect[1],
                    'width': rect[2] - rect[0],
                    'height': rect[3] - rect[1],
                    'is_primary': monitor == 0
                }

            # Fallback to primary monitor
            width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            return {'x': 0, 'y': 0, 'width': width, 'height': height, 'is_primary': True}

        except Exception as e:
            self.logger.error(f"Failed to get screen geometry: {e}")
            return {'x': 0, 'y': 0, 'width': 1920, 'height': 1080, 'is_primary': True}

    def get_best_pattern(self, num_windows: int) -> GridPattern:
        """Suggest best grid pattern for number of windows"""
        if num_windows == 2:
            return GridPattern.MAIN_PLUS_SIDES
        elif num_windows == 3:
            return GridPattern.GRID_3X1
        elif num_windows == 4:
            return GridPattern.GRID_2X2
        elif num_windows <= 6:
            return GridPattern.GRID_2X2
        else:
            return GridPattern.CASCADE
