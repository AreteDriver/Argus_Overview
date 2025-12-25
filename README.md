# EVE Overview Pro v2.1 Ultimate Edition

**The Complete Professional Multi-Boxing Solution for EVE Online**

![Version](https://img.shields.io/badge/version-2.1.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Platform](https://img.shields.io/badge/platform-Linux%20|%20Windows-lightgrey)

## 💻 Platform Support

- **🐧 Linux Version**: Full-featured native Linux application (this README)
- **🪟 Windows Version**: See [windows/README_WINDOWS.md](windows/README_WINDOWS.md) for Windows .exe

## ☕ Support Development

If you find EVE Overview Pro useful, consider supporting development:

- **In-Game**: Send ISK donations to **AreteDriver** in EVE Online
- **Buy Me a Coffee**: [buymeacoffee.com/aretedriver](https://buymeacoffee.com/aretedriver)

Your support helps keep this project maintained and improving! o7

---

## 🌟 **v2.1 Ultimate Edition - 6 Major Features!**

This release transforms EVE Overview Pro into the **most powerful multi-boxing tool** available for EVE Online on Linux.

### ✅ **NEW in v2.1:**

#### 1. **Layout Presets** ⭐⭐⭐⭐⭐
- Save and restore complete window arrangements
- Named layouts for different activities (Mining, PvP, Market)
- One-click switching between configurations
- Per-layout performance settings

#### 2. **Auto-Tiling & Grid Layouts** ⭐⭐⭐⭐⭐
- Professional grid patterns: 2x2, 3x1, 1x3, 4x1
- Main+Sides pattern for focus gameplay
- Cascade layout for quick overview
- Configurable spacing and monitor selection
- Fill screen/monitor efficiently

#### 3. **Team & Character Management** ⭐⭐⭐⭐⭐
- Full character database (even offline characters!)
- Account grouping (3 characters per account)
- Activity-based teams (Mining, PvP, Exploration)
- Drag-and-drop team builder
- Auto-assignment when characters log in
- Link teams to layouts

#### 4. **Visual Activity Alerts** ⭐⭐⭐⭐
- Red flash detection (damage/combat alerts!)
- Screen change monitoring
- Configurable thresholds
- Visual border flashing
- Sound alerts (optional)

#### 5. **Multi-Monitor Support** ⭐⭐⭐⭐
- Auto-detect all monitors
- Per-monitor layouts
- "Send to Monitor X" command
- Spread windows across monitors
- Remember monitor assignments

#### 6. **EVE Settings Sync** ⭐⭐⭐⭐⭐
- Copy keybindings between characters
- Sync UI layouts
- Copy overview settings  
- Sync all game settings
- Batch sync to entire team
- Automatic backups before sync

---

## 🚀 **Quick Start**

### Installation

```bash
# Extract and install
tar -xzf eve-overview-pro-v2.1-ultimate.tar.gz
cd eve-overview-pro-v2.1-complete
./install.sh

# Run
~/eve-overview-pro/run.sh
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
- Check logs: `~/.config/eve-overview-pro/eve-overview-pro.log`
- Report issues with full details

---

**Fly safe, capsuleers! o7**

*EVE Overview Pro v2.1 Ultimate Edition*
*The Complete Professional Solution for Linux Multi-Boxing*
