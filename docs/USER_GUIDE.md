# Argus Overview User Guide

Complete reference for all features in Argus Overview v3.2.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Main Interface](#main-interface)
3. [Overview Tab](#overview-tab)
4. [Characters & Teams Tab](#characters--teams-tab)
5. [Layouts Tab](#layouts-tab)
6. [Cycle Control Tab](#cycle-control-tab)
7. [Settings Sync Tab](#settings-sync-tab)
8. [Settings Tab](#settings-tab)
9. [Intel Tab](#intel-tab)
10. [Focus Mode](#focus-mode)
11. [Replay Strip](#replay-strip)
12. [System Tray](#system-tray)
13. [Keyboard Shortcuts](#keyboard-shortcuts)
14. [Configuration Files](#configuration-files)
15. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Linux with X11 or Wayland (XWayland)
- EVE Online installed via Steam or standalone
- System tools: `wmctrl`, `xdotool`

### Installation

```bash
# Recommended: Install via pipx
pipx install argus-overview

# Run
argus-overview
```

### First Launch

1. Start your EVE clients and log in to your characters
2. Launch Argus Overview
3. Go to **Overview tab** → Click **Import All** to add all EVE windows
4. Arrange previews by dragging them
5. Save your layout in the **Layouts tab**

---

## Main Interface

Argus Overview uses a tabbed interface:

| Tab | Purpose |
|-----|---------|
| **Overview** | Live window previews, capture settings |
| **Characters & Teams** | Character database, team management |
| **Layouts** | Window arrangement presets |
| **Cycle Control** | Hotkeys, cycling groups |
| **Settings Sync** | EVE settings synchronization |
| **Settings** | Application configuration |

### Window Controls

- **Always on Top**: Keep Argus above other windows
- **Minimize to Tray**: Close button minimizes to system tray
- **Position Lock**: Prevent accidental preview movement

---

## Overview Tab

The Overview tab is your main workspace for managing EVE window previews.

### Toolbar Actions

| Button | Action |
|--------|--------|
| **Import All** | Scan and add all EVE windows |
| **Refresh** | Re-scan window list |
| **Lock** | Toggle position lock (Ctrl+Shift+L) |
| **Low Power** | Reduce FPS to 5 for power saving |
| **Disable Previews** | Stop capture entirely |

### Preview Filter

The search box filters visible previews by character name. Type to filter, clear to show all.

### Preview Thumbnails

Each preview shows:
- **Character name** or custom label
- **Activity indicator**: Green (focused), Yellow (recent), Gray (idle)
- **Session timer** (optional): How long the character has been active
- **Status border**: Shows window state

### Preview Controls

- **Left-click**: Activate the EVE window
- **Right-click**: Context menu
- **Drag title bar**: Move preview
- **Drag corner**: Resize preview

### Context Menu Options

| Option | Description |
|--------|-------------|
| **Focus Window** | Bring EVE window to front |
| **Minimize** | Minimize the EVE window |
| **Set Label** | Custom display name (e.g., "Scout", "Logi") |
| **Zoom Level** | Adjust preview size |
| **Remove** | Remove from preview list |

### Keyboard Window Control

When the Overview tab is focused, press **1-9** to activate windows by position (left-to-right, top-to-bottom order).

---

## Characters & Teams Tab

Manage your entire EVE roster, including offline characters.

### Character Database

Add characters even when not logged in:
1. Click **Add Character**
2. Enter character name
3. Optionally set account group and role

**Character Properties:**
- **Name**: Character name (must match EVE window title)
- **Account**: Group by Omega account (3 chars per account)
- **Role**: Miner, Scout, DPS, Logi, Hauler, Trader
- **Notes**: Personal notes

### Team Management

Teams group characters for activities:

1. Click **New Team**
2. Name your team (e.g., "Mining Fleet", "PvP Squad")
3. Drag characters into the team
4. Link team to a layout preset (optional)

**Team Features:**
- Auto-add windows when team members log in
- Apply layouts to entire team
- Sync settings to team members

### Account Grouping

Group characters by Omega account:
- Visual separation in character list
- Quick-select all characters from one account
- Track which accounts are logged in

---

## Layouts Tab

Save and restore window arrangements.

### Creating Layouts

1. Arrange EVE windows on your screen
2. Position previews in Argus Overview
3. Click **Save Layout**
4. Enter a descriptive name

### Applying Layouts

- Select layout from list → Click **Apply**
- Or use the tray menu quick-access
- Or bind to a hotkey

### Auto-Tiling Patterns

One-click arrangements:

| Pattern | Description |
|---------|-------------|
| **2x2 Grid** | 4 windows in a square |
| **3x1 Row** | 3 windows horizontal |
| **1x3 Column** | 3 windows vertical |
| **4x1 Wide** | 4 windows horizontal (ultrawide) |
| **Main + Sides** | 1 large center, 3 small sides |
| **Cascade** | Overlapping diagonal |

### Drag-Drop Layout

1. Select a grid pattern
2. Drag previews from the preview area to grid positions
3. Click **Apply** to move actual windows

### Multi-Monitor Layouts

- Layouts remember which monitor each window belongs to
- Use "Send to Monitor X" in context menu
- Different layouts can span different monitors

---

## Cycle Control Tab

Configure hotkeys and window cycling.

### Global Hotkeys

**Window Cycling:**
- **F13**: Next window
- **F14**: Previous window
- Cycles through all active EVE windows
- Works even when EVE has focus

**Per-Character Hotkeys:**
- Bind specific keys to specific characters
- Example: Ctrl+1 → "Main Character"
- Configure in the character hotkey list

### Cycling Groups

Create custom cycling groups:
- Group specific characters together
- Cycle through only group members
- Useful for separating fleets/activities

---

## Settings Sync Tab

Synchronize EVE settings between characters.

### What Gets Synced

- Keybindings and shortcuts
- UI layouts and window positions
- Overview settings and columns
- Chat window configurations
- D-scan and probe settings
- All client preferences

### Sync Process

1. Click **Scan EVE Settings** to find character profiles
2. Select **Source Character** (your main with perfect settings)
3. Select **Target Characters** (alts to receive settings)
4. Click **Sync Settings**

**Sync takes ~6 seconds per character** vs hours of manual copying.

### EVE Installation Path

If characters aren't found:
1. Click **Add Custom Path**
2. Browse to your EVE installation
3. Common locations:
   - Steam: `~/.local/share/Steam/steamapps/compatdata/8500/...`
   - Standalone: `~/.eve/`

### Backup

Settings are backed up before sync:
- Location: `~/.config/argus-overview/backups/`
- Restore manually if needed

---

## Settings Tab

Application configuration.

### Performance Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Preview FPS** | Refresh rate (1-60) | 30 |
| **Low Power FPS** | FPS when in low power mode | 5 |
| **Auto-Minimize Inactive** | Minimize previous window when cycling | Off |
| **Disable Previews** | Stop all capture | Off |

### Appearance Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Theme** | Dark, Light, EVE | Dark |
| **Hover Opacity** | Transparency on mouse hover | 30% |
| **Show Session Timers** | Display play time on previews | Off |
| **Show Activity Dots** | Display status indicators | On |

### Behavior Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Start Minimized** | Launch to system tray | Off |
| **Minimize to Tray** | Close button minimizes | On |
| **Auto-Discovery** | Scan for new EVE windows | On |
| **Discovery Interval** | Seconds between scans | 5 |

---

## Intel Tab

The Intel tab provides real-time threat detection by monitoring EVE Online chat logs.

### Threat Detection

- **Log Watcher**: Monitors `Chatlogs/` directory for new messages
- **Parser**: Extracts system names, ship types, and pilot counts from chat
- **Alert Engine**: Highlights hostile presence based on configured rules
- **Threat Chrome**: Visual overlay on the Overview tab showing current threat level

### Configuration

Threat filters are configured in `~/.config/argus-overview/settings.json`:

```json
{
  "alert_sensitivity": 50,
  "intel_enabled": true
}
```

### Data Files

- `intel/data/systems.json` — EVE system database
- `intel/data/jumpbridges.json` — Jump bridge connections

---

## Focus Mode

Focus Mode minimizes distractions by dimming inactive windows and highlighting the active EVE client.

- **Activation**: Toggle via hotkey or tray menu
- **Behavior**: Active window stays bright; inactive windows dim to configurable opacity
- **Opacity Control**: Adjustable in Settings (default 0.3)

---

## Replay Strip

The Replay Strip shows a timeline of recent window captures for quick review.

- **Navigation**: Scroll or click thumbnails to jump to specific moments
- **Cache**: Frames cached in memory; configurable retention
- **Export**: Right-click to save a frame to disk

---

## Platform Notes

### Linux X11

Fully supported. Uses `wmctrl`, `xdotool`, and `xwd`/`convert` for window operations.

### Linux Wayland

Best-effort support via `wlroots` protocols and `grim`/`slurp`. Some features (window activation, precise positioning) may be limited depending on compositor.

### Windows

Supported via Win32 API (`EnumWindows`, `SetForegroundWindow`, `PrintWindow`). Install from the Windows installer or run from source with Python 3.10+.

---

## System Tray

The orange "V" icon provides quick access:

### Tray Menu

| Option | Action |
|--------|--------|
| **Show/Hide** | Toggle main window |
| **Layouts** | Quick-switch submenu |
| **Low Power Mode** | Toggle power saving |
| **Settings** | Open settings tab |
| **Reload Config** | Apply settings.json changes |
| **Quit** | Exit application |

### Tray Actions

- **Double-click**: Show/hide main window
- **Right-click**: Open menu

### Notifications

The tray shows notifications for:
- New characters detected
- Sync completion

---

## Keyboard Shortcuts

### Global (work anywhere)

| Shortcut | Action |
|----------|--------|
| **F13** | Cycle to next EVE window |
| **F14** | Cycle to previous EVE window |
| **Ctrl+Shift+M** | Minimize all EVE windows |
| **Ctrl+Shift+R** | Restore all EVE windows |

### Application (Argus focused)

| Shortcut | Action |
|----------|--------|
| **Ctrl+Tab** | Next preview |
| **Ctrl+Shift+Tab** | Previous preview |
| **Ctrl+Shift+L** | Toggle position lock |
| **1-9** | Activate window by position |
| **Escape** | Clear preview filter |

### Configurable

Per-character hotkeys and cycling groups are user-configurable in the Cycle Control tab.

---

## Configuration Files

All configuration is stored in `~/.config/argus-overview/`:

| File | Purpose |
|------|---------|
| `settings.json` | Application settings |
| `characters.json` | Character database |
| `teams.json` | Team definitions |
| `layouts.json` | Saved layouts |
| `hotkeys.json` | Hotkey bindings |
| `argus-overview.log` | Application log |

### Hot Reload

Edit `settings.json` while running, then use **Tray → Reload Config** to apply changes without restart.

---

## Troubleshooting

### Characters not found in Settings Sync

**Cause**: EVE installation path not detected

**Fix**:
1. Open Settings Sync tab
2. Click "Add Custom Path"
3. Navigate to your EVE settings folder
4. Steam path: `~/.local/share/Steam/steamapps/compatdata/8500/pfx/drive_c/users/steamuser/AppData/Local/CCP/EVE/`

### High CPU usage

**Cause**: Too many previews at high FPS

**Fix**:
1. Reduce Preview FPS in Settings (15-20 is usually sufficient)
2. Use Low Power Mode when not actively playing
3. Disable previews entirely if only using hotkeys

### Windows not auto-arranging

**Cause**: Character names don't match

**Fix**:
1. Ensure character names in Argus match EVE window titles exactly
2. EVE window title format: "EVE - CharacterName"
3. Re-import windows with Import All

### Preview not updating

**Cause**: Window capture issue

**Fix (X11)**:
1. Click Refresh in Overview toolbar
2. Re-add the window
3. Check that `xdotool` and `wmctrl` are installed

**Fix (Wayland)**:
1. Ensure compositor supports `wlr-screenshot` or `grim`
2. Try XWayland fallback mode
3. Some compositors do not support window-level capture

**Fix (Windows)**:
1. Ensure EVE is not running elevated (Admin) while Argus is not
2. Try the "Compatibility Capture" mode in Settings

### Hotkeys not working

**Cause**: Key conflict or EVE has exclusive focus

**Fix**:
1. Check for conflicting system hotkeys
2. Try different key combinations
3. Ensure Argus has permission to grab global hotkeys

### Wayland-specific issues

**Cause**: Wayland compositors vary in protocol support

**Fix**:
1. Check compositor supports `wlroots` protocols
2. Use XWayland for EVE client if native capture fails
3. Window activation may require manual focus on some compositors

### Windows-specific issues

**Cause**: Win32 API differences, UAC elevation

**Fix**:
1. Run Argus and EVE at same privilege level
2. Disable "Game Mode" if it interferes with window detection
3. Check Windows Defender exclusions for Python/PySide6

### Logs

Check the log file for detailed error messages:
```bash
cat ~/.config/argus-overview/argus-overview.log
```

---

## Getting Help

- **GitHub Issues**: [Report bugs](https://github.com/AreteDriver/Argus_Overview/issues)
- **Discussions**: Ask questions in GitHub Discussions
- **In-Game**: Contact AreteDriver

---

**Fly safe, capsuleers! o7**
