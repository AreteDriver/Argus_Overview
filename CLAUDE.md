# Argus Overview - Project Instructions

## Project Overview
Professional multi-boxing tool for EVE Online on Linux. Window preview management, team organization, layout presets, and settings synchronization.

**Stack**: Python, PySide6 (Qt), python-xlib
**Version**: 2.8.x
**Platforms**: Linux (native), Windows (separate repo)

---

## Architecture

### Source Structure
```
src/argus_overview/
├── ui/                  # PySide6 widgets and windows
│   ├── action_registry.py  # Single source of truth for all UI actions
│   ├── main_window.py
│   └── tabs/            # Overview, Roster, Layouts, Cycle Control, Sync, Settings
├── core/                # Business logic
├── capture/             # Window capture (X11/Wayland)
└── config/              # Settings persistence
```

### Action Registry System (v2.3+)
All UI actions follow tier rules:

| Tier | Scope | Primary Home | Example |
|------|-------|--------------|---------|
| 1 | Global | TRAY_MENU, APP_MENU, HELP_MENU | Quit, Show/Hide |
| 2 | Tab | *_TOOLBAR, SETTINGS_PANEL | Tab-specific workflows |
| 3 | Object | *_CONTEXT | Actions on selected items |

**Rule**: Every action has exactly ONE primary home. No duplicate clickable UI elements.

---

## Development Workflow

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run
python src/main.py
# or
./run.sh

# Test
pytest

# Lint
ruff check src/
ruff format src/

# Audit action registry
python -m argus_overview.ui.action_registry
```

---

## Tab Structure

| Tab | Purpose | Toolbar |
|-----|---------|---------|
| Overview | Window preview, capture | OVERVIEW_TOOLBAR |
| Roster | Characters & teams | ROSTER_TOOLBAR |
| Layouts | Window arrangement patterns | LAYOUTS_TOOLBAR |
| Cycle Control | Hotkeys, cycling | CYCLE_CONTROL_TOOLBAR |
| Sync | EVE settings sync | SYNC_TOOLBAR |
| Settings | App configuration | SETTINGS_PANEL |

---

## Distribution

```bash
# Build AppImage
./build-appimage.sh

# Output in dist/
```

---

## Code Conventions
- PySide6 signal/slot architecture
- ActionRegistry for all UI actions (no ad-hoc menus)
- Type hints required
- ruff for linting/formatting
- X11 via python-xlib, Wayland support where possible

---

## Adding New Actions

1. Determine scope (Global/Tab/Object)
2. Choose primary home based on tier rules
3. Register in `ui/action_registry.py`
4. Bind handler in appropriate widget
5. Run audit: `python -m argus_overview.ui.action_registry`

---

## CCP Attribution
```
EVE Online and the EVE logo are registered trademarks of CCP hf.
This is a fan project, not affiliated with or endorsed by CCP hf.
```
