# Screenshots Needed

Capture these with high quality (1920x1080 or higher):

## Required Screenshots

1. **main-window.png** - Main UI with 4+ EVE previews visible
   - Show the main tab with multiple thumbnail previews
   - Ensure the dark theme is visible
   - Include the toolbar and tab bar

2. **team-management.png** - Characters & Teams tab with groups
   - Show character list with roles assigned
   - Display at least one team created
   - Show the drag-and-drop interface

3. **layout-presets.png** - Layout tab showing saved presets
   - Display grid pattern options
   - Show saved layout list
   - Include the preview area

4. **visual-alerts.png** - Red flash alert in action
   - Show a thumbnail with alert border flashing
   - Capture the activity indicator dot
   - If possible, show the notification

5. **settings-sync.png** - EVE settings sync dialog
   - Show character selection
   - Display source and target selection
   - Include the sync button

6. **system-tray.png** - Tray menu expanded
   - Show the orange "V" icon in system tray
   - Expand the context menu
   - Show all menu options

## GIF Demo Instructions

For the demo.gif, capture these steps in sequence:

1. Launch the application
2. Auto-detect EVE windows (or show import button)
3. Show thumbnails appearing
4. Switch between clients via clicking
5. Show a hotkey switch (if visible)
6. Show alert triggering (optional)

### Recommended Tools

**Linux Screenshot:**
```bash
# Using GNOME Screenshot
gnome-screenshot -i

# Using Flameshot
flameshot gui

# Using scrot
scrot -s
```

**GIF Recording:**
```bash
# Using Peek (recommended)
sudo apt install peek
peek

# Using Kazam
sudo apt install kazam
kazam

# Using gifski + ffmpeg
ffmpeg -i input.mp4 -vf "fps=10,scale=800:-1" output.gif
```

### Image Optimization

Before committing, optimize images:

```bash
# Install optipng
sudo apt install optipng

# Optimize all PNGs
for f in *.png; do optipng -o5 "$f"; done

# For GIFs, use gifsicle
sudo apt install gifsicle
gifsicle -O3 --lossy=80 demo.gif -o demo.gif
```

## Naming Convention

- Use lowercase with hyphens: `main-window.png`
- Keep names descriptive but short
- Use `.png` for screenshots, `.gif` for animations

## Quality Guidelines

- Minimum resolution: 1920x1080
- Maximum file size: 500KB for PNGs, 2MB for GIFs
- Dark theme preferred (matches README)
- Clean desktop background
- No personal information visible
