# EVE Veles Eyes v2.2 Ultimate Edition - Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Extract the package
tar -xzf eve-veles-eyes-v2.2.tar.gz
cd eve-veles-eyes

# 2. Run the installer
./install.sh

# 3. Launch the application
~/eve-veles-eyes/run.sh
# OR find it in your applications menu!
```

---

## First-Time Setup

### Step 1: Launch Your EVE Clients
Log in to your EVE characters as normal.

### Step 2: Start EVE Veles Eyes
- Run: `~/eve-veles-eyes/run.sh`
- Or click the desktop icon

### Step 3: Characters & Teams Tab
- Add your characters (even offline ones!)
- Group them by account (3 per account)
- Create teams for activities (Mining, PvP, etc.)

### Step 4: Main Tab
- Click "Refresh Window List"
- Add EVE windows to previews
- Try "Minimize Inactive" to save GPU!

### Step 5: Layouts Tab
- Arrange your windows
- Try "2x2 Grid" or "Main + Sides"
- Click "Save Layout" with a name

### Step 6: Settings Sync Tab (HUGE TIME SAVER!)
- Click "Scan EVE Settings"
- Select your MAIN character as source
- Select target characters (or whole team)
- Click "Sync Settings" - Done in 6 seconds!

---

## Top Features (v2.2)

### System Tray Integration
- Orange "V" icon in system tray
- Minimize to tray instead of closing
- Quick access to profiles and settings

### One-Click Import
- Scan and import ALL EVE windows with one button
- Automatically detects character names

### Auto-Discovery
- Background process scans every 5 seconds
- Automatically adds new EVE windows when they launch

### Per-Character Hotkeys
- Bind Ctrl+1 to "Main Character", Ctrl+2 to "Scout Alt"
- Global hotkeys work even when EVE has focus

### Layout Presets
- Save window arrangements
- Quick-switch between setups
- Different layouts for different activities

### Auto-Grid Patterns
- 2x2, 3x1, 1x3, 4x1 grids
- Main + Sides pattern
- Cascade style
- One-click organization!

### Character & Team Management
- Full character database
- Activity-based teams
- Auto-assignment when logging in
- Link teams to layouts

### Visual Activity Alerts
- Red flash detection (combat!)
- Screen change monitoring
- Border flashing on alerts

### Multi-Monitor Support
- Auto-detect all monitors
- Per-monitor layouts
- Spread windows across screens

### EVE Settings Sync
- Copy ALL settings between chars
- Keybindings, UI, overviews
- 6 seconds vs 6 hours manual!

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Tab | Cycle to next window |
| Ctrl+Shift+Tab | Cycle to previous window |
| Ctrl+Alt+1-9 | Jump to specific window |
| Ctrl+Shift+L | Toggle position lock |
| Ctrl+Shift+M | Minimize all EVE windows |
| Ctrl+Shift+R | Restore all EVE windows |

### Mouse Actions
- **Left-click preview** → Activate EVE window
- **Right-click preview** → Context menu
- **Drag title bar** → Move preview
- **Drag corner** → Resize preview

---

## Pro Tips

### GPU Savings
- Use "Minimize Inactive" to save 50-80% GPU
- Only active window renders at full FPS
- Perfect for multi-boxing on older hardware

### Best Workflows
- Create one layout per activity
- Link teams to layouts
- Sync settings from MAIN to all alts once
- Enable alerts for safety

### Performance
- Lower refresh rate = less CPU
- Smaller previews = faster capture
- Threaded capture is automatic

### Organization
- Name characters by role
- Group by account
- Create teams for operations
- Save layouts with descriptive names

---

## Example Workflows

### Mining Fleet
1. Create "Mining Team" (Orca + 3 miners)
2. Use 2x2 grid layout
3. Save as "Mining Layout"
4. Enable visual alerts
5. Minimize inactive to save GPU

### PvP Operations
1. Create "PvP Team" (FC + Logi + Scouts)
2. Use Main + Sides layout (FC big, others small)
3. Link to team
4. Red flash alerts on all
5. Quick Ctrl+Tab cycling

### Market Trading
1. Sync overview settings from main to all traders
2. Use 3x1 horizontal layout
3. Monitor all market hubs
4. One-click switching

---

## Troubleshooting

**Characters not found for sync?**
→ Add custom EVE path in Settings Sync tab

**Alerts not triggering?**
→ Adjust sensitivity in Settings tab

**Windows not auto-arranging?**
→ Check character names match EVE window titles

**High CPU usage?**
→ Reduce refresh rate or number of previews

**Check logs:**
```bash
~/.config/eve-veles-eyes/eve-veles-eyes.log
```

---

## Documentation

| File | Description |
|------|-------------|
| README.md | Complete user guide |
| WHATS_NEW.md | All new features explained |
| PACKAGE_INFO.md | Technical architecture |
| LICENSE | MIT License |

---

## Support

- **In-Game**: Send ISK to **AreteDriver**
- **Buy Me a Coffee**: [buymeacoffee.com/aretedriver](https://buymeacoffee.com/aretedriver)

---

**Fly safe, capsuleers! o7**

*EVE Veles Eyes v2.2 Ultimate Edition*
