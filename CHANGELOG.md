# Changelog

All notable changes to Argus Overview will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.1] - 2026-02-02

### Added
- **Intel Alert Sounds** - Four new audio alert files for different threat levels
  - `info.wav` - Low-priority intel (440Hz, 0.3s)
  - `warning.wav` - Neutral/unknown hostiles (587Hz, 0.4s)
  - `danger.wav` - Confirmed hostiles nearby (880Hz, 0.5s)
  - `critical.wav` - Immediate threat (dual-tone, 0.6s)
- **Windows Build Configuration** - PyInstaller spec file for building Windows .exe
- **GitHub Actions CI/CD** - Cross-platform build workflow
  - Automated testing with pytest and coverage
  - Linux AppImage builds
  - Windows PyInstaller builds
  - Automated releases on version tags

### Changed
- **Test Coverage** - Improved from 92% to 93% (97% excluding Windows-only code)
  - 55+ new tests for `intel_tab.py` and `main_window_v21.py`
  - `intel_tab.py`: 77% → 93%
  - `main_window_v21.py`: 79% → 89%
  - 1798 total tests passing

## [3.0.0] - 2026-02-01

### Added
- **Cross-Platform Support** - Single unified codebase supporting both Linux and Windows
- **Platform Abstraction Layer** - New `argus_overview.platform` module with clean separation
  - `base.py` - Abstract interfaces for window management, capture, and screen utilities
  - `linux.py` - Linux implementation using X11 tools (wmctrl, xdotool, xrandr)
  - `windows.py` - Windows implementation using native Win32 API (pywin32)
- **Platform-specific dependencies** - Install with `pip install argus-overview[linux]` or `[windows]`
- **Platform tests** - 25 new tests for platform abstraction layer (1612 total tests)

### Changed
- **Unified Windows support** - Windows version now built from same codebase (previously separate repo)
- **Core modules refactored** - `discovery.py`, `window_capture_threaded.py`, `eve_settings_sync.py`, `screen.py`, `window_utils.py` now delegate to platform layer
- **CI/CD updated** - GitHub Actions workflows updated for cross-platform builds
- **Coverage threshold** - Adjusted to 80% to account for platform-specific code paths

### Deprecated
- **Argus_Overview_Windows repository** - Now archived; all development in main repo

## [2.9.0] - 2026-01-29

### Added
- **Intel Channel Parser** - New Intel tab that monitors EVE chat logs for intel reports
  - Detects null-sec system names (HED-GP, 1DQ1-A, etc.)
  - Recognizes 100+ EVE ship types including capitals
  - Parses hostile counts (+5, x10, gang of 20, etc.)
  - Threat level assessment (clear, info, warning, danger, critical)
  - Configurable alert thresholds and cooldowns
  - Multiple intel channel support (Alliance, Intel, etc.)
  - Auto-detection of EVE log directory (native and Proton)

## [2.8.6] - 2026-01-29

### Removed
- **Visual Alerts (Red Flash Detection)** - Removed feature for CCP EULA/Fair Play compliance. The red flash detection system that monitored EVE windows for combat/damage indicators has been completely removed.

### Added
- **CCP EULA / Fair Play Compliance Note** - Argus Overview is designed to operate strictly within CCP's third-party software policies. It does not broadcast inputs, automate gameplay, execute macros, inject into the EVE client, or read/interpret game memory or state. It only displays live window previews, switches focus between clients, and manages window positioning/layouts.

## [2.8.5] - 2026-01-27

### Added
- Config schema validation for characters, teams, and layout presets (#19)
- Input validation for EVE settings sync imports (#23)
- Character name sanitization against path traversal (#25)
- X11 subprocess retry logic with exponential backoff (#21)
- UniqueConnection flags to prevent duplicate signal connections (#24)
- Architecture and thread-safety documentation (#26)

### Fixed
- Memory leak from Qt signal connections never disconnected on close (#18)
- UI lag from missing debounce on widget rebuild methods (#22)

### Changed
- Updated Reddit launch post screenshots (#27)

## [2.8.4] - 2026-01-26

### Removed
- **Broadcast hotkeys** - Removed feature that violated EVE Online EULA (input broadcasting banned since Jan 2015)

### Added
- **Wayland detection** - Detects pure Wayland sessions and shows warning with workarounds
- **Security policy** - Added SECURITY.md for vulnerability reporting
- **Portable tarball** - New build script for portable distribution

### Fixed
- Unused import lint errors in tests

## [2.8.1] - 2026-01-12

### Added
- **Coverage enforcement** - CI now fails if test coverage drops below 90%
- **Auto-tag workflow** - Automatically creates version tags when `pyproject.toml` version changes
- **Dependabot auto-merge** - Automatically merges patch/minor dependency updates

### Changed
- Test coverage improved from 94% to 96%
- `hotkeys_tab.py` now at 100% coverage (was 92%)
- `screen.py` now at 100% coverage (was 70%)
- `main_window_v21.py` improved to 90% coverage (was 81%)
- Total tests: 1536 (up from 1497)

## [2.8.0] - 2026-01-10

### Added
- **Preview Filter** - Quick filter in Overview toolbar to search windows by character name
  - Type to filter visible previews
  - Status bar shows filtered count
- **Keyboard Window Control** - Number keys 1-9 activate windows by position when Overview tab is focused
- **Performance Benchmarks** - New `benchmarks/benchmark_core.py` for profiling hot paths

### Changed
- Consolidated duplicate `ScreenGeometry` class and `get_screen_geometry()` function into shared `utils/screen.py` module (DRY refactoring)
- Refactored `auto_arrange_grid` into shared `get_pattern_positions()` function (complexity 16 → 6)
- Refactored `calculate_grid_layout` into helper methods (complexity 16 → 7)
- Refactored `_on_key_press` by extracting `_MODIFIER_KEYS`, `_track_modifier_press()`, `_get_key_char()` helpers
- Refactored EVE settings sync functions by extracting `_iter_settings_dirs()`, `_process_log_files()`, `_create_char_info()` helpers
- Refactored `audit_actions` by extracting `_count_actions_by_home_and_scope()`, `_find_duplicate_homes()` helpers
- Refactored `build_window_context_menu` by extracting `_build_zoom_submenu()`, `_add_registry_action()` helpers
- All functions now pass cyclomatic complexity threshold (C901 ≤ 10)

### Security
- Added Bandit security scanner to dev dependencies and CI
- Configured pyproject.toml with appropriate skips for X11 tool usage

### Testing
- Added tests for v2.7 features (preview filter, keyboard control)
- Total test count: 1497

## [2.7.0] - 2026-01-10

### Performance
- Fixed CPU busy loop in capture result processing (15-20% CPU reduction)
- Fixed memory leak storing full-resolution frames (~600x memory reduction per window)
- Added wmctrl result caching (1-second TTL) to reduce subprocess overhead
- Fixed O(n²) duplicate detection in hotkey group drag-drop
- Moved uuid import from hot path to module level
- Increased config watcher fallback polling from 2s to 5s
- Increased status timer from 1s to 2s

### Security
- Added window ID validation to all subprocess calls (defense-in-depth)
- Path traversal prevention in layout manager
- Narrowed exception handlers to specific types

### Fixed
- Thread safety improvements using threading.Event()
- Lock file resource leak on exit
- Unicode errors handling (replace instead of ignore)

### Testing
- Improved test coverage from 94% to 96%
- Added SingleInstance class tests
- Added pause/resume tests for hotkey manager

## [2.4.2] - 2025-12-29

### Changed
- **Complete Rebrand Cleanup** - Finished rebranding from EVE Veles Eyes to Argus Overview
  - Updated all Windows source files (9 files): app names, paths, URLs, window titles
  - Renamed Flatpak files to `io.github.aretedriver.ArgusOverview.*`
  - Updated all documentation with new branding
  - Fixed GitHub URLs in Help menu links

### Fixed
- **GitHub Actions** - Updated `actions/checkout` and `actions/setup-python` from v4/v5 to v6
- **Documentation** - Fixed remaining old branding in CONTRIBUTING.md, issue templates, QUICKSTART.md, PACKAGE_INFO.md, windows/README_WINDOWS.md

### Removed
- Old `veles-eyes.sh` launcher script
- Obsolete build artifacts (`argus-overview.desktop`, `argus-overview.spec`)

## [2.4.0] - 2025-12-28

### Added
- **New Triglavian Icon** - Hexagonal geometric design with red color scheme
- **Layouts Tab Integration** - Full layouts tab now integrated into main window
- **Unit Test Suite** - 68 tests for ActionRegistry and MenuBuilder modules
- **Window Icon Support** - App icon now displays in window titlebar and system tray

### Changed
- **Rebrand to Argus Overview** - Complete rebrand from "EVE Veles Eyes"
  - New app name, window title, desktop entry
  - Config directory: `~/.config/argus-overview/`
  - Log file: `argus-overview.log`
- **GitHub Repository** - Renamed to `AreteDriver/Argus_Overview`

### Fixed
- **xdotool Timeout Errors** - Fixed layout arrangement failures with Wine/Proton windows
  - EVE windows now resize correctly without 2-second timeouts
  - Automatic fallback for non-sync mode with brief delay
- **Icon Loading** - Fixed icon path resolution (4 levels up from ui/ to project root)
- **Desktop Entry** - Fixed StartupWMClass to match actual window class

### Technical
- pytest configuration added to pyproject.toml
- All GitHub URLs updated to new repository name
- Install/uninstall scripts updated with new branding

## [2.3.0] - 2025-12-28

### Added
- **ActionRegistry** - Single source of truth for all 42 UI actions
- **ToolbarBuilder** - Centralized toolbar construction from registry
- **ContextMenuBuilder** - Context menu construction from registry
- **MenuBuilder** - Tray and app menu construction from registry
- **CLI Audit Tool** - `python -m eve_overview_pro.ui.action_registry` for redundancy checks
- **DEV_NOTES.md** - Developer documentation for action tier rules

### Changed
- **Tab Renames** - Main→Overview, Characters & Teams→Roster, Hotkeys & Cycling→Cycle Control, Settings Sync→Sync
- All menus now built from ActionRegistry (no hard-coded duplicates)
- Tray menu includes Minimize All / Restore All actions
- Consistent button styling via ToolbarBuilder (PRIMARY, SUCCESS, DANGER)

### Technical
- 42 registered actions across 3 tiers (Global, Tab, Object)
- 0 duplicate actions across primary homes (enforced by audit)
- All toolbars use registry-based button creation

## [2.2.0] - 2025-12-27

### Added
- **System Tray Integration** - Minimize to tray, quick access menu, double-click show/hide
- **One-Click Import** - Scan and import all EVE windows instantly
- **Auto-Discovery** - Background process detects new EVE clients automatically
- **Per-Character Hotkeys** - Bind specific keys to specific characters (Ctrl+1, Ctrl+2, etc.)
- **Position Lock** - Lock thumbnail positions to prevent accidental moves
- **Custom Labels** - Display "Scout", "Logi", "DPS" instead of character names
- **Hover Effects** - Opacity fade on hover to see through thumbnails
- **Activity Indicators** - Colored dots (green/yellow/gray) show window state
- **Session Timers** - Track how long each character has been logged in
- **Themes** - Dark, Light, and EVE (orange) themes
- **Quick Minimize/Restore All** - Ctrl+Shift+M/R to manage all windows
- **Hot Reload Config** - Changes apply without restart
- **Enhanced Context Menu** - More control per thumbnail
- **Smart Position Inheritance** - New thumbnails position intelligently

### Changed
- Renamed project from "EVE Overview Pro" to "Argus Overview"
- Updated all configuration paths to use `~/.config/argus-overview/`
- Improved error handling for window capture failures

### Fixed
- Handle None images gracefully in frame capture

## [2.1.0] - 2025-12-25

### Added
- **Layout Presets** - Save and restore complete window arrangements
- **Auto-Tiling** - 6 professional grid patterns (2x2, 3x1, 1x3, 4x1, Main+Sides, Cascade)
- **Team & Character Management** - Group characters by activity with offline tracking
- **Multi-Monitor Support** - Per-monitor layouts and window spreading
- **EVE Settings Sync** - Copy keybindings, UI, and overview between characters

### Changed
- Improved performance of threaded capture system
- Enhanced profile management with more options

## [2.0.0] - 2025-12-01

### Added
- Low-latency multi-window previews (up to 30 FPS)
- Draggable, resizable preview frames
- Global hotkeys (Ctrl+Alt+1-9)
- Profile management system
- Adjustable refresh rates (1-60 FPS)
- Always-on-top mode
- Click-to-activate windows
- Minimize inactive windows (50-80% GPU savings)
- Threaded capture system for no UI lag
- Smart caching for performance

### Changed
- Complete rewrite from v1.x architecture

## [1.0.0] - 2025-11-01

### Added
- Initial release
- Basic window preview functionality
- Simple hotkey support
- Single window capture

[Unreleased]: https://github.com/AreteDriver/Argus_Overview/compare/v2.8.0...HEAD
[2.8.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.7.0...v2.8.0
[2.7.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.4.2...v2.7.0
[2.4.2]: https://github.com/AreteDriver/Argus_Overview/compare/v2.4.0...v2.4.2
[2.4.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/AreteDriver/Argus_Overview/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/AreteDriver/Argus_Overview/releases/tag/v1.0.0
