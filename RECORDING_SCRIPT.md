# Argus Overview - 90 Second Demo Recording Script

## Recording Setup
- **Tool:** `peek` (install: `sudo apt install peek`)
- **Resolution:** 1920x1080 (full screen)
- **FPS:** 20
- **Duration:** 90 seconds
- **Output:** `demo.gif` (target <10MB)

## Pre-Recording Checklist
- [ ] 4+ EVE Online clients running and logged in
- [ ] Argus Overview closed (will launch during recording)
- [ ] Desktop clear of clutter
- [ ] Recording area selected in peek

---

## Shot-by-Shot Script (90 seconds)

### 0:00-0:15 | Launch & Initial View (15s)
**Action:**
1. Launch Argus Overview from terminal or desktop
2. Main window appears with empty preview grid
3. Show clean, professional dark-themed interface
4. Hover over toolbar buttons briefly

**Key Visual:** Professional GUI, dark theme, empty state ready for windows

---

### 0:15-0:30 | Auto-Detect & Add Windows (15s)
**Action:**
1. Click **"Add Window"** button
2. Dialog appears showing list of detected EVE clients
3. Shows 4 EVE clients auto-detected with character names
4. Click **"Add Selected"** or **"Add All"**
5. Watch preview frames populate in real-time

**Key Visual:** Automatic character detection, instant window capture

---

### 0:30-0:45 | Apply Grid Layout (15s)
**Action:**
1. Switch to **"Layouts"** tab (click tab at top)
2. Select **2x2 Grid** pattern from list
3. Click **"Apply Layout"** button
4. **Camera switches to show actual EVE windows on desktop**
5. Watch all 4 EVE windows automatically tile into perfect 2x2 grid
6. Windows move and resize instantly (xdotool magic)

**Key Visual:** Instant auto-tiling, professional window management

---

### 0:45-0:60 | Character & Team Management (15s)
**Action:**
1. Switch to **"Characters & Teams"** tab
2. Show character table with 4 characters listed
3. Shows: Name, Account, Role, Status columns
4. **Right panel:** Team Builder
5. Type team name: "Mining Fleet"
6. Drag 1 Orca + 3 Miners into team list
7. Select layout: "Main + Sides" from dropdown

**Key Visual:** Drag-drop team building, professional database UI

---

### 0:75-0:90 | Team Quick Switch (15s)
**Action:**
1. Click **"Apply Team Layout"** button
2. **Camera switches to desktop again**
3. Watch windows automatically rearrange:
   - Orca takes large center position
   - 3 Miners tile on the side
4. **Camera back to app**
5. Show status bar: "Layout applied: Main + Sides"
6. End with professional, polished main interface view

**Key Visual:** Team-based layout system, instant window orchestration

---

## Post-Recording

### Optimize GIF
```bash
# If using peek, output is already optimized
# If file is >10MB, reduce FPS or scale down:
ffmpeg -i demo.gif -vf "fps=15,scale=1280:-1:flags=lanczos" -y demo_optimized.gif

# Check size
ls -lh demo.gif
```

### Add to Repository
```bash
# Copy to repo root
cp demo.gif /home/arete/Argus_Overview/demo.gif

# Update README.md (add at top after title)
# ![Demo](demo.gif)

git add demo.gif README.md
git commit -m "Add 90-second capability demo GIF"
git push origin main
```

---

## Recording Tips

**Smooth Mouse Movement:**
- Move cursor deliberately and smoothly
- Pause briefly on buttons before clicking (1 second)
- No erratic movements

**Timing:**
- Practice the sequence 2-3 times before recording
- Use a timer to stay under 90 seconds
- Actions should feel deliberate but not rushed

**Visual Quality:**
- Ensure EVE clients are showing interesting scenes (space, asteroids, ships)
- Make sure character names are visible (but can obscure if needed for privacy)
- Window borders and titles should be clear

**What NOT to Show:**
- Don't fumble with UI
- Don't show error messages or bugs
- Don't include unnecessary waiting/loading
- No narration needed - let capability speak for itself

---

## Alternative: Split Recording
If 90 seconds is too tight, record in segments and merge:

```bash
# Record 3 separate clips
# Merge with ffmpeg
ffmpeg -i part1.gif -i part2.gif -i part3.gif -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1[outv]" -map "[outv]" demo.gif
```

---

**Goal:** Viewer watches and thinks "This is professional, powerful, and exactly what I need for multi-boxing."
