"""
Unit tests for the Characters & Teams Tab module
Tests CharacterTable, CharacterDialog, TeamBuilder, CharactersTeamsTab
"""

from unittest.mock import MagicMock, patch


# Test CharacterTable
class TestCharacterTable:
    """Tests for CharacterTable widget"""

    @patch("argus_overview.ui.characters_teams_tab.QTableWidget.__init__")
    @patch("argus_overview.ui.characters_teams_tab.QHeaderView")
    def test_init_sets_columns(self, mock_header, mock_table_init):
        """Test that init sets up correct columns"""
        mock_table_init.return_value = None

        from argus_overview.ui.characters_teams_tab import CharacterTable

        mock_manager = MagicMock()
        mock_manager.get_all_characters.return_value = []

        with patch.object(CharacterTable, "setColumnCount") as mock_set_cols:
            with patch.object(CharacterTable, "setHorizontalHeaderLabels") as mock_labels:
                with patch.object(CharacterTable, "horizontalHeader", return_value=MagicMock()):
                    with patch.object(CharacterTable, "setSelectionBehavior"):
                        with patch.object(CharacterTable, "setAlternatingRowColors"):
                            with patch.object(CharacterTable, "setSortingEnabled"):
                                with patch.object(
                                    CharacterTable, "itemSelectionChanged", MagicMock()
                                ):
                                    with patch.object(CharacterTable, "populate_table"):
                                        CharacterTable(mock_manager)

                                        mock_set_cols.assert_called_once_with(6)
                                        mock_labels.assert_called_once()
                                        labels = mock_labels.call_args[0][0]
                                        assert "Name" in labels
                                        assert "Account" in labels
                                        assert "Role" in labels

    def test_roles_defined(self):
        """Test that ROLES constant is defined"""
        from argus_overview.ui.characters_teams_tab import CharacterTable

        assert hasattr(CharacterTable, "ROLES")
        assert "DPS" in CharacterTable.ROLES
        assert "Miner" in CharacterTable.ROLES
        assert "Scout" in CharacterTable.ROLES
        assert "Logi" in CharacterTable.ROLES

    @patch("argus_overview.ui.characters_teams_tab.QTableWidget.__init__")
    @patch("argus_overview.ui.characters_teams_tab.QHeaderView")
    def test_get_selected_characters_empty(self, mock_header, mock_table_init):
        """Test get_selected_characters with no selection"""
        mock_table_init.return_value = None

        from argus_overview.ui.characters_teams_tab import CharacterTable

        mock_manager = MagicMock()
        mock_manager.get_all_characters.return_value = []

        with patch.object(CharacterTable, "setColumnCount"):
            with patch.object(CharacterTable, "setHorizontalHeaderLabels"):
                with patch.object(CharacterTable, "horizontalHeader", return_value=MagicMock()):
                    with patch.object(CharacterTable, "setSelectionBehavior"):
                        with patch.object(CharacterTable, "setAlternatingRowColors"):
                            with patch.object(CharacterTable, "setSortingEnabled"):
                                with patch.object(
                                    CharacterTable, "itemSelectionChanged", MagicMock()
                                ):
                                    with patch.object(CharacterTable, "populate_table"):
                                        with patch.object(
                                            CharacterTable, "selectedItems", return_value=[]
                                        ):
                                            table = CharacterTable(mock_manager)

                                            result = table.get_selected_characters()

                                            assert result == []


# Test CharacterDialog
class TestCharacterDialog:
    """Tests for CharacterDialog"""

    @patch("argus_overview.ui.characters_teams_tab.QDialog.__init__")
    @patch("argus_overview.ui.characters_teams_tab.QFormLayout")
    @patch("argus_overview.ui.characters_teams_tab.QLineEdit")
    @patch("argus_overview.ui.characters_teams_tab.QComboBox")
    @patch("argus_overview.ui.characters_teams_tab.QCheckBox")
    @patch("argus_overview.ui.characters_teams_tab.QTextEdit")
    @patch("argus_overview.ui.characters_teams_tab.QDialogButtonBox")
    def test_init_add_mode(
        self,
        mock_bbox,
        mock_textedit,
        mock_checkbox,
        mock_combo,
        mock_lineedit,
        mock_layout,
        mock_dialog,
    ):
        """Test dialog initialization in add mode"""
        mock_dialog.return_value = None

        from argus_overview.ui.characters_teams_tab import CharacterDialog

        mock_manager = MagicMock()
        mock_manager.get_accounts.return_value = ["Account1", "Account2"]

        with patch.object(CharacterDialog, "setWindowTitle") as mock_title:
            with patch.object(CharacterDialog, "setModal"):
                with patch.object(CharacterDialog, "resize"):
                    with patch.object(CharacterDialog, "setLayout"):
                        CharacterDialog(mock_manager, character=None)

                        mock_title.assert_called_with("Add Character")

    @patch("argus_overview.ui.characters_teams_tab.QDialog.__init__")
    @patch("argus_overview.ui.characters_teams_tab.QFormLayout")
    @patch("argus_overview.ui.characters_teams_tab.QLineEdit")
    @patch("argus_overview.ui.characters_teams_tab.QComboBox")
    @patch("argus_overview.ui.characters_teams_tab.QCheckBox")
    @patch("argus_overview.ui.characters_teams_tab.QTextEdit")
    @patch("argus_overview.ui.characters_teams_tab.QDialogButtonBox")
    def test_init_edit_mode(
        self,
        mock_bbox,
        mock_textedit,
        mock_checkbox,
        mock_combo,
        mock_lineedit,
        mock_layout,
        mock_dialog,
    ):
        """Test dialog initialization in edit mode"""
        mock_dialog.return_value = None

        from argus_overview.ui.characters_teams_tab import CharacterDialog

        mock_manager = MagicMock()
        mock_manager.get_accounts.return_value = []

        mock_char = MagicMock()
        mock_char.name = "TestPilot"

        with patch.object(CharacterDialog, "setWindowTitle") as mock_title:
            with patch.object(CharacterDialog, "setModal"):
                with patch.object(CharacterDialog, "resize"):
                    with patch.object(CharacterDialog, "setLayout"):
                        with patch.object(CharacterDialog, "_load_character"):
                            CharacterDialog(mock_manager, character=mock_char)

                            mock_title.assert_called_with("Edit Character")


# Test TeamBuilder
class TestTeamBuilder:
    """Tests for TeamBuilder widget"""

    @patch("argus_overview.ui.characters_teams_tab.QWidget.__init__")
    @patch("argus_overview.ui.characters_teams_tab.QVBoxLayout")
    @patch("argus_overview.ui.characters_teams_tab.QGroupBox")
    @patch("argus_overview.ui.characters_teams_tab.QFormLayout")
    @patch("argus_overview.ui.characters_teams_tab.QLineEdit")
    @patch("argus_overview.ui.characters_teams_tab.QTextEdit")
    @patch("argus_overview.ui.characters_teams_tab.QComboBox")
    @patch("argus_overview.ui.characters_teams_tab.QPushButton")
    @patch("argus_overview.ui.characters_teams_tab.QListWidget")
    @patch("argus_overview.ui.characters_teams_tab.QHBoxLayout")
    @patch("argus_overview.ui.characters_teams_tab.QLabel")
    def test_init(
        self,
        mock_label,
        mock_hbox,
        mock_list,
        mock_btn,
        mock_combo,
        mock_textedit,
        mock_lineedit,
        mock_form,
        mock_group,
        mock_vbox,
        mock_widget,
    ):
        """Test TeamBuilder initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.characters_teams_tab import TeamBuilder

        mock_char_manager = MagicMock()
        mock_layout_manager = MagicMock()
        mock_layout_manager.get_all_presets.return_value = []

        with patch.object(TeamBuilder, "setLayout"):
            builder = TeamBuilder(mock_char_manager, mock_layout_manager)

            assert builder.character_manager is mock_char_manager
            assert builder.layout_manager is mock_layout_manager
            assert builder.current_team is None

    @patch("argus_overview.ui.characters_teams_tab.QWidget.__init__")
    @patch("argus_overview.ui.characters_teams_tab.QVBoxLayout")
    @patch("argus_overview.ui.characters_teams_tab.QGroupBox")
    @patch("argus_overview.ui.characters_teams_tab.QFormLayout")
    @patch("argus_overview.ui.characters_teams_tab.QLineEdit")
    @patch("argus_overview.ui.characters_teams_tab.QTextEdit")
    @patch("argus_overview.ui.characters_teams_tab.QComboBox")
    @patch("argus_overview.ui.characters_teams_tab.QPushButton")
    @patch("argus_overview.ui.characters_teams_tab.QListWidget")
    @patch("argus_overview.ui.characters_teams_tab.QHBoxLayout")
    @patch("argus_overview.ui.characters_teams_tab.QLabel")
    def test_set_color(
        self,
        mock_label,
        mock_hbox,
        mock_list,
        mock_btn,
        mock_combo,
        mock_textedit,
        mock_lineedit,
        mock_form,
        mock_group,
        mock_vbox,
        mock_widget,
    ):
        """Test _set_color method"""
        mock_widget.return_value = None

        from argus_overview.ui.characters_teams_tab import TeamBuilder

        mock_char_manager = MagicMock()
        mock_layout_manager = MagicMock()
        mock_layout_manager.get_all_presets.return_value = []

        with patch.object(TeamBuilder, "setLayout"):
            builder = TeamBuilder(mock_char_manager, mock_layout_manager)

            builder._set_color("#ff0000")

            assert builder.team_color == "#ff0000"


# Test CharactersTeamsTab
class TestCharactersTeamsTab:
    """Tests for CharactersTeamsTab main widget"""

    @patch("argus_overview.ui.characters_teams_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test CharactersTeamsTab initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_teams.return_value = []
        mock_char_manager.get_all_characters.return_value = []

        mock_layout_manager = MagicMock()
        mock_layout_manager.get_all_presets.return_value = []

        with patch.object(CharactersTeamsTab, "_setup_ui"):
            tab = CharactersTeamsTab(mock_char_manager, mock_layout_manager)

            assert tab.character_manager is mock_char_manager
            assert tab.layout_manager is mock_layout_manager

    @patch("argus_overview.ui.characters_teams_tab.QWidget.__init__")
    def test_init_with_settings_sync(self, mock_widget):
        """Test CharactersTeamsTab with settings_sync parameter"""
        mock_widget.return_value = None

        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        mock_char_manager = MagicMock()
        mock_char_manager.get_all_teams.return_value = []
        mock_char_manager.get_all_characters.return_value = []

        mock_layout_manager = MagicMock()
        mock_layout_manager.get_all_presets.return_value = []

        mock_settings_sync = MagicMock()

        with patch.object(CharactersTeamsTab, "_setup_ui"):
            tab = CharactersTeamsTab(
                mock_char_manager, mock_layout_manager, settings_sync=mock_settings_sync
            )

            assert tab.settings_sync is mock_settings_sync


# Test signal definitions
class TestSignals:
    """Tests for signal definitions"""

    def test_character_table_signal_exists(self):
        """Test CharacterTable has character_selected signal"""
        from argus_overview.ui.characters_teams_tab import CharacterTable

        assert hasattr(CharacterTable, "character_selected")

    def test_team_builder_signal_exists(self):
        """Test TeamBuilder has team_modified signal"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        assert hasattr(TeamBuilder, "team_modified")

    def test_characters_teams_tab_signals_exist(self):
        """Test CharactersTeamsTab has expected signals"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        assert hasattr(CharactersTeamsTab, "team_selected")
        assert hasattr(CharactersTeamsTab, "characters_imported")


# Test CharacterTable methods in detail
class TestCharacterTableMethods:
    """Tests for CharacterTable methods"""

    def test_populate_table_with_characters(self):
        """Test populate_table with character list"""
        from argus_overview.ui.characters_teams_tab import CharacterTable

        with patch.object(CharacterTable, "__init__", return_value=None):
            table = CharacterTable.__new__(CharacterTable)
            table.logger = MagicMock()
            table.character_manager = MagicMock()

            # Mock characters
            char1 = MagicMock()
            char1.name = "Pilot1"
            char1.account = "Account1"
            char1.role = "DPS"
            char1.is_main = True
            char1.window_id = "0x123"
            char1.notes = "Main pilot"

            char2 = MagicMock()
            char2.name = "Pilot2"
            char2.account = None
            char2.role = "Miner"
            char2.is_main = False
            char2.window_id = None
            char2.notes = None

            table.character_manager.get_all_characters.return_value = [char1, char2]

            # Mock table methods
            table.setSortingEnabled = MagicMock()
            table.setRowCount = MagicMock()
            table.setItem = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QTableWidgetItem") as mock_item:
                mock_item.return_value = MagicMock()
                table.populate_table()

            table.setRowCount.assert_called_once_with(2)
            assert mock_item.call_count >= 12  # 6 columns * 2 rows

    def test_update_character_status_active(self):
        """Test update_character_status when character becomes active"""
        from argus_overview.ui.characters_teams_tab import CharacterTable

        with patch.object(CharacterTable, "__init__", return_value=None):
            table = CharacterTable.__new__(CharacterTable)
            table.logger = MagicMock()

            # Mock table with one row
            mock_name_item = MagicMock()
            mock_name_item.text.return_value = "Pilot1"
            mock_status_item = MagicMock()
            mock_window_item = MagicMock()

            table.rowCount = MagicMock(return_value=1)
            table.item = MagicMock(
                side_effect=lambda row, col: {
                    (0, 0): mock_name_item,
                    (0, 3): mock_status_item,
                    (0, 4): mock_window_item,
                }.get((row, col))
            )

            table.update_character_status("Pilot1", "0x456")

            mock_status_item.setText.assert_called_with("Active")
            mock_window_item.setText.assert_called_with("0x456")

    def test_update_character_status_offline(self):
        """Test update_character_status when character goes offline"""
        from argus_overview.ui.characters_teams_tab import CharacterTable

        with patch.object(CharacterTable, "__init__", return_value=None):
            table = CharacterTable.__new__(CharacterTable)
            table.logger = MagicMock()

            mock_name_item = MagicMock()
            mock_name_item.text.return_value = "Pilot1"
            mock_status_item = MagicMock()
            mock_window_item = MagicMock()

            table.rowCount = MagicMock(return_value=1)
            table.item = MagicMock(
                side_effect=lambda row, col: {
                    (0, 0): mock_name_item,
                    (0, 3): mock_status_item,
                    (0, 4): mock_window_item,
                }.get((row, col))
            )

            table.update_character_status("Pilot1", None)

            mock_status_item.setText.assert_called_with("Offline")
            mock_window_item.setText.assert_called_with("")

    def test_update_character_status_not_found(self):
        """Test update_character_status when character not in table"""
        from argus_overview.ui.characters_teams_tab import CharacterTable

        with patch.object(CharacterTable, "__init__", return_value=None):
            table = CharacterTable.__new__(CharacterTable)
            table.logger = MagicMock()

            mock_name_item = MagicMock()
            mock_name_item.text.return_value = "Pilot1"

            table.rowCount = MagicMock(return_value=1)
            table.item = MagicMock(
                side_effect=lambda row, col: mock_name_item if col == 0 else None
            )

            # Should not raise, just not find the character
            table.update_character_status("NonExistent", "0x123")

    def test_get_selected_characters_with_selection(self):
        """Test get_selected_characters with selected items"""
        from argus_overview.ui.characters_teams_tab import CharacterTable

        with patch.object(CharacterTable, "__init__", return_value=None):
            table = CharacterTable.__new__(CharacterTable)

            # Mock selected items - only column 0 items should be included
            mock_item1 = MagicMock()
            mock_item1.column.return_value = 0
            mock_item1.text.return_value = "Pilot1"

            mock_item2 = MagicMock()
            mock_item2.column.return_value = 1  # Not name column
            mock_item2.text.return_value = "Account1"

            mock_item3 = MagicMock()
            mock_item3.column.return_value = 0
            mock_item3.text.return_value = "Pilot2"

            table.selectedItems = MagicMock(return_value=[mock_item1, mock_item2, mock_item3])

            result = table.get_selected_characters()

            assert result == ["Pilot1", "Pilot2"]

    def test_on_selection_changed_with_selection(self):
        """Test _on_selection_changed emits signal"""
        from argus_overview.ui.characters_teams_tab import CharacterTable

        with patch.object(CharacterTable, "__init__", return_value=None):
            table = CharacterTable.__new__(CharacterTable)
            table.character_selected = MagicMock()
            table.get_selected_characters = MagicMock(return_value=["Pilot1"])

            table._on_selection_changed()

            table.character_selected.emit.assert_called_once_with("Pilot1")

    def test_on_selection_changed_empty(self):
        """Test _on_selection_changed with no selection"""
        from argus_overview.ui.characters_teams_tab import CharacterTable

        with patch.object(CharacterTable, "__init__", return_value=None):
            table = CharacterTable.__new__(CharacterTable)
            table.character_selected = MagicMock()
            table.get_selected_characters = MagicMock(return_value=[])

            table._on_selection_changed()

            table.character_selected.emit.assert_not_called()


# Test CharacterDialog methods in detail
class TestCharacterDialogMethods:
    """Tests for CharacterDialog methods"""

    def test_load_character(self):
        """Test _load_character populates form"""
        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)

            mock_char = MagicMock()
            mock_char.name = "TestPilot"
            mock_char.account = "TestAccount"
            mock_char.role = "DPS"
            mock_char.is_main = True
            mock_char.notes = "Test notes"
            dialog.character = mock_char

            dialog.name_edit = MagicMock()
            dialog.account_combo = MagicMock()
            dialog.role_combo = MagicMock()
            dialog.is_main_check = MagicMock()
            dialog.notes_edit = MagicMock()

            dialog._load_character()

            dialog.name_edit.setText.assert_called_with("TestPilot")
            dialog.name_edit.setEnabled.assert_called_with(False)
            dialog.account_combo.setCurrentText.assert_called_with("TestAccount")
            dialog.role_combo.setCurrentText.assert_called_with("DPS")
            dialog.is_main_check.setChecked.assert_called_with(True)
            dialog.notes_edit.setPlainText.assert_called_with("Test notes")

    def test_on_accept_valid(self):
        """Test _on_accept when validation passes"""
        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)
            dialog.validate = MagicMock(return_value=True)
            dialog.accept = MagicMock()

            dialog._on_accept()

            dialog.accept.assert_called_once()

    def test_on_accept_invalid(self):
        """Test _on_accept when validation fails"""
        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)
            dialog.validate = MagicMock(return_value=False)
            dialog.accept = MagicMock()

            dialog._on_accept()

            dialog.accept.assert_not_called()

    def test_validate_empty_name(self):
        """Test validate with empty name"""
        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)
            dialog.character = None
            dialog.character_manager = MagicMock()
            dialog.name_edit = MagicMock()
            dialog.name_edit.text.return_value = "  "
            dialog.account_combo = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                result = dialog.validate()

            assert result is False
            mock_msg.warning.assert_called_once()

    def test_validate_duplicate_name(self):
        """Test validate with duplicate character name"""
        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)
            dialog.character = None  # Adding new
            dialog.character_manager = MagicMock()
            dialog.character_manager.get_character.return_value = MagicMock()  # Already exists
            dialog.name_edit = MagicMock()
            dialog.name_edit.text.return_value = "ExistingPilot"
            dialog.account_combo = MagicMock()
            dialog.account_combo.currentText.return_value = ""

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox"):
                result = dialog.validate()

            assert result is False

    def test_validate_account_full_user_declines(self):
        """Test validate when account has 3+ chars and user declines"""
        from PySide6.QtWidgets import QMessageBox

        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)
            dialog.character = None
            dialog.character_manager = MagicMock()
            dialog.character_manager.get_character.return_value = None
            dialog.character_manager.get_characters_by_account.return_value = [1, 2, 3]  # 3 chars
            dialog.name_edit = MagicMock()
            dialog.name_edit.text.return_value = "NewPilot"
            dialog.account_combo = MagicMock()
            dialog.account_combo.currentText.return_value = "FullAccount"

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                mock_msg.StandardButton.No = QMessageBox.StandardButton.No
                mock_msg.question.return_value = QMessageBox.StandardButton.No
                result = dialog.validate()

            assert result is False

    def test_validate_account_full_user_accepts(self):
        """Test validate when account has 3+ chars and user accepts"""
        from PySide6.QtWidgets import QMessageBox

        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)
            dialog.character = None
            dialog.character_manager = MagicMock()
            dialog.character_manager.get_character.return_value = None
            dialog.character_manager.get_characters_by_account.return_value = [1, 2, 3]
            dialog.name_edit = MagicMock()
            dialog.name_edit.text.return_value = "NewPilot"
            dialog.account_combo = MagicMock()
            dialog.account_combo.currentText.return_value = "FullAccount"

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                mock_msg.StandardButton.Yes = QMessageBox.StandardButton.Yes
                mock_msg.StandardButton.No = QMessageBox.StandardButton.No
                mock_msg.question.return_value = QMessageBox.StandardButton.Yes
                result = dialog.validate()

            assert result is True

    def test_validate_success(self):
        """Test validate with valid data"""
        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)
            dialog.character = None
            dialog.character_manager = MagicMock()
            dialog.character_manager.get_character.return_value = None
            dialog.character_manager.get_characters_by_account.return_value = []
            dialog.name_edit = MagicMock()
            dialog.name_edit.text.return_value = "NewPilot"
            dialog.account_combo = MagicMock()
            dialog.account_combo.currentText.return_value = ""

            result = dialog.validate()

            assert result is True

    def test_get_character_new(self):
        """Test get_character creates new character"""
        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)
            dialog.character = None  # Adding new

            dialog.name_edit = MagicMock()
            dialog.name_edit.text.return_value = "NewPilot"
            dialog.account_combo = MagicMock()
            dialog.account_combo.currentText.return_value = "Account1"
            dialog.role_combo = MagicMock()
            dialog.role_combo.currentText.return_value = "DPS"
            dialog.is_main_check = MagicMock()
            dialog.is_main_check.isChecked.return_value = True
            dialog.notes_edit = MagicMock()
            dialog.notes_edit.toPlainText.return_value = "Test notes"

            with patch("argus_overview.ui.characters_teams_tab.Character") as mock_char_class:
                mock_char_class.return_value = MagicMock()
                dialog.get_character()

            mock_char_class.assert_called_once_with(
                name="NewPilot", account="Account1", role="DPS", is_main=True, notes="Test notes"
            )

    def test_get_character_update_existing(self):
        """Test get_character updates existing character"""
        from argus_overview.ui.characters_teams_tab import CharacterDialog

        with patch.object(CharacterDialog, "__init__", return_value=None):
            dialog = CharacterDialog.__new__(CharacterDialog)

            mock_char = MagicMock()
            mock_char.name = "ExistingPilot"
            dialog.character = mock_char

            dialog.name_edit = MagicMock()
            dialog.name_edit.text.return_value = "ExistingPilot"
            dialog.account_combo = MagicMock()
            dialog.account_combo.currentText.return_value = "NewAccount"
            dialog.role_combo = MagicMock()
            dialog.role_combo.currentText.return_value = "Miner"
            dialog.is_main_check = MagicMock()
            dialog.is_main_check.isChecked.return_value = False
            dialog.notes_edit = MagicMock()
            dialog.notes_edit.toPlainText.return_value = "Updated notes"

            result = dialog.get_character()

            assert result is mock_char
            assert mock_char.account == "NewAccount"
            assert mock_char.role == "Miner"
            assert mock_char.is_main is False
            assert mock_char.notes == "Updated notes"


# Test TeamBuilder methods in detail
class TestTeamBuilderMethods:
    """Tests for TeamBuilder methods"""

    def test_refresh_layouts(self):
        """Test _refresh_layouts populates dropdown"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.layout_manager = MagicMock()

            mock_preset1 = MagicMock()
            mock_preset1.name = "Preset1"
            mock_preset2 = MagicMock()
            mock_preset2.name = "Preset2"
            builder.layout_manager.get_all_presets.return_value = [mock_preset1, mock_preset2]

            builder.layout_combo = MagicMock()

            builder._refresh_layouts()

            builder.layout_combo.clear.assert_called_once()
            assert builder.layout_combo.addItem.call_count == 3  # Default + 2 presets

    def test_choose_color_valid(self):
        """Test _choose_color with valid color selection"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.team_color = "#4287f5"
            builder._set_color = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QColorDialog") as mock_dialog:
                with patch("argus_overview.ui.characters_teams_tab.QColor"):
                    mock_color = MagicMock()
                    mock_color.isValid.return_value = True
                    mock_color.name.return_value = "#ff0000"
                    mock_dialog.getColor.return_value = mock_color

                    builder._choose_color()

            builder._set_color.assert_called_with("#ff0000")

    def test_choose_color_cancelled(self):
        """Test _choose_color when dialog is cancelled"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.team_color = "#4287f5"
            builder._set_color = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QColorDialog") as mock_dialog:
                with patch("argus_overview.ui.characters_teams_tab.QColor"):
                    mock_color = MagicMock()
                    mock_color.isValid.return_value = False
                    mock_dialog.getColor.return_value = mock_color

                    builder._choose_color()

            builder._set_color.assert_not_called()

    def test_load_team(self):
        """Test load_team populates builder"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.logger = MagicMock()
            builder.character_manager = MagicMock()

            mock_char = MagicMock()
            mock_char.name = "Pilot1"
            builder.character_manager.get_character.return_value = mock_char

            builder.name_edit = MagicMock()
            builder.description_edit = MagicMock()
            builder.layout_combo = MagicMock()
            builder._set_color = MagicMock()
            builder.member_list = MagicMock()
            builder._add_member_to_list = MagicMock()

            mock_team = MagicMock()
            mock_team.name = "TestTeam"
            mock_team.description = "Test description"
            mock_team.layout_name = "Layout1"
            mock_team.color = "#ff0000"
            mock_team.characters = ["Pilot1"]

            builder.load_team(mock_team)

            assert builder.current_team is mock_team
            builder.name_edit.setText.assert_called_with("TestTeam")
            builder.description_edit.setPlainText.assert_called_with("Test description")
            builder._set_color.assert_called_with("#ff0000")
            builder._add_member_to_list.assert_called_once_with(mock_char)

    def test_new_team(self):
        """Test _new_team resets builder"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.logger = MagicMock()
            builder.current_team = MagicMock()

            builder.name_edit = MagicMock()
            builder.description_edit = MagicMock()
            builder.layout_combo = MagicMock()
            builder._set_color = MagicMock()
            builder.member_list = MagicMock()

            builder._new_team()

            assert builder.current_team is None
            builder.name_edit.clear.assert_called_once()
            builder.description_edit.clear.assert_called_once()
            builder._set_color.assert_called_with("#4287f5")
            builder.member_list.clear.assert_called_once()

    def test_add_member_success(self):
        """Test add_member adds character to list"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.logger = MagicMock()
            builder.character_manager = MagicMock()

            mock_char = MagicMock()
            mock_char.name = "Pilot1"
            builder.character_manager.get_character.return_value = mock_char

            builder.member_list = MagicMock()
            builder.member_list.count.return_value = 0  # Empty list
            builder._add_member_to_list = MagicMock()

            builder.add_member("Pilot1")

            builder._add_member_to_list.assert_called_once_with(mock_char)

    def test_add_member_not_found(self):
        """Test add_member when character not found"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.character_manager = MagicMock()
            builder.character_manager.get_character.return_value = None
            builder._add_member_to_list = MagicMock()

            builder.add_member("NonExistent")

            builder._add_member_to_list.assert_not_called()

    def test_add_member_already_in_list(self):
        """Test add_member when character already in team"""

        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.logger = MagicMock()
            builder.character_manager = MagicMock()

            mock_char = MagicMock()
            mock_char.name = "Pilot1"
            builder.character_manager.get_character.return_value = mock_char

            # Mock existing item in list
            mock_item = MagicMock()
            mock_item.data.return_value = "Pilot1"  # Same name stored

            builder.member_list = MagicMock()
            builder.member_list.count.return_value = 1
            builder.member_list.item.return_value = mock_item
            builder._add_member_to_list = MagicMock()

            builder.add_member("Pilot1")

            builder._add_member_to_list.assert_not_called()

    def test_add_member_to_list(self):
        """Test _add_member_to_list creates list item"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.member_list = MagicMock()

            mock_char = MagicMock()
            mock_char.name = "Pilot1"
            mock_char.role = "DPS"

            with patch("argus_overview.ui.characters_teams_tab.QListWidgetItem") as mock_item_class:
                mock_item = MagicMock()
                mock_item_class.return_value = mock_item

                builder._add_member_to_list(mock_char)

            mock_item_class.assert_called_once_with("Pilot1 (DPS)")
            builder.member_list.addItem.assert_called_once_with(mock_item)

    def test_remove_selected_member(self):
        """Test _remove_selected_member removes from list"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.logger = MagicMock()

            mock_item = MagicMock()
            mock_item.data.return_value = "Pilot1"

            builder.member_list = MagicMock()
            builder.member_list.currentItem.return_value = mock_item
            builder.member_list.row.return_value = 0

            builder._remove_selected_member()

            builder.member_list.takeItem.assert_called_once_with(0)

    def test_remove_selected_member_no_selection(self):
        """Test _remove_selected_member with no selection"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.member_list = MagicMock()
            builder.member_list.currentItem.return_value = None

            builder._remove_selected_member()

            builder.member_list.takeItem.assert_not_called()

    def test_validate_empty_name(self):
        """Test _validate with empty team name"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.current_team = None
            builder.character_manager = MagicMock()

            builder.name_edit = MagicMock()
            builder.name_edit.text.return_value = "  "
            builder.member_list = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox"):
                result = builder._validate()

            assert result is False

    def test_validate_no_members(self):
        """Test _validate with no team members"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.current_team = None
            builder.character_manager = MagicMock()

            builder.name_edit = MagicMock()
            builder.name_edit.text.return_value = "MyTeam"
            builder.member_list = MagicMock()
            builder.member_list.count.return_value = 0

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox"):
                result = builder._validate()

            assert result is False

    def test_validate_duplicate_team_name(self):
        """Test _validate with duplicate team name"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.current_team = None  # Creating new team
            builder.character_manager = MagicMock()
            builder.character_manager.get_team.return_value = MagicMock()  # Team exists

            builder.name_edit = MagicMock()
            builder.name_edit.text.return_value = "ExistingTeam"
            builder.member_list = MagicMock()
            builder.member_list.count.return_value = 1

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox"):
                result = builder._validate()

            assert result is False

    def test_validate_success(self):
        """Test _validate with valid data"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.current_team = None
            builder.character_manager = MagicMock()
            builder.character_manager.get_team.return_value = None

            builder.name_edit = MagicMock()
            builder.name_edit.text.return_value = "NewTeam"
            builder.member_list = MagicMock()
            builder.member_list.count.return_value = 2

            result = builder._validate()

            assert result is True

    def test_get_team_new(self):
        """Test _get_team creates new team"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.current_team = None
            builder.team_color = "#ff0000"

            builder.name_edit = MagicMock()
            builder.name_edit.text.return_value = "NewTeam"
            builder.description_edit = MagicMock()
            builder.description_edit.toPlainText.return_value = "Team desc"
            builder.layout_combo = MagicMock()
            builder.layout_combo.currentText.return_value = "Default"

            mock_item = MagicMock()
            mock_item.data.return_value = "Pilot1"
            builder.member_list = MagicMock()
            builder.member_list.count.return_value = 1
            builder.member_list.item.return_value = mock_item

            with patch("argus_overview.ui.characters_teams_tab.Team") as mock_team_class:
                mock_team_class.return_value = MagicMock()
                builder._get_team()

            mock_team_class.assert_called_once()
            call_kwargs = mock_team_class.call_args[1]
            assert call_kwargs["name"] == "NewTeam"
            assert call_kwargs["characters"] == ["Pilot1"]

    def test_get_team_update_existing(self):
        """Test _get_team updates existing team"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)

            mock_existing = MagicMock()
            mock_existing.created_at = "2024-01-01"
            builder.current_team = mock_existing
            builder.team_color = "#00ff00"

            builder.name_edit = MagicMock()
            builder.name_edit.text.return_value = "UpdatedTeam"
            builder.description_edit = MagicMock()
            builder.description_edit.toPlainText.return_value = "Updated desc"
            builder.layout_combo = MagicMock()
            builder.layout_combo.currentText.return_value = "Layout2"

            builder.member_list = MagicMock()
            builder.member_list.count.return_value = 0

            with patch("argus_overview.ui.characters_teams_tab.Team") as mock_team_class:
                builder._get_team()

            # Should preserve created_at from existing team
            call_kwargs = mock_team_class.call_args[1]
            assert call_kwargs["created_at"] == "2024-01-01"

    def test_save_team_create_new_success(self):
        """Test _save_team creates new team successfully"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.current_team = None
            builder.character_manager = MagicMock()
            builder.character_manager.create_team.return_value = True
            builder.team_modified = MagicMock()

            builder._validate = MagicMock(return_value=True)

            mock_team = MagicMock()
            mock_team.name = "NewTeam"
            mock_team.characters = ["Pilot1"]
            builder._get_team = MagicMock(return_value=mock_team)

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox"):
                builder._save_team()

            builder.character_manager.create_team.assert_called_once_with(mock_team)
            builder.character_manager.add_character_to_team.assert_called_once()
            builder.team_modified.emit.assert_called_once()
            assert builder.current_team is mock_team

    def test_save_team_create_new_failure(self):
        """Test _save_team when create fails"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.current_team = None
            builder.character_manager = MagicMock()
            builder.character_manager.create_team.return_value = False
            builder.team_modified = MagicMock()

            builder._validate = MagicMock(return_value=True)

            mock_team = MagicMock()
            mock_team.name = "NewTeam"
            mock_team.characters = []
            builder._get_team = MagicMock(return_value=mock_team)

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox"):
                builder._save_team()

            builder.team_modified.emit.assert_called_once()

    def test_save_team_update_existing(self):
        """Test _save_team updates existing team"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)

            mock_existing = MagicMock()
            mock_existing.name = "ExistingTeam"
            mock_existing.characters = ["OldPilot"]
            builder.current_team = mock_existing

            builder.character_manager = MagicMock()
            builder.team_modified = MagicMock()

            builder._validate = MagicMock(return_value=True)

            mock_team = MagicMock()
            mock_team.name = "ExistingTeam"
            mock_team.description = "Updated"
            mock_team.layout_name = "Layout2"
            mock_team.color = "#ff0000"
            mock_team.characters = ["NewPilot"]  # Changed members
            builder._get_team = MagicMock(return_value=mock_team)

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox"):
                builder._save_team()

            builder.character_manager.update_team.assert_called_once()
            builder.character_manager.remove_character_from_team.assert_called_once()
            builder.character_manager.add_character_to_team.assert_called_once()

    def test_save_team_validation_fails(self):
        """Test _save_team when validation fails"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder._validate = MagicMock(return_value=False)
            builder._get_team = MagicMock()

            builder._save_team()

            builder._get_team.assert_not_called()


# Test CharactersTeamsTab methods in detail
class TestCharactersTeamsTabMethods:
    """Tests for CharactersTeamsTab methods"""

    def test_refresh_teams(self):
        """Test _refresh_teams populates dropdown"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()

            mock_team = MagicMock()
            mock_team.name = "Team1"
            tab.character_manager.get_all_teams.return_value = [mock_team]

            tab.team_combo = MagicMock()
            tab.team_combo.currentText.return_value = "Team1"
            tab.team_combo.findText.return_value = 1

            tab._refresh_teams()

            tab.team_combo.clear.assert_called_once()
            assert tab.team_combo.addItem.call_count == 2  # "-- New Team --" + Team1

    def test_add_character_dialog_accepted(self):
        """Test _add_character when dialog is accepted"""
        from PySide6.QtWidgets import QDialog

        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.logger = MagicMock()
            tab.character_manager = MagicMock()
            tab.character_manager.add_character.return_value = True

            mock_char = MagicMock()
            mock_char.name = "NewPilot"

            tab.character_table = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.CharacterDialog") as mock_dialog:
                mock_instance = MagicMock()
                mock_instance.exec.return_value = QDialog.DialogCode.Accepted
                mock_instance.get_character.return_value = mock_char
                mock_dialog.return_value = mock_instance

                tab._add_character()

            tab.character_manager.add_character.assert_called_once_with(mock_char)
            tab.character_table.populate_table.assert_called_once()

    def test_add_character_dialog_cancelled(self):
        """Test _add_character when dialog is cancelled"""
        from PySide6.QtWidgets import QDialog

        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.character_table = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.CharacterDialog") as mock_dialog:
                mock_instance = MagicMock()
                mock_instance.exec.return_value = QDialog.DialogCode.Rejected
                mock_dialog.return_value = mock_instance

                tab._add_character()

            tab.character_manager.add_character.assert_not_called()

    def test_edit_character_no_selection(self):
        """Test _edit_character with no selection"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_table = MagicMock()
            tab.character_table.get_selected_characters.return_value = []

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                tab._edit_character()

            mock_msg.information.assert_called_once()

    def test_edit_character_success(self):
        """Test _edit_character with valid selection"""
        from PySide6.QtWidgets import QDialog

        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.logger = MagicMock()
            tab.character_manager = MagicMock()

            mock_char = MagicMock()
            mock_char.name = "Pilot1"
            tab.character_manager.get_character.return_value = mock_char

            tab.character_table = MagicMock()
            tab.character_table.get_selected_characters.return_value = ["Pilot1"]

            with patch("argus_overview.ui.characters_teams_tab.CharacterDialog") as mock_dialog:
                mock_updated = MagicMock()
                mock_instance = MagicMock()
                mock_instance.exec.return_value = QDialog.DialogCode.Accepted
                mock_instance.get_character.return_value = mock_updated
                mock_dialog.return_value = mock_instance

                tab._edit_character()

            tab.character_manager.update_character.assert_called_once()
            tab.character_table.populate_table.assert_called_once()

    def test_delete_character_no_selection(self):
        """Test _delete_character with no selection"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_table = MagicMock()
            tab.character_table.get_selected_characters.return_value = []

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                tab._delete_character()

            mock_msg.information.assert_called_once()

    def test_delete_character_confirmed(self):
        """Test _delete_character when user confirms"""
        from PySide6.QtWidgets import QMessageBox

        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.logger = MagicMock()
            tab.character_manager = MagicMock()
            tab.character_manager.remove_character.return_value = True

            tab.character_table = MagicMock()
            tab.character_table.get_selected_characters.return_value = ["Pilot1"]

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                mock_msg.StandardButton.Yes = QMessageBox.StandardButton.Yes
                mock_msg.StandardButton.No = QMessageBox.StandardButton.No
                mock_msg.question.return_value = QMessageBox.StandardButton.Yes

                tab._delete_character()

            tab.character_manager.remove_character.assert_called_once_with("Pilot1")

    def test_delete_character_cancelled(self):
        """Test _delete_character when user cancels"""
        from PySide6.QtWidgets import QMessageBox

        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.character_table = MagicMock()
            tab.character_table.get_selected_characters.return_value = ["Pilot1"]

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                mock_msg.StandardButton.Yes = QMessageBox.StandardButton.Yes
                mock_msg.StandardButton.No = QMessageBox.StandardButton.No
                mock_msg.question.return_value = QMessageBox.StandardButton.No

                tab._delete_character()

            tab.character_manager.remove_character.assert_not_called()

    def test_scan_eve_folder_no_sync(self):
        """Test _scan_eve_folder when settings_sync is None"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.settings_sync = None

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                tab._scan_eve_folder()

            mock_msg.warning.assert_called_once()

    def test_scan_eve_folder_no_characters(self):
        """Test _scan_eve_folder when no characters found"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.settings_sync = MagicMock()
            tab.settings_sync.get_all_known_characters.return_value = []

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                tab._scan_eve_folder()

            assert mock_msg.warning.call_count == 1

    def test_scan_eve_folder_success(self):
        """Test _scan_eve_folder with characters found"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.logger = MagicMock()
            tab.settings_sync = MagicMock()
            tab.settings_sync.get_all_known_characters.return_value = [
                {"name": "Pilot1"},
                {"name": "Pilot2"},
            ]

            tab.character_manager = MagicMock()
            tab.character_manager.import_from_eve_sync.return_value = 2

            tab.character_table = MagicMock()
            tab.characters_imported = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox"):
                tab._scan_eve_folder()

            tab.character_manager.import_from_eve_sync.assert_called_once()
            tab.character_table.populate_table.assert_called_once()
            tab.characters_imported.emit.assert_called_once_with(2)

    def test_scan_eve_folder_exception(self):
        """Test _scan_eve_folder when exception occurs"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.logger = MagicMock()
            tab.settings_sync = MagicMock()
            tab.settings_sync.get_all_known_characters.side_effect = Exception("Test error")

            with patch("argus_overview.ui.characters_teams_tab.QMessageBox") as mock_msg:
                tab._scan_eve_folder()

            mock_msg.critical.assert_called_once()

    def test_on_team_selected_new_team(self):
        """Test _on_team_selected with 'New Team' option"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.team_builder = MagicMock()

            tab._on_team_selected("-- New Team --")

            tab.team_builder._new_team.assert_called_once()

    def test_on_team_selected_existing_team(self):
        """Test _on_team_selected with existing team"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.team_selected = MagicMock()

            mock_team = MagicMock()
            tab.character_manager.get_team.return_value = mock_team

            tab.team_builder = MagicMock()

            tab._on_team_selected("TestTeam")

            tab.team_builder.load_team.assert_called_once_with(mock_team)
            tab.team_selected.emit.assert_called_once_with(mock_team)

    def test_on_team_selected_team_not_found(self):
        """Test _on_team_selected when team not found"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.character_manager.get_team.return_value = None
            tab.team_builder = MagicMock()

            tab._on_team_selected("NonExistent")

            tab.team_builder.load_team.assert_not_called()

    def test_on_team_modified(self):
        """Test _on_team_modified refreshes teams"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.logger = MagicMock()
            tab._refresh_teams = MagicMock()

            tab._on_team_modified()

            tab._refresh_teams.assert_called_once()

    def test_update_character_status(self):
        """Test update_character_status delegates to table"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_table = MagicMock()

            tab.update_character_status("Pilot1", "0x123")

            tab.character_table.update_character_status.assert_called_once_with("Pilot1", "0x123")

    def test_edit_character_not_found(self):
        """Test _edit_character when character not found in manager"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.character_manager.get_character.return_value = None  # Not found

            tab.character_table = MagicMock()
            tab.character_table.get_selected_characters.return_value = ["NonExistent"]

            with patch("argus_overview.ui.characters_teams_tab.CharacterDialog") as mock_dialog:
                tab._edit_character()

            # Dialog should not be created if character not found
            mock_dialog.assert_not_called()


# Test TeamBuilder._add_selected_character stub
class TestTeamBuilderStub:
    """Test stub methods"""

    def test_add_selected_character_stub(self):
        """Test _add_selected_character is a stub (pass)"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)

            # Should not raise - just passes
            builder._add_selected_character()


# Test load_team with character not found
class TestTeamBuilderEdgeCases:
    """Additional edge case tests for TeamBuilder"""

    def test_load_team_character_not_found(self):
        """Test load_team when a team member character doesn't exist"""
        from argus_overview.ui.characters_teams_tab import TeamBuilder

        with patch.object(TeamBuilder, "__init__", return_value=None):
            builder = TeamBuilder.__new__(TeamBuilder)
            builder.logger = MagicMock()
            builder.character_manager = MagicMock()
            builder.character_manager.get_character.return_value = None  # Not found

            builder.name_edit = MagicMock()
            builder.description_edit = MagicMock()
            builder.layout_combo = MagicMock()
            builder._set_color = MagicMock()
            builder.member_list = MagicMock()
            builder._add_member_to_list = MagicMock()

            mock_team = MagicMock()
            mock_team.name = "TestTeam"
            mock_team.description = "Test"
            mock_team.layout_name = "Default"
            mock_team.color = "#ff0000"
            mock_team.characters = ["NonExistentPilot"]

            builder.load_team(mock_team)

            # _add_member_to_list should NOT be called because char was not found
            builder._add_member_to_list.assert_not_called()


class TestUISetupMethods:
    """Tests for _setup_ui, _create_left_panel, _create_right_panel"""

    def test_setup_ui_creates_splitter(self):
        """Test _setup_ui creates horizontal splitter with panels"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)

            mock_left_panel = MagicMock()
            mock_right_panel = MagicMock()
            tab._create_left_panel = MagicMock(return_value=mock_left_panel)
            tab._create_right_panel = MagicMock(return_value=mock_right_panel)

            with patch(
                "argus_overview.ui.characters_teams_tab.QHBoxLayout"
            ) as mock_layout_cls, patch(
                "argus_overview.ui.characters_teams_tab.QSplitter"
            ) as mock_splitter_cls:
                mock_layout = MagicMock()
                mock_layout_cls.return_value = mock_layout

                mock_splitter = MagicMock()
                mock_splitter_cls.return_value = mock_splitter

                tab.setLayout = MagicMock()

                tab._setup_ui()

                # Verify layout created and set
                mock_layout.setContentsMargins.assert_called_once_with(5, 5, 5, 5)
                tab.setLayout.assert_called_once_with(mock_layout)

                # Verify splitter created and panels added
                mock_layout.addWidget.assert_called_once_with(mock_splitter)
                assert mock_splitter.addWidget.call_count == 2
                mock_splitter.setSizes.assert_called_once_with([600, 400])

    def test_setup_ui_calls_panel_creators(self):
        """Test _setup_ui calls both panel creation methods"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)

            tab._create_left_panel = MagicMock(return_value=MagicMock())
            tab._create_right_panel = MagicMock(return_value=MagicMock())
            tab.setLayout = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QHBoxLayout"), patch(
                "argus_overview.ui.characters_teams_tab.QSplitter"
            ):
                tab._setup_ui()

            tab._create_left_panel.assert_called_once()
            tab._create_right_panel.assert_called_once()

    def test_create_left_panel_creates_toolbar(self):
        """Test _create_left_panel creates toolbar with action buttons"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.settings_sync = None  # No scan button
            tab._add_character = MagicMock()
            tab._edit_character = MagicMock()
            tab._delete_character = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QWidget") as mock_widget_cls, patch(
                "argus_overview.ui.characters_teams_tab.QVBoxLayout"
            ) as mock_vlayout_cls, patch(
                "argus_overview.ui.characters_teams_tab.QHBoxLayout"
            ) as mock_hlayout_cls, patch(
                "argus_overview.ui.characters_teams_tab.ToolbarBuilder"
            ) as mock_builder_cls, patch(
                "argus_overview.ui.characters_teams_tab.CharacterTable"
            ) as mock_table_cls:
                mock_panel = MagicMock()
                mock_widget_cls.return_value = mock_panel

                mock_vlayout = MagicMock()
                mock_vlayout_cls.return_value = mock_vlayout

                mock_hlayout = MagicMock()
                mock_hlayout_cls.return_value = mock_hlayout

                mock_builder = MagicMock()
                mock_builder.create_button.return_value = MagicMock()  # Return a button
                mock_builder_cls.return_value = mock_builder

                mock_table = MagicMock()
                mock_table_cls.return_value = mock_table

                result = tab._create_left_panel()

                # Verify panel setup
                mock_panel.setLayout.assert_called_once_with(mock_vlayout)

                # Verify toolbar buttons created
                assert mock_builder.create_button.call_count >= 3  # add, edit, delete

                # Verify character table created
                mock_table_cls.assert_called_once_with(tab.character_manager)
                assert result == mock_panel

    def test_create_left_panel_with_settings_sync(self):
        """Test _create_left_panel adds scan button when settings_sync available"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.settings_sync = MagicMock()  # Has settings_sync
            tab._add_character = MagicMock()
            tab._edit_character = MagicMock()
            tab._delete_character = MagicMock()
            tab._scan_eve_folder = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QWidget"), patch(
                "argus_overview.ui.characters_teams_tab.QVBoxLayout"
            ), patch("argus_overview.ui.characters_teams_tab.QHBoxLayout"), patch(
                "argus_overview.ui.characters_teams_tab.ToolbarBuilder"
            ) as mock_builder_cls, patch("argus_overview.ui.characters_teams_tab.CharacterTable"):
                mock_builder = MagicMock()
                mock_builder.create_button.return_value = MagicMock()
                mock_builder_cls.return_value = mock_builder

                tab._create_left_panel()

                # Verify scan_eve_folder button was requested
                button_names = [call[0][0] for call in mock_builder.create_button.call_args_list]
                assert "scan_eve_folder" in button_names

    def test_create_left_panel_handles_none_buttons(self):
        """Test _create_left_panel handles None return from create_button"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.settings_sync = None
            tab._add_character = MagicMock()
            tab._edit_character = MagicMock()
            tab._delete_character = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QWidget") as mock_widget_cls, patch(
                "argus_overview.ui.characters_teams_tab.QVBoxLayout"
            ), patch(
                "argus_overview.ui.characters_teams_tab.QHBoxLayout"
            ) as mock_hlayout_cls, patch(
                "argus_overview.ui.characters_teams_tab.ToolbarBuilder"
            ) as mock_builder_cls, patch("argus_overview.ui.characters_teams_tab.CharacterTable"):
                mock_panel = MagicMock()
                mock_widget_cls.return_value = mock_panel

                mock_hlayout = MagicMock()
                mock_hlayout_cls.return_value = mock_hlayout

                mock_builder = MagicMock()
                mock_builder.create_button.return_value = None  # Return None
                mock_builder_cls.return_value = mock_builder

                result = tab._create_left_panel()

                # Should not crash, toolbar addWidget not called for None buttons
                # But addStretch should still be called
                mock_hlayout.addStretch.assert_called_once()
                assert result == mock_panel

    def test_create_right_panel_creates_team_selector(self):
        """Test _create_right_panel creates team selector combo"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.layout_manager = MagicMock()
            tab.character_table = MagicMock()  # Set by _create_left_panel
            tab._on_team_selected = MagicMock()
            tab._on_team_modified = MagicMock()
            tab._refresh_teams = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QWidget") as mock_widget_cls, patch(
                "argus_overview.ui.characters_teams_tab.QVBoxLayout"
            ) as mock_vlayout_cls, patch(
                "argus_overview.ui.characters_teams_tab.QHBoxLayout"
            ) as mock_hlayout_cls, patch("argus_overview.ui.characters_teams_tab.QLabel"), patch(
                "argus_overview.ui.characters_teams_tab.QComboBox"
            ) as mock_combo_cls, patch(
                "argus_overview.ui.characters_teams_tab.TeamBuilder"
            ) as mock_builder_cls:
                mock_panel = MagicMock()
                mock_widget_cls.return_value = mock_panel

                mock_vlayout = MagicMock()
                mock_vlayout_cls.return_value = mock_vlayout

                mock_hlayout = MagicMock()
                mock_hlayout_cls.return_value = mock_hlayout

                mock_combo = MagicMock()
                mock_combo_cls.return_value = mock_combo

                mock_team_builder = MagicMock()
                mock_builder_cls.return_value = mock_team_builder

                result = tab._create_right_panel()

                # Verify combo created and connected
                mock_combo.currentTextChanged.connect.assert_called_once()
                tab._refresh_teams.assert_called_once()

                # Verify team builder created
                mock_builder_cls.assert_called_once_with(tab.character_manager, tab.layout_manager)
                mock_team_builder.team_modified.connect.assert_called_once()

                assert result == mock_panel
                assert tab.team_combo == mock_combo
                assert tab.team_builder == mock_team_builder

    def test_create_right_panel_connects_character_table(self):
        """Test _create_right_panel connects character_table to team_builder"""
        from argus_overview.ui.characters_teams_tab import CharactersTeamsTab

        with patch.object(CharactersTeamsTab, "__init__", return_value=None):
            tab = CharactersTeamsTab.__new__(CharactersTeamsTab)
            tab.character_manager = MagicMock()
            tab.layout_manager = MagicMock()
            tab.character_table = MagicMock()  # Already created
            tab._on_team_selected = MagicMock()
            tab._on_team_modified = MagicMock()
            tab._refresh_teams = MagicMock()

            with patch("argus_overview.ui.characters_teams_tab.QWidget"), patch(
                "argus_overview.ui.characters_teams_tab.QVBoxLayout"
            ), patch("argus_overview.ui.characters_teams_tab.QHBoxLayout"), patch(
                "argus_overview.ui.characters_teams_tab.QLabel"
            ), patch("argus_overview.ui.characters_teams_tab.QComboBox"), patch(
                "argus_overview.ui.characters_teams_tab.TeamBuilder"
            ) as mock_builder_cls:
                mock_team_builder = MagicMock()
                mock_builder_cls.return_value = mock_team_builder

                tab._create_right_panel()

                # Verify character_table.character_selected connected to team_builder.add_member
                tab.character_table.character_selected.connect.assert_called_once_with(
                    mock_team_builder.add_member
                )
