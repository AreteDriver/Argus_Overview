# EVE Veles Eyes v2.2 Ultimate Edition - Package Information

## What's Included in This Package

This is the **complete core architecture** for EVE Veles Eyes v2.2 Ultimate Edition with all features!

### Core Modules (100% Complete):

1. **character_manager.py** - Full character & team management system
2. **layout_manager.py** - Complete layout presets & grid patterns
3. **alert_detector.py** - Visual activity alert system
4. **eve_settings_sync.py** - EVE settings synchronization
5. **window_capture_threaded.py** - High-performance threaded capture
6. **hotkey_manager.py** - Global hotkey system
7. **discovery.py** - Auto-discovery of EVE windows
8. **config_watcher.py** - Hot-reload configuration

### UI Modules (100% Complete):

1. **main_window_v21.py** - Main window with tabbed interface
2. **main_tab.py** - Window preview & management
3. **characters_teams_tab.py** - Character roster & teams
4. **layouts_tab.py** - Layout presets & grid patterns
5. **settings_sync_tab.py** - EVE settings synchronization
6. **settings_tab.py** - Application settings
7. **hotkeys_tab.py** - Hotkey configuration
8. **about_dialog.py** - About dialog
9. **tray.py** - System tray integration
10. **themes.py** - Theme management
11. **settings_manager.py** - Settings persistence

### Infrastructure:

- Complete installation system (install.sh)
- Python package structure
- Dependencies (requirements.txt)
- Launcher scripts
- Desktop integration
- Configuration management
- CI/CD workflows

### Documentation:

- README.md - Complete user guide
- QUICKSTART.md - Quick start guide
- WHATS_NEW.md - Feature changelog
- PACKAGE_INFO.md - This file
- LICENSE - MIT License

---

## Quick Start

```bash
# Extract
tar -xzf eve-veles-eyes-v2.2.tar.gz
cd eve-veles-eyes

# Install
./install.sh

# Run
~/eve-veles-eyes/run.sh
```

---

## Architecture Overview

```
eve-veles-eyes/
├── src/
│   ├── main.py                          # Application entry point
│   └── eve_overview_pro/
│       ├── __init__.py
│       ├── core/                        # Core modules
│       │   ├── character_manager.py     # Character & team system
│       │   ├── layout_manager.py        # Layout presets & grids
│       │   ├── alert_detector.py        # Visual alerts
│       │   ├── eve_settings_sync.py     # Settings synchronization
│       │   ├── window_capture_threaded.py # Threaded capture
│       │   ├── hotkey_manager.py        # Global hotkeys
│       │   ├── discovery.py             # Auto-discovery
│       │   ├── config_watcher.py        # Hot reload
│       │   └── position.py              # Window positioning
│       ├── ui/                          # UI modules
│       │   ├── main_window_v21.py       # Main window
│       │   ├── main_tab.py              # Preview tab
│       │   ├── characters_teams_tab.py  # Characters tab
│       │   ├── layouts_tab.py           # Layouts tab
│       │   ├── settings_sync_tab.py     # Sync tab
│       │   ├── settings_tab.py          # Settings tab
│       │   ├── hotkeys_tab.py           # Hotkeys tab
│       │   ├── about_dialog.py          # About dialog
│       │   ├── tray.py                  # System tray
│       │   ├── themes.py                # Theme management
│       │   └── settings_manager.py      # Settings persistence
│       └── utils/                       # Utilities
├── assets/                              # Application assets
│   └── icon.png                         # Application icon
├── windows/                             # Windows version
│   └── src/                             # Windows source
├── requirements.txt                     # Python dependencies
├── install.sh                           # Installation script
├── README.md                            # User documentation
├── QUICKSTART.md                        # Quick start guide
├── WHATS_NEW.md                         # Feature changelog
└── LICENSE                              # MIT License
```

---

## Configuration Paths

- **Config Directory**: `~/.config/eve-veles-eyes/`
- **Data Directory**: `~/.local/share/eve-veles-eyes/`
- **Log File**: `~/.config/eve-veles-eyes/eve-veles-eyes.log`
- **Lock File**: `~/.config/eve-veles-eyes/eve-veles-eyes.lock`

---

## Key Dependencies

```
PySide6>=6.6.0        # Qt GUI framework
python-xlib>=0.33     # X11 window management
Pillow>=10.4.0        # Image processing
pynput>=1.7.7         # Keyboard/mouse input
numpy>=1.26.4         # Numerical computations
watchdog>=4.0.0       # File system monitoring
```

---

## API Examples

### Character Management
```python
from eve_overview_pro.core.character_manager import CharacterManager, Character, Team

manager = CharacterManager()

# Add characters
char = Character(name="Drunk'n Sailor", account="Main", role="Miner")
manager.add_character(char)

# Create teams
team = Team(name="Mining Fleet", description="Ore extraction ops")
manager.create_team(team)
manager.add_character_to_team("Mining Fleet", "Drunk'n Sailor")
```

### Layout Management
```python
from eve_overview_pro.core.layout_manager import LayoutManager, GridPattern

manager = LayoutManager()

# Calculate grid layout
screen = {'x': 0, 'y': 0, 'width': 1920, 'height': 1080}
windows = ['0x123', '0x124', '0x125', '0x126']
layout = manager.calculate_grid_layout(GridPattern.GRID_2X2, windows, screen)
```

### Alert Detection
```python
from eve_overview_pro.core.alert_detector import AlertDetector, AlertLevel

detector = AlertDetector()

def on_alert(level):
    print(f"ALERT: {level}")

detector.register_callback('0x123', on_alert)
alert_level = detector.analyze_frame('0x123', image)
```

### Settings Sync
```python
from eve_overview_pro.core.eve_settings_sync import EVESettingsSync

sync = EVESettingsSync()
characters = sync.scan_for_characters()
results = sync.sync_settings("Main Character", ["Alt 1", "Alt 2"])
```

---

## Contributing

To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See CONTRIBUTING.md for detailed guidelines.

---

## License

MIT License - See LICENSE file

---

**Built for the EVE Online community**

Fly safe, capsuleers! o7
