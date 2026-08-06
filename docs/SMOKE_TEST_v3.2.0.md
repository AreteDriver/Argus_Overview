# v3.2.0 Smoke Test Plan

A structured walkthrough for the Intel-Aware Edition. Run with EVE Online open
and at least 2-3 characters logged in. Every test below has an explicit "do X,
expect Y" so a missing or broken behavior is unambiguous.

Total time budget: ~30 minutes for the happy path, ~60 minutes if you hit edge
cases. File issues against this checklist as you go.

---

## Setup (one-time, ~5 min)

1. Pull and run from main:
   ```bash
   cd ~/projects/Argus_Overview
   git pull
   ./run.sh
   ```
2. **Settings → Intel** — verify all four controls render:
   - "Show threat chrome on previews" (master toggle, on)
   - "Track per-character location" (on)
   - "Max jumps for tinting" (default 1, range 0-5)
   - Replay strip count summary
3. **Overview tab** — click "Import Windows" or use One-Click Import.
   Expect: thumbnails appear for every running EVE client, each with its
   character name in the info label.
4. **Status dock** — verify it appears below the preview grid with one
   chip per imported character. Each chip shows:
   - Colored-initials avatar (e.g., "AB" for AreteBoss)
   - Character name in bold
   - "—" in the system label slot
5. **Per-character accent border (PR #70)** — each preview frame should
   render with a thin 2px border in the same color as the chip avatar.
   Different characters → different border colors.

If any of the above is missing, stop here — the import path is broken
and nothing downstream will work.

---

## Test 1 — Per-character accent border at small grid sizes (PR #70)

**Why**: Accent border was added so identity is glanceable when the grid
gets cramped.

1. Resize the Argus window so previews shrink to ~150x110.
2. **Expect**: each frame's accent border is still visible. Different
   characters render in distinct colors.
3. Restart Argus, re-import.
4. **Expect**: same character → same color as before. (PR #79 fix —
   if colors swap on restart, that's a regression.)

---

## Test 2 — Per-character system tracking (PR #65)

**Why**: Each character's system label should update independently from
their own EVE Local channel log.

1. Pick one of your characters and jump to a different system in EVE.
2. Wait up to 2 seconds (tracker poll interval).
3. **Expect**: that character's chip system label updates from "—" to
   the new system name. Other characters' labels do NOT change.
4. Jump again to a third system.
5. **Expect**: chip updates again to the new system name.
6. Repeat with another character.
7. **Expect**: each character tracks independently.

**If broken**: most likely the EVE log path detection failed. Check
`~/.eve/logs/Chatlogs/` for `Local_*.txt` files dated today. If those
exist but tracking doesn't update, file an issue with the directory
path.

---

## Test 3 — Threat chrome master toggle (PR #78, your "make it optional" ask)

**Why**: Verify the toggle actually suppresses everything.

1. Click "Test Alert" in the Intel tab. (This fires a WARNING report.)
2. **Expect (chrome ON)**: every preview frame's border tints orange
   for ~30s, every chip dot lights up orange.
3. **Settings → Intel → uncheck "Show threat chrome on previews"**.
4. **Expect**: all active threat tints clear immediately. No frame
   borders, no chip dots.
5. Click "Test Alert" again with chrome OFF.
6. **Expect**: NOTHING visual changes on previews or chips. But the
   intel report should still appear in the Intel tab's log.
7. Re-enable the toggle.
8. **Expect**: future test alerts tint normally again.

---

## Test 4 — Same-system threat fan-out (PR #66)

**Why**: With per-character tracking on, only the matching character
should tint.

1. Move character A to system X, character B to system Y. Wait for
   chip labels to update.
2. Edit `intel/parser.py` test injection or use the Python console (see
   "Manual report injection" below) to fire a DANGER report **for
   system X**.
3. **Expect**: only character A's frame border + chip dot tint red.
   Character B stays calm.
4. **Expect**: character A's frame pulses (border thickens 3→5px for
   ~600ms then settles).
5. **Expect**: tint decays to invisible over ~30s.

---

## Test 5 — Jumps-from fan-out + "+Nj" badges (PR #67, #68, #71)

**Why**: Adjacent characters should also tint at reduced intensity with
a distance badge.

1. With characters in two different systems that are 1 jump apart
   (use jump info in EVE map):
2. Fire a DANGER report for the system character A is in.
3. **Expect**:
   - Character A's frame: full red border, no badge (same-system).
   - Character B's frame: half-opacity red border, "+1j" badge near
     top-left.
   - Both chips: same dot intensities, "+1j" text next to character
     B's chip dot.
4. Move character B 2 jumps away.
5. Fire DANGER for character A's system.
6. **Expect**: character B's frame tints at the floor alpha (~40%)
   with "+2j" badge.
7. Move character B 3+ jumps away.
8. Fire same alert.
9. **Expect**: character B's frame is **untinted** (default
   `intel.threat_jumps_threshold = 1` excludes it).
10. **Settings → Intel → set "Max jumps" to 3**.
11. Re-fire same alert.
12. **Expect**: character B now tints at the floor alpha with "+3j".

---

## Test 6 — Focus mode (PR #64)

**Why**: Spotlight one preview when something dangerous is happening.

1. **Double-click** any preview frame.
2. **Expect**:
   - That frame scales up larger (past the normal 600x450 cap).
   - All other frames fade to 25% opacity.
3. Press **Esc**.
4. **Expect**: focus exits, all frames return to normal.
5. Double-click frame A. While focused, double-click frame B.
6. **Expect**: spotlight swaps to frame B; frame A drops to dimmed.
7. While focused on a frame, fire a DANGER alert for that character's
   system.
8. **Expect**: focused frame still pulses, but the dim frames don't
   fight it for attention. (Visual sanity check.)

---

## Test 7 — Replay strip (PR #72)

**Why**: Combat scrubbing for the "did I see a sabre uncloak?" case.

1. Right-click a preview frame → **"Toggle Replay Strip"**.
2. **Expect**: a horizontal strip of ~6 thumbnail cells appears at the
   bottom of that frame. Initially empty (the buffer takes ~5 seconds
   to fill).
3. Wait 5+ seconds while the EVE client renders different content
   (e.g., undock, look around).
4. **Expect**: the strip cells fill left-to-right with thumbnails of
   the recent capture history.
5. Hover the leftmost cell.
6. **Expect**: the main image label of that frame swaps to the older
   captured frame. A blue highlight appears on the hovered cell.
7. Move the mouse off the strip.
8. **Expect**: main image returns to live capture.
9. Right-click → **"Toggle Replay Strip"** again.
10. **Expect**: strip vanishes. Buffer keeps accumulating in the
    background but isn't visible.
11. Restart Argus.
12. **Expect**: the strip you toggled on is restored on launch.

---

## Test 8 — Decay timing (cross-cutting)

**Why**: 30s decay was tuned with no real-world data. Validate it.

1. Fire a DANGER alert.
2. Stopwatch the time from full intensity to invisible.
3. **Expect**: ~30 seconds, smooth linear fade.
4. Subjective: does it linger too long during a busy fleet op? Or
   disappear too fast? File a tuning note if either.

---

## Manual report injection (advanced)

The "Test Alert" button only fires a generic WARNING. To exercise
DANGER/CRITICAL or specific systems, paste this into a running Python
console attached to the app (or modify `_test_alert` temporarily):

```python
from argus_overview.intel.parser import IntelReport, ThreatLevel
from datetime import datetime

# In MainWindowV21 instance scope (e.g., self):
report = IntelReport(
    system="HED-GP",  # change to test specific systems
    threat_level=ThreatLevel.DANGER,  # CLEAR / INFO / WARNING / DANGER / CRITICAL
    hostile_count=3,
    ship_types=["sabre", "broadsword"],
    player_names=[],
    raw_message="hostiles HED-GP +3 sabre broadsword",
    timestamp=datetime.now(),
)
self.intel_tab.alert_dispatcher.dispatch(report)
```

For per-character system testing, override the location tracker:

```python
# Force a character to a specific system without waiting for log parsing
self.main_tab.window_manager.set_character_system("CharName", "HED-GP")
self.main_tab.status_dock.set_character_system("CharName", "HED-GP")
```

---

## Filing issues

For each broken behavior:

```
**Test #N step Y**
**Expected**: <copy from the doc>
**Got**: <what actually happened>
**Setup**: <character count, theme, FPS, OS>
```

Use the [issue tracker](https://github.com/AreteDriver/Argus_Overview/issues).
Tag with `smoke-test-v3.2.0` if you create the label.

---

## Out of scope

These are known limitations, not bugs:

- Test Alert button only fires WARNING; use the manual injection
  recipe for DANGER/CRITICAL.
- The `replay_strip_enabled` summary in IntelPanel is read-only —
  per-character toggles live in the right-click menu.
- Replay strip uses 800ms throttle; capture rates higher than ~1.25 FPS
  do not increase the buffer's temporal resolution.
- Auto-tag → release.yml workflow can't auto-publish GitHub releases
  without a PAT (debt #4 in the post-v3.2.0 audit).
