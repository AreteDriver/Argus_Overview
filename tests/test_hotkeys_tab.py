"""
Unit tests for the Hotkeys & Cycling Tab module
Tests DraggableCharacterList, CyclingGroupList, HotkeysTab
"""
from unittest.mock import MagicMock, patch


# Test DraggableCharacterList
class TestDraggableCharacterList:
    """Tests for DraggableCharacterList widget"""

    @patch('eve_overview_pro.ui.hotkeys_tab.QListWidget.__init__')
    def test_init_enables_drag(self, mock_init):
        """Test that init enables drag"""
        mock_init.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import DraggableCharacterList

        with patch.object(DraggableCharacterList, 'setDragEnabled') as mock_drag:
            with patch.object(DraggableCharacterList, 'setDefaultDropAction'):
                with patch.object(DraggableCharacterList, 'setSelectionMode'):
                    with patch.object(DraggableCharacterList, 'setAlternatingRowColors'):
                        DraggableCharacterList()

                        mock_drag.assert_called_once_with(True)


# Test CyclingGroupList
class TestCyclingGroupList:
    """Tests for CyclingGroupList widget"""

    @patch('eve_overview_pro.ui.hotkeys_tab.QListWidget.__init__')
    def test_init_accepts_drops(self, mock_init):
        """Test that init enables drop accepting"""
        mock_init.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, 'setAcceptDrops') as mock_drops:
            with patch.object(CyclingGroupList, 'setDragEnabled'):
                with patch.object(CyclingGroupList, 'setDragDropMode'):
                    with patch.object(CyclingGroupList, 'setDefaultDropAction'):
                        with patch.object(CyclingGroupList, 'setSelectionMode'):
                            with patch.object(CyclingGroupList, 'setAlternatingRowColors'):
                                with patch.object(CyclingGroupList, 'setStyleSheet'):
                                    CyclingGroupList()

                                    mock_drops.assert_called_once_with(True)

    @patch('eve_overview_pro.ui.hotkeys_tab.QListWidget.__init__')
    def test_get_members_empty(self, mock_init):
        """Test get_members with empty list"""
        mock_init.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import CyclingGroupList

        with patch.object(CyclingGroupList, 'setAcceptDrops'):
            with patch.object(CyclingGroupList, 'setDragEnabled'):
                with patch.object(CyclingGroupList, 'setDragDropMode'):
                    with patch.object(CyclingGroupList, 'setDefaultDropAction'):
                        with patch.object(CyclingGroupList, 'setSelectionMode'):
                            with patch.object(CyclingGroupList, 'setAlternatingRowColors'):
                                with patch.object(CyclingGroupList, 'setStyleSheet'):
                                    with patch.object(CyclingGroupList, 'count', return_value=0):
                                        list_widget = CyclingGroupList()

                                        result = list_widget.get_members()

                                        assert result == []

    def test_signal_exists(self):
        """Test that members_changed signal exists"""
        from eve_overview_pro.ui.hotkeys_tab import CyclingGroupList

        assert hasattr(CyclingGroupList, 'members_changed')


# Test HotkeysTab
class TestHotkeysTab:
    """Tests for HotkeysTab widget"""

    @patch('eve_overview_pro.ui.hotkeys_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test HotkeysTab initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, '_setup_ui'):
            with patch.object(HotkeysTab, '_load_groups'):
                tab = HotkeysTab(mock_char_manager, mock_settings_manager)

                assert tab.character_manager is mock_char_manager
                assert tab.settings_manager is mock_settings_manager

    @patch('eve_overview_pro.ui.hotkeys_tab.QWidget.__init__')
    def test_load_groups_creates_default(self, mock_widget):
        """Test that _load_groups creates Default group if missing"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}  # No groups

        with patch.object(HotkeysTab, '_setup_ui'):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            assert "Default" in tab.cycling_groups
            assert tab.cycling_groups["Default"] == []


# Test format_hotkey helper
class TestFormatHotkey:
    """Tests for _format_hotkey method"""

    @patch('eve_overview_pro.ui.hotkeys_tab.QWidget.__init__')
    def test_format_simple_combo(self, mock_widget):
        """Test formatting simple key combo"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, '_setup_ui'):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab._format_hotkey("ctrl+shift+]")

            assert result == "<ctrl>+<shift>+<]>"

    @patch('eve_overview_pro.ui.hotkeys_tab.QWidget.__init__')
    def test_format_already_bracketed(self, mock_widget):
        """Test formatting already bracketed keys"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, '_setup_ui'):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab._format_hotkey("<ctrl>+<shift>+<]>")

            assert result == "<ctrl>+<shift>+<]>"

    @patch('eve_overview_pro.ui.hotkeys_tab.QWidget.__init__')
    def test_format_empty(self, mock_widget):
        """Test formatting empty string"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, '_setup_ui'):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab._format_hotkey("")

            assert result == ""


# Test group management
class TestGroupManagement:
    """Tests for cycling group management"""

    @patch('eve_overview_pro.ui.hotkeys_tab.QWidget.__init__')
    def test_get_cycling_group(self, mock_widget):
        """Test get_cycling_group method"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {
            "TestGroup": ["Char1", "Char2"]
        }

        with patch.object(HotkeysTab, '_setup_ui'):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab.get_cycling_group("TestGroup")

            assert result == ["Char1", "Char2"]

    @patch('eve_overview_pro.ui.hotkeys_tab.QWidget.__init__')
    def test_get_nonexistent_group(self, mock_widget):
        """Test get_cycling_group for nonexistent group"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        with patch.object(HotkeysTab, '_setup_ui'):
            tab = HotkeysTab(mock_char_manager, mock_settings_manager)

            result = tab.get_cycling_group("NonexistentGroup")

            assert result == []

    @patch('eve_overview_pro.ui.hotkeys_tab.QWidget.__init__')
    def test_get_all_groups(self, mock_widget):
        """Test get_all_groups method"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.hotkeys_tab import HotkeysTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_characters.return_value = []

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {
            "Group1": ["A", "B"],
            "Group2": ["C", "D"]
        }

        with patch.object(HotkeysTab, '_setup_ui'):
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
        from eve_overview_pro.ui.hotkeys_tab import HotkeysTab

        assert hasattr(HotkeysTab, 'group_changed')

    def test_cycling_group_list_signal_exists(self):
        """Test CyclingGroupList has members_changed signal"""
        from eve_overview_pro.ui.hotkeys_tab import CyclingGroupList

        assert hasattr(CyclingGroupList, 'members_changed')
