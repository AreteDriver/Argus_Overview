# [Tool] EVE Veles Eyes - Professional Multi-Boxing for Linux (and Windows!)

**TL;DR**: I built EVE-O Preview for Linux, but better. Free, open source, MIT licensed.

---

## What is it?

EVE Veles Eyes is a multi-window preview and management tool for EVE Online, designed specifically for Linux (with Windows support included).

Think EVE-O Preview, but native Linux with even more features.

---

## Features

**Core Features:**
- Live Previews - Real-time thumbnails of all your EVE clients (up to 30 FPS)
- Global Hotkeys - Per-character hotkeys (Ctrl+1 = Main, Ctrl+2 = Scout, etc.)
- Auto-Tiling - 6 grid patterns for instant window arrangement
- Team Management - Group characters by activity (Mining, PvP, Market)
- Visual Alerts - Red flash detection for combat/damage warnings
- Settings Sync - Copy keybinds/overview from main to all alts in seconds
- Layout Presets - Save and restore window arrangements

**v2.2 New Features:**
- System Tray - Minimize to tray, quick access menu
- One-Click Import - Scan and add all EVE windows instantly
- Auto-Discovery - Automatically detects new EVE clients when they launch
- Per-Character Hotkeys - Bind specific keys to specific characters
- Hover Effects - Transparency on hover to see through thumbnails
- Activity Indicators - Green/Yellow/Gray dots show window state
- Session Timers - Track how long each character has been logged in
- Themes - Dark, Light, and EVE (orange) themes

---

## Screenshots

[Main Window - TODO: Add actual screenshot link]

[Team Management - TODO: Add actual screenshot link]

[Visual Alerts - TODO: Add actual screenshot link]

---

## Installation

```bash
# One-liner install
curl -sSL https://raw.githubusercontent.com/AreteDriver/EVE_VelesEyes/main/install.sh | bash

# Or manual
git clone https://github.com/AreteDriver/EVE_VelesEyes
cd EVE_VelesEyes && ./install.sh

# Run
~/eve-veles-eyes/run.sh
```

**Requirements:**
- Linux with X11 (Wayland works via XWayland)
- Python 3.8+
- wmctrl, xdotool, ImageMagick

**Windows users:** Check the releases page for the Windows .exe build.

---

## Is it EULA legal?

Yes. It's the same type of tool as EVE-O Preview, which CCP has explicitly allowed. It only:
- Shows preview thumbnails of your EVE windows
- Switches focus between windows
- Manages window positions

**No input broadcasting. No automation. No macros.**

---

## Why Linux?

Because there was nothing like EVE-O Preview for Linux. Wine users had to alt-tab like animals. Not anymore.

If you run EVE through Lutris, Steam Proton, or native Wine, this tool works great.

---

## Performance

- Memory: ~50-100 MB total (not per window)
- CPU: 2-5% per preview at 30 FPS
- GPU Savings: 50-80% with "minimize inactive" feature
- Capture Latency: <50ms with threaded system

---

## Comparison to EVE-O Preview

| Feature | EVE-O Preview | EVE Veles Eyes |
|---------|---------------|----------------|
| Platform | Windows only | Linux + Windows |
| System Tray | Yes | Yes |
| Auto-Discovery | No | Yes |
| Per-Char Hotkeys | Limited | Full support |
| Layout Presets | Basic | Advanced |
| Team Management | No | Yes |
| EVE Settings Sync | No | Yes |
| Grid Patterns | Basic | 6+ patterns |
| Visual Alerts | Basic | Advanced |
| Hover Effects | No | Yes |
| Session Timers | No | Yes |
| Themes | No | 3 themes |
| Open Source | No | Yes (MIT) |
| Price | Free | Free |

---

## Links

- **GitHub**: https://github.com/AreteDriver/EVE_VelesEyes
- **Releases**: https://github.com/AreteDriver/EVE_VelesEyes/releases
- **Issues**: https://github.com/AreteDriver/EVE_VelesEyes/issues

---

## Support Development

If you find this useful:
- **In-game ISK**: Send to **AreteDriver**
- **Buy Me a Coffee**: https://buymeacoffee.com/aretedriver

---

## Roadmap

- [ ] Wayland native support (currently works via XWayland)
- [ ] Cloud profile sync
- [ ] More layout patterns
- [ ] Plugin system

---

Fly safe, capsuleers! o7

---

*P.S. - If you have feature requests or find bugs, please open an issue on GitHub. Pull requests welcome!*
