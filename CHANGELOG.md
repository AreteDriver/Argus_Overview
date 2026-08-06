# Changelog

All notable changes to Argus Overview will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — Operational Truth UI Polish

Visual consistency pass across all tabs following the Operational Truth
release theme. Every surface now derives from the design-system token set
instead of hardcoded values.

### Changed
- **Design system tokens** — semantic colors, spacing, typography, metrics,
  and states centralized under `ui/design_system/`.
- **Settings tab navigation** — `QTreeWidget` category list now shows a clear
  selection highlight (`SURFACE_HOVER` background + `INFO` left accent bar)
  and defaults to "General" on first open.
- **Settings panels** — all `QGroupBox` containers styled as cards with
  `SURFACE_RAISED` background, `BORDER_SUBTLE` border, and rounded corners.
- **Danger buttons** — `ToolbarBuilder` destructive actions (`delete_character`,
  `delete_group`, etc.) switched from solid bright-red fill to an outline style
  (red text + red border) that fills on hover. Reduces visual alarm in toolbars.
- **Splitter handles** — `QSplitter::handle` styled as a 2px `BORDER_SUBTLE`
  line, eliminating default Qt grip dots in the Sync and Settings tabs.
- **Tab bar** — styled with `CANVAS` pane, `SURFACE` tabs, `SURFACE_RAISED`
  selected state, and `SURFACE_HOVER` hover state.
- **Screenshots** — all README and docs screenshots regenerated at 1440×900
  reflecting the current UI state.
- **Replay strip layout stability** — every `WindowPreviewWidget` now reserves a
  fixed-height container for the replay strip in its internal layout. Toggling
  the strip on/off no longer changes card height, preventing grid reflow shifts
  in the `FlowLayout` preview area. The strip is parented inside the container
  instead of being dynamically added/removed from the main card layout.
- **Replay strip styling** — migrated hardcoded `rgba(20,20,20,220)` background
  and `#3a3a3a` border to `SURFACE` + `BORDER_SUBTLE`. Cell borders and hover
  highlight in the strip `paintEvent` now use design-system tokens
  (`BORDER_SUBTLE`, `INFO`).
- **Fleet rail positioning** — the character status dock (`StatusDock`) moved from
  above the preview grid to below it. This prioritizes vertical space for the
  live preview area, placing operational status in a bottom rail consistent with
  the Operational Truth principle that the preview grid is the primary product.
- **Capture health badge colors** — migrated `_capture_health_color` from
  hardcoded RGB `QColor` objects to design-system semantic tokens
  (`HEALTHY`, `TEXT_SECONDARY`, `WARNING`, `CRITICAL`, `TEXT_MUTED`).

## [Unreleased] — IA Overhaul: COMMAND / FLEET / LAYOUTS / SYSTEM

Six v2.2 tabs collapsed to four IA-aligned tabs that match the operator's
mental model. The Command Center (v3.3 OPS flagship surface) is now the
default home tab, with all live fleet operations under one roof.

### Added
- **Tab containers** under `src/argus_overview/ui/tabs/`:
  - `CommandTab` — hosts the flagship `CommandCenterWidget`.
  - `FleetTab` — Roster + Intel side-by-side via `QSplitter` (60/40).
  - `LayoutsContainer` — Layout presets + Cycle Control via `QSplitter` (70/30).
  - `SystemTab` — Settings + Sync via `QSplitter` (60/40).
- **`MainWindowV21._create_tabs()`** — single entry point that builds the
  inner widgets, then wraps them in IA containers. The legacy six factory
  methods (`_create_main_tab`, `_create_characters_tab`, etc.) remain the
  source of truth for cross-tab signal wiring.
- **`MainWindowV21._create_layouts_tab()`** — builds the inner `LayoutsTab`
  consumed by the LAYOUTS container, stored as `self.presets_panel`. The
  container occupies `self.layouts_tab`.
- **`TestPhase4InformationArchitecture`** + **`tests/test_tab_containers.py`**
  — 24 new tests pin the four IA labels, container wiring, and splitter
  orientations.
- **IA contract pin** — `_TAB_LABELS` is now `["Command", "Fleet", "Layouts",
  "System"]`. `_show_settings` lands on SYSTEM.

### Changed
- **`_show_settings`** — points at the SYSTEM container (which holds
  SettingsTab on the left), since "Settings" is no longer a top-level tab.
- **ActionRegistry section comments** — section headers now note the
  Phase 4 IA mapping (`OVERVIEW_TOOLBAR → COMMAND`, `ROSTER_TOOLBAR` /
  `INTEL_TOOLBAR → FLEET`, `LAYOUTS_TOOLBAR` / `CYCLE_CONTROL_TOOLBAR →
  LAYOUTS`, `SYNC_TOOLBAR` / `SETTINGS_PANEL → SYSTEM`). The `PrimaryHome`
  enum values are unchanged — actions still bind to the same inner widget.
- **Refresh Layout Groups tooltip** — now says "from the LAYOUTS tab
  (Cycle Control pane)" instead of "from Cycle Control tab".

### Tests
- 24 new tests across `tests/test_tab_containers.py` and the new
  `TestPhase4InformationArchitecture` class in `tests/test_main_window_v21.py`.
- Full suite: 2,580 passed, 5 skipped.

### Senior review fixes
Addressed 11 findings from the Phase 4 senior review (1 critical):
- **Critical**: `_create_layouts_tab` passed `character_manager` as the
  second positional arg to `LayoutsTab` — the actual signature is
  `(layout_manager, main_tab, settings_manager=None, character_manager=None)`.
  Switched to kwargs, pinned by `test_create_layouts_tab_passes_main_tab_to_main_slot`.
- **Naming symmetry**: inner widget renamed `self.layouts_tab` →
  `self.presets_panel` so `self.layouts_tab` consistently denotes the
  IA container (matches `command_tab` / `fleet_tab` / `system_tab`).
- **Duplicate signal**: dropped redundant `layouts_tab.layout_applied`
  connection; `main_tab.layout_applied` remains the single canonical
  source for `_on_layout_applied` and the `CommandIntegrator`.
- **Tautological alias**: removed the `LayoutPresetsPanel` re-export
  from `tabs/layouts_tab.py` (and its pinning test). The inner widget
  is accessed via `window.presets_panel`; the alias was unconsumed
  after the rename.

## [3.2.0] - 2026-04-26 — Intel-Aware Edition

This release ships a 10-PR arc that turns Argus's preview chrome into an
intel-aware UI. Frame borders and chip dots now carry threat state from
the chat-log parser; per-character system tracking unlocks smart fan-out;
adjacent-system alerts tint at reduced intensity with a "+Nj" badge.
EVE-O Preview cannot match any tier of this — it has no access to
the parser running inside the same process.

### Added
- **Intel-aware preview borders** — frames tint by IntelReport threat level
  (clear / info / warning / danger / critical) with 30s linear alpha
  decay and a 600ms pulse on upgrade into danger or critical.
- **Character status dock** — horizontal chip strip above the preview
  grid. Each chip shows a colored-initials avatar (deterministic
  per-character accent), name, current system, and a threat-tint dot.
  Click a chip to focus the matching window.
- **Preview focus mode** — double-click any thumbnail to spotlight it
  (scales up, others fade to 25% opacity). Press Escape or
  double-click again to exit.
- **Per-character system tracking** — new `intel/character_location.py`
  polls EVE Local channel logs (UTF-16-LE), parses each file's
  `Listener:` header, and tails for "Channel changed to Local : X" so
  every character has an independent current-system map.
- **Smart per-character threat fan-out** — alerts only tint frames + chips
  for characters in the affected system. Unknown locations fall through
  to full intensity (graceful upgrade).
- **Jumps-from threat fan-out** — adjacent-system alerts also tint, with
  per-jump alpha falloff (`0.5 ^ distance`, floor 0.4). Configurable via
  `intel.threat_jumps_threshold` (default 1, set 0 to disable).
- **"+Nj" distance badge** on chips and frames during adjacent-system
  alerts. Tooltip explicitly shows `Threat: warning (1j away)`.
- **Per-character accent border** on preview frames during clear state.
  Same color as the chip avatar — instant visual identity at small
  grid sizes.
- **Replay strip** — toggleable horizontal strip below each preview that
  holds the last ~5 seconds of capture as 6 thumbnails. Hover a cell to
  swap the main image to that buffered frame; mouse leave restores live.
  Toggle via right-click → "Show replay strip"; persists per-character
  via `replay_strip_enabled` setting.

### Internals
- **`intel/threat_filter.resolve_tint`** — single-source-of-truth filter
  used by both `WindowManager` and `StatusDock` so per-character tinting
  rules stay symmetric across grid + dock.
- **Promoted accent palette** to `main_tab.py` (`CHARACTER_ACCENT_COLORS`,
  `character_accent_color`) so frame border + chip avatar + future
  surfaces all draw the same color for the same character.
- **`WindowPreviewWidget.set_threat_state`** gained `initial_alpha` and
  `distance` kwargs. Pulse animation gates on `initial_alpha >= 0.9` so
  distant adjacent alerts glow but don't pulse.

### Settings (new)
- `intel.threat_jumps_threshold` — int, default 1. Max jumps to consider
  for adjacent-system tinting; 0 disables.
- `intel.track_character_locations` — bool, default true. Toggles the
  Local-log location tracker.
- `replay_strip_enabled` — `dict[character_name, bool]`. Per-character
  replay-strip visibility, persisted across sessions.

### Tests
- **+212 new tests**, full suite at 2391 passed / 5 skipped.
- New test files: `test_character_location.py`, `test_threat_filter.py`,
  `test_status_dock.py`, `test_replay_strip.py`.

### CI
- Ignored `CVE-2026-3219` (pip itself, no upstream patch yet) in
  `pip-audit` so PRs aren't blocked by a vulnerability we can't fix.

## [3.1.2] - 2026-04-15

### Security
- **Pillow 12.2.0** — bump from 12.1.1 to patch FITS GZIP decompression bomb (GHSA high severity, CVE in Pillow < 12.2.0)

## [3.1.1] - 2026-04-15

### Fixed
- **Signal lifecycle leaks** - Disconnect dynamic `frame.signal` connections in `closeEvent()` across all preview frames and cross-tab signals to prevent leaks after widget deletion
- **Capture pipeline stability** - Snapshot `preview_frames.items()` via `list()` to prevent crashes from concurrent window removal; timestamped `pending_requests`; orphan image cleanup
- **Frame dedup performance** - Crop-based fingerprinting (top 32 rows) is ~22× cheaper than full `tobytes()` on unchanged frames; only compute full hash after dedup confirms change
- **Preview frame hang on client close** - Remove preview frame on client disconnect to prevent capture loop hang
- **Wayland import guard** - Guard `pynput` import for Wayland-only environments (#55)

### Security
- Scrub local filesystem paths from recording script

### Other
- Bump `codecov/codecov-action` from 5 to 6
- Format codebase with CI-matching black version (#58)
- Docs: add CI/CD and testing sections to CLAUDE.md
- 100% coverage milestone, Flatpak PyPI URL, Wayland hardware test report

## [3.1.0] - 2026-03-13

### Added
- **Wayland POC** - New `platform/wayland.py` with Sway and Hyprland compositor support
  - Window enumeration via `swaymsg` / `hyprctl`
  - Window capture via `grim`
  - Screen geometry via `wlr-randr`
  - Factory routing: pure Wayland → Wayland classes, XWayland → Linux (X11) classes
  - Optional `wayland` dependency group with `dbus-next` for future portal integration
- **Intel System Database** - 350 EVE systems from SDE (`intel/data/systems.json`)
  - Replaces hardcoded 20-system set with comprehensive intel-relevant systems
  - Trade hubs, null-sec entry systems, low-sec hotspots, Pochven
- **Multi-word System Matching** - Intel parser now detects "Old Man Star", "New Caldari", etc.
- **Multi-word Ship Detection** - "force auxiliary" now detected in intel messages
- **Windows Platform Tests** - 97 mock tests for full `windows.py` coverage on Linux

### Fixed
- **Windows Parity** - Four fixes aligning Windows behavior with Linux
  - Added `IsIconic()` check to skip minimized windows in capture (matches Linux `map_state` guard)
  - GDI resource cleanup moved to `finally` block to prevent handle leaks on exception
  - Worker stop mechanism changed from boolean flag to `threading.Event` (proper memory barrier)
  - `capture_window_async` now uses consistent `is_valid_window_id()` validation

### Changed
- **Test Coverage** - 96% → 99% (1902 → 2094 tests, +192)
  - `windows.py`: 0% → 97%
  - `parser.py`: 99% → 100%
  - New `intel/systems.py`: 100%
  - New `platform/wayland.py`: 86%
- **Packaging Updated** - Flatpak manifests and metainfo updated to v3.0.6→v3.1.0
- **AppImage Script** - Uses dynamic versioning from pyproject.toml, warns on missing runtime tools
- **CLAUDE.md** - Regenerated via claudemd-forge with domain context merged

## [3.0.6] - 2026-03-12

### Fixed
- Skip minimized windows in xlib capture, reset Display connection on failure
- Resolve Windows layout crash and cross-platform `move_window` (#43)
- Narrow `except Exception` to specific types and modernize type hints (#46)
- Set watchdog observer as daemon thread for clean shutdown

### Changed
- Overhaul capture pipeline — xlib direct capture, bounded queue, frame dedup
- Eliminate redundant copies, fix memory leaks, use platform abstraction (#50)
- Test coverage improved to 96% (1902 tests)

### Security
- Added gitleaks secret scanning and pip-audit dependency scanning

## [3.0.5] - 2026-02-15

### Changed
- **Test Coverage** - Improved from 94% to 95% with 14 new tests covering all non-Windows stragglers to 100%
- 1870 total tests passing

## [3.0.4] - 2026-02-10

### Added
- **Real-time Cycling Hotkeys** - Enable cycling hotkey activation without restart
- Batch listener restarts during cycling hotkey re-registration

### Changed
- Added CodeQL security scanning
- Extended PySide6 skipif to Python 3.10+ for CI compatibility

## [3.0.3] - 2026-02-02

### Changed
- **Test Coverage** - Improved overall coverage from 93% to 94%
  - `alerts.py`: 93% → 100%
  - `intel_tab.py`: 91% → 96%
  - `parser.py`: 96% → 99%
  - `platform/linux.py`: 95% → 97%
  - `main_tab.py`: 92% → 93%
  - `main_window_v21.py`: 89% → 90%
  - 1827 total tests passing (up from 1798)
- **Test Stability** - Added Python 3.12 skipif decorators for PySide6 segfault-prone tests

## [3.0.2] - 2026-02-02

### Fixed
- **CI Build Fixes** - Resolved Linux AppImage build failures
  - Added `xvfb-run` wrapper for PyInstaller pynput X11 initialization
  - Changed spec to use COLLECT for directory output (required by AppImage)
  - Removed redundant `build.yml` workflow (replaced by dedicated workflows)
- **Test Stability** - Skip `test_process_message` on Python 3.12 (PySide6 segfault)
- **Version Strings** - Unified version display across all UI components
  - Window title, tray tooltip, and logs now use `__version__` from package

### Changed
- **Removed Deprecated Workflow** - Deleted `build.yml` in favor of `build-linux.yml` and `build-windows.yml`

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

[Unreleased]: https://github.com/AreteDriver/Argus_Overview/compare/v3.1.0...HEAD
[3.1.0]: https://github.com/AreteDriver/Argus_Overview/compare/v3.0.6...v3.1.0
[3.0.6]: https://github.com/AreteDriver/Argus_Overview/compare/v3.0.5...v3.0.6
[3.0.5]: https://github.com/AreteDriver/Argus_Overview/compare/v3.0.4...v3.0.5
[3.0.4]: https://github.com/AreteDriver/Argus_Overview/compare/v3.0.3...v3.0.4
[3.0.3]: https://github.com/AreteDriver/Argus_Overview/compare/v3.0.2...v3.0.3
[3.0.2]: https://github.com/AreteDriver/Argus_Overview/compare/v3.0.1...v3.0.2
[3.0.1]: https://github.com/AreteDriver/Argus_Overview/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.9.0...v3.0.0
[2.9.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.8.6...v2.9.0
[2.8.6]: https://github.com/AreteDriver/Argus_Overview/compare/v2.8.5...v2.8.6
[2.8.5]: https://github.com/AreteDriver/Argus_Overview/compare/v2.8.4...v2.8.5
[2.8.4]: https://github.com/AreteDriver/Argus_Overview/compare/v2.8.1...v2.8.4
[2.8.1]: https://github.com/AreteDriver/Argus_Overview/compare/v2.8.0...v2.8.1
[2.8.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.7.0...v2.8.0
[2.7.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.4.2...v2.7.0
[2.4.2]: https://github.com/AreteDriver/Argus_Overview/compare/v2.4.0...v2.4.2
[2.4.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/AreteDriver/Argus_Overview/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/AreteDriver/Argus_Overview/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/AreteDriver/Argus_Overview/releases/tag/v1.0.0
