# Argus Overview - Professional Multi-Boxing for EVE Online on Linux

## Forum Post Draft

*For posting to r/Eve, EVE Forums, or other community platforms*

---

**Title:** [Linux] Argus Overview v2.8 - The Complete Multi-Boxing Solution

---

**Post:**

Fellow capsuleers,

I'm excited to share **Argus Overview**, a native Linux application for managing multiple EVE Online clients. After years of using various solutions (and envying Windows users with EVE-O-Preview), I built something purpose-designed for our platform.

### What It Does

Argus Overview provides live window previews, team management, and hotkey controls for multiboxing EVE Online on Linux. Think of it as a command center for your fleet.

**Screenshot:** [Main window with 4 EVE previews in 2x2 grid]

---

### Key Features

**NEW in v2.8:**
- **Preview Filter** - Type to instantly filter windows by character name
- **Keyboard Control** - Press 1-9 to activate windows by position

**Core Features:**
- Live window previews at configurable FPS (1-60)
- Layout presets (2x2, 3x1, Main+Sides, custom)
- One-click import of all EVE windows
- Auto-discovery of new EVE clients
- Per-character global hotkeys (Ctrl+1 = character 1)
- Visual activity alerts (red flash detection for combat)
- EVE Settings Sync - copy ALL settings between characters in 30 seconds
- System tray with minimize-to-tray
- Multi-monitor support
- Dark, Light, and EVE themes

---

### Performance

Argus is designed for minimal resource impact:

- ~50MB memory per preview
- 2-5% CPU at 30 FPS
- **50-80% GPU savings** with "Minimize Inactive" feature
- Alert detection optimized to <1ms (previously 42ms)

The v2.7 update fixed a memory leak that was causing ~600MB/hour of creep. If you tried an earlier version and had issues, give it another shot.

---

### Installation

**Easiest (pipx):**
```bash
pipx install argus-overview
argus-overview
```

**AppImage:**
Download from [GitHub Releases](https://github.com/AreteDriver/Argus_Overview/releases)

**Flatpak:**
Available via Flathub (pending review)

---

### Use Cases

**Mining Fleet:**
Create "Mining Team" with your Orca + 3 miners. Set to 2x2 grid. Enable alerts for bumping or ganks.

**PvP Operations:**
FC in center, scouts and logi on sides. Red flash alerts let you react instantly to combat on any client. Press 5 to jump to your tackle alt when they get a point.

**AFK Activities:**
Keep one main window visible, others minimized. "Minimize Inactive" saves GPU while you do your thing. Activity indicators show status at a glance.

---

### Why Not Just Use...?

- **ISBoxer**: Windows only, not natively supported on Linux
- **EVE-O-Preview**: Windows only
- **Virtual desktops**: No live previews, no alerts, no hotkey cycling
- **Manual window management**: Life's too short

Argus is MIT-licensed open source. No account linking, no third-party servers, no shenanigans.

---

### Technical Details

Built with:
- Python 3.8+ / PySide6 (Qt)
- Native X11 window management (python-xlib, wmctrl, xdotool)
- 1,500+ automated tests, 96% code coverage

Works with:
- Steam (native and Proton)
- Lutris
- Native launchers
- Any X11/Wayland desktop

---

### FAQ

**Q: Does this violate EULA?**
A: No. Argus only manages windows and relays keypresses - the same as alt-tabbing or using system hotkeys. It does not automate gameplay, inject inputs, or interact with the game client.

**Q: Wayland support?**
A: Partial. Best experience is on X11. Some Wayland compositors work via XWayland.

**Q: Why is it called "Argus"?**
A: In Greek mythology, Argus Panoptes was the all-seeing giant with a hundred eyes. Seemed fitting for a multi-window observer.

---

### Links

- **GitHub:** https://github.com/AreteDriver/Argus_Overview
- **Documentation:** https://github.com/AreteDriver/Argus_Overview/wiki
- **Issues/Feature Requests:** https://github.com/AreteDriver/Argus_Overview/issues

---

### Support

If Argus saves you time or makes multiboxing on Linux bearable:
- Star the repo on GitHub
- In-game ISK to **AreteDriver**
- [Buy Me a Coffee](https://buymeacoffee.com/aretedriver)

---

Fly safe,
AreteDriver

---

## Suggested Images

1. **Main window screenshot** - 2x2 layout with 4 EVE windows
2. **Settings panel** - showing hotkey configuration
3. **System tray** - showing the orange "V" icon
4. **Before/after GPU usage** - showing resource savings

## Tags (for Reddit/forums)

`linux` `multiboxing` `tool` `open-source` `window-management`

## Cross-Post Locations

- [ ] r/Eve
- [ ] EVE Online Forums > General Discussion
- [ ] EVE Online Forums > Third Party Developers
- [ ] r/linux_gaming
- [ ] Linux gaming Discord servers
