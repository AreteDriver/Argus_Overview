"""
Layout Manager - Presets and Auto-Grid System
Handles saving/loading window layouts and auto-tiling patterns
"""
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


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
        data['windows'] = [asdict(w) for w in self.windows]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'LayoutPreset':
        """Create from dictionary"""
        windows_data = data.pop('windows', [])
        preset = cls(**data)
        preset.windows = [WindowLayout(**w) for w in windows_data]
        return preset


class LayoutManager:
    """Manages layout presets and grid patterns"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)

        if config_dir is None:
            config_dir = Path.home() / '.config' / 'eve-overview-pro'

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.layouts_dir = self.config_dir / 'layouts'
        self.layouts_dir.mkdir(exist_ok=True)

        self.presets: Dict[str, LayoutPreset] = {}
        self._load_presets()

    def _load_presets(self):
        """Load all layout presets"""
        for preset_file in self.layouts_dir.glob('*.json'):
            try:
                with open(preset_file) as f:
                    data = json.load(f)
                    preset = LayoutPreset.from_dict(data)
                    self.presets[preset.name] = preset
            except Exception as e:
                self.logger.error(f"Failed to load preset {preset_file}: {e}")

        self.logger.info(f"Loaded {len(self.presets)} layout presets")

    def save_preset(self, preset: LayoutPreset) -> bool:
        """Save a layout preset"""
        try:
            preset.modified_at = datetime.now().isoformat()
            preset_file = self.layouts_dir / f"{preset.name}.json"

            with open(preset_file, 'w') as f:
                json.dump(preset.to_dict(), f, indent=2)

            self.presets[preset.name] = preset
            self.logger.info(f"Saved layout preset '{preset.name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save preset '{preset.name}': {e}")
            return False

    def delete_preset(self, preset_name: str) -> bool:
        """Delete a layout preset"""
        if preset_name not in self.presets:
            return False

        preset_file = self.layouts_dir / f"{preset_name}.json"
        try:
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

    def create_preset_from_current(self, name: str, description: str,
                                   current_windows: Dict) -> LayoutPreset:
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
                x=geom.get('x', 0),
                y=geom.get('y', 0),
                width=geom.get('width', 400),
                height=geom.get('height', 300),
                monitor=geom.get('monitor', 0),
                opacity=geom.get('opacity', 1.0),
                zoom=geom.get('zoom', 0.3),
                always_on_top=geom.get('always_on_top', True)
            )
            windows.append(layout)

        preset = LayoutPreset(
            name=name,
            description=description,
            windows=windows
        )

        return preset

    # Grid Pattern Calculations
    def calculate_grid_layout(self, pattern: GridPattern, windows: List[str],
                              screen_geometry: Dict,
                              spacing: int = 10) -> Dict[str, Dict]:
        """Calculate grid layout positions
        
        Args:
            pattern: Grid pattern to use
            windows: List of window IDs
            screen_geometry: Dict with screen x, y, width, height
            spacing: Spacing between windows in pixels
            
        Returns:
            Dict mapping window_id to geometry dict {x, y, width, height}
        """
        num_windows = len(windows)
        if num_windows == 0:
            return {}

        screen_x = screen_geometry.get('x', 0)
        screen_y = screen_geometry.get('y', 0)
        screen_width = screen_geometry.get('width', 1920)
        screen_height = screen_geometry.get('height', 1080)

        layouts = {}

        if pattern == GridPattern.GRID_2X2:
            # 2x2 grid
            cols, rows = 2, 2
            win_width = (screen_width - spacing * 3) // cols
            win_height = (screen_height - spacing * 3) // rows

            for i, window_id in enumerate(windows[:4]):
                col = i % cols
                row = i // cols
                layouts[window_id] = {
                    'x': screen_x + spacing + col * (win_width + spacing),
                    'y': screen_y + spacing + row * (win_height + spacing),
                    'width': win_width,
                    'height': win_height
                }

        elif pattern == GridPattern.GRID_3X1:
            # 3 windows horizontally
            win_width = (screen_width - spacing * 4) // 3
            win_height = screen_height - spacing * 2

            for i, window_id in enumerate(windows[:3]):
                layouts[window_id] = {
                    'x': screen_x + spacing + i * (win_width + spacing),
                    'y': screen_y + spacing,
                    'width': win_width,
                    'height': win_height
                }

        elif pattern == GridPattern.GRID_1X3:
            # 3 windows vertically
            win_width = screen_width - spacing * 2
            win_height = (screen_height - spacing * 4) // 3

            for i, window_id in enumerate(windows[:3]):
                layouts[window_id] = {
                    'x': screen_x + spacing,
                    'y': screen_y + spacing + i * (win_height + spacing),
                    'width': win_width,
                    'height': win_height
                }

        elif pattern == GridPattern.GRID_4X1:
            # 4 windows horizontally
            win_width = (screen_width - spacing * 5) // 4
            win_height = screen_height - spacing * 2

            for i, window_id in enumerate(windows[:4]):
                layouts[window_id] = {
                    'x': screen_x + spacing + i * (win_width + spacing),
                    'y': screen_y + spacing,
                    'width': win_width,
                    'height': win_height
                }

        elif pattern == GridPattern.MAIN_PLUS_SIDES:
            # One large main window + 3 smaller sides
            if num_windows >= 1:
                # Main window (left 60%)
                main_width = int(screen_width * 0.6) - spacing * 2
                layouts[windows[0]] = {
                    'x': screen_x + spacing,
                    'y': screen_y + spacing,
                    'width': main_width,
                    'height': screen_height - spacing * 2
                }

            # Side windows (right 40%, stacked vertically)
            if num_windows > 1:
                side_width = screen_width - main_width - spacing * 3
                side_height = (screen_height - spacing * (num_windows)) // (num_windows - 1)
                side_x = screen_x + main_width + spacing * 2

                for i, window_id in enumerate(windows[1:4]):
                    layouts[window_id] = {
                        'x': side_x,
                        'y': screen_y + spacing + i * (side_height + spacing),
                        'width': side_width,
                        'height': side_height
                    }

        elif pattern == GridPattern.CASCADE:
            # Cascading windows
            base_width = 600
            base_height = 400
            offset = 30

            for i, window_id in enumerate(windows):
                layouts[window_id] = {
                    'x': screen_x + spacing + i * offset,
                    'y': screen_y + spacing + i * offset,
                    'width': base_width,
                    'height': base_height
                }

        return layouts

    def auto_arrange(self, windows: List[str], pattern: GridPattern,
                     screen_geometry: Dict, spacing: int = 10) -> Dict[str, Dict]:
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
