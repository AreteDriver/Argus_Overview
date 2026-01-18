"""
Unit tests for the Hotkeys & Cycling Tab module
Tests DraggableCharacterList, CyclingGroupList, HotkeysTab
"""

from unittest.mock import MagicMock, patch


# Test DraggableCharacterList
class TestDraggableCharacterList:
    """Tests for DraggableCharacterList widget"""

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_init_enables_drag(self, mock_init):
        """Test that init enables drag"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import DraggableCharacterList

        with patch.object(DraggableCharacterList, "setDragEnabled") as mock_drag:
            with patch.object(DraggableCharacterList, "setDefaultDropAction"):
                with patch.object(DraggableCharacterList, "setSelectionMode"):
                    with patch.object(DraggableCharacterList, "setAlternatingRowColors"):
                        DraggableCharacterList()

                        mock_drag.assert_called_once_with(True)


# Test CyclingGroupList
class TestCyclingGroupList:
    """Tests for CyclingGroupList widget"""

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_init_accepts_drops(self, mock_init):
        """Test that init enables drop accepting"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, "setAcceptDrops") as mock_drops:
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    CyclingGroupList()

                                    mock_drops.assert_called_once_with(True)

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_get_members_empty(self, mock_init):
        """Test get_members with empty list"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    with patch.object(CyclingGroupList, "count", return_value=0):
                                        list_widget = CyclingGroupList()

                                        result = list_widget.get_members()

                                        assert result == []

    def test_signal_exists(self):
        """Test that members_changed signal exists"""
        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        assert hasattr(CyclingGroupList, "members_changed")


# Test HotkeysTab
class TestHotkeysTab:
    """Tests for HotkeysTab widget"""

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test HotkeysTab initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            with patch.object(HotkeysTab, "_load_groups"):
                tab = HotkeysTab(mock_char_manager, mock_settings_manager)

                assert tab.character_manager is mock_char_manager
                assert tab.settings_manager is mock_settings_manager

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_load_groups_creates_default(self, mock_widget):
        """Test that _load_groups creates Default group if missing"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}  # No groups

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            assert "Default" in tab.cycling_groups
            assert tab.cycling_groups["Default"] == []


# Test format_hotkey helper
class TestFormatHotkey:
    """Tests for _format_hotkey method"""

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_format_simple_combo(self, mock_widget):
        """Test formatting simple key combo"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab._format_hotkey("ctrl+shift+]")

            assert result == "<ctrl>+<shift>+<]>"

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_format_already_bracketed(self, mock_widget):
        """Test formatting already bracketed keys"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab._format_hotkey("<ctrl>+<shift>+<]>")

            assert result == "<ctrl>+<shift>+<]>"

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_format_empty(self, mock_widget):
        """Test formatting empty string"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab._format_hotkey("")

            assert result == ""


# Test group management
class TestGroupManagement:
    """Tests for cycling group management"""

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_get_cycling_group(self, mock_widget):
        """Test get_cycling_group method"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {"TestGroup": ["Char1", "Char2"]}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab.get_cycling_group("TestGroup")

            assert result == ["Char1", "Char2"]

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_get_nonexistent_group(self, mock_widget):
        """Test get_cycling_group for nonexistent group"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab.get_cycling_group("NonexistentGroup")

            assert result == []

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_get_all_groups(self, mock_widget):
        """Test get_all_groups method"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {"Group1": ["A", "B"], "Group2": ["C", "D"]}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab.get_all_groups()

            assert "Group1" in result
            assert "Group2" in result
            assert "Default" in result  # Always added


# Test signal definitions
class TestSignals:
    """Tests for signal definitions"""

    def test_hotkeys_tab_signal_exists(self):
        """Test HotkeysTab has group_changed signal"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        assert hasattr(HotkeysTab, "group_changed")

    def test_cycling_group_list_signal_exists(self):
        """Test CyclingGroupList has members_changed signal"""
        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        assert hasattr(CyclingGroupList, "members_changed")


# =============================================================================
# Additional tests to improve coverage
# =============================================================================


class TestCyclingGroupListDragDrop:
    """Tests for CyclingGroupList drag and drop functionality"""

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_drag_enter_accepts_text(self, mock_init):
        """Test dragEnterEvent accepts text MIME data"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    list_widget = CyclingGroupList()

                                    mock_event = MagicMock()
                                    mock_event.mimeData.return_value.hasText.return_value = True

                                    list_widget.dragEnterEvent(mock_event)

                                    mock_event.acceptProposedAction.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_drag_enter_accepts_from_self(self, mock_init):
        """Test dragEnterEvent accepts from self (reorder)"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    list_widget = CyclingGroupList()

                                    mock_event = MagicMock()
                                    mock_event.mimeData.return_value.hasText.return_value = False
                                    mock_event.source.return_value = list_widget

                                    list_widget.dragEnterEvent(mock_event)

                                    mock_event.acceptProposedAction.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_drag_enter_accepts_from_character_list(self, mock_init):
        """Test dragEnterEvent accepts from DraggableCharacterList"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList, DraggableCharacterList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    list_widget = CyclingGroupList()

                                    # Create mock source that is DraggableCharacterList
                                    mock_source = MagicMock(spec=DraggableCharacterList)
                                    mock_event = MagicMock()
                                    mock_event.mimeData.return_value.hasText.return_value = False
                                    mock_event.source.return_value = mock_source

                                    list_widget.dragEnterEvent(mock_event)

                                    mock_event.acceptProposedAction.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_drag_enter_ignores_other_sources(self, mock_init):
        """Test dragEnterEvent ignores other sources"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    list_widget = CyclingGroupList()

                                    mock_event = MagicMock()
                                    mock_event.mimeData.return_value.hasText.return_value = False
                                    mock_event.source.return_value = MagicMock()  # Unknown source

                                    list_widget.dragEnterEvent(mock_event)

                                    mock_event.ignore.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_drag_move_accepts(self, mock_init):
        """Test dragMoveEvent accepts proposed action"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    list_widget = CyclingGroupList()

                                    mock_event = MagicMock()

                                    list_widget.dragMoveEvent(mock_event)

                                    mock_event.acceptProposedAction.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QListWidget.dropEvent")
    def test_drop_from_self_reorders(self, mock_super_drop, mock_init):
        """Test dropEvent from self triggers reorder"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    list_widget = CyclingGroupList()
                                    list_widget.members_changed = MagicMock()

                                    mock_event = MagicMock()
                                    mock_event.source.return_value = list_widget

                                    list_widget.dropEvent(mock_event)

                                    mock_super_drop.assert_called_once()
                                    list_widget.members_changed.emit.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QListWidgetItem")
    def test_drop_from_character_list_adds_items(self, mock_item, mock_init):
        """Test dropEvent from character list adds items"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList, DraggableCharacterList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    with patch.object(CyclingGroupList, "count", return_value=0):
                                        with patch.object(
                                            CyclingGroupList, "item", return_value=None
                                        ):
                                            with patch.object(CyclingGroupList, "addItem"):
                                                list_widget = CyclingGroupList()
                                                list_widget.members_changed = MagicMock()

                                                # Mock source as DraggableCharacterList
                                                mock_source = MagicMock(spec=DraggableCharacterList)
                                                mock_char_item = MagicMock()
                                                mock_char_item.text.return_value = "TestChar"
                                                mock_source.selectedItems.return_value = [
                                                    mock_char_item
                                                ]

                                                mock_event = MagicMock()
                                                mock_event.source.return_value = mock_source

                                                list_widget.dropEvent(mock_event)

                                                list_widget.members_changed.emit.assert_called_once()
                                                mock_event.acceptProposedAction.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_drop_ignores_other_sources(self, mock_init):
        """Test dropEvent ignores other sources"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    list_widget = CyclingGroupList()

                                    mock_event = MagicMock()
                                    mock_event.source.return_value = MagicMock()  # Unknown

                                    list_widget.dropEvent(mock_event)

                                    mock_event.ignore.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QListWidget.__init__")
    def test_get_members_with_items(self, mock_init):
        """Test get_members with items in list"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, "setAcceptDrops"):
            with patch.object(CyclingGroupList, "setDragEnabled"):
                with patch.object(CyclingGroupList, "setDragDropMode"):
                    with patch.object(CyclingGroupList, "setDefaultDropAction"):
                        with patch.object(CyclingGroupList, "setSelectionMode"):
                            with patch.object(CyclingGroupList, "setAlternatingRowColors"):
                                with patch.object(CyclingGroupList, "setStyleSheet"):
                                    list_widget = CyclingGroupList()

                                    # Mock count and items
                                    with patch.object(list_widget, "count", return_value=2):
                                        mock_item1 = MagicMock()
                                        mock_item1.text.return_value = "Char1"
                                        mock_item2 = MagicMock()
                                        mock_item2.text.return_value = "Char2"

                                        with patch.object(
                                            list_widget,
                                            "item",
                                            side_effect=[mock_item1, mock_item2],
                                        ):
                                            result = list_widget.get_members()

                                            assert result == ["Char1", "Char2"]


class TestHotkeysTabInteraction:
    """Tests for HotkeysTab interaction methods"""

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_save_groups(self, mock_widget):
        """Test _save_groups saves to settings"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.cycling_groups = {"Test": ["A", "B"]}

            tab._save_groups()

            mock_settings_manager.set.assert_called_with(
                "cycling_groups", {"Test": ["A", "B"]}, auto_save=True
            )

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_load_groups_with_invalid_data(self, mock_widget):
        """Test _load_groups handles invalid data"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = "invalid"  # Not a dict

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            assert tab.cycling_groups == {"Default": []}

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_on_group_selected(self, mock_widget):
        """Test _on_group_selected loads members"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {"TestGroup": ["A", "B"]}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab._load_group_members = MagicMock()

            tab._on_group_selected("TestGroup")

            assert tab.current_group == "TestGroup"
            tab._load_group_members.assert_called_with("TestGroup")

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_on_group_selected_empty(self, mock_widget):
        """Test _on_group_selected with empty name"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab._load_group_members = MagicMock()

            tab._on_group_selected("")

            tab._load_group_members.assert_not_called()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_on_members_changed(self, mock_widget):
        """Test _on_members_changed saves and emits signal"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.current_group = "TestGroup"
            tab.group_member_list = MagicMock()
            tab.group_member_list.get_members.return_value = ["A", "B"]
            tab.group_changed = MagicMock()
            tab._save_groups = MagicMock()

            tab._on_members_changed()

            assert tab.cycling_groups["TestGroup"] == ["A", "B"]
            tab._save_groups.assert_called_once()
            tab.group_changed.emit.assert_called_with("TestGroup", ["A", "B"])

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_on_members_changed_no_current_group(self, mock_widget):
        """Test _on_members_changed with no current group"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.current_group = None
            tab._save_groups = MagicMock()

            tab._on_members_changed()

            tab._save_groups.assert_not_called()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QInputDialog")
    def test_create_new_group_success(self, mock_dialog, mock_widget):
        """Test _create_new_group successful creation"""
        mock_widget.return_value = None
        mock_dialog.getText.return_value = ("NewGroup", True)

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab._save_groups = MagicMock()
            tab._refresh_group_combo = MagicMock()
            tab.group_combo = MagicMock()

            tab._create_new_group()

            assert "NewGroup" in tab.cycling_groups
            tab._save_groups.assert_called_once()
            tab._refresh_group_combo.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QInputDialog")
    def test_create_new_group_cancelled(self, mock_dialog, mock_widget):
        """Test _create_new_group when cancelled"""
        mock_widget.return_value = None
        mock_dialog.getText.return_value = ("", False)

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            initial_groups = tab.cycling_groups.copy()

            tab._create_new_group()

            assert tab.cycling_groups == initial_groups

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QInputDialog")
    @patch("argus_overview.ui.hotkeys_tab.QMessageBox")
    def test_create_new_group_duplicate(self, mock_msgbox, mock_dialog, mock_widget):
        """Test _create_new_group with duplicate name"""
        mock_widget.return_value = None
        mock_dialog.getText.return_value = ("Default", True)

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            tab._create_new_group()

            mock_msgbox.warning.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_delete_current_group_none(self, mock_widget):
        """Test _delete_current_group with no current group"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.current_group = None
            initial_groups = tab.cycling_groups.copy()

            tab._delete_current_group()

            assert tab.cycling_groups == initial_groups

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QMessageBox")
    def test_delete_current_group_default(self, mock_msgbox, mock_widget):
        """Test _delete_current_group cannot delete Default"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.current_group = "Default"

            tab._delete_current_group()

            mock_msgbox.warning.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QMessageBox")
    def test_delete_current_group_confirmed(self, mock_msgbox, mock_widget):
        """Test _delete_current_group when confirmed"""
        mock_widget.return_value = None

        from PySide6.QtWidgets import QMessageBox

        mock_msgbox.StandardButton = QMessageBox.StandardButton
        mock_msgbox.question.return_value = QMessageBox.StandardButton.Yes

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {"TestGroup": ["A"]}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.current_group = "TestGroup"
            tab._save_groups = MagicMock()
            tab._refresh_group_combo = MagicMock()

            tab._delete_current_group()

            assert "TestGroup" not in tab.cycling_groups
            tab._save_groups.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_remove_selected_member(self, mock_widget):
        """Test _remove_selected_member removes current item"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.group_member_list = MagicMock()
            tab.group_member_list.currentItem.return_value = MagicMock()
            tab.group_member_list.row.return_value = 0
            tab._on_members_changed = MagicMock()

            tab._remove_selected_member()

            tab.group_member_list.takeItem.assert_called_once()
            tab._on_members_changed.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_remove_selected_member_none_selected(self, mock_widget):
        """Test _remove_selected_member with no selection"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.group_member_list = MagicMock()
            tab.group_member_list.currentItem.return_value = None
            tab._on_members_changed = MagicMock()

            tab._remove_selected_member()

            tab.group_member_list.takeItem.assert_not_called()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QMessageBox")
    def test_clear_group_members_empty(self, mock_msgbox, mock_widget):
        """Test _clear_group_members with empty list"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.group_member_list = MagicMock()
            tab.group_member_list.count.return_value = 0

            tab._clear_group_members()

            mock_msgbox.question.assert_not_called()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QMessageBox")
    def test_clear_group_members_confirmed(self, mock_msgbox, mock_widget):
        """Test _clear_group_members when confirmed"""
        mock_widget.return_value = None

        from PySide6.QtWidgets import QMessageBox

        mock_msgbox.StandardButton = QMessageBox.StandardButton
        mock_msgbox.question.return_value = QMessageBox.StandardButton.Yes

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.group_member_list = MagicMock()
            tab.group_member_list.count.return_value = 3
            tab._on_members_changed = MagicMock()

            tab._clear_group_members()

            tab.group_member_list.clear.assert_called_once()
            tab._on_members_changed.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QMessageBox")
    def test_load_active_windows_no_main_tab(self, mock_msgbox, mock_widget):
        """Test _load_active_windows with no main_tab"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.main_tab = None

            tab._load_active_windows()

            mock_msgbox.warning.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QMessageBox")
    def test_load_active_windows_no_active(self, mock_msgbox, mock_widget):
        """Test _load_active_windows with no active windows"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.main_tab = MagicMock()
            tab.main_tab.window_manager.preview_frames = {}

            tab._load_active_windows()

            mock_msgbox.information.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QMessageBox")
    @patch("argus_overview.ui.hotkeys_tab.QListWidgetItem")
    def test_load_active_windows_success(self, mock_item, mock_msgbox, mock_widget):
        """Test _load_active_windows with active windows"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            mock_frame = MagicMock()
            mock_frame.character_name = "TestChar"

            tab.main_tab = MagicMock()
            tab.main_tab.window_manager.preview_frames = {1: mock_frame}
            tab.group_member_list = MagicMock()
            tab._on_members_changed = MagicMock()

            tab._load_active_windows()

            tab.group_member_list.clear.assert_called_once()
            tab.group_member_list.addItem.assert_called()
            tab._on_members_changed.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_move_member_up(self, mock_widget):
        """Test _move_member_up moves item up"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.group_member_list = MagicMock()
            tab.group_member_list.currentRow.return_value = 2
            mock_item = MagicMock()
            tab.group_member_list.takeItem.return_value = mock_item
            tab._on_members_changed = MagicMock()

            tab._move_member_up()

            tab.group_member_list.insertItem.assert_called_with(1, mock_item)
            tab.group_member_list.setCurrentRow.assert_called_with(1)
            tab._on_members_changed.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_move_member_up_at_top(self, mock_widget):
        """Test _move_member_up at top does nothing"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.group_member_list = MagicMock()
            tab.group_member_list.currentRow.return_value = 0
            tab._on_members_changed = MagicMock()

            tab._move_member_up()

            tab.group_member_list.takeItem.assert_not_called()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_move_member_down(self, mock_widget):
        """Test _move_member_down moves item down"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.group_member_list = MagicMock()
            tab.group_member_list.currentRow.return_value = 1
            tab.group_member_list.count.return_value = 5
            mock_item = MagicMock()
            tab.group_member_list.takeItem.return_value = mock_item
            tab._on_members_changed = MagicMock()

            tab._move_member_down()

            tab.group_member_list.insertItem.assert_called_with(2, mock_item)
            tab.group_member_list.setCurrentRow.assert_called_with(2)
            tab._on_members_changed.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_move_member_down_at_bottom(self, mock_widget):
        """Test _move_member_down at bottom does nothing"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.group_member_list = MagicMock()
            tab.group_member_list.currentRow.return_value = 4
            tab.group_member_list.count.return_value = 5
            tab._on_members_changed = MagicMock()

            tab._move_member_down()

            tab.group_member_list.takeItem.assert_not_called()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    @patch("argus_overview.ui.hotkeys_tab.QMessageBox")
    def test_save_hotkeys(self, mock_msgbox, mock_widget):
        """Test _save_hotkeys saves settings"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.cycle_forward_edit = MagicMock()
            tab.cycle_forward_edit.text.return_value = "<ctrl>+<shift>+]"
            tab.cycle_backward_edit = MagicMock()
            tab.cycle_backward_edit.text.return_value = "<ctrl>+<shift>+["
            # Mock the broadcast_hotkeys_changed signal since Qt signals don't work with mocked QWidget
            tab.broadcast_hotkeys_changed = MagicMock()

            tab._save_hotkeys()

            mock_settings_manager.set.assert_any_call(
                "hotkeys.cycle_next", "<ctrl>+<shift>+]", auto_save=False
            )
            mock_settings_manager.set.assert_any_call(
                "hotkeys.cycle_prev", "<ctrl>+<shift>+[", auto_save=False
            )
            # Verify broadcast signal was emitted
            tab.broadcast_hotkeys_changed.emit.assert_called_once()
            mock_msgbox.information.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_refresh_characters(self, mock_widget):
        """Test refresh_characters calls _populate_character_list"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab._populate_character_list = MagicMock()

            tab.refresh_characters()

            tab._populate_character_list.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_format_hotkey_with_spaces(self, mock_widget):
        """Test _format_hotkey handles spaces"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab._format_hotkey(" ctrl + shift + ] ")

            assert result == "<ctrl>+<shift>+<]>"

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_format_hotkey_empty_parts(self, mock_widget):
        """Test _format_hotkey handles empty parts"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab._format_hotkey("ctrl++shift")

            assert result == "<ctrl>+<shift>"


class TestHotkeysTabSetupUI:
    """Tests for HotkeysTab UI setup methods"""

    def test_setup_ui_creates_layout(self):
        """Test _setup_ui creates main layout"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.logger = MagicMock()
            tab.character_manager = MagicMock()
            tab.character_manager.get_all_characters.return_value = []
            tab.settings_manager = MagicMock()
            tab.settings_manager.get.return_value = "<ctrl>+<shift>+]"
            tab.cycling_groups = {"Default": []}
            tab.current_group = "Default"

            mock_layout = MagicMock()
            mock_splitter = MagicMock()

            with patch("argus_overview.ui.hotkeys_tab.QHBoxLayout", return_value=mock_layout):
                with patch("argus_overview.ui.hotkeys_tab.QSplitter", return_value=mock_splitter):
                    with patch.object(tab, "setLayout"):
                        with patch.object(tab, "_create_character_panel", return_value=MagicMock()):
                            with patch.object(
                                tab, "_create_cycling_panel", return_value=MagicMock()
                            ):
                                tab._setup_ui()

                                mock_layout.setContentsMargins.assert_called_with(10, 10, 10, 10)
                                mock_splitter.setSizes.assert_called_with([350, 550])

    def test_create_character_panel(self):
        """Test _create_character_panel creates panel structure"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.logger = MagicMock()
            tab.character_manager = MagicMock()
            tab.character_manager.get_all_characters.return_value = []
            tab.settings_manager = MagicMock()

            mock_panel = MagicMock()
            mock_layout = MagicMock()

            with patch("argus_overview.ui.hotkeys_tab.QGroupBox", return_value=mock_panel):
                with patch("argus_overview.ui.hotkeys_tab.QVBoxLayout", return_value=mock_layout):
                    with patch("argus_overview.ui.hotkeys_tab.QLabel"):
                        with patch("argus_overview.ui.hotkeys_tab.DraggableCharacterList"):
                            with patch("argus_overview.ui.hotkeys_tab.QPushButton") as mock_btn:
                                mock_btn_instance = MagicMock()
                                mock_btn.return_value = mock_btn_instance

                                result = tab._create_character_panel()

                                assert result == mock_panel
                                mock_panel.setLayout.assert_called_with(mock_layout)

    def test_create_cycling_panel(self):
        """Test _create_cycling_panel creates panel with all sections"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.logger = MagicMock()
            tab.character_manager = MagicMock()
            tab.settings_manager = MagicMock()
            tab.settings_manager.get.return_value = "<ctrl>+<shift>+]"
            tab.cycling_groups = {"Default": []}
            tab.current_group = None

            mock_panel = MagicMock()
            mock_vlayout = MagicMock()
            mock_combo = MagicMock()
            mock_combo.count.return_value = 0

            with patch("argus_overview.ui.hotkeys_tab.QWidget", return_value=mock_panel):
                with patch("argus_overview.ui.hotkeys_tab.QVBoxLayout", return_value=mock_vlayout):
                    with patch("argus_overview.ui.hotkeys_tab.ToolbarBuilder"):
                        with patch("argus_overview.ui.hotkeys_tab.QGroupBox"):
                            with patch("argus_overview.ui.hotkeys_tab.QHBoxLayout"):
                                with patch(
                                    "argus_overview.ui.hotkeys_tab.QComboBox",
                                    return_value=mock_combo,
                                ):
                                    with patch("argus_overview.ui.hotkeys_tab.QLabel"):
                                        with patch(
                                            "argus_overview.ui.hotkeys_tab.CyclingGroupList"
                                        ):
                                            with patch("argus_overview.ui.hotkeys_tab.QPushButton"):
                                                with patch(
                                                    "argus_overview.ui.hotkeys_tab.QFormLayout"
                                                ):
                                                    with patch(
                                                        "argus_overview.ui.hotkeys_tab.HotkeyEdit"
                                                    ):
                                                        result = tab._create_cycling_panel()

                                                        assert result == mock_panel
                                                        mock_panel.setLayout.assert_called()

    def test_create_cycling_panel_loads_initial_group(self):
        """Test _create_cycling_panel loads first group if present"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.logger = MagicMock()
            tab.character_manager = MagicMock()
            tab.settings_manager = MagicMock()
            tab.settings_manager.get.return_value = "<ctrl>+<shift>+]"
            tab.cycling_groups = {"TestGroup": ["Char1"], "Default": []}
            tab.current_group = None

            mock_combo = MagicMock()
            mock_combo.count.return_value = 0

            with patch("argus_overview.ui.hotkeys_tab.QWidget"):
                with patch("argus_overview.ui.hotkeys_tab.QVBoxLayout"):
                    with patch("argus_overview.ui.hotkeys_tab.ToolbarBuilder"):
                        with patch("argus_overview.ui.hotkeys_tab.QGroupBox"):
                            with patch("argus_overview.ui.hotkeys_tab.QHBoxLayout"):
                                with patch(
                                    "argus_overview.ui.hotkeys_tab.QComboBox",
                                    return_value=mock_combo,
                                ):
                                    with patch("argus_overview.ui.hotkeys_tab.QLabel"):
                                        with patch(
                                            "argus_overview.ui.hotkeys_tab.CyclingGroupList"
                                        ):
                                            with patch("argus_overview.ui.hotkeys_tab.QPushButton"):
                                                with patch(
                                                    "argus_overview.ui.hotkeys_tab.QFormLayout"
                                                ):
                                                    with patch(
                                                        "argus_overview.ui.hotkeys_tab.HotkeyEdit"
                                                    ):
                                                        with patch.object(
                                                            tab, "_load_group_members"
                                                        ) as mock_load:
                                                            tab._create_cycling_panel()

                                                            # First group alphabetically should be loaded
                                                            mock_combo.setCurrentText.assert_called()
                                                            mock_load.assert_called()

    def test_populate_character_list(self):
        """Test _populate_character_list adds characters"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.logger = MagicMock()

            mock_char1 = MagicMock()
            mock_char1.name = "TestChar1"
            mock_char1.window_id = 12345  # Online

            mock_char2 = MagicMock()
            mock_char2.name = "TestChar2"
            mock_char2.window_id = None  # Offline

            tab.character_manager = MagicMock()
            tab.character_manager.get_all_characters.return_value = [mock_char1, mock_char2]

            tab.character_list = MagicMock()

            with patch("argus_overview.ui.hotkeys_tab.QListWidgetItem") as mock_item:
                mock_item_instance = MagicMock()
                mock_item.return_value = mock_item_instance

                tab._populate_character_list()

                assert mock_item.call_count == 2
                tab.character_list.clear.assert_called_once()
                assert tab.character_list.addItem.call_count == 2
                tab.logger.info.assert_called()

    def test_populate_character_list_color_online(self):
        """Test _populate_character_list colors online characters green"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.logger = MagicMock()

            mock_char = MagicMock()
            mock_char.name = "OnlineChar"
            mock_char.window_id = 12345

            tab.character_manager = MagicMock()
            tab.character_manager.get_all_characters.return_value = [mock_char]
            tab.character_list = MagicMock()

            with patch("argus_overview.ui.hotkeys_tab.QListWidgetItem") as mock_item:
                with patch("argus_overview.ui.hotkeys_tab.QColor") as mock_color:
                    mock_item_instance = MagicMock()
                    mock_item.return_value = mock_item_instance

                    tab._populate_character_list()

                    # Green for online
                    mock_color.assert_called_with(0, 200, 0)
                    mock_item_instance.setForeground.assert_called()

    def test_populate_character_list_color_offline(self):
        """Test _populate_character_list colors offline characters gray"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.logger = MagicMock()

            mock_char = MagicMock()
            mock_char.name = "OfflineChar"
            mock_char.window_id = None

            tab.character_manager = MagicMock()
            tab.character_manager.get_all_characters.return_value = [mock_char]
            tab.character_list = MagicMock()

            with patch("argus_overview.ui.hotkeys_tab.QListWidgetItem") as mock_item:
                with patch("argus_overview.ui.hotkeys_tab.QColor") as mock_color:
                    mock_item_instance = MagicMock()
                    mock_item.return_value = mock_item_instance

                    tab._populate_character_list()

                    # Gray for offline
                    mock_color.assert_called_with(150, 150, 150)

    def test_refresh_group_combo(self):
        """Test _refresh_group_combo populates dropdown"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.cycling_groups = {"Alpha": [], "Beta": [], "Default": []}
            tab.group_combo = MagicMock()
            tab.group_combo.count.return_value = 0
            tab.group_combo.findText.return_value = -1

            tab._refresh_group_combo()

            tab.group_combo.blockSignals.assert_any_call(True)
            tab.group_combo.blockSignals.assert_any_call(False)
            tab.group_combo.clear.assert_called_once()
            assert tab.group_combo.addItem.call_count == 3

    def test_refresh_group_combo_restores_selection(self):
        """Test _refresh_group_combo restores previous selection"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.cycling_groups = {"Alpha": [], "Beta": []}
            tab.group_combo = MagicMock()
            tab.group_combo.count.return_value = 2
            tab.group_combo.currentText.return_value = "Beta"
            tab.group_combo.findText.return_value = 1

            tab._refresh_group_combo()

            tab.group_combo.setCurrentText.assert_called_with("Beta")

    def test_load_group_members(self):
        """Test _load_group_members populates list"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.cycling_groups = {"TestGroup": ["Char1", "Char2"]}
            tab.group_member_list = MagicMock()

            with patch("argus_overview.ui.hotkeys_tab.QListWidgetItem") as mock_item:
                mock_item_instance = MagicMock()
                mock_item.return_value = mock_item_instance

                tab._load_group_members("TestGroup")

                tab.group_member_list.clear.assert_called_once()
                assert mock_item.call_count == 2
                assert tab.group_member_list.addItem.call_count == 2

    def test_load_group_members_nonexistent_group(self):
        """Test _load_group_members with nonexistent group"""
        from argus_overview.ui.hotkeys_tab import HotkeysTab

        with patch.object(HotkeysTab, "__init__", return_value=None):
            tab = HotkeysTab.__new__(HotkeysTab)
            tab.cycling_groups = {"Default": []}
            tab.group_member_list = MagicMock()

            tab._load_group_members("NonexistentGroup")

            tab.group_member_list.clear.assert_called_once()
            tab.group_member_list.addItem.assert_not_called()


# =============================================================================
# Broadcast Hotkeys Tests
# =============================================================================


class TestBroadcastHotkeysLoad:
    """Tests for broadcast hotkeys loading"""

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_load_broadcast_hotkeys_empty(self, mock_widget):
        """Test _load_broadcast_hotkeys with no saved hotkeys"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = []

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.broadcast_container_layout = MagicMock()

            tab._load_broadcast_hotkeys()

            # No entries should be added
            assert len(tab.broadcast_entries) == 0

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_load_broadcast_hotkeys_with_entries(self, mock_widget):
        """Test _load_broadcast_hotkeys with saved hotkeys"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()

        def settings_get(key, default=None):
            if key == "broadcast_hotkeys":
                return [
                    {"trigger": "<ctrl>+<f1>", "key_to_send": "<f1>"},
                    {"trigger": "<ctrl>+<f2>", "key_to_send": "<f2>"},
                ]
            return default

        mock_settings_manager.get.side_effect = settings_get

        with patch.object(HotkeysTab, "_setup_ui"):
            with patch.object(HotkeysTab, "_add_broadcast_entry") as mock_add:
                tab = HotkeysTab(mock_char_manager, mock_settings_manager)
                tab.broadcast_container_layout = MagicMock()

                tab._load_broadcast_hotkeys()

                # Should add 2 entries
                assert mock_add.call_count == 2

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_load_broadcast_hotkeys_invalid_data(self, mock_widget):
        """Test _load_broadcast_hotkeys with invalid data"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        # Return non-list data
        mock_settings_manager.get.return_value = "invalid"

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.broadcast_container_layout = MagicMock()

            # Should not raise
            tab._load_broadcast_hotkeys()
            assert len(tab.broadcast_entries) == 0


class TestBroadcastHotkeysSave:
    """Tests for broadcast hotkeys saving"""

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_save_broadcast_hotkeys_empty(self, mock_widget):
        """Test _save_broadcast_hotkeys with no entries"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.broadcast_entries = []

            result = tab._save_broadcast_hotkeys()

            assert result == []
            mock_settings_manager.set.assert_called_with("broadcast_hotkeys", [], auto_save=True)

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_save_broadcast_hotkeys_with_entries(self, mock_widget):
        """Test _save_broadcast_hotkeys with entries"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            # Mock entries
            mock_trigger = MagicMock()
            mock_trigger.text.return_value = "<ctrl>+<f1>"
            mock_key = MagicMock()
            mock_key.text.return_value = "<f1>"

            tab.broadcast_entries = [{"trigger_edit": mock_trigger, "key_to_send_edit": mock_key}]

            result = tab._save_broadcast_hotkeys()

            assert len(result) == 1
            assert result[0] == {"trigger": "<ctrl>+<f1>", "key_to_send": "<f1>"}

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_save_broadcast_hotkeys_skips_empty(self, mock_widget):
        """Test _save_broadcast_hotkeys skips empty entries"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            # Mock entries with empty values
            mock_trigger_empty = MagicMock()
            mock_trigger_empty.text.return_value = ""
            mock_key_empty = MagicMock()
            mock_key_empty.text.return_value = ""

            mock_trigger_valid = MagicMock()
            mock_trigger_valid.text.return_value = "<ctrl>+<f1>"
            mock_key_valid = MagicMock()
            mock_key_valid.text.return_value = "<f1>"

            tab.broadcast_entries = [
                {"trigger_edit": mock_trigger_empty, "key_to_send_edit": mock_key_empty},
                {"trigger_edit": mock_trigger_valid, "key_to_send_edit": mock_key_valid},
            ]

            result = tab._save_broadcast_hotkeys()

            # Only valid entry should be saved
            assert len(result) == 1


class TestBroadcastHotkeysGetAll:
    """Tests for get_broadcast_hotkeys method"""

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_get_broadcast_hotkeys(self, mock_widget):
        """Test get_broadcast_hotkeys returns current entries"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            mock_trigger = MagicMock()
            mock_trigger.text.return_value = "<ctrl>+<f1>"
            mock_key = MagicMock()
            mock_key.text.return_value = "<f1>"

            tab.broadcast_entries = [{"trigger_edit": mock_trigger, "key_to_send_edit": mock_key}]

            result = tab.get_broadcast_hotkeys()

            assert len(result) == 1
            assert result[0]["trigger"] == "<ctrl>+<f1>"
            assert result[0]["key_to_send"] == "<f1>"


class TestAddBroadcastEntry:
    """Tests for _add_broadcast_entry method"""

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_add_broadcast_entry_creates_widget(self, mock_widget):
        """Test _add_broadcast_entry creates entry widget"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.broadcast_entries = []
            tab.broadcast_container_layout = MagicMock()

            # Mock the widget creation inside _add_broadcast_entry
            with patch("argus_overview.ui.hotkeys_tab.QWidget") as mock_qw:
                with patch("argus_overview.ui.hotkeys_tab.QHBoxLayout"):
                    with patch("argus_overview.ui.hotkeys_tab.HotkeyEdit") as mock_edit:
                        with patch("argus_overview.ui.hotkeys_tab.QLabel"):
                            with patch("argus_overview.ui.hotkeys_tab.QPushButton"):
                                mock_entry = MagicMock()
                                mock_qw.return_value = mock_entry
                                mock_trigger = MagicMock()
                                mock_key = MagicMock()
                                mock_edit.side_effect = [mock_trigger, mock_key]

                                tab._add_broadcast_entry("<ctrl>+<f1>", "F1")

                                assert len(tab.broadcast_entries) == 1
                                mock_trigger.setText.assert_called_with("<ctrl>+<f1>")
                                mock_key.setText.assert_called_with("F1")
                                tab.broadcast_container_layout.addWidget.assert_called()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_add_broadcast_entry_empty_values(self, mock_widget):
        """Test _add_broadcast_entry with empty trigger and key"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.broadcast_entries = []
            tab.broadcast_container_layout = MagicMock()

            with patch("argus_overview.ui.hotkeys_tab.QWidget") as mock_qw:
                with patch("argus_overview.ui.hotkeys_tab.QHBoxLayout"):
                    with patch("argus_overview.ui.hotkeys_tab.HotkeyEdit") as mock_edit:
                        with patch("argus_overview.ui.hotkeys_tab.QLabel"):
                            with patch("argus_overview.ui.hotkeys_tab.QPushButton"):
                                mock_entry = MagicMock()
                                mock_qw.return_value = mock_entry
                                mock_trigger = MagicMock()
                                mock_key = MagicMock()
                                mock_edit.side_effect = [mock_trigger, mock_key]

                                tab._add_broadcast_entry("", "")

                                assert len(tab.broadcast_entries) == 1
                                # setText should not be called for empty strings
                                mock_trigger.setText.assert_not_called()
                                mock_key.setText.assert_not_called()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_add_broadcast_entry_connects_recording_signals(self, mock_widget):
        """Test _add_broadcast_entry connects recording signals when available"""
        mock_widget.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.broadcast_entries = []
            tab.broadcast_container_layout = MagicMock()
            tab.broadcast_recording_started = MagicMock()
            tab.broadcast_recording_stopped = MagicMock()

            with patch("argus_overview.ui.hotkeys_tab.QWidget") as mock_qw:
                with patch("argus_overview.ui.hotkeys_tab.QHBoxLayout"):
                    with patch("argus_overview.ui.hotkeys_tab.HotkeyEdit") as mock_edit:
                        with patch("argus_overview.ui.hotkeys_tab.QLabel"):
                            with patch("argus_overview.ui.hotkeys_tab.QPushButton"):
                                mock_entry = MagicMock()
                                mock_qw.return_value = mock_entry
                                mock_trigger = MagicMock()
                                mock_key = MagicMock()
                                mock_edit.side_effect = [mock_trigger, mock_key]

                                tab._add_broadcast_entry("<ctrl>+<f2>", "F2")

                                # Should connect recording signals
                                mock_trigger.recordingStarted.connect.assert_called()
                                mock_trigger.recordingStopped.connect.assert_called()
                                mock_key.recordingStarted.connect.assert_called()
                                mock_key.recordingStopped.connect.assert_called()


class TestRemoveBroadcastEntry:
    """Tests for _remove_broadcast_entry method"""

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_remove_broadcast_entry(self, mock_init):
        """Test _remove_broadcast_entry removes entry from list"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            mock_widget = MagicMock()
            entry_data = {
                "widget": mock_widget,
                "trigger_edit": MagicMock(),
                "key_to_send_edit": MagicMock(),
            }
            tab.broadcast_entries = [entry_data]

            tab._remove_broadcast_entry(entry_data)

            assert len(tab.broadcast_entries) == 0
            mock_widget.deleteLater.assert_called_once()

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_remove_broadcast_entry_not_in_list(self, mock_init):
        """Test _remove_broadcast_entry handles entry not in list"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)
            tab.broadcast_entries = []

            # Should not raise
            entry_data = {"widget": MagicMock()}
            tab._remove_broadcast_entry(entry_data)

            assert len(tab.broadcast_entries) == 0

    @patch("argus_overview.ui.hotkeys_tab.QWidget.__init__")
    def test_remove_broadcast_entry_multiple_entries(self, mock_init):
        """Test _remove_broadcast_entry removes correct entry"""
        mock_init.return_value = None

        from argus_overview.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []
        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, "_setup_ui"):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            entry1 = {
                "widget": MagicMock(),
                "trigger_edit": MagicMock(),
                "key_to_send_edit": MagicMock(),
            }
            entry2 = {
                "widget": MagicMock(),
                "trigger_edit": MagicMock(),
                "key_to_send_edit": MagicMock(),
            }
            entry3 = {
                "widget": MagicMock(),
                "trigger_edit": MagicMock(),
                "key_to_send_edit": MagicMock(),
            }
            tab.broadcast_entries = [entry1, entry2, entry3]

            tab._remove_broadcast_entry(entry2)

            assert len(tab.broadcast_entries) == 2
            assert entry1 in tab.broadcast_entries
            assert entry2 not in tab.broadcast_entries
            assert entry3 in tab.broadcast_entries
            entry2["widget"].deleteLater.assert_called_once()
