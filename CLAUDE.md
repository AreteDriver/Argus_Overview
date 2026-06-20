# CLAUDE.md — Argus_Overview

## Project Overview

Professional multi-boxing tool for EVE Online on Linux & Windows. Window preview management, team organization, layout presets, and settings synchronization.

**Stack**: Python, PySide6 (Qt), platform abstraction layer
**Platforms**: Linux (native X11), Windows (native Win32)

## Current State

- **Version**: 3.2.0
- **Language**: Python
- **Files**: 154 across 2 languages
- **Lines**: 58,394

## Architecture

```
Argus_Overview/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
├── assets/
├── benchmarks/
├── docs/
│   └── screenshots/
├── flatpak/
├── packaging/
├── src/
│   └── argus_overview/
├── tests/
├── windows/
├── .gitignore
├── .gitleaks.toml
├── Argus_Overview.spec
├── CHANGELOG.md
├── CLAUDE.md
├── CODE_REVIEW.md
├── CONTRIBUTING.md
├── DEV_NOTES.md
├── LICENSE
├── PACKAGE_INFO.md
├── QUICKSTART.md
├── README.md
├── RECORDING_SCRIPT.md
├── REVIEW_COMPLETE.txt
├── REVIEW_SUMMARY.md
├── SECURITY.md
├── WHATS_NEW.md
├── argus-overview.spec
├── build-appimage.sh
├── build-portable.sh
├── install.sh
├── pyproject.toml
├── requirements-windows.txt
├── requirements.txt
├── run.sh
├── uninstall.sh
```

## Tech Stack

- **Language**: Python, Shell
- **Package Manager**: pip
- **Linters**: ruff
- **Formatters**: ruff
- **Test Frameworks**: pytest
- **CI/CD**: GitHub Actions

## Coding Standards

- **Naming**: snake_case
- **Quote Style**: double quotes
- **Type Hints**: present
- **Docstrings**: google style
- **Imports**: absolute
- **Path Handling**: pathlib
- **Line Length (p95)**: 76 characters

## Common Commands

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
pytest tests/ -v

# Lint
ruff check src/ tests/
ruff format src/ tests/

# Audit action registry
python -m argus_overview.ui.action_registry

# Build AppImage
./build-appimage.sh
```

## Anti-Patterns (Do NOT Do)

- Do NOT commit secrets, API keys, or credentials
- Do NOT skip writing tests for new code
- Do NOT use `os.path` or raw X11 calls — use `pathlib.Path` and `argus_overview.platform`
- Do NOT use bare `except:` — catch specific exceptions
- Do NOT use mutable default arguments
- Do NOT use `print()` for logging — use the `logging` module
- Do NOT create ad-hoc menus — use ActionRegistry for all UI actions

## Dependencies

### Core
- PySide6-Essentials
- Pillow
- pynput
- watchdog

### Dev
- ruff
- isort
- pytest
- pytest-cov
- bandit

## Domain Context

### Source Structure
```
src/argus_overview/
├── ui/                  # PySide6 widgets and windows
│   ├── action_registry.py  # Single source of truth for all UI actions
│   ├── main_window.py
│   └── tabs/            # Overview, Roster, Layouts, Cycle Control, Sync, Settings
├── core/                # Business logic
├── platform/            # Cross-platform abstraction layer
│   ├── base.py          # Abstract base classes
│   ├── linux.py         # Linux (X11/xdotool/wmctrl)
│   └── windows.py       # Windows (Win32 API)
├── intel/               # Intel channel parser
└── utils/               # Shared utilities (screen, constants)
```

### Action Registry System (v2.3+)
All UI actions follow tier rules:

| Tier | Scope | Primary Home | Example |
|------|-------|--------------|---------|
| 1 | Global | TRAY_MENU, APP_MENU, HELP_MENU | Quit, Show/Hide |
| 2 | Tab | *_TOOLBAR, SETTINGS_PANEL | Tab-specific workflows |
| 3 | Object | *_CONTEXT | Actions on selected items |

**Rule**: Every action has exactly ONE primary home. No duplicate clickable UI elements.

### Adding New Actions
1. Determine scope (Global/Tab/Object)
2. Choose primary home based on tier rules
3. Register in `ui/action_registry.py`
4. Bind handler in appropriate widget
5. Run audit: `python -m argus_overview.ui.action_registry`

### Tab Structure

| Tab | Purpose | Toolbar |
|-----|---------|---------|
| Overview | Window preview, capture | OVERVIEW_TOOLBAR |
| Roster | Characters & teams | ROSTER_TOOLBAR |
| Layouts | Window arrangement patterns | LAYOUTS_TOOLBAR |
| Cycle Control | Hotkeys, cycling | CYCLE_CONTROL_TOOLBAR |
| Sync | EVE settings sync | SYNC_TOOLBAR |
| Settings | App configuration | SETTINGS_PANEL |

### Platform Abstraction
- PySide6 signal/slot architecture
- Linux: X11 via python-xlib, xdotool, wmctrl
- Windows: Win32 API via pywin32
- Use `argus_overview.platform` for all window/screen ops

### Outstanding Items
- **NOTE**: MainWindowV21 is imported INSIDE main() AFTER single-instance check (`src/main.py`)

### CCP Attribution
```
EVE Online and the EVE logo are registered trademarks of CCP hf.
This is a fan project, not affiliated with or endorsed by CCP hf.
```

## CI/CD

9 GitHub Actions workflows:
- **ci.yml** — lint + test on push/PR
- **build-linux.yml** — AppImage packaging
- **build-windows.yml** — Windows portable build
- **release.yml** — Tagged release automation
- **codeql.yml** — Static analysis (CodeQL)
- **secret-scan.yml** — gitleaks secret scanning
- **security.yml** — Dependency audit (pip-audit, bandit)
- **dependabot-auto-merge.yml** — Auto-merge patch updates
- **auto-tag.yml** — Version tag on merge to main

## Testing

- **2,184 tests** via pytest
- Python 3.10, 3.11, 3.12 matrix
- Platform-specific tests guarded by `sys.platform` checks
- Run: `pytest tests/ -v` or `pytest tests/ -v --cov=src/argus_overview`

## Git Conventions

- Commit messages: Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
- Branch naming: `feat/description`, `fix/description`
- Run tests before committing
