# EVE Veles Eyes - Developer Notes

## UI Action Registry System (v2.3)

This document describes the Action Registry system introduced in v2.3 to eliminate
menu redundancy and establish a single source of truth for all UI actions.

### Tier Rules

Every user action must have exactly ONE primary home, organized into tiers:

| Tier | Scope | Primary Home(s) | Purpose |
|------|-------|-----------------|---------|
| 1 | Global | `TRAY_MENU`, `APP_MENU`, `HELP_MENU` | Available anywhere (quit, show/hide, reload config, profiles) |
| 2 | Tab | `*_TOOLBAR`, `SETTINGS_PANEL` | Primary workflow for that tab only |
| 3 | Object | `*_CONTEXT` | Operates on a selected item/window/character |

**Exception**: Keyboard shortcuts may exist in addition to the canonical home,
but must not create duplicate clickable UI elements.

### Tab Structure (v2.3)

| Tab | Purpose | Toolbar Home |
|-----|---------|--------------|
| Overview | Window preview management, capture | `OVERVIEW_TOOLBAR` |
| Roster | Characters & teams management | `ROSTER_TOOLBAR` |
| Layouts | Window arrangement patterns | `LAYOUTS_TOOLBAR` |
| Automation | Hotkeys, cycling groups, alerts | `AUTOMATION_TOOLBAR` |
| Sync | EVE settings synchronization | `SYNC_TOOLBAR` |
| Settings | Application configuration | `SETTINGS_PANEL` |

**Note**: Help menu is in the menu bar, not a tab.

### Adding New Actions

1. **Determine the scope**: Is it global, tab-specific, or object-specific?
2. **Choose the primary home**: Based on tier rules above
3. **Register in ActionRegistry**: Edit `ui/action_registry.py`

```python
self.register(ActionSpec(
    id="my_new_action",
    label="My Action Label",
    scope=ActionScope.TAB,  # or GLOBAL, OBJECT
    primary_home=PrimaryHome.OVERVIEW_TOOLBAR,  # canonical location
    tooltip="Description of action",
    shortcut="<ctrl>+<shift>+a",  # optional
    handler_name="_my_action_handler",
))
```

4. **Connect handler**: In the appropriate widget/tab, bind the handler:

```python
from eve_overview_pro.ui.action_registry import ActionRegistry

registry = ActionRegistry.get_instance()
registry.bind_handler("my_new_action", self._my_action_handler)
```

5. **Run audit to verify**: `python -m eve_overview_pro.ui.action_registry`

### Primary Home Definitions

```python
class PrimaryHome(Enum):
    # Tier 1 (Global)
    TRAY_MENU = "tray_menu"
    APP_MENU = "app_menu"
    HELP_MENU = "help_menu"

    # Tier 2 (Tab)
    OVERVIEW_TOOLBAR = "overview_toolbar"
    ROSTER_TOOLBAR = "roster_toolbar"
    LAYOUTS_TOOLBAR = "layouts_toolbar"
    AUTOMATION_TOOLBAR = "automation_toolbar"
    SYNC_TOOLBAR = "sync_toolbar"
    SETTINGS_PANEL = "settings_panel"

    # Tier 3 (Object)
    WINDOW_CONTEXT = "window_context"
    CHARACTER_CONTEXT = "character_context"
    TEAM_CONTEXT = "team_context"
    GROUP_CONTEXT = "group_context"
```

### Running the Redundancy Audit

The audit tool checks for:
- Actions appearing in multiple primary homes (FAIL)
- Missing handler names (WARNING)
- Action counts by home and scope

```bash
# From project root
cd src
python -m eve_overview_pro.ui.action_registry

# Expected output:
# AUDIT RESULT: PASSED
```

The audit exits with code 0 if passed, 1 if failed.

### Current Action Inventory (v2.3)

#### Tier 1: Global Actions (Tray/App Menu)

| Action ID | Label | Home | Shortcut |
|-----------|-------|------|----------|
| `show_hide` | Show/Hide Veles Eyes | Tray | - |
| `toggle_thumbnails` | Toggle Thumbnails | Tray | Ctrl+Shift+T |
| `minimize_all` | Minimize All | Tray | Ctrl+Shift+M |
| `restore_all` | Restore All | Tray | Ctrl+Shift+R |
| `settings` | Settings | Tray | - |
| `reload_config` | Reload Config | Tray | - |
| `quit` | Quit | Tray | - |
| `about` | About EVE Veles Eyes | Help Menu | - |
| `donate` | Support Development | Help Menu | - |
| `documentation` | Documentation | Help Menu | - |
| `report_issue` | Report Issue | Help Menu | - |

#### Tier 2: Tab Actions

| Action ID | Label | Home | Shortcut |
|-----------|-------|------|----------|
| `import_windows` | Import All EVE Windows | Overview | - |
| `add_window` | Add Window | Overview | - |
| `remove_all_windows` | Remove All | Overview | - |
| `lock_positions` | Lock | Overview | Ctrl+Shift+L |
| `minimize_inactive` | Minimize Inactive | Overview | - |
| `add_character` | Add Character | Roster | - |
| `scan_eve_folder` | Scan EVE Folder | Roster | - |
| `new_team` | New Team | Roster | - |
| `apply_layout` | Apply Layout | Layouts | - |
| `auto_arrange` | Auto-Arrange | Layouts | - |
| `new_group` | New Group | Automation | - |
| `load_active_windows` | Load Active Windows | Automation | - |
| `save_hotkeys` | Save Hotkeys | Automation | - |
| `scan_eve_settings` | Scan for EVE Settings | Sync | - |
| `preview_sync` | Preview Sync | Sync | - |
| `sync_settings` | Sync Settings | Sync | - |
| `reset_all_settings` | Reset All to Defaults | Settings | - |
| `export_settings` | Export Settings | Settings | - |
| `import_settings` | Import Settings | Settings | - |

#### Tier 3: Object Actions (Context Menus)

| Action ID | Label | Home |
|-----------|-------|------|
| `focus_window` | Focus Window | Window Context |
| `minimize_window` | Minimize | Window Context |
| `close_window` | Close | Window Context |
| `set_label` | Set Label... | Window Context |
| `remove_from_preview` | Remove from Preview | Window Context |
| `edit_character` | Edit | Character Context |
| `delete_character` | Delete | Character Context |
| `save_team` | Save Team | Team Context |
| `delete_group` | Delete Group | Group Context |
| `remove_group_member` | Remove Selected | Group Context |
| `clear_group` | Clear All | Group Context |

### Migration Notes (v2.2 → v2.3)

**Tab Renames:**
- Main → Overview
- Characters & Teams → Roster
- Hotkeys & Cycling → Automation
- Settings Sync → Sync

**Removed Redundancies:**
- Removed duplicate "Settings" button that just navigated to Settings tab
  (kept in tray for when app is minimized)
- Consolidated window management actions in Overview toolbar
- Moved hotkey editing from Settings tab to Automation tab

**New Features:**
- Minimize All / Restore All in tray menu
- ActionRegistry single source of truth
- CLI audit tool for CI/test integration
