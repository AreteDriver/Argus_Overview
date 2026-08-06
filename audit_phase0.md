# Argus Overview v3.2.0 — Phase 0 Audit Report

## Baseline Test Result

```
Passed:   2446
Failed:   1  (test_cross_process_determinism — subprocess PYTHONPATH issue, pre-existing)
Skipped:  5
Warnings: 16 (DeprecationWarning: QMouseEvent constructor)
Runtime:  ~7s
```

The single failure is an environment issue (subprocess cannot import `argus_overview` because PYTHONPATH is not propagated). All functional tests pass.

---

## Current UI Architecture Map

### Widget Hierarchy

```
MainWindowV21 (QMainWindow)
├── MenuBar (MenuBuilder)
├── CentralWidget (QWidget)
│   └── QVBoxLayout
│       └── QTabWidget
│           ├── MainTab (Overview)          — FlowLayout + WindowManager
│           │   ├── Toolbar (QWidget)         — ActionRegistry OVERVIEW_TOOLBAR
│           │   ├── StatusDock (QScrollArea) — CharacterChip strip
│           │   └── PreviewArea (QScrollArea) — FlowLayout of WindowPreviewWidget
│           ├── HotkeysTab (Cycle Control)    — per-character hotkey UI
│           ├── CharactersTeamsTab (Roster)   — character/team tables
│           ├── IntelTab                      — log monitor + alert settings
│           ├── SettingsSyncTab               — EVE settings sync
│           └── SettingsTab                   — app configuration
├── StatusBar
│   └── SystemStatusBar (QWidget)             — 5 subsystem dots
└── SystemTray
```

### Core Signals

| Signal | Emitter | Consumer |
|--------|---------|----------|
| `frame_ready` | WindowCaptureThreaded | WindowManager.update_frame |
| `character_detected` | MainTab | MainWindowV21._on_character_detected |
| `intel_received` | IntelTab | MainWindowV21._on_intel_received |
| `alert_triggered` | IntelTab | MainWindowV21._on_intel_alert |
| `border_flash_requested` | AlertDispatcher | MainTab._flash_preview_borders |
| `new_character_found` | AutoDiscovery | MainWindowV21._on_new_character_discovered |
| `character_gone` | AutoDiscovery | MainWindowV21._on_character_gone |
| `team_selected` | CharactersTeamsTab | MainWindowV21._on_team_selected |
| `settings_changed` | SettingsTab | MainWindowV21._apply_setting |
| `health_changed` | HotkeyManager | MainWindowV21._on_hotkey_health_changed |
| `pipeline_health_changed` | IntelTab | MainWindowV21 (PR5) |

### State Sources of Truth

| State | Source | UI Consumer |
|-------|--------|-------------|
| Client detected | AutoDiscovery / scan_eve_windows | MainTab, StatusDock |
| Capture health | `WindowPreviewWidget._last_frame_received_at` | paintEvent badge |
| Latest successful frame | `WindowPreviewWidget.current_pixmap` | image_label |
| Character location | CharacterLocationTracker (Local logs) | CharacterChip, WindowPreviewWidget tooltip |
| Threat severity | IntelParser → ThreatLevel | WindowPreviewWidget border, CharacterChip dot |
| Threat age | `WindowPreviewWidget._threat_set_at` | paintEvent age pill, tooltip |
| Focused client | `WindowPreviewWidget.is_focused` / activity dot | WindowManager |
| Global-hotkey status | HotkeyManager._health | SystemStatusBar |
| Active layout | LayoutManager presets | LayoutsTab, Overview toolbar combo |

---

## Top Ten Visual and Interaction Findings

### 1. No centralized design system (Blocker — Architecture)
**Evidence:** Colors hardcoded across 10+ files: `#2b2b2b` in `status_dock.py`, `#353535` in `themes.py`, `#444` in `CharacterChip`, `#4CAF50` in `intel_tab.py`, `#F44336` in multiple files, inline `QColor(r,g,b)` in `main_tab.py` paintEvent.  
**Impact:** Inconsistent appearance, impossible to theme globally, high maintenance cost for any visual change.  
**Recommendation:** Create `ui/design_system/` with semantic tokens (colors, spacing, radius, typography, control sizes). Migrate widgets incrementally.

### 2. WindowPreviewWidget paintEvent is 160+ lines of mixed concerns (High — Visual Design)
**Evidence:** `paintEvent` draws: accent border, threat border, system pill, age pill, legacy flash, activity dot + text, lock emoji, focus affordance emoji, capture health badge. All inline with hardcoded coordinates and colors.  
**Impact:** Difficult to modify, test, or reason about. High risk of clipping or overlap at small sizes.  
**Recommendation:** Decompose paint into semantic layers using the design system. Extract badge/pill drawing into reusable helpers.

### 3. Theme system is palette-only, no component styles (High — Architecture)
**Evidence:** `themes.py` defines `ThemeColors` with window/base/button/highlight but no semantic tokens for threat, capture health, or component chrome. `ThemeManager.apply_theme` only sets `QApplication.palette()`.  
**Impact:** Custom-painted widgets (preview borders, chips, status bar) ignore theme changes. Light theme would leave dark-painted widgets unchanged.  
**Recommendation:** Extend ThemeManager to expose semantic tokens and generate component QSS.

### 4. Status dock chips use hardcoded stylesheet strings (Medium — Consistency)
**Evidence:** `CharacterChip._apply_base_style()` embeds `#2b2b2b`, `#444`, `#353535`, `#6a6a6a` as inline QSS. `_update_avatar_style()` computes `darker(160)` and luminance manually inline.  
**Impact:** Visual inconsistency with the rest of the app; no theme adaptation.  
**Recommendation:** Drive chip styling from the design system with semantic tokens.

### 5. SystemStatusBar uses rich-text colored dots with no theme awareness (Medium — Consistency)
**Evidence:** `_STATUS_COLORS` dictionary uses `#4caf50`, `#ff9800`, `#f44336`, `#9e9e9e`. Text is HTML rich text.  
**Impact:** Colors may clash with light theme or user preferences.  
**Recommendation:** Use design-system semantic colors and draw indicators with QPainter for crispness.

### 6. Preview health and threat state are entangled in paintEvent (High — Honesty)
**Evidence:** `paintEvent` draws threat border when `_threat_level is not None`, otherwise accent border. But health (LIVE/STATIC/STALE/ERROR) is only shown as a bottom-right text badge. A stale frame can still show a bright threat border because they are painted independently.  
**Impact:** Operator may see a "CRITICAL" border on a stale 8-second-old frame and not realize the preview is not live.  
**Recommendation:** Make capture health visually primary. Dim or override threat styling when health is STALE/ERROR/DISCONNECTED.

### 7. Activity indicator uses color-only plus a small text label (Low — Accessibility)
**Evidence:** Green/yellow/gray dot with capitalized text label "Focused" / "Recent" / "Idle" painted in top-right.  
**Impact:** Text is small (7pt) and may be hard to read at distance. Color is redundant with text, which is good.  
**Recommendation:** Keep text, increase contrast, or move to a more scannable location.

### 8. Replay strip shifts layout when enabled (Medium — Interaction)
**Evidence:** `enable_replay_strip()` calls `self.layout().addWidget(self._replay_strip)` on the preview widget's VBoxLayout. This pushes the existing image_label and info_label up.  
**Impact:** Content jumps when toggling replay strip. Layout reflows.  
**Recommendation:** Reserve fixed space for the strip or overlay it to avoid layout shift.

### 9. Overview toolbar still contains preset combo + multiple buttons (Medium — Visual hierarchy)
**Evidence:** `_create_toolbar` builds: import button, lock button, minimize button, refresh button, replay toggle, preset combo, refresh rate spinbox, opacity slider. 12+ widgets in one row.  
**Impact:** Operational screen dominated by chrome. The preset combo (operational) is mixed with opacity slider (configuration).  
**Recommendation:** Separate operational controls from configuration. Move setup-only actions out of persistent toolbar (already partially done in PR5).

### 10. Minimum window size 1000×700 may exclude 1024×768 users (Medium — Responsive)
**Evidence:** `MainWindowV21.setMinimumSize(1000, 700)`.  
**Impact:** Users on 1024×768 (common on older laptops, VMs, remote desktop) cannot resize the window to fit their screen.  
**Recommendation:** Reduce minimum size to 960×600 or allow scroll/panel collapse at small sizes.

---

## Proposed File-by-File Implementation Plan

### Batch 1 — Design System Foundation
*Create the shared token system and verify it compiles/tests.*

- **NEW** `src/argus_overview/ui/design_system/__init__.py`
- **NEW** `src/argus_overview/ui/design_system/colors.py` — semantic tokens
- **NEW** `src/argus_overview/ui/design_system/spacing.py` — 4px grid
- **NEW** `src/argus_overview/ui/design_system/typography.py` — font roles
- **NEW** `src/argus_overview/ui/design_system/metrics.py` — radii, heights
- **NEW** `src/argus_overview/ui/design_system/states.py` — health/threat enums, preview state model
- **NEW** `tests/test_design_system.py` — token existence, valid colors, scale checks
- **MODIFY** `src/argus_overview/ui/themes.py` — expose semantic tokens from ThemeManager

### Batch 2 — Preview Card Redesign
*Decompose paintEvent, make health primary, add explicit state model.*

- **MODIFY** `src/argus_overview/ui/main_tab.py` — WindowPreviewWidget paintEvent refactor
- **NEW** `src/argus_overview/ui/design_system/painting.py` — badge/pill/rounded rect helpers
- **MODIFY** `tests/test_main_tab.py` — paint state tests

### Batch 3 — Status Dock & System Status Bar
*Drive chips and status bar from design system.*

- **MODIFY** `src/argus_overview/ui/status_dock.py` — CharacterChip styling
- **MODIFY** `src/argus_overview/ui/system_status_bar.py` — semantic colors, crisp rendering
- **MODIFY** `tests/test_status_dock.py`

### Batch 4 — Toolbar & Command Surface
*Reduce chrome, separate operational from configuration.*

- **MODIFY** `src/argus_overview/ui/main_tab.py` — _create_toolbar
- **MODIFY** `src/argus_overview/ui/main_window_v21.py` — command bar concept

### Batch 5 — Navigation Consolidation
*Map 6 tabs into 4 coherent areas.*

- **MODIFY** `src/argus_overview/ui/main_window_v21.py` — tab widget restructuring

### Batch 6 — Accessibility & Keyboard
*Tab order, focus indicators, accessible names.*

- **MODIFY** `src/argus_overview/ui/main_tab.py` — focus, accessible text
- **MODIFY** `src/argus_overview/ui/status_dock.py` — keyboard nav
- **NEW** `tests/test_accessibility.py`

### Batch 7 — Responsive & DPI
*Minimum sizes, panel collapse, scaling.*

- **MODIFY** `src/argus_overview/ui/main_window_v21.py` — min size, splitter behavior
- **MODIFY** `src/argus_overview/ui/main_tab.py` — preview min sizes

### Batch 8 — Performance Hardening
*Timer cleanup, repaint bounds, static dedup.*

- **MODIFY** `src/argus_overview/ui/main_tab.py` — bounded repaint regions

### Batch 9 — Documentation & Screenshots
*Update docs, capture screenshot matrix.*

- **MODIFY** `README.md`, `docs/USER_GUIDE.md`

---

## First Smallest Coherent Implementation Batch

**Batch 1: Design System Foundation**

Rationale: Every subsequent batch depends on shared tokens. Without a design system, Batch 2 would add more hardcoded colors. Creating the token layer first:
1. Gives us testable constants.
2. Prevents drift in later batches.
3. Is purely additive — zero risk to existing behavior.
4. Can be immediately verified with unit tests.

Scope:
- Create `design_system/` package.
- Define semantic color tokens, spacing scale, radii, control heights, typography roles.
- Add `PreviewHealth` and `ThreatLevel` enums + `PreviewState` dataclass.
- Wire `ThemeManager` to expose the current semantic palette.
- Add tests verifying all tokens exist and are valid hex colors.
- No widget changes yet.

Acceptance:
- `pytest tests/test_design_system.py` passes.
- `python -m argus_overview.ui.design_system` runs without error.
- No existing tests fail.
