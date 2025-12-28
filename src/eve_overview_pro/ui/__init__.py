"""
UI modules for EVE Veles Eyes

v2.3: Added ActionRegistry for UI action management
"""
from eve_overview_pro.ui.action_registry import (
    ActionRegistry,
    ActionScope,
    ActionSpec,
    PrimaryHome,
    audit_actions,
    print_audit_report,
)
from eve_overview_pro.ui.menu_builder import (
    ContextMenuBuilder,
    MenuBuilder,
    ToolbarBuilder,
    build_toolbar_actions,
)

__all__ = [
    "ActionRegistry",
    "ActionScope",
    "ActionSpec",
    "PrimaryHome",
    "ContextMenuBuilder",
    "MenuBuilder",
    "ToolbarBuilder",
    "audit_actions",
    "print_audit_report",
    "build_toolbar_actions",
]
