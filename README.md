# EVE Veles Eyes v2.2 Ultimate Edition

**The Complete Professional Multi-Boxing Solution for EVE Online**

[![CI](https://github.com/AreteDriver/EVE_VelesEyes/actions/workflows/ci.yml/badge.svg)](https://github.com/AreteDriver/EVE_VelesEyes/actions)
[![Version](https://img.shields.io/badge/version-2.2.0-blue)](https://github.com/AreteDriver/EVE_VelesEyes/releases)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey)]()
[![Downloads](https://img.shields.io/github/downloads/AreteDriver/EVE_VelesEyes/total)](https://github.com/AreteDriver/EVE_VelesEyes/releases)

## Screenshots

<p align="center">
  <img src="docs/screenshots/main-window.png" alt="Main Window" width="800"/>
</p>

<details>
<summary>More Screenshots</summary>

### Team Management
![Team Management](docs/screenshots/team-management.png)

### Layout Presets
![Layouts](docs/screenshots/layout-presets.png)

### Visual Alerts
![Alerts](docs/screenshots/visual-alerts.png)

</details>

## Demo

![Demo GIF](docs/screenshots/demo.gif)

---

## Platform Support

- **Linux Version**: Full-featured native Linux application (this README)
- **Windows Version**: See [windows/README_WINDOWS.md](windows/README_WINDOWS.md) for Windows .exe

## ☕ Support Development

If you find EVE Veles Eyes useful, consider supporting development:

- **In-Game**: Send ISK donations to **AreteDriver** in EVE Online
- **Buy Me a Coffee**: [buymeacoffee.com/aretedriver](https://buymeacoffee.com/aretedriver)

Your support helps keep this project maintained and improving! o7

---

## 🌟 **v2.2 Ultimate Edition - Major UX Overhaul!**

This release focuses on **usability, automation, and polish** with 14 new features!

### ✅ **NEW in v2.2:**

#### 1. **System Tray Integration** ⭐⭐⭐⭐⭐
- Orange "V" icon in system tray
- Minimize to tray instead of closing
- Quick access menu (Show/Hide, Profiles, Settings)
- Double-click to show/hide main window
- Notifications for new characters

#### 2. **One-Click Import** ⭐⭐⭐⭐⭐
- Scan and import ALL EVE windows with one button
- Automatically detects character names from window titles
- Skip duplicates automatically
- Shows count of imported characters

#### 3. **Auto-Discovery** ⭐⭐⭐⭐⭐
- Background process scans every 5 seconds (configurable)
- Automatically adds new EVE windows when they launch
- Shows notification for each new character
- No more manual adding required!

#### 4. **Per-Character Hotkeys** ⭐⭐⭐⭐
- Bind Ctrl+1 to "Main Character", Ctrl+2 to "Scout Alt"
- Global hotkeys work even when EVE has focus
- Configure in settings.json

#### 5. **Position Lock** ⭐⭐⭐⭐
- Lock thumbnail positions to prevent accidental moves
- Lock button in toolbar + Ctrl+Shift+L hotkey
- Visual lock icon on thumbnails when locked

#### 6. **Custom Labels** ⭐⭐⭐⭐
- Right-click thumbnail → "Set Label..."
- Display "Scout", "Logi", "DPS" instead of character names
- Persists across sessions

#### 7. **Hover Effects** ⭐⭐⭐
- Opacity fade on hover (30% default, configurable)
- See through thumbnails to underlying windows
- Smooth transitions

#### 8. **Activity Indicators** ⭐⭐⭐
- Small colored dot on each thumbnail
- Green = focused, Yellow = recent activity, Gray = idle
- Quickly identify active windows

#### 9. **Session Timers** ⭐⭐⭐
- Optional "2h 15m" display on thumbnails
- Shows how long each character has been logged in
- Enable in settings

#### 10. **Themes** ⭐⭐⭐
- Dark (default), Light, EVE (orange accents)
- Configure in settings.json
- Affects all UI elements

#### 11. **Quick Minimize/Restore All** ⭐⭐⭐
- Ctrl+Shift+M: Minimize all EVE windows
- Ctrl+Shift+R: Restore all EVE windows
- Tray notifications show count

#### 12. **Hot Reload Config** ⭐⭐⭐
- Edit settings.json while running
- Click "Reload Config" in tray menu
- Changes apply without restart

#### 13. **Enhanced Context Menu** ⭐⭐⭐
- Focus Window, Minimize, Close (with confirmation)
- Set Label, Zoom Level
- Remove from Preview

#### 14. **Smart Position Inheritance** ⭐⭐⭐
- New thumbnails position relative to existing ones
- Fills right-to-left, then starts new row
- Respects screen boundaries
- Grid snapping (10px)

---

### From v2.1:

#### Layout Presets ⭐⭐⭐⭐⭐
- Save and restore complete window arrangements
- Named layouts for different activities
- One-click switching between configurations

#### Auto-Tiling & Grid Layouts ⭐⭐⭐⭐⭐
- Professional grid patterns: 2x2, 3x1, 1x3, 4x1
- Main+Sides pattern for focus gameplay
- Cascade layout for quick overview

#### Team & Character Management ⭐⭐⭐⭐⭐
- Full character database
- Account grouping
- Activity-based teams
- Auto-assignment when characters log in

#### Visual Activity Alerts ⭐⭐⭐⭐
- Red flash detection (damage/combat alerts!)
- Screen change monitoring
- Visual border flashing

#### Multi-Monitor Support ⭐⭐⭐⭐
- Auto-detect all monitors
- Per-monitor layouts
- Spread windows across monitors

#### EVE Settings Sync ⭐⭐⭐⭐⭐
- Copy keybindings between characters
- Sync UI layouts, overview settings
- Batch sync to entire team

---

## 🚀 **Quick Start**

### Installation

```bash
# One-liner install
curl -sSL https://raw.githubusercontent.com/AreteDriver/EVE_VelesEyes/main/install.sh | bash

# Or manual installation
git clone https://github.com/AreteDriver/EVE_VelesEyes
cd EVE_VelesEyes
./install.sh

# Run
~/eve-veles-eyes/run.sh
```

### First-Time Setup

1. **Main Tab**: Add EVE windows, minimize inactive to save GPU
2. **Characters & Teams Tab**: Add your characters, create teams
3. **Layouts Tab**: Save your window arrangements
4. **Settings Sync Tab**: Copy settings from your main to alts

---

## 📋 **Features Overview**

### From v2.0:
- ✅ Low-latency multi-window previews
- ✅ Draggable, resizable preview frames
- ✅ Global hotkeys (Ctrl+Alt+1-9)
- ✅ Profile management
- ✅ Adjustable refresh rates (1-60 FPS)
- ✅ Always-on-top mode
- ✅ Click-to-activate
- ✅ Minimize inactive windows (50-80% GPU savings!)
- ✅ Threaded capture system (no UI lag!)

### NEW in v2.1:
- ✅ Layout presets with quick-switch
- ✅ Auto-grid tiling (6+ patterns)
- ✅ Character & team management
- ✅ Visual activity alerts
- ✅ Multi-monitor support
- ✅ EVE settings synchronization

---

## 💡 **Usage Examples**

### Mining Fleet
```
1. Create "Mining Team" with Orca + 3 miners
2. Arrange in 2x2 grid
3. Save as "Mining Layout"
4. Enable visual alerts for danger
5. Minimize inactive miners to save GPU
```

### PvP Fleet  
```
1. Create "PvP Team" with FC + Logi + DPS
2. Use Main+Sides layout (FC center, others on side)
3. Link to "PvP Layout"
4. Enable red flash alerts for all
5. Quick-switch with Ctrl+Tab
```

### Multi-Account Trading
```
1. Create "Market Team" with trader alts
2. Use 3x1 horizontal layout
3. Sync overview settings from main to all alts
4. Monitor all markets simultaneously
```

---

## ⚙️ **System Requirements**

- **OS**: Linux (X11 or Wayland/XWayland)
- **Python**: 3.8 or higher
- **System Tools**: wmctrl, xdotool, ImageMagick, x11-apps

### Dependencies
```bash
# Ubuntu/Debian
sudo apt-get install wmctrl xdotool imagemagick x11-apps python3-pip

# Fedora/RHEL
sudo dnf install wmctrl xdotool ImageMagick xorg-x11-apps python3-pip

# Arch Linux
sudo pacman -S wmctrl xdotool imagemagick xorg-xwd python-pip
```

---

## 📖 **Documentation**

- `WHATS_NEW.md` - Complete feature changelog
- `QUICKSTART.md` - Get started in 5 minutes
- `USER_GUIDE.md` - Comprehensive user manual
- `INTEGRATION_GUIDE.md` - Developer integration guide

---

## 🎯 **Performance**

- **Memory**: ~50-100 MB per preview
- **CPU**: 2-5% per preview at 30 FPS
- **GPU Savings**: 50-80% with minimize inactive feature
- **Capture Latency**: <50ms with threaded system

---

## 🛠️ **Troubleshooting**

**Characters not found for settings sync?**
→ Add custom EVE installation path in Settings Sync tab

**Alerts not triggering?**
→ Adjust sensitivity thresholds in Settings

**Windows not auto-arranging?**
→ Ensure character names match EVE window titles

**High CPU usage?**
→ Reduce refresh rate or number of active previews

---

## 🤝 **Contributing**

Contributions welcome! This is a community project.

- Feature requests
- Bug reports
- Code improvements
- Documentation
- Translations

---

## 📄 **License**

MIT License - See LICENSE file

---

## 🎮 **Credits**

- Inspired by EVE-O-Preview for Windows
- Built for the EVE Online community
- Special thanks to all contributors and testers

---

## 💬 **Support**

- Check documentation
- Review troubleshooting section
- Check logs: `~/.config/eve-veles-eyes/eve-veles-eyes.log`
- Report issues with full details

---

**Fly safe, capsuleers! o7**

*EVE Veles Eyes v2.2 Ultimate Edition*
*The Complete Professional Solution for Linux Multi-Boxing*
