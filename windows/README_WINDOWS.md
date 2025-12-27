# EVE Veles Eyes v2.2 - Windows Edition

Professional multi-boxing tool for EVE Online on Windows.

## ✨ Features

- **Real-time Window Preview**: 30 FPS capture of all EVE windows with async processing
- **Character Management**: Organize characters, create teams, track accounts
- **EVE Folder Scanning**: Import ALL characters from EVE installation (even logged off)
- **Smart Layouts**: 7 grid patterns (2x2, 3x1, Main+Sides, Cascade, etc.)
- **Alert Detection**: Visual alerts for red flashes (damage) and screen changes
- **Settings Sync**: Synchronize EVE settings between characters with backup
- **Global Hotkeys**: Control windows with customizable hotkey bindings
- **System Tray**: Minimize to tray, quick access menu
- **Auto-Discovery**: Automatically detect new EVE clients
- **Themes**: Dark, Light, and EVE themes
- **Multi-Monitor Support**: Works across multiple displays

## 📋 Requirements

- **Windows 10/11** (64-bit)
- **Python 3.10+** (for development) or use pre-built .exe
- **EVE Online** installed

## 🚀 Quick Start (Pre-built .exe)

### Option 1: Download Release

1. Download `EVE-Veles-Eyes-v2.2-Windows.exe` from [Releases](https://github.com/AreteDriver/EVE_VelesEyes/releases)
2. Run the executable
3. That's it! No installation needed.

### Option 2: Build from Source

```cmd
# Clone repository
git clone https://github.com/AreteDriver/EVE_VelesEyes.git
cd EVE_VelesEyes/windows

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python src/main.py
```

## 🔨 Building .exe

To create your own standalone executable:

```cmd
# Install PyInstaller
pip install pyinstaller

# Build .exe
pyinstaller build.spec

# Executable will be in dist/EVE-Overview-Pro.exe
```

## 📖 Usage Guide

### 1. Main Tab - Window Preview
- Click **"Add Window"** to add EVE client windows
- Preview updates at 30 FPS with alert detection
- Red borders appear when damage is taken
- Right-click windows for options (Minimize, Remove, etc.)

### 2. Characters & Teams
- Add your EVE characters with **"Add Character"**
- Assign roles: Miner, Scout, DPS, Logi, etc.
- Create teams and link them to layouts
- Track which characters are online

### 3. Layouts
- **Save Current**: Save current window positions as a preset
- **Apply Pattern**: Apply grid patterns (2x2, 3x1, etc.)
- **Visual Preview**: See layout before applying
- Multi-monitor support included

### 4. Settings Sync
- **Scan**: Find all EVE character settings automatically
- **Select Source**: Choose character with desired settings
- **Select Targets**: Choose characters to sync to
- **Preview**: See what files will be synced
- **Sync**: Copy settings with automatic backup

### 5. Settings
- **General**: Startup options, notifications
- **Performance**: Refresh rate, worker threads, caching
- **Alerts**: Configure red flash detection thresholds
- **Hotkeys**: Customize global hotkey bindings
- **Appearance**: Theme, font size, colors
- **Advanced**: Logging, export/import settings

## ⌨️ Default Hotkeys

- `Ctrl+Alt+1-9`: Activate window 1-9
- `Ctrl+Alt+M`: Minimize all windows
- `Ctrl+Alt+R`: Restore all windows
- `Ctrl+Alt+F5`: Refresh all previews
- `Ctrl+Alt+]`: Next layout
- `Ctrl+Alt+[`: Previous layout
- `Ctrl+Alt+A`: Toggle alerts
- `Ctrl+Alt+T`: Toggle always on top

*All hotkeys are customizable in Settings > Hotkeys*

## 📁 Configuration

Settings are stored in:
```
%LOCALAPPDATA%\eve-overview-pro\
├── settings.json          # Application settings
├── characters.json        # Character database
├── teams.json            # Team definitions
└── layout_presets.json   # Saved layouts
```

## 🐛 Troubleshooting

### Windows Defender Warning
If Windows Defender blocks the .exe, you may need to add an exception:
1. Open Windows Security
2. Virus & threat protection > Manage settings
3. Add exclusion > Add folder > Select EVE-Overview-Pro folder

### No Windows Detected
- Make sure EVE Online clients are running
- Run EVE-Overview-Pro as Administrator if needed
- Check that windows are not minimized

### Hotkeys Not Working
- Check for conflicts with other applications
- Verify hotkey syntax in Settings
- Some keys may be reserved by Windows

### Performance Issues
- Reduce refresh rate in Settings > Performance
- Lower capture quality setting
- Reduce number of preview windows
- Close unused EVE clients

## 🔧 Development

### Project Structure
```
windows/
├── src/
│   └── eve_overview_pro/
│       ├── core/              # Windows-specific implementations
│       │   ├── window_capture_threaded.py  # Win32 API capture
│       │   ├── layout_manager.py           # Win32 window positioning
│       │   ├── hotkey_manager.py           # RegisterHotKey API
│       │   ├── character_manager.py        # Cross-platform
│       │   ├── alert_detector.py           # Cross-platform
│       │   └── eve_settings_sync.py        # Cross-platform
│       ├── ui/                # PySide6 GUI (cross-platform)
│       └── utils/             # Helper utilities
├── requirements.txt
├── build.spec                 # PyInstaller spec
└── README_WINDOWS.md         # This file
```

### Key Windows APIs Used
- **Win32 API**: Window capture with PrintWindow
- **GDI**: Bitmap manipulation
- **RegisterHotKey**: Global hotkey support
- **SetWindowPos**: Window positioning
- **EnumWindows**: Window enumeration

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test on Windows 10 and 11
4. Submit pull request

## ☕ Support Development

If you find EVE Overview Pro useful, consider supporting development:

**[Buy Me a Coffee ☕](https://buymeacoffee.com/aretedriver)**

Your support helps keep this project maintained and improving!

## 📜 License

MIT License - See LICENSE file for details

## 🔗 Links

- **GitHub**: https://github.com/AreteDriver/eve-overview-pro
- **Linux Version**: See main README.md in root directory
- **Issues**: https://github.com/AreteDriver/eve-overview-pro/issues
- **Donate**: https://buymeacoffee.com/aretedriver

## 📝 Version History

### v2.1 (2025)
- ✅ Complete Windows implementation
- ✅ All 5 tabs fully functional
- ✅ Win32 API integration
- ✅ Global hotkeys support
- ✅ Multi-monitor support
- ✅ Standalone .exe builds

## 🙏 Credits

- **EVE Online** by CCP Games
- Built with **PySide6** (Qt for Python)
- Uses **pywin32** for Windows API access
- Developed with ❤️ for the EVE community

---

**Made with ❤️ by AreteDriver** | [Support on Buy Me a Coffee](https://buymeacoffee.com/aretedriver)
