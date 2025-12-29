"""
Menu Builder - Constructs menus from the Action Registry

This module provides utilities to build Qt menus (QMenu, QAction) from the
centralized Action Registry, ensuring all menus are populated from a single
source of truth.
"""
import logging
from typing import Callable, Dict, List, Optional

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QPushButton

from eve_overview_pro.ui.action_registry import (
    ActionRegistry,
    ActionSpec,
    PrimaryHome,
)


class MenuBuilder:
    """
    Builds Qt menus from the Action Registry.

    Usage:
        builder = MenuBuilder(registry)
        tray_menu = builder.build_tray_menu(parent_widget, handlers)
    """

    def __init__(self, registry: Optional[ActionRegistry] = None):
        self.logger = logging.getLogger(__name__)
        self.registry = registry or ActionRegistry.get_instance()

    def build_menu(
        self,
        home: PrimaryHome,
        parent=None,
        handlers: Optional[Dict[str, Callable]] = None,
        menu: Optional[QMenu] = None,
    ) -> QMenu:
        """
        Build a QMenu from actions registered for a specific home.

        Args:
            home: PrimaryHome location to build menu for
            parent: Parent widget for the menu
            handlers: Dict mapping action_id -> handler callable
            menu: Optional existing menu to add to

        Returns:
            QMenu populated with actions
        """
        if menu is None:
            menu = QMenu(parent)

        handlers = handlers or {}
        actions = self.registry.get_by_home(home)

        for action_spec in actions:
            qt_action = self._create_action(action_spec, menu, handlers.get(action_spec.id))
            menu.addAction(qt_action)

        return menu

    def build_tray_menu(
        self,
        parent=None,
        handlers: Optional[Dict[str, Callable]] = None,
        profile_handler: Optional[Callable] = None,
        profiles: Optional[List[str]] = None,
        current_profile: Optional[str] = None,
    ) -> QMenu:
        """
        Build the system tray context menu.

        Args:
            parent: Parent widget
            handlers: Dict mapping action_id -> handler callable
            profile_handler: Callback for profile selection
            profiles: List of available profile names
            current_profile: Currently active profile name

        Returns:
            QMenu for system tray
        """
        menu = QMenu(parent)
        handlers = handlers or {}
        profiles = profiles or []

        # Order: show_hide, toggle_thumbnails, separator, minimize_all, restore_all,
        #        separator, profiles, separator, settings, reload_config, separator, quit
        action_order = [
            "show_hide",
            "toggle_thumbnails",
            None,  # separator
            "minimize_all",
            "restore_all",
            None,  # separator
            "profiles",  # special: submenu
            None,  # separator
            "settings",
            "reload_config",
            None,  # separator
            "quit",
        ]

        for item in action_order:
            if item is None:
                menu.addSeparator()
            elif item == "profiles":
                # Add profiles submenu
                profiles_menu = menu.addMenu("Profiles")
                self._populate_profiles_menu(
                    profiles_menu,
                    profiles,
                    current_profile,
                    profile_handler
                )
            else:
                action_spec = self.registry.get(item)
                if action_spec:
                    qt_action = self._create_action(
                        action_spec,
                        menu,
                        handlers.get(item)
                    )
                    menu.addAction(qt_action)

        return menu

    def build_help_menu(
        self,
        parent=None,
        handlers: Optional[Dict[str, Callable]] = None,
    ) -> QMenu:
        """
        Build the Help menu for the menu bar.

        Args:
            parent: Parent widget
            handlers: Dict mapping action_id -> handler callable

        Returns:
            QMenu for Help menu
        """
        menu = QMenu("&Help", parent)
        handlers = handlers or {}

        # Order: about, separator, donate, separator, documentation, report_issue
        action_order = [
            "about",
            None,  # separator
            "donate",
            None,  # separator
            "documentation",
            "report_issue",
        ]

        for item in action_order:
            if item is None:
                menu.addSeparator()
            else:
                action_spec = self.registry.get(item)
                if action_spec:
                    qt_action = self._create_action(
                        action_spec,
                        menu,
                        handlers.get(item)
                    )
                    menu.addAction(qt_action)

        return menu

    def _create_action(
        self,
        spec: ActionSpec,
        parent=None,
        handler: Optional[Callable] = None,
    ) -> QAction:
        """
        Create a QAction from an ActionSpec.

        Args:
            spec: ActionSpec defining the action
            parent: Parent widget
            handler: Handler callable to connect

        Returns:
            QAction configured per spec
        """
        action = QAction(spec.label, parent)

        if spec.tooltip:
            action.setToolTip(spec.tooltip)

        if spec.shortcut:
            # Note: shortcut display only, actual hotkey via HotkeyManager
            action.setStatusTip(f"{spec.tooltip} ({spec.shortcut})")

        if spec.checkable:
            action.setCheckable(True)

        if handler:
            action.triggered.connect(handler)
        else:
            self.logger.debug(f"No handler provided for action: {spec.id}")

        return action

    def _populate_profiles_menu(
        self,
        menu: QMenu,
        profiles: List[str],
        current_profile: Optional[str],
        handler: Optional[Callable],
    ):
        """
        Populate profiles submenu.

        Args:
            menu: QMenu to populate
            profiles: List of profile names
            current_profile: Currently active profile
            handler: Callback(profile_name) for selection
        """
        menu.clear()

        if not profiles:
            no_profiles = QAction("(No profiles saved)", menu)
            no_profiles.setEnabled(False)
            menu.addAction(no_profiles)
            return

        for profile in profiles:
            action = QAction(profile, menu)
            action.setCheckable(True)
            action.setChecked(profile == current_profile)

            if handler:
                # Create closure to capture profile name
                def make_callback(p=profile):
                    return lambda: handler(p)
                action.triggered.connect(make_callback())

            menu.addAction(action)


def build_toolbar_actions(
    home: PrimaryHome,
    handlers: Optional[Dict[str, Callable]] = None,
    registry: Optional[ActionRegistry] = None,
) -> List[QAction]:
    """
    Build a list of QActions for a toolbar.

    Args:
        home: PrimaryHome location (must be a toolbar type)
        handlers: Dict mapping action_id -> handler callable
        registry: Optional ActionRegistry instance

    Returns:
        List of QActions for the toolbar
    """
    if registry is None:
        registry = ActionRegistry.get_instance()

    handlers = handlers or {}
    builder = MenuBuilder(registry)
    actions = registry.get_by_home(home)

    return [
        builder._create_action(spec, None, handlers.get(spec.id))
        for spec in actions
    ]


class ContextMenuBuilder:
    """
    Builds context menus from the ActionRegistry.

    Context menus are for object-level actions (right-click on items).
    """

    def __init__(self, registry: Optional[ActionRegistry] = None):
        self.logger = logging.getLogger(__name__)
        self.registry = registry or ActionRegistry.get_instance()

    def build_window_context_menu(
        self,
        handlers: Dict[str, Callable],
        zoom_handler: Optional[Callable] = None,
        current_zoom: float = 0.3,
        parent=None,
    ) -> QMenu:
        """
        Build context menu for window preview frames.

        Args:
            handlers: Dict mapping action_id -> handler callable
            zoom_handler: Callback for zoom level changes (zoom_value)
            current_zoom: Current zoom level for checkmark
            parent: Parent widget

        Returns:
            QMenu for window context
        """
        menu = QMenu(parent)

        # Window actions from registry
        action_order = [
            "focus_window",
            "minimize_window",
            "close_window",
            None,  # separator
            "set_label",
            None,  # separator
            "zoom",  # special: submenu
            None,  # separator
            "remove_from_preview",
        ]

        for item in action_order:
            if item is None:
                menu.addSeparator()
            elif item == "zoom":
                # Zoom submenu (not from registry - dynamic state)
                zoom_menu = menu.addMenu("Zoom Level")
                for zoom in [0.2, 0.3, 0.4, 0.5]:
                    zoom_action = QAction(f"{int(zoom*100)}%", menu)
                    if zoom == current_zoom:
                        zoom_action.setCheckable(True)
                        zoom_action.setChecked(True)
                    if zoom_handler:
                        # Create closure to capture zoom value
                        def make_zoom_callback(z=zoom):
                            return lambda: zoom_handler(z)
                        zoom_action.triggered.connect(make_zoom_callback())
                    zoom_menu.addAction(zoom_action)
            else:
                spec = self.registry.get(item)
                if spec:
                    action = QAction(spec.label, menu)
                    if spec.tooltip:
                        action.setToolTip(spec.tooltip)
                    handler = handlers.get(item)
                    if handler:
                        action.triggered.connect(handler)
                    menu.addAction(action)

        return menu


class ToolbarBuilder:
    """
    Builds Qt toolbar widgets from the ActionRegistry.

    This creates QPushButton widgets rather than QActions, allowing for
    more control over styling and layout.
    """

    # Styling for specific action types
    PRIMARY_STYLE = """
        QPushButton {
            background-color: #ff8c00;
            color: black;
            font-weight: bold;
            padding: 5px 10px;
        }
        QPushButton:hover { background-color: #ffa500; }
    """

    SUCCESS_STYLE = """
        QPushButton {
            background-color: #2d5a27;
            color: white;
            padding: 5px 10px;
        }
        QPushButton:hover { background-color: #3d7a37; }
    """

    DANGER_STYLE = """
        QPushButton {
            background-color: #8b0000;
            color: white;
        }
        QPushButton:hover { background-color: #a50000; }
    """

    # Actions that get special styling
    PRIMARY_ACTIONS = {"import_windows", "apply_layout", "sync_settings", "save_hotkeys"}
    SUCCESS_ACTIONS = {"scan_eve_folder", "new_group", "load_active_windows", "new_team"}
    DANGER_ACTIONS = {"delete_group", "delete_character", "remove_all_windows"}

    def __init__(self, registry: Optional[ActionRegistry] = None):
        self.logger = logging.getLogger(__name__)
        self.registry = registry or ActionRegistry.get_instance()

    def build_toolbar_buttons(
        self,
        home: PrimaryHome,
        handlers: Dict[str, Callable],
        action_order: Optional[List[str]] = None,
        parent=None,
    ) -> Dict[str, QPushButton]:
        """
        Build toolbar buttons from the registry.

        Args:
            home: PrimaryHome location
            handlers: Dict mapping action_id -> handler callable
            action_order: Optional list of action IDs to specify order
            parent: Parent widget

        Returns:
            Dict mapping action_id -> QPushButton
        """
        actions = self.registry.get_by_home(home)
        buttons = {}

        # Use specified order or registry order
        if action_order:
            action_map = {a.id: a for a in actions}
            ordered_actions = [action_map[aid] for aid in action_order if aid in action_map]
        else:
            ordered_actions = actions

        for spec in ordered_actions:
            btn = QPushButton(spec.label, parent)

            if spec.tooltip:
                btn.setToolTip(spec.tooltip)

            if spec.checkable:
                btn.setCheckable(True)

            # Apply styling based on action type
            if spec.id in self.PRIMARY_ACTIONS:
                btn.setStyleSheet(self.PRIMARY_STYLE)
            elif spec.id in self.SUCCESS_ACTIONS:
                btn.setStyleSheet(self.SUCCESS_STYLE)
            elif spec.id in self.DANGER_ACTIONS:
                btn.setStyleSheet(self.DANGER_STYLE)

            # Connect handler
            handler = handlers.get(spec.id)
            if handler:
                btn.clicked.connect(handler)
            else:
                self.logger.debug(f"No handler for toolbar action: {spec.id}")

            buttons[spec.id] = btn

        return buttons

    def create_button(
        self,
        action_id: str,
        handler: Optional[Callable] = None,
        parent=None,
    ) -> Optional[QPushButton]:
        """
        Create a single button from a registry action.

        Args:
            action_id: Action ID from registry
            handler: Handler callable
            parent: Parent widget

        Returns:
            QPushButton or None if action not found
        """
        spec = self.registry.get(action_id)
        if not spec:
            self.logger.warning(f"Action not found: {action_id}")
            return None

        btn = QPushButton(spec.label, parent)

        if spec.tooltip:
            btn.setToolTip(spec.tooltip)

        if spec.checkable:
            btn.setCheckable(True)

        # Apply styling
        if spec.id in self.PRIMARY_ACTIONS:
            btn.setStyleSheet(self.PRIMARY_STYLE)
        elif spec.id in self.SUCCESS_ACTIONS:
            btn.setStyleSheet(self.SUCCESS_STYLE)
        elif spec.id in self.DANGER_ACTIONS:
            btn.setStyleSheet(self.DANGER_STYLE)

        if handler:
            btn.clicked.connect(handler)

        return btn
