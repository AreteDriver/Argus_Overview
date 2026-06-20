# Argus Overview Architecture

Technical architecture documentation for developers and contributors.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Argus Overview v3.2                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        UI Layer (PySide6/Qt)                     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │   │
│  │  │ Overview │ │  Roster  │ │ Layouts  │ │  Cycle   │ ...        │   │
│  │  │   Tab    │ │   Tab    │ │   Tab    │ │   Tab    │           │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │   │
│  │       │            │            │            │                  │   │
│  │  ┌────┴────────────┴────────────┴────────────┴─────────────┐   │   │
│  │  │              ActionRegistry (Single Source of Truth)     │   │   │
│  │  └──────────────────────────┬──────────────────────────────┘   │   │
│  └─────────────────────────────┼───────────────────────────────────┘   │
│                                │                                        │
│  ┌─────────────────────────────┼───────────────────────────────────┐   │
│  │                        Core Layer                                │   │
│  │  ┌────────────┐  ┌─────────────────┐  ┌───────────────────┐    │   │
│  │  │  Window    │  │   Character     │  │     Layout        │    │   │
│  │  │  Capture   │  │   Manager       │  │     Manager       │    │   │
│  │  └────────────┘  └─────────────────┘  └───────────────────┘    │   │
│  │  ┌────────────┐  ┌─────────────────┐  ┌───────────────────┐    │   │
│  │  │  Config    │  │   Hotkey        │  │   EVE Settings    │    │   │
│  │  │  Detector  │  │   Manager       │  │      Sync         │    │   │
│  │  └────────────┘  └─────────────────┘  └───────────────────┘    │   │
│  │  ┌────────────┐  ┌─────────────────┐  ┌───────────────────┐    │   │
│  │  │ Discovery  │  │  Config         │  │   Intel / Threat  │    │   │
│  │  │  Service   │  │  Watcher        │  │   Detection       │    │   │
│  │  └────────────┘  └─────────────────┘  └───────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│  ┌─────────────────────────────┼───────────────────────────────────┐   │
│  │                      Platform Layer                              │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │   │
│  │  │  X11 / XWayland │  │    Wayland      │  │    Windows     │  │   │
│  │  │  (python-xlib)  │  │  (wlroots)      │  │  (Win32 API)   │  │   │
│  │  └─────────────────┘  └─────────────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
src/
├── main.py                          # Application entry point
└── argus_overview/
    ├── __init__.py
    ├── core/                        # Business logic (no Qt dependencies)
    │   ├── position.py              # Window position utilities
    │   ├── character_manager.py     # Character & team database
    │   ├── config_watcher.py        # Hot-reload configuration
    │   ├── discovery.py             # Auto-discover EVE windows
    │   ├── eve_settings_sync.py     # Sync EVE client settings
    │   ├── hotkey_manager.py        # Global hotkey registration
    │   ├── layout_manager.py        # Window arrangement patterns
    │   ├── position.py              # Window positioning utilities
    │   └── window_capture_threaded.py # Threaded screen capture
    │
    ├── intel/                       # Chat-log parsing & threat detection
    │   ├── log_watcher.py           # EVE log file watcher
    │   ├── parser.py                # Chat message parser
    │   ├── alerts.py                # Threat alert engine
    │   ├── threat_filter.py         # Threat filtering rules
    │   ├── character_location.py    # Character location tracking
    │   ├── jumps.py                 # Jump bridge / gate tracking
    │   ├── systems.py               # EVE system database
    │   └── data/                    # Intel data assets
    │
    ├── ui/                          # PySide6 widgets and windows
    │   ├── action_registry.py       # Single source of truth for actions
    │   ├── main_window_v21.py       # Main application window
    │   ├── main_tab.py              # Overview/preview tab
    │   ├── characters_teams_tab.py  # Roster management tab
    │   ├── layouts_tab.py           # Layout presets tab
    │   ├── hotkeys_tab.py           # Cycle Control tab
    │   ├── settings_sync_tab.py     # EVE sync tab
    │   ├── settings_tab.py          # Application settings tab
    │   ├── menu_builder.py          # Menu construction
    │   ├── tray.py                  # System tray integration
    │   ├── themes.py                # Theme definitions
    │   ├── settings_manager.py      # Settings persistence
    │   ├── hotkey_edit.py           # Hotkey recording widget
    │   └── about_dialog.py          # About dialog
    │
    ├── platform/                    # Platform abstraction
    │   ├── base.py                  # Platform interface base
    │   ├── linux.py                 # X11 implementation
    │   ├── wayland.py               # Wayland implementation
    │   └── windows.py               # Windows implementation
    │
    └── utils/                       # Shared utilities
        ├── constants.py             # Application constants
        ├── screen.py                # Screen/monitor utilities
        └── window_utils.py          # Window ID utilities
```

---

## Core Components

### Window Capture System

The capture system runs in a background thread to prevent UI blocking.

```
┌──────────────────────────────────────────────────────────────┐
│                    WindowCaptureThreaded                      │
├──────────────────────────────────────────────────────────────┤
│  Main Thread               │  Capture Thread                  │
│  ┌──────────────┐         │  ┌──────────────────────┐        │
│  │ Qt Event     │         │  │ Capture Loop         │        │
│  │ Loop         │         │  │ ┌──────────────────┐ │        │
│  │              │  signal │  │ │ xwd (screenshot) │ │        │
│  │ ┌──────────┐ │ ◄────── │  │ └────────┬─────────┘ │        │
│  │ │ Preview  │ │         │  │          │           │        │
│  │ │ Widget   │ │         │  │ ┌────────▼─────────┐ │        │
│  │ └──────────┘ │         │  │ │ PIL Processing   │ │        │
│  └──────────────┘         │  │ └────────┬─────────┘ │        │
│                           │  │          │           │        │
│                           │  │ ┌────────▼─────────┐ │        │
│                           │  │ │ Frame Cache      │ │        │
│                           │  │ └──────────────────┘ │        │
│                           │  └──────────────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

**Key Classes:**
- `WindowCaptureThreaded`: Manages capture thread lifecycle
- `CaptureWorker`: Background thread that captures window contents
- Emits `frame_ready(window_id, QPixmap)` signal to UI

**Performance Features:**
- Configurable FPS (1-60)
- Frame caching to reduce redundant captures
- Low power mode (5 FPS for power saving)
- Complete disable option for hotkey-only usage

### Character & Team Management

Persistent storage for character roster and team definitions.

```
┌───────────────────────────────────────────────────────────────┐
│                     CharacterManager                           │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    Character Database                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │ Character    │  │ Character    │  │ Character    │  │  │
│  │  │ - name       │  │ - name       │  │ - name       │  │  │
│  │  │ - account    │  │ - account    │  │ - account    │  │  │
│  │  │ - role       │  │ - role       │  │ - role       │  │  │
│  │  │ - notes      │  │ - notes      │  │ - notes      │  │  │
│  │  │ - window_id  │  │ - window_id  │  │ - window_id  │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                      Team Database                       │  │
│  │  ┌────────────────────────┐  ┌────────────────────────┐│  │
│  │  │ Team: "Mining Fleet"   │  │ Team: "PvP Squad"      ││  │
│  │  │ - members: [...]       │  │ - members: [...]       ││  │
│  │  │ - linked_layout: "..."│  │ - linked_layout: "..." ││  │
│  │  └────────────────────────┘  └────────────────────────┘│  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  Storage: ~/.config/argus-overview/characters.json             │
│           ~/.config/argus-overview/teams.json                  │
└───────────────────────────────────────────────────────────────┘
```

### Layout Manager

Window arrangement patterns and saved presets.

```
GridPattern Enum:
┌─────────┐  ┌─────────────────┐  ┌─────┐
│ 1 │ 2 │  │  1  │  2  │  3  │  │  1  │
├───┼───┤  └─────────────────┘  ├─────┤
│ 3 │ 4 │       3x1 ROW        │  2  │
└─────────┘                      ├─────┤
  2x2 GRID                       │  3  │
                                 └─────┘
                                 1x3 COLUMN

┌─────────────────────────────┐
│           1 (MAIN)          │
├────────┬─────────┬──────────┤
│   2    │    3    │    4     │
└────────┴─────────┴──────────┘
        MAIN + SIDES
```

**Layout Persistence:**
```json
{
  "name": "Mining Layout",
  "windows": {
    "0x12345": {"x": 0, "y": 0, "width": 960, "height": 540},
    "0x12346": {"x": 960, "y": 0, "width": 960, "height": 540}
  },
  "grid_pattern": "2x2"
}
```

---

## UI Architecture

### Action Registry System

All UI actions are centralized in the ActionRegistry to prevent duplication.

```
┌───────────────────────────────────────────────────────────────────┐
│                         ActionRegistry                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  TIER 1: Global Actions                                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ TRAY_MENU:  show_hide, minimize_all, restore_all, quit       │ │
│  │ APP_MENU:   (reserved for future menu bar)                   │ │
│  │ HELP_MENU:  about, donate, documentation, report_issue       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  TIER 2: Tab Actions                                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ OVERVIEW_TOOLBAR:  import_windows, lock_positions, ...       │ │
│  │ ROSTER_TOOLBAR:    add_character, new_team, ...              │ │
│  │ LAYOUTS_TOOLBAR:   apply_layout, auto_arrange, ...           │ │
│  │ CYCLE_CONTROL_TOOLBAR: new_group, save_hotkeys, ...          │ │
│  │ SYNC_TOOLBAR:      scan_eve_settings, sync_settings, ...     │ │
│  │ SETTINGS_PANEL:    reset_all_settings, export/import, ...    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  TIER 3: Object Actions (Context Menus)                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ WINDOW_CONTEXT:    focus_window, minimize, close, set_label  │ │
│  │ CHARACTER_CONTEXT: edit_character, delete_character          │ │
│  │ TEAM_CONTEXT:      save_team, delete_team                    │ │
│  │ GROUP_CONTEXT:     delete_group, clear_group                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

**Rule**: Every action has exactly ONE primary home. No duplicate clickable UI elements.

### Tab Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  MainWindow (main_window_v21.py)                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Menu Bar                                                  │ │
│  │  [File] [View] [Help]                                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Tab Bar                                                   │ │
│  │  [Overview] [Roster] [Layouts] [Cycle Control] [Sync] [Settings]│
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Tab Content (QStackedWidget)                              │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │  Each tab has:                                       │  │ │
│  │  │  - Toolbar (TIER 2 actions)                          │  │ │
│  │  │  - Main content area                                 │  │ │
│  │  │  - Status bar / info panel                           │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Status Bar                                                │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Window Activation Flow

```
User clicks preview
        │
        ▼
┌───────────────────┐
│ MainTab           │
│ _on_preview_click │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌───────────────────┐
│ window_utils.py   │────►│ wmctrl -i -a      │
│ activate_window() │     │ (subprocess)      │
└─────────┬─────────┘     └───────────────────┘
          │
          ▼
┌───────────────────┐
│ Auto-minimize     │ (if enabled in settings)
│ previous window   │
└───────────────────┘
```

### Settings Sync Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                      EVE Settings Sync Flow                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. SCAN                                                           │
│  ┌────────────┐     ┌─────────────────────────────────────────┐   │
│  │ Scan EVE   │────►│ Find: ~/.local/share/Steam/...          │   │
│  │ Settings   │     │       ~/EVE/settings.../                 │   │
│  └────────────┘     └─────────────────────────────────────────┘   │
│                                                                     │
│  2. SELECT                                                         │
│  ┌────────────┐     ┌─────────────────────────────────────────┐   │
│  │ Source:    │     │ core_char_12345678.dat                   │   │
│  │ Main Char  │────►│ core_user_12345678.dat                   │   │
│  └────────────┘     └─────────────────────────────────────────┘   │
│                                                                     │
│  3. SYNC                                                           │
│  ┌────────────┐     ┌─────────────────────────────────────────┐   │
│  │ Targets:   │     │ Copy core_char_*.dat                     │   │
│  │ Alt 1, 2.. │────►│ Copy core_user_*.dat                     │   │
│  └────────────┘     │ Preserve character-specific IDs          │   │
│                     └─────────────────────────────────────────┘   │
│                                                                     │
│  4. BACKUP                                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ ~/.config/argus-overview/backups/YYYY-MM-DD_HHMMSS/        │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## Threading Model

```
┌─────────────────────────────────────────────────────────────────┐
│                        Thread Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MAIN THREAD (Qt Event Loop)                                    │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ - UI rendering and updates                                  ││
│  │ - User input handling                                       ││
│  │ - Signal/slot connections                                   ││
│  │ - Settings persistence                                      ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  CAPTURE THREAD (QThread)                                       │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ - Window screenshot capture                                 ││
│  │ - Image processing (resize, convert)                        ││
│  │ - Window state analysis                                     ││
│  │ - Frame caching                                             ││
│  │                                                              ││
│  │ Communication: Qt signals (frame_ready, alert_detected)     ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  DISCOVERY THREAD (QTimer-based)                                │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ - Periodic EVE window scanning                              ││
│  │ - Window list comparison                                    ││
│  │ - New window notification                                   ││
│  │                                                              ││
│  │ Interval: Configurable (default 5 seconds)                  ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  HOTKEY THREAD (pynput listener)                                │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ - Global keyboard monitoring                                ││
│  │ - Hotkey detection and dispatch                             ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Platform Integration

### X11 Window Management

```
┌───────────────────────────────────────────────────────────────────┐
│                        X11 Integration                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  WINDOW DISCOVERY (wmctrl -l)                                     │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Output: 0x12345678  0 hostname EVE - CharacterName            ││
│  │         window_id   desktop    window_title                   ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                    │
│  WINDOW ACTIVATION (wmctrl -i -a 0x12345678)                      │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Raises and focuses the specified window                       ││
│  │ Result caching: 1 second TTL                                  ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                    │
│  WINDOW CAPTURE (xwd -id 0x12345678 | convert -)                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Screenshots window contents via X11 protocol                  ││
│  │ Converted to PIL Image for processing                         ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### Wayland Window Management

```
┌───────────────────────────────────────────────────────────────────┐
│                       Wayland Integration                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  WINDOW DISCOVERY (wlr-screenshot / wlroots protocols)           │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Uses wlroots-compatible screenshot protocols                  ││
│  │ Falls back to XWayland when native protocol unavailable       ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                    │
│  WINDOW CAPTURE (grim + slurp / wlr-screenshot)                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Screenshots via Wayland compositor protocol                 ││
│  │ Converted to PIL Image for processing                         ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### Windows Window Management

```
┌───────────────────────────────────────────────────────────────────┐
│                       Windows Integration                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  WINDOW DISCOVERY (EnumWindows + GetWindowText)                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Iterates top-level windows via Win32 API                      ││
│  │ Filters by process name (exefile.exe)                         ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                    │
│  WINDOW ACTIVATION (SetForegroundWindow + ShowWindow)            │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Raises and focuses the specified window                       ││
│  │ Result caching: 1 second TTL                                  ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                    │
│  WINDOW CAPTURE (PrintWindow / BitBlt)                           │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Screenshots via GDI/Win32 API                                  ││
│  │ Converted to PIL Image for processing                         ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### Security Considerations

All subprocess calls validate window IDs to prevent command injection:

```python
# Window ID validation regex
WINDOW_ID_PATTERN = re.compile(r'^0x[0-9a-fA-F]+$')

def validate_window_id(window_id: str) -> bool:
    """Validate window ID format before subprocess calls."""
    return bool(WINDOW_ID_PATTERN.match(window_id))
```

---

## Configuration

### File Locations

| File | Purpose |
|------|---------|
| `~/.config/argus-overview/settings.json` | Application settings |
| `~/.config/argus-overview/characters.json` | Character database |
| `~/.config/argus-overview/teams.json` | Team definitions |
| `~/.config/argus-overview/layouts.json` | Saved layouts |
| `~/.config/argus-overview/hotkeys.json` | Hotkey bindings |
| `~/.config/argus-overview/argus-overview.log` | Application log |
| `~/.config/argus-overview/backups/` | Settings sync backups |

### Settings Schema

```json
{
  "preview_fps": 30,
  "low_power_fps": 5,
  "theme": "dark",
  "auto_discovery": true,
  "discovery_interval": 5,
  "auto_minimize_inactive": false,
  "minimize_to_tray": true,
  "show_session_timers": false,
  "hover_opacity": 0.3,
  "alert_sensitivity": 50
}
```

---

## Development

### Running from Source

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run
python src/main.py

# Test
pytest

# Lint
ruff check src/
ruff format src/

# Audit actions
python -m argus_overview.ui.action_registry
```

### Adding New Features

1. **Core logic**: Add to `core/` (no Qt dependencies)
2. **UI components**: Add to `ui/`
3. **Register actions**: Update `ui/action_registry.py`
4. **Write tests**: Add to `tests/`
5. **Run audit**: Verify no action duplication

---

## See Also

- [USER_GUIDE.md](USER_GUIDE.md) - End-user documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [DEV_NOTES.md](../DEV_NOTES.md) - Action Registry details
- [CHANGELOG.md](../CHANGELOG.md) - Version history
