# Changelog

All notable changes to EVE Veles Eyes will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.3.0] - 2025-12-28

### Added
- **ActionRegistry** - Single source of truth for all 42 UI actions
- **ToolbarBuilder** - Centralized toolbar construction from registry
- **ContextMenuBuilder** - Context menu construction from registry
- **MenuBuilder** - Tray and app menu construction from registry
- **CLI Audit Tool** - `python -m eve_overview_pro.ui.action_registry` for redundancy checks
- **DEV_NOTES.md** - Developer documentation for action tier rules

### Changed
- **Tab Renames** - Main→Overview, Characters & Teams→Roster, Hotkeys & Cycling→Automation, Settings Sync→Sync
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
- Renamed project from "EVE Overview Pro" to "EVE Veles Eyes"
- Updated all configuration paths to use `~/.config/eve-veles-eyes/`
- Improved error handling for window capture failures

### Fixed
- Handle None images gracefully in frame capture

## [2.1.0] - 2025-12-25

### Added
- **Layout Presets** - Save and restore complete window arrangements
- **Auto-Tiling** - 6 professional grid patterns (2x2, 3x1, 1x3, 4x1, Main+Sides, Cascade)
- **Team & Character Management** - Group characters by activity with offline tracking
- **Visual Activity Alerts** - Red flash detection for combat/damage warnings
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

[Unreleased]: https://github.com/AreteDriver/EVE_VelesEyes/compare/v2.3.0...HEAD
[2.3.0]: https://github.com/AreteDriver/EVE_VelesEyes/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/AreteDriver/EVE_VelesEyes/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/AreteDriver/EVE_VelesEyes/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/AreteDriver/EVE_VelesEyes/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/AreteDriver/EVE_VelesEyes/releases/tag/v1.0.0
