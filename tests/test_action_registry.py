"""
Unit tests for the ActionRegistry module.

Tests cover:
- ActionSpec creation
- ActionRegistry registration and lookup
- Filtering by home and scope
- Handler binding
- Audit functions for duplicate detection
"""
import pytest
from eve_overview_pro.ui.action_registry import (
    ActionSpec,
    ActionScope,
    PrimaryHome,
    ActionRegistry,
    HOME_TIERS,
    audit_actions,
)


class TestActionSpec:
    """Tests for ActionSpec dataclass"""

    def test_create_minimal_spec(self):
        """Create ActionSpec with minimal required fields"""
        spec = ActionSpec(
            id="test_action",
            label="Test Action",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
        )
        assert spec.id == "test_action"
        assert spec.label == "Test Action"
        assert spec.scope == ActionScope.GLOBAL
        assert spec.primary_home == PrimaryHome.TRAY_MENU
        assert spec.tooltip == ""
        assert spec.shortcut is None
        assert spec.handler_name is None
        assert spec.checkable is False

    def test_create_full_spec(self):
        """Create ActionSpec with all fields"""
        spec = ActionSpec(
            id="full_action",
            label="Full Action",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.OVERVIEW_TOOLBAR,
            tooltip="This is a tooltip",
            shortcut="<ctrl>+a",
            icon="test_icon",
            handler_name="_handle_action",
            enabled_when="has_selection",
            checkable=True,
        )
        assert spec.id == "full_action"
        assert spec.tooltip == "This is a tooltip"
        assert spec.shortcut == "<ctrl>+a"
        assert spec.icon == "test_icon"
        assert spec.handler_name == "_handle_action"
        assert spec.enabled_when == "has_selection"
        assert spec.checkable is True


class TestActionScope:
    """Tests for ActionScope enum"""

    def test_scope_values(self):
        """Verify all expected scopes exist"""
        assert ActionScope.GLOBAL
        assert ActionScope.TAB
        assert ActionScope.OBJECT

    def test_scope_uniqueness(self):
        """Verify scopes are distinct"""
        scopes = [ActionScope.GLOBAL, ActionScope.TAB, ActionScope.OBJECT]
        assert len(scopes) == len(set(scopes))


class TestPrimaryHome:
    """Tests for PrimaryHome enum"""

    def test_tier1_homes_exist(self):
        """Verify Tier 1 (Global) homes exist"""
        assert PrimaryHome.TRAY_MENU
        assert PrimaryHome.APP_MENU
        assert PrimaryHome.HELP_MENU

    def test_tier2_homes_exist(self):
        """Verify Tier 2 (Tab) homes exist"""
        assert PrimaryHome.OVERVIEW_TOOLBAR
        assert PrimaryHome.ROSTER_TOOLBAR
        assert PrimaryHome.LAYOUTS_TOOLBAR
        assert PrimaryHome.AUTOMATION_TOOLBAR
        assert PrimaryHome.SYNC_TOOLBAR
        assert PrimaryHome.SETTINGS_PANEL

    def test_tier3_homes_exist(self):
        """Verify Tier 3 (Object) homes exist"""
        assert PrimaryHome.WINDOW_CONTEXT
        assert PrimaryHome.CHARACTER_CONTEXT
        assert PrimaryHome.TEAM_CONTEXT
        assert PrimaryHome.GROUP_CONTEXT

    def test_all_homes_have_tiers(self):
        """All PrimaryHome values must be in HOME_TIERS"""
        for home in PrimaryHome:
            assert home in HOME_TIERS, f"{home} missing from HOME_TIERS"


class TestHomeTiers:
    """Tests for HOME_TIERS mapping"""

    def test_tier_values(self):
        """Tiers should be 1, 2, or 3"""
        for home, tier in HOME_TIERS.items():
            assert tier in [1, 2, 3], f"{home} has invalid tier {tier}"

    def test_tier1_assignments(self):
        """Verify Tier 1 homes"""
        assert HOME_TIERS[PrimaryHome.TRAY_MENU] == 1
        assert HOME_TIERS[PrimaryHome.APP_MENU] == 1
        assert HOME_TIERS[PrimaryHome.HELP_MENU] == 1

    def test_tier2_assignments(self):
        """Verify Tier 2 homes"""
        tier2_homes = [
            PrimaryHome.OVERVIEW_TOOLBAR,
            PrimaryHome.ROSTER_TOOLBAR,
            PrimaryHome.LAYOUTS_TOOLBAR,
            PrimaryHome.AUTOMATION_TOOLBAR,
            PrimaryHome.SYNC_TOOLBAR,
            PrimaryHome.SETTINGS_PANEL,
        ]
        for home in tier2_homes:
            assert HOME_TIERS[home] == 2, f"{home} should be Tier 2"

    def test_tier3_assignments(self):
        """Verify Tier 3 homes"""
        tier3_homes = [
            PrimaryHome.WINDOW_CONTEXT,
            PrimaryHome.CHARACTER_CONTEXT,
            PrimaryHome.TEAM_CONTEXT,
            PrimaryHome.GROUP_CONTEXT,
        ]
        for home in tier3_homes:
            assert HOME_TIERS[home] == 3, f"{home} should be Tier 3"


class TestActionRegistry:
    """Tests for ActionRegistry class"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset singleton before each test"""
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    def test_singleton_pattern(self):
        """Registry should be a singleton"""
        r1 = ActionRegistry.get_instance()
        r2 = ActionRegistry.get_instance()
        assert r1 is r2

    def test_reset_instance(self):
        """reset_instance should create new instance"""
        r1 = ActionRegistry.get_instance()
        ActionRegistry.reset_instance()
        r2 = ActionRegistry.get_instance()
        assert r1 is not r2

    def test_default_actions_registered(self):
        """Registry should have pre-registered actions"""
        registry = ActionRegistry.get_instance()
        actions = registry.all_actions()
        assert len(actions) > 0, "Should have default actions"

    def test_get_existing_action(self):
        """get() returns action for valid ID"""
        registry = ActionRegistry.get_instance()
        action = registry.get("quit")
        assert action is not None
        assert action.id == "quit"
        assert action.label == "Quit"

    def test_get_nonexistent_action(self):
        """get() returns None for invalid ID"""
        registry = ActionRegistry.get_instance()
        action = registry.get("nonexistent_action_xyz")
        assert action is None

    def test_get_by_home_tray_menu(self):
        """get_by_home returns actions for TRAY_MENU"""
        registry = ActionRegistry.get_instance()
        actions = registry.get_by_home(PrimaryHome.TRAY_MENU)
        assert len(actions) > 0
        # All returned actions should have TRAY_MENU as primary_home
        for action in actions:
            assert action.primary_home == PrimaryHome.TRAY_MENU

    def test_get_by_home_overview_toolbar(self):
        """get_by_home returns actions for OVERVIEW_TOOLBAR"""
        registry = ActionRegistry.get_instance()
        actions = registry.get_by_home(PrimaryHome.OVERVIEW_TOOLBAR)
        assert len(actions) > 0
        for action in actions:
            assert action.primary_home == PrimaryHome.OVERVIEW_TOOLBAR

    def test_get_by_scope_global(self):
        """get_by_scope returns GLOBAL actions"""
        registry = ActionRegistry.get_instance()
        actions = registry.get_by_scope(ActionScope.GLOBAL)
        assert len(actions) > 0
        for action in actions:
            assert action.scope == ActionScope.GLOBAL

    def test_get_by_scope_object(self):
        """get_by_scope returns OBJECT actions"""
        registry = ActionRegistry.get_instance()
        actions = registry.get_by_scope(ActionScope.OBJECT)
        assert len(actions) > 0
        for action in actions:
            assert action.scope == ActionScope.OBJECT

    def test_register_new_action(self):
        """Register custom action"""
        registry = ActionRegistry.get_instance()
        initial_count = len(registry.all_actions())

        custom = ActionSpec(
            id="custom_test",
            label="Custom Test",
            scope=ActionScope.TAB,
            primary_home=PrimaryHome.OVERVIEW_TOOLBAR,
        )
        registry.register(custom)

        assert len(registry.all_actions()) == initial_count + 1
        assert registry.get("custom_test") is custom

    def test_register_overwrites_duplicate_id(self):
        """Registering same ID overwrites existing"""
        registry = ActionRegistry.get_instance()

        spec1 = ActionSpec(
            id="dupe_test",
            label="First",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
        )
        spec2 = ActionSpec(
            id="dupe_test",
            label="Second",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
        )

        registry.register(spec1)
        registry.register(spec2)

        action = registry.get("dupe_test")
        assert action.label == "Second"

    def test_bind_and_get_handler(self):
        """bind_handler and get_handler work correctly"""
        registry = ActionRegistry.get_instance()

        called = []
        def handler():
            called.append(True)

        registry.bind_handler("quit", handler)
        retrieved = registry.get_handler("quit")
        assert retrieved is handler

        retrieved()
        assert len(called) == 1

    def test_invoke_calls_handler(self):
        """invoke() calls the bound handler"""
        registry = ActionRegistry.get_instance()

        result = []
        def handler(value):
            result.append(value)

        registry.bind_handler("quit", handler)
        registry.invoke("quit", "test_value")
        assert result == ["test_value"]

    def test_invoke_without_handler(self):
        """invoke() without handler doesn't crash"""
        registry = ActionRegistry.get_instance()
        # This should not raise
        registry.invoke("unbound_action")


class TestAuditActions:
    """Tests for audit_actions function"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset singleton before each test"""
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    def test_audit_default_registry_passes(self):
        """Default registry should pass audit (no duplicates)"""
        registry = ActionRegistry.get_instance()
        results = audit_actions(registry)

        assert results["passed"] is True
        assert len(results["duplicates"]) == 0

    def test_audit_counts_actions(self):
        """Audit should count total actions"""
        registry = ActionRegistry.get_instance()
        results = audit_actions(registry)

        assert results["total_actions"] == len(registry.all_actions())
        assert results["total_actions"] > 0

    def test_audit_groups_by_home(self):
        """Audit should group actions by home"""
        registry = ActionRegistry.get_instance()
        results = audit_actions(registry)

        assert "by_home" in results
        assert "tray_menu" in results["by_home"]
        assert len(results["by_home"]["tray_menu"]) > 0

    def test_audit_groups_by_scope(self):
        """Audit should group actions by scope"""
        registry = ActionRegistry.get_instance()
        results = audit_actions(registry)

        assert "by_scope" in results
        assert "GLOBAL" in results["by_scope"]
        assert "TAB" in results["by_scope"]
        assert "OBJECT" in results["by_scope"]

    def test_audit_detects_missing_handlers(self):
        """Audit should warn about missing handler_name"""
        registry = ActionRegistry.get_instance()

        # Add action without handler
        spec = ActionSpec(
            id="no_handler_test",
            label="No Handler",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.TRAY_MENU,
            handler_name=None,
        )
        registry.register(spec)

        results = audit_actions(registry)
        assert any("no_handler_test" in issue for issue in results["issues"])


class TestRegistryActionCoverage:
    """Tests verifying expected actions are registered"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    def test_quit_action_exists(self):
        """quit action should exist"""
        registry = ActionRegistry.get_instance()
        action = registry.get("quit")
        assert action is not None
        assert action.scope == ActionScope.GLOBAL
        assert action.primary_home == PrimaryHome.TRAY_MENU

    def test_about_action_exists(self):
        """about action should exist"""
        registry = ActionRegistry.get_instance()
        action = registry.get("about")
        assert action is not None
        assert action.primary_home == PrimaryHome.HELP_MENU

    def test_import_windows_action_exists(self):
        """import_windows action should exist"""
        registry = ActionRegistry.get_instance()
        action = registry.get("import_windows")
        assert action is not None
        assert action.primary_home == PrimaryHome.OVERVIEW_TOOLBAR

    def test_focus_window_action_exists(self):
        """focus_window context action should exist"""
        registry = ActionRegistry.get_instance()
        action = registry.get("focus_window")
        assert action is not None
        assert action.scope == ActionScope.OBJECT
        assert action.primary_home == PrimaryHome.WINDOW_CONTEXT

    def test_lock_positions_is_checkable(self):
        """lock_positions should be checkable"""
        registry = ActionRegistry.get_instance()
        action = registry.get("lock_positions")
        assert action is not None
        assert action.checkable is True

    def test_minimize_all_has_shortcut(self):
        """minimize_all should have shortcut"""
        registry = ActionRegistry.get_instance()
        action = registry.get("minimize_all")
        assert action is not None
        assert action.shortcut == "<ctrl>+<shift>+m"

    def test_all_actions_have_labels(self):
        """All actions must have non-empty labels"""
        registry = ActionRegistry.get_instance()
        for action in registry.all_actions():
            assert action.label, f"Action {action.id} has no label"
            assert len(action.label) > 0

    def test_all_actions_have_valid_scope(self):
        """All actions must have valid scope"""
        registry = ActionRegistry.get_instance()
        for action in registry.all_actions():
            assert action.scope in ActionScope

    def test_all_actions_have_valid_home(self):
        """All actions must have valid primary_home"""
        registry = ActionRegistry.get_instance()
        for action in registry.all_actions():
            assert action.primary_home in PrimaryHome

    def test_expected_action_count(self):
        """Registry should have expected number of actions (42)"""
        registry = ActionRegistry.get_instance()
        actions = registry.all_actions()
        # Allow some flexibility for future additions
        assert len(actions) >= 40, f"Expected ~42 actions, got {len(actions)}"
