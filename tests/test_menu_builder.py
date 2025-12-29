"""
Unit tests for the MenuBuilder module.

Tests cover:
- ToolbarBuilder styling logic
- ContextMenuBuilder structure
- MenuBuilder action ordering

Note: These tests focus on logic that can be tested without a full Qt display.
Full integration tests would require pytest-qt and a display.
"""
import pytest
from unittest.mock import MagicMock, patch

from eve_overview_pro.ui.action_registry import (
    ActionSpec,
    ActionScope,
    PrimaryHome,
    ActionRegistry,
)
from eve_overview_pro.ui.menu_builder import (
    MenuBuilder,
    ToolbarBuilder,
    ContextMenuBuilder,
    build_toolbar_actions,
)


class TestToolbarBuilderStyling:
    """Tests for ToolbarBuilder styling constants"""

    def test_primary_actions_defined(self):
        """PRIMARY_ACTIONS set should exist"""
        assert hasattr(ToolbarBuilder, "PRIMARY_ACTIONS")
        assert "import_windows" in ToolbarBuilder.PRIMARY_ACTIONS
        assert "apply_layout" in ToolbarBuilder.PRIMARY_ACTIONS
        assert "sync_settings" in ToolbarBuilder.PRIMARY_ACTIONS
        assert "save_hotkeys" in ToolbarBuilder.PRIMARY_ACTIONS

    def test_success_actions_defined(self):
        """SUCCESS_ACTIONS set should exist"""
        assert hasattr(ToolbarBuilder, "SUCCESS_ACTIONS")
        assert "scan_eve_folder" in ToolbarBuilder.SUCCESS_ACTIONS
        assert "new_group" in ToolbarBuilder.SUCCESS_ACTIONS
        assert "load_active_windows" in ToolbarBuilder.SUCCESS_ACTIONS
        assert "new_team" in ToolbarBuilder.SUCCESS_ACTIONS

    def test_danger_actions_defined(self):
        """DANGER_ACTIONS set should exist"""
        assert hasattr(ToolbarBuilder, "DANGER_ACTIONS")
        assert "delete_group" in ToolbarBuilder.DANGER_ACTIONS
        assert "delete_character" in ToolbarBuilder.DANGER_ACTIONS
        assert "remove_all_windows" in ToolbarBuilder.DANGER_ACTIONS

    def test_primary_style_has_orange(self):
        """PRIMARY_STYLE should use orange color"""
        assert "#ff8c00" in ToolbarBuilder.PRIMARY_STYLE.lower()

    def test_success_style_has_green(self):
        """SUCCESS_STYLE should use green color"""
        assert "#2d5a27" in ToolbarBuilder.SUCCESS_STYLE.lower()

    def test_danger_style_has_red(self):
        """DANGER_STYLE should use red color"""
        assert "#8b0000" in ToolbarBuilder.DANGER_STYLE.lower()

    def test_no_overlap_between_action_sets(self):
        """Action styling sets should not overlap"""
        primary = ToolbarBuilder.PRIMARY_ACTIONS
        success = ToolbarBuilder.SUCCESS_ACTIONS
        danger = ToolbarBuilder.DANGER_ACTIONS

        assert primary.isdisjoint(success), "PRIMARY and SUCCESS overlap"
        assert primary.isdisjoint(danger), "PRIMARY and DANGER overlap"
        assert success.isdisjoint(danger), "SUCCESS and DANGER overlap"


class TestToolbarBuilderInit:
    """Tests for ToolbarBuilder initialization"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    def test_uses_provided_registry(self):
        """Builder should use provided registry"""
        registry = ActionRegistry.get_instance()
        builder = ToolbarBuilder(registry)
        assert builder.registry is registry

    def test_uses_singleton_when_none(self):
        """Builder should use singleton when no registry provided"""
        builder = ToolbarBuilder(None)
        assert builder.registry is ActionRegistry.get_instance()


class TestMenuBuilderInit:
    """Tests for MenuBuilder initialization"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    def test_uses_provided_registry(self):
        """Builder should use provided registry"""
        registry = ActionRegistry.get_instance()
        builder = MenuBuilder(registry)
        assert builder.registry is registry

    def test_uses_singleton_when_none(self):
        """Builder should use singleton when no registry provided"""
        builder = MenuBuilder(None)
        assert builder.registry is ActionRegistry.get_instance()


class TestContextMenuBuilderInit:
    """Tests for ContextMenuBuilder initialization"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    def test_uses_provided_registry(self):
        """Builder should use provided registry"""
        registry = ActionRegistry.get_instance()
        builder = ContextMenuBuilder(registry)
        assert builder.registry is registry

    def test_uses_singleton_when_none(self):
        """Builder should use singleton when no registry provided"""
        builder = ContextMenuBuilder(None)
        assert builder.registry is ActionRegistry.get_instance()


class TestToolbarBuilderLogic:
    """Tests for ToolbarBuilder create_button logic (mocked Qt)"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    def test_create_button_returns_none_for_unknown_action(self):
        """create_button returns None for unknown action ID"""
        builder = ToolbarBuilder()

        # Mock QPushButton at the point of import inside the method
        with patch.dict("sys.modules", {"PySide6.QtWidgets": MagicMock()}):
            with patch("PySide6.QtWidgets.QPushButton") as MockButton:
                mock_btn = MagicMock()
                MockButton.return_value = mock_btn
                result = builder.create_button("nonexistent_action_xyz")
                assert result is None

    def test_create_button_finds_existing_action(self):
        """create_button finds action from registry"""
        builder = ToolbarBuilder()
        # The action exists in registry - verify spec is found
        spec = builder.registry.get("import_windows")
        assert spec is not None
        assert spec.id == "import_windows"

    def test_action_in_primary_set(self):
        """import_windows should be in PRIMARY_ACTIONS"""
        assert "import_windows" in ToolbarBuilder.PRIMARY_ACTIONS

    def test_action_in_success_set(self):
        """new_team should be in SUCCESS_ACTIONS"""
        assert "new_team" in ToolbarBuilder.SUCCESS_ACTIONS

    def test_action_in_danger_set(self):
        """delete_group should be in DANGER_ACTIONS"""
        assert "delete_group" in ToolbarBuilder.DANGER_ACTIONS

    def test_checkable_action_spec(self):
        """lock_positions spec should have checkable=True"""
        builder = ToolbarBuilder()
        spec = builder.registry.get("lock_positions")
        assert spec is not None
        assert spec.checkable is True

    def test_action_with_handler_name(self):
        """Actions should have handler_name defined"""
        builder = ToolbarBuilder()
        spec = builder.registry.get("quit")
        assert spec is not None
        assert spec.handler_name is not None


class TestBuildToolbarActions:
    """Tests for build_toolbar_actions helper function"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    def test_returns_list(self):
        """Function returns a list"""
        with patch("eve_overview_pro.ui.menu_builder.MenuBuilder") as MockBuilder:
            mock_builder = MagicMock()
            MockBuilder.return_value = mock_builder
            mock_builder._create_action.return_value = MagicMock()

            result = build_toolbar_actions(PrimaryHome.OVERVIEW_TOOLBAR)
            assert isinstance(result, list)


class TestActionRegistryIntegration:
    """Integration tests verifying builders work with real registry"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    def test_toolbar_builder_finds_overview_actions(self):
        """ToolbarBuilder can find Overview toolbar actions"""
        builder = ToolbarBuilder()
        registry = builder.registry

        actions = registry.get_by_home(PrimaryHome.OVERVIEW_TOOLBAR)
        assert len(actions) > 0, "Should have Overview toolbar actions"

        # Verify expected actions
        action_ids = [a.id for a in actions]
        assert "import_windows" in action_ids
        assert "add_window" in action_ids

    def test_toolbar_builder_finds_roster_actions(self):
        """ToolbarBuilder can find Roster toolbar actions"""
        builder = ToolbarBuilder()
        registry = builder.registry

        actions = registry.get_by_home(PrimaryHome.ROSTER_TOOLBAR)
        assert len(actions) > 0, "Should have Roster toolbar actions"

        action_ids = [a.id for a in actions]
        assert "add_character" in action_ids
        assert "scan_eve_folder" in action_ids

    def test_menu_builder_finds_tray_actions(self):
        """MenuBuilder can find tray menu actions"""
        builder = MenuBuilder()
        registry = builder.registry

        actions = registry.get_by_home(PrimaryHome.TRAY_MENU)
        assert len(actions) > 0, "Should have tray menu actions"

        action_ids = [a.id for a in actions]
        assert "quit" in action_ids
        assert "show_hide" in action_ids

    def test_menu_builder_finds_help_actions(self):
        """MenuBuilder can find help menu actions"""
        builder = MenuBuilder()
        registry = builder.registry

        actions = registry.get_by_home(PrimaryHome.HELP_MENU)
        assert len(actions) > 0, "Should have help menu actions"

        action_ids = [a.id for a in actions]
        assert "about" in action_ids
        assert "donate" in action_ids

    def test_context_builder_finds_window_actions(self):
        """ContextMenuBuilder can find window context actions"""
        builder = ContextMenuBuilder()
        registry = builder.registry

        actions = registry.get_by_home(PrimaryHome.WINDOW_CONTEXT)
        assert len(actions) > 0, "Should have window context actions"

        action_ids = [a.id for a in actions]
        assert "focus_window" in action_ids
        assert "minimize_window" in action_ids
        assert "close_window" in action_ids
