"""
Unit tests for the MenuBuilder module.

Tests cover:
- ToolbarBuilder styling logic
- ContextMenuBuilder structure
- MenuBuilder action ordering

Note: These tests focus on logic that can be tested without a full Qt display.
Full integration tests would require pytest-qt and a display.
"""
from unittest.mock import MagicMock, patch

import pytest

from eve_overview_pro.ui.action_registry import (
    ActionRegistry,
    ActionScope,
    ActionSpec,
    PrimaryHome,
)
from eve_overview_pro.ui.menu_builder import (
    ContextMenuBuilder,
    MenuBuilder,
    ToolbarBuilder,
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

    def test_toolbar_builder_finds_layouts_actions(self):
        """ToolbarBuilder can find Layouts toolbar actions"""
        builder = ToolbarBuilder()
        registry = builder.registry

        actions = registry.get_by_home(PrimaryHome.LAYOUTS_TOOLBAR)
        assert len(actions) >= 4, "Should have at least 4 Layouts toolbar actions"

        action_ids = [a.id for a in actions]
        assert "apply_layout" in action_ids
        assert "auto_arrange" in action_ids
        assert "save_layout_preset" in action_ids
        assert "refresh_layout_groups" in action_ids


class TestMenuBuilderBuildMenu:
    """Tests for MenuBuilder.build_menu method"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QMenu')
    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_build_menu_creates_menu(self, mock_action, mock_menu):
        """build_menu creates QMenu with actions"""
        mock_menu_instance = MagicMock()
        mock_menu.return_value = mock_menu_instance

        builder = MenuBuilder()
        result = builder.build_menu(PrimaryHome.HELP_MENU)

        assert result == mock_menu_instance
        assert mock_menu_instance.addAction.called

    @patch('eve_overview_pro.ui.menu_builder.QMenu')
    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_build_menu_uses_existing_menu(self, mock_action, mock_menu):
        """build_menu can add to existing menu"""
        existing_menu = MagicMock()

        builder = MenuBuilder()
        result = builder.build_menu(PrimaryHome.HELP_MENU, menu=existing_menu)

        assert result == existing_menu


class TestMenuBuilderBuildTrayMenu:
    """Tests for MenuBuilder.build_tray_menu method"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QMenu')
    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_build_tray_menu_creates_menu(self, mock_action, mock_menu):
        """build_tray_menu creates menu with actions"""
        mock_menu_instance = MagicMock()
        mock_menu.return_value = mock_menu_instance

        builder = MenuBuilder()
        result = builder.build_tray_menu()

        assert result == mock_menu_instance
        assert mock_menu_instance.addSeparator.called

    @patch('eve_overview_pro.ui.menu_builder.QMenu')
    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_build_tray_menu_with_profiles(self, mock_action, mock_menu):
        """build_tray_menu includes profiles submenu"""
        mock_menu_instance = MagicMock()
        mock_submenu = MagicMock()
        mock_menu.return_value = mock_menu_instance
        mock_menu_instance.addMenu.return_value = mock_submenu

        builder = MenuBuilder()
        builder.build_tray_menu(profiles=["Profile1", "Profile2"])

        mock_menu_instance.addMenu.assert_called_with("Profiles")


class TestMenuBuilderBuildHelpMenu:
    """Tests for MenuBuilder.build_help_menu method"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QMenu')
    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_build_help_menu_creates_menu(self, mock_action, mock_menu):
        """build_help_menu creates Help menu"""
        mock_menu_instance = MagicMock()
        mock_menu.return_value = mock_menu_instance

        builder = MenuBuilder()
        result = builder.build_help_menu()

        assert result == mock_menu_instance
        mock_menu.assert_called_with("&Help", None)


class TestMenuBuilderCreateAction:
    """Tests for MenuBuilder._create_action method"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_create_action_sets_label(self, mock_action):
        """_create_action sets action label"""
        mock_action_instance = MagicMock()
        mock_action.return_value = mock_action_instance

        builder = MenuBuilder()
        spec = ActionSpec(
            id="test",
            label="Test Action",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.HELP_MENU
        )

        builder._create_action(spec)

        mock_action.assert_called_with("Test Action", None)

    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_create_action_sets_tooltip(self, mock_action):
        """_create_action sets tooltip"""
        mock_action_instance = MagicMock()
        mock_action.return_value = mock_action_instance

        builder = MenuBuilder()
        spec = ActionSpec(
            id="test",
            label="Test",
            tooltip="Test tooltip",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.HELP_MENU
        )

        builder._create_action(spec)

        mock_action_instance.setToolTip.assert_called_with("Test tooltip")

    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_create_action_sets_checkable(self, mock_action):
        """_create_action sets checkable"""
        mock_action_instance = MagicMock()
        mock_action.return_value = mock_action_instance

        builder = MenuBuilder()
        spec = ActionSpec(
            id="test",
            label="Test",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.HELP_MENU,
            checkable=True
        )

        builder._create_action(spec)

        mock_action_instance.setCheckable.assert_called_with(True)

    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_create_action_connects_handler(self, mock_action):
        """_create_action connects handler"""
        mock_action_instance = MagicMock()
        mock_action.return_value = mock_action_instance
        handler = MagicMock()

        builder = MenuBuilder()
        spec = ActionSpec(
            id="test",
            label="Test",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.HELP_MENU
        )

        builder._create_action(spec, handler=handler)

        mock_action_instance.triggered.connect.assert_called_with(handler)


class TestMenuBuilderPopulateProfiles:
    """Tests for MenuBuilder._populate_profiles_menu method"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_populate_profiles_empty(self, mock_action):
        """Shows 'No profiles saved' when empty"""
        mock_action_instance = MagicMock()
        mock_action.return_value = mock_action_instance

        builder = MenuBuilder()
        mock_menu = MagicMock()

        builder._populate_profiles_menu(mock_menu, [], None, None)

        mock_menu.clear.assert_called_once()
        mock_action.assert_called_with("(No profiles saved)", mock_menu)
        mock_action_instance.setEnabled.assert_called_with(False)

    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_populate_profiles_with_profiles(self, mock_action):
        """Adds action for each profile"""
        mock_action_instance = MagicMock()
        mock_action.return_value = mock_action_instance

        builder = MenuBuilder()
        mock_menu = MagicMock()

        builder._populate_profiles_menu(
            mock_menu,
            ["Profile1", "Profile2"],
            "Profile1",
            MagicMock()
        )

        assert mock_action.call_count == 2
        mock_action_instance.setCheckable.assert_called_with(True)


class TestContextMenuBuilderBuildWindowContext:
    """Tests for ContextMenuBuilder.build_window_context_menu method"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QMenu')
    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_build_window_context_menu(self, mock_action, mock_menu):
        """build_window_context_menu creates menu"""
        mock_menu_instance = MagicMock()
        mock_submenu = MagicMock()
        mock_menu.return_value = mock_menu_instance
        mock_menu_instance.addMenu.return_value = mock_submenu

        builder = ContextMenuBuilder()
        handlers = {"focus_window": MagicMock()}

        result = builder.build_window_context_menu(handlers)

        assert result == mock_menu_instance
        mock_menu_instance.addSeparator.assert_called()
        mock_menu_instance.addMenu.assert_called_with("Zoom Level")


class TestToolbarBuilderBuildButtons:
    """Tests for ToolbarBuilder.build_toolbar_buttons method"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QPushButton')
    def test_build_toolbar_buttons_returns_dict(self, mock_button):
        """build_toolbar_buttons returns dict of buttons"""
        mock_button_instance = MagicMock()
        mock_button.return_value = mock_button_instance

        builder = ToolbarBuilder()
        handlers = {"import_windows": MagicMock()}

        result = builder.build_toolbar_buttons(PrimaryHome.OVERVIEW_TOOLBAR, handlers)

        assert isinstance(result, dict)
        assert "import_windows" in result

    @patch('eve_overview_pro.ui.menu_builder.QPushButton')
    def test_build_toolbar_buttons_custom_order(self, mock_button):
        """build_toolbar_buttons respects custom order"""
        mock_button_instance = MagicMock()
        mock_button.return_value = mock_button_instance

        builder = ToolbarBuilder()
        handlers = {}

        result = builder.build_toolbar_buttons(
            PrimaryHome.OVERVIEW_TOOLBAR,
            handlers,
            action_order=["import_windows"]
        )

        # Should only include the ordered action
        assert "import_windows" in result


class TestToolbarBuilderCreateButton:
    """Tests for ToolbarBuilder.create_button method"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QPushButton')
    def test_create_button_primary_style(self, mock_button):
        """create_button applies PRIMARY_STYLE for primary actions"""
        mock_button_instance = MagicMock()
        mock_button.return_value = mock_button_instance

        builder = ToolbarBuilder()
        result = builder.create_button("import_windows")

        assert result == mock_button_instance
        mock_button_instance.setStyleSheet.assert_called()
        # Check that primary style (orange) was applied
        call_args = mock_button_instance.setStyleSheet.call_args[0][0]
        assert "#ff8c00" in call_args

    @patch('eve_overview_pro.ui.menu_builder.QPushButton')
    def test_create_button_success_style(self, mock_button):
        """create_button applies SUCCESS_STYLE for success actions"""
        mock_button_instance = MagicMock()
        mock_button.return_value = mock_button_instance

        builder = ToolbarBuilder()
        builder.create_button("new_team")

        mock_button_instance.setStyleSheet.assert_called()
        call_args = mock_button_instance.setStyleSheet.call_args[0][0]
        assert "#2d5a27" in call_args

    @patch('eve_overview_pro.ui.menu_builder.QPushButton')
    def test_create_button_danger_style(self, mock_button):
        """create_button applies DANGER_STYLE for danger actions"""
        mock_button_instance = MagicMock()
        mock_button.return_value = mock_button_instance

        builder = ToolbarBuilder()
        builder.create_button("delete_group")

        mock_button_instance.setStyleSheet.assert_called()
        call_args = mock_button_instance.setStyleSheet.call_args[0][0]
        assert "#8b0000" in call_args

    @patch('eve_overview_pro.ui.menu_builder.QPushButton')
    def test_create_button_connects_handler(self, mock_button):
        """create_button connects handler"""
        mock_button_instance = MagicMock()
        mock_button.return_value = mock_button_instance
        handler = MagicMock()

        builder = ToolbarBuilder()
        builder.create_button("import_windows", handler=handler)

        mock_button_instance.clicked.connect.assert_called_with(handler)

    @patch('eve_overview_pro.ui.menu_builder.QPushButton')
    def test_create_button_checkable(self, mock_button):
        """create_button sets checkable when spec has checkable=True"""
        mock_button_instance = MagicMock()
        mock_button.return_value = mock_button_instance

        # Register a checkable action
        registry = ActionRegistry.get_instance()
        registry.register(ActionSpec(
            id="test_checkable",
            label="Test Checkable",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.OVERVIEW_TOOLBAR,
            checkable=True
        ))

        builder = ToolbarBuilder()
        builder.create_button("test_checkable")

        mock_button_instance.setCheckable.assert_called_with(True)


class TestToolbarBuilderBuildButtonsSuccessStyle:
    """Tests for ToolbarBuilder SUCCESS_STYLE in build_toolbar_buttons"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QPushButton')
    def test_build_toolbar_buttons_success_style(self, mock_button):
        """build_toolbar_buttons applies SUCCESS_STYLE for success actions"""
        mock_button_instance = MagicMock()
        mock_button.return_value = mock_button_instance

        # Register a success action (scan_eve_folder is in SUCCESS_ACTIONS)
        registry = ActionRegistry.get_instance()
        registry.register(ActionSpec(
            id="scan_eve_folder",
            label="Scan",
            scope=ActionScope.GLOBAL,
            primary_home=PrimaryHome.SYNC_TOOLBAR
        ))

        builder = ToolbarBuilder()
        # Call build_toolbar_buttons which uses SUCCESS_STYLE for scan_eve_folder
        result = builder.build_toolbar_buttons(
            PrimaryHome.SYNC_TOOLBAR,
            {"scan_eve_folder": MagicMock()},
            action_order=["scan_eve_folder"]
        )

        assert "scan_eve_folder" in result
        # Verify setStyleSheet was called
        assert mock_button_instance.setStyleSheet.called


class TestContextMenuBuilderZoomHandler:
    """Tests for ContextMenuBuilder zoom_handler callback"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        ActionRegistry.reset_instance()
        yield
        ActionRegistry.reset_instance()

    @patch('eve_overview_pro.ui.menu_builder.QMenu')
    @patch('eve_overview_pro.ui.menu_builder.QAction')
    def test_build_window_context_menu_with_zoom_handler(self, mock_action, mock_menu):
        """build_window_context_menu connects zoom_handler callback"""
        mock_menu_instance = MagicMock()
        mock_submenu = MagicMock()
        mock_menu.return_value = mock_menu_instance
        mock_menu_instance.addMenu.return_value = mock_submenu

        mock_action_instance = MagicMock()
        mock_action.return_value = mock_action_instance

        zoom_handler = MagicMock()
        builder = ContextMenuBuilder()
        handlers = {"focus_window": MagicMock()}

        # Pass zoom_handler as a separate parameter (not in handlers dict)
        builder.build_window_context_menu(handlers, zoom_handler=zoom_handler, current_zoom=0.5)

        # Verify triggered.connect was called for zoom actions
        assert mock_action_instance.triggered.connect.called
