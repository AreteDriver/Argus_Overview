"""
Action Registry - Single Source of Truth for UI Actions

This module implements a centralized registry for all UI actions, ensuring:
1. No duplicate actions across primary homes
2. Clear tier-based organization (Global/Tab/Object)
3. Easy auditing of action placement

Tier Rules:
- Tier 1 (Global): App menu + system tray only
- Tier 2 (Tab): Tab toolbar only (per-tab primary workflow actions)
- Tier 3 (Object): Right-click context menu only (per-item/window actions)

Exceptions: Keyboard shortcuts may exist in addition to canonical home,
but must not create duplicate clickable UI.
"""
import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Set


class ActionScope(Enum):
    """Scope of an action - where it can be triggered from"""
    GLOBAL = auto()    # Available anywhere (quit, show/hide, reload config, profile switch)
    TAB = auto()       # Primary workflow for specific tab
    OBJECT = auto()    # Operates on selected item/window/character


class PrimaryHome(Enum):
    """Primary canonical location for an action's UI element"""
    # Global actions (Tier 1)
    TRAY_MENU = "tray_menu"
    APP_MENU = "app_menu"

    # Tab actions (Tier 2)
    OVERVIEW_TOOLBAR = "overview_toolbar"
    ROSTER_TOOLBAR = "roster_toolbar"
    LAYOUTS_TOOLBAR = "layouts_toolbar"
    AUTOMATION_TOOLBAR = "automation_toolbar"
    SYNC_TOOLBAR = "sync_toolbar"
    SETTINGS_PANEL = "settings_panel"  # Settings tab is special - uses panels not toolbar
    HELP_MENU = "help_menu"

    # Object actions (Tier 3)
    WINDOW_CONTEXT = "window_context"
    CHARACTER_CONTEXT = "character_context"
    TEAM_CONTEXT = "team_context"
    GROUP_CONTEXT = "group_context"


# Mapping of homes to their tier for redundancy checking
HOME_TIERS = {
    PrimaryHome.TRAY_MENU: 1,
    PrimaryHome.APP_MENU: 1,
    PrimaryHome.HELP_MENU: 1,  # Part of app menu
    PrimaryHome.OVERVIEW_TOOLBAR: 2,
    PrimaryHome.ROSTER_TOOLBAR: 2,
    PrimaryHome.LAYOUTS_TOOLBAR: 2,
    PrimaryHome.AUTOMATION_TOOLBAR: 2,
    PrimaryHome.SYNC_TOOLBAR: 2,
    PrimaryHome.SETTINGS_PANEL: 2,
    PrimaryHome.WINDOW_CONTEXT: 3,
    PrimaryHome.CHARACTER_CONTEXT: 3,
    PrimaryHome.TEAM_CONTEXT: 3,
    PrimaryHome.GROUP_CONTEXT: 3,
}


@dataclass
class ActionSpec:
    """
    Specification for a single UI action.

    Attributes:
        id: Unique identifier for this action
        label: Display text for the action
        tooltip: Optional tooltip text
        scope: ActionScope indicating where action applies
        primary_home: Canonical location for this action's UI element
        shortcut: Optional keyboard shortcut (may exist in addition to primary home)
        icon: Optional icon name/path
        handler_name: Name of the handler method (connected at runtime)
        enabled_when: Optional condition function for enabling/disabling
        checkable: Whether action has a checked state
    """
    id: str
    label: str
    scope: ActionScope
    primary_home: PrimaryHome
    tooltip: str = ""
    shortcut: Optional[str] = None
    icon: Optional[str] = None
    handler_name: Optional[str] = None
    enabled_when: Optional[str] = None  # Condition name, evaluated at runtime
    checkable: bool = False


class ActionRegistry:
    """
    Centralized registry for all UI actions.

    Usage:
        registry = ActionRegistry.get_instance()
        action = registry.get("quit")
        actions_for_tray = registry.get_by_home(PrimaryHome.TRAY_MENU)
    """
    _instance = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._actions: Dict[str, ActionSpec] = {}
        self._by_home: Dict[PrimaryHome, List[str]] = {home: [] for home in PrimaryHome}
        self._handlers: Dict[str, Callable] = {}

        # Register all actions
        self._register_all_actions()

    @classmethod
    def get_instance(cls) -> "ActionRegistry":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton (for testing)"""
        cls._instance = None

    def _register_all_actions(self):
        """Register all application actions"""

        # =====================================================================
        # TIER 1: GLOBAL ACTIONS (Tray Menu / App Menu)
        # =====================================================================

        # Tray Menu Actions
        self.register(ActionSpec(
            id="show_hide",
            label="Show/Hide Argus Overview",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
            tooltip="Toggle main window visibility",
            handler_name="_toggle_visibility",
        ))

        self.register(ActionSpec(
            id="toggle_thumbnails",
            label="Toggle Thumbnails",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
            tooltip="Toggle thumbnail visibility (Ctrl+Shift+T)",
            shortcut="<ctrl>+<shift>+t",
            handler_name="_toggle_thumbnails",
        ))

        self.register(ActionSpec(
            id="reload_config",
            label="Reload Config",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
            tooltip="Hot reload configuration",
            handler_name="_reload_config",
        ))

        self.register(ActionSpec(
            id="settings",
            label="Settings",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
            tooltip="Open settings",
            handler_name="_show_settings",
        ))

        self.register(ActionSpec(
            id="quit",
            label="Quit",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
            tooltip="Quit application",
            handler_name="_quit_application",
        ))

        # App Menu / Help Menu Actions
        self.register(ActionSpec(
            id="about",
            label="About Argus Overview",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.HELP_MENU,
            tooltip="Show about dialog",
            handler_name="_show_about_dialog",
        ))

        self.register(ActionSpec(
            id="donate",
            label="Support Development (Buy Me a Coffee)",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.HELP_MENU,
            tooltip="Support development",
            icon="coffee",
            handler_name="_open_donation_link",
        ))

        self.register(ActionSpec(
            id="documentation",
            label="Documentation",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.HELP_MENU,
            tooltip="Open documentation",
            handler_name="_open_documentation",
        ))

        self.register(ActionSpec(
            id="report_issue",
            label="Report Issue",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.HELP_MENU,
            tooltip="Report an issue on GitHub",
            handler_name="_open_issue_tracker",
        ))

        # =====================================================================
        # TIER 2: TAB ACTIONS (Tab Toolbars)
        # =====================================================================

        # --- Overview Tab (formerly Main) ---
        self.register(ActionSpec(
            id="import_windows",
            label="Import All EVE Windows",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.OVERVIEW_TOOLBAR,
            tooltip="Scan and import all EVE windows with one click",
            handler_name="one_click_import",
        ))

        self.register(ActionSpec(
            id="add_window",
            label="Add Window",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.OVERVIEW_TOOLBAR,
            tooltip="Manually select EVE windows to add",
            handler_name="show_add_window_dialog",
        ))

        self.register(ActionSpec(
            id="remove_all_windows",
            label="Remove All",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.OVERVIEW_TOOLBAR,
            tooltip="Remove all windows from preview",
            handler_name="_remove_all_windows",
        ))

        self.register(ActionSpec(
            id="lock_positions",
            label="Lock",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.OVERVIEW_TOOLBAR,
            tooltip="Lock thumbnail positions (Ctrl+Shift+L)",
            shortcut="<ctrl>+<shift>+l",
            handler_name="_toggle_lock",
            checkable=True,
        ))

        self.register(ActionSpec(
            id="minimize_inactive",
            label="Minimize Inactive",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.OVERVIEW_TOOLBAR,
            tooltip="Minimize all windows except the currently focused one",
            handler_name="minimize_inactive_windows",
        ))

        self.register(ActionSpec(
            id="refresh_capture",
            label="Refresh",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.OVERVIEW_TOOLBAR,
            tooltip="Restart capture for all windows",
            handler_name="_refresh_all",
        ))

        self.register(ActionSpec(
            id="minimize_all",
            label="Minimize All",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
            tooltip="Minimize all EVE windows (Ctrl+Shift+M)",
            shortcut="<ctrl>+<shift>+m",
            handler_name="_minimize_all_windows",
        ))

        self.register(ActionSpec(
            id="restore_all",
            label="Restore All",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
            tooltip="Restore all EVE windows (Ctrl+Shift+R)",
            shortcut="<ctrl>+<shift>+r",
            handler_name="_restore_all_windows",
        ))

        # --- Roster Tab (Characters & Teams) ---
        self.register(ActionSpec(
            id="add_character",
            label="Add Character",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.ROSTER_TOOLBAR,
            tooltip="Add new character",
            handler_name="_add_character",
        ))

        self.register(ActionSpec(
            id="scan_eve_folder",
            label="Scan EVE Folder",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.ROSTER_TOOLBAR,
            tooltip="Import ALL characters from EVE installation",
            icon="folder",
            handler_name="_scan_eve_folder",
        ))

        self.register(ActionSpec(
            id="new_team",
            label="New Team",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.ROSTER_TOOLBAR,
            tooltip="Create new team",
            handler_name="_new_team",
        ))

        # --- Layouts Tab ---
        self.register(ActionSpec(
            id="apply_layout",
            label="Apply to Windows",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.LAYOUTS_TOOLBAR,
            tooltip="Apply current arrangement to EVE windows",
            handler_name="_apply_to_active_windows",
        ))

        self.register(ActionSpec(
            id="auto_arrange",
            label="Auto-Arrange",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.LAYOUTS_TOOLBAR,
            tooltip="Arrange tiles based on selected pattern",
            handler_name="_auto_arrange",
        ))

        self.register(ActionSpec(
            id="save_layout_preset",
            label="Save Preset",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.LAYOUTS_TOOLBAR,
            tooltip="Save current arrangement as a preset",
            handler_name="_save_preset",
        ))

        self.register(ActionSpec(
            id="refresh_layout_groups",
            label="Refresh Groups",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.LAYOUTS_TOOLBAR,
            tooltip="Reload cycling groups from Automation tab",
            handler_name="_refresh_groups",
        ))

        # --- Automation Tab (Hotkeys + Alerts) ---
        self.register(ActionSpec(
            id="new_group",
            label="New Group",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.AUTOMATION_TOOLBAR,
            tooltip="Create new cycling group",
            handler_name="_create_new_group",
        ))

        self.register(ActionSpec(
            id="load_active_windows",
            label="Load Active Windows",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.AUTOMATION_TOOLBAR,
            tooltip="Load all currently active EVE windows into this group",
            handler_name="_load_active_windows",
        ))

        self.register(ActionSpec(
            id="save_hotkeys",
            label="Save Hotkeys",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.AUTOMATION_TOOLBAR,
            tooltip="Save hotkey settings",
            handler_name="_save_hotkeys",
        ))

        # --- Sync Tab ---
        self.register(ActionSpec(
            id="scan_eve_settings",
            label="Scan for EVE Settings",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.SYNC_TOOLBAR,
            tooltip="Scan EVE Online directory for character settings",
            handler_name="_scan_settings",
        ))

        self.register(ActionSpec(
            id="preview_sync",
            label="Preview Sync",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.SYNC_TOOLBAR,
            tooltip="Preview what will be synced",
            handler_name="_preview_sync",
        ))

        self.register(ActionSpec(
            id="sync_settings",
            label="Sync Settings",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.SYNC_TOOLBAR,
            tooltip="Sync settings from source to targets",
            handler_name="_sync_settings",
        ))

        # --- Settings Panel ---
        self.register(ActionSpec(
            id="reset_all_settings",
            label="Reset All to Defaults",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.SETTINGS_PANEL,
            tooltip="Reset all settings to defaults",
            handler_name="_reset_all",
        ))

        self.register(ActionSpec(
            id="export_settings",
            label="Export Settings",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.SETTINGS_PANEL,
            tooltip="Export settings to file",
            handler_name="_export_settings",
        ))

        self.register(ActionSpec(
            id="import_settings",
            label="Import Settings",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.SETTINGS_PANEL,
            tooltip="Import settings from file",
            handler_name="_import_settings",
        ))

        # =====================================================================
        # TIER 3: OBJECT ACTIONS (Context Menus)
        # =====================================================================

        # Window Preview Context Menu
        self.register(ActionSpec(
            id="focus_window",
            label="Focus Window",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.WINDOW_CONTEXT,
            tooltip="Activate this window",
            handler_name="_focus_window",
        ))

        self.register(ActionSpec(
            id="minimize_window",
            label="Minimize",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.WINDOW_CONTEXT,
            tooltip="Minimize this window",
            handler_name="_minimize_window",
        ))

        self.register(ActionSpec(
            id="close_window",
            label="Close",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.WINDOW_CONTEXT,
            tooltip="Close this window",
            handler_name="_close_window",
        ))

        self.register(ActionSpec(
            id="set_label",
            label="Set Label...",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.WINDOW_CONTEXT,
            tooltip="Set custom label for this window",
            handler_name="_show_label_dialog",
        ))

        self.register(ActionSpec(
            id="remove_from_preview",
            label="Remove from Preview",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.WINDOW_CONTEXT,
            tooltip="Remove from preview (keeps window open)",
            handler_name="_remove_from_preview",
        ))

        # Character Context Menu
        self.register(ActionSpec(
            id="edit_character",
            label="Edit",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.CHARACTER_CONTEXT,
            tooltip="Edit character details",
            handler_name="_edit_character",
        ))

        self.register(ActionSpec(
            id="delete_character",
            label="Delete",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.CHARACTER_CONTEXT,
            tooltip="Delete character",
            handler_name="_delete_character",
        ))

        # Team Context Menu
        self.register(ActionSpec(
            id="save_team",
            label="Save Team",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.TEAM_CONTEXT,
            tooltip="Save team changes",
            handler_name="_save_team",
        ))

        # Group Context Menu
        self.register(ActionSpec(
            id="delete_group",
            label="Delete Group",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.GROUP_CONTEXT,
            tooltip="Delete cycling group",
            handler_name="_delete_current_group",
        ))

        self.register(ActionSpec(
            id="remove_group_member",
            label="Remove Selected",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.GROUP_CONTEXT,
            tooltip="Remove selected member from group",
            handler_name="_remove_selected_member",
        ))

        self.register(ActionSpec(
            id="clear_group",
            label="Clear All",
            scope=ActionScope.OBJECT,
            primary_home=PrimaryHome.GROUP_CONTEXT,
            tooltip="Clear all members from group",
            handler_name="_clear_group_members",
        ))

    def register(self, action: ActionSpec):
        """Register an action"""
        if action.id in self._actions:
            self.logger.warning(f"Action '{action.id}' already registered, overwriting")

        self._actions[action.id] = action
        self._by_home[action.primary_home].append(action.id)
        self.logger.debug(f"Registered action: {action.id} -> {action.primary_home.value}")

    def get(self, action_id: str) -> Optional[ActionSpec]:
        """Get action by ID"""
        return self._actions.get(action_id)

    def get_by_home(self, home: PrimaryHome) -> List[ActionSpec]:
        """Get all actions for a specific home"""
        return [self._actions[aid] for aid in self._by_home.get(home, [])]

    def get_by_scope(self, scope: ActionScope) -> List[ActionSpec]:
        """Get all actions for a specific scope"""
        return [a for a in self._actions.values() if a.scope == scope]

    def all_actions(self) -> List[ActionSpec]:
        """Get all registered actions"""
        return list(self._actions.values())

    def bind_handler(self, action_id: str, handler: Callable):
        """Bind a handler function to an action"""
        if action_id not in self._actions:
            self.logger.warning(f"Cannot bind handler: action '{action_id}' not found")
            return
        self._handlers[action_id] = handler

    def get_handler(self, action_id: str) -> Optional[Callable]:
        """Get bound handler for an action"""
        return self._handlers.get(action_id)

    def invoke(self, action_id: str, *args, **kwargs):
        """Invoke an action's handler"""
        handler = self._handlers.get(action_id)
        if handler:
            return handler(*args, **kwargs)
        else:
            self.logger.warning(f"No handler bound for action: {action_id}")


def audit_actions(registry: Optional[ActionRegistry] = None) -> Dict:
    """
    Audit the action registry for duplicates and issues.

    Returns:
        Dict with audit results including duplicates and action counts
    """
    if registry is None:
        registry = ActionRegistry.get_instance()

    results = {
        "total_actions": 0,
        "by_home": {},
        "by_scope": {},
        "duplicates": [],
        "issues": [],
        "passed": True,
    }

    actions = registry.all_actions()
    results["total_actions"] = len(actions)

    # Count by home and scope
    for action in actions:
        home = action.primary_home.value
        scope = action.scope.name

        if home not in results["by_home"]:
            results["by_home"][home] = []
        results["by_home"][home].append(action.id)

        if scope not in results["by_scope"]:
            results["by_scope"][scope] = []
        results["by_scope"][scope].append(action.id)

    # Check for actions that appear in multiple primary homes (should be impossible with current design)
    action_homes: Dict[str, Set[str]] = {}
    for action in actions:
        if action.id not in action_homes:
            action_homes[action.id] = set()
        action_homes[action.id].add(action.primary_home.value)

    for action_id, homes in action_homes.items():
        if len(homes) > 1:
            results["duplicates"].append({
                "action_id": action_id,
                "homes": list(homes),
            })
            results["passed"] = False

    # Check for missing handlers (warning, not failure)
    for action in actions:
        if not action.handler_name:
            results["issues"].append(f"Action '{action.id}' has no handler_name defined")

    return results


def print_audit_report(results: Optional[Dict] = None):
    """Print a human-readable audit report"""
    if results is None:
        results = audit_actions()

    print("\n" + "=" * 60)
    print("UI ACTION REGISTRY AUDIT REPORT")
    print("=" * 60)

    print(f"\nTotal Actions: {results['total_actions']}")

    print("\n--- Actions by Primary Home ---")
    for home, actions in sorted(results["by_home"].items()):
        print(f"  {home}: {len(actions)}")
        for action in actions:
            print(f"    - {action}")

    print("\n--- Actions by Scope ---")
    for scope, actions in sorted(results["by_scope"].items()):
        print(f"  {scope}: {len(actions)}")

    if results["duplicates"]:
        print("\n!!! DUPLICATES FOUND (FAIL) !!!")
        for dup in results["duplicates"]:
            print(f"  Action '{dup['action_id']}' appears in: {', '.join(dup['homes'])}")
    else:
        print("\n[OK] No duplicate actions across primary homes")

    if results["issues"]:
        print("\n--- Warnings ---")
        for issue in results["issues"]:
            print(f"  [!] {issue}")

    print("\n" + "=" * 60)
    print(f"AUDIT RESULT: {'PASSED' if results['passed'] else 'FAILED'}")
    print("=" * 60 + "\n")

    return results["passed"]


if __name__ == "__main__":
    # Run audit when executed directly
    import sys
    registry = ActionRegistry.get_instance()
    passed = print_audit_report()
    sys.exit(0 if passed else 1)
