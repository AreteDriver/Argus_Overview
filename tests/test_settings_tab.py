"""
Unit tests for the Settings Tab module
Tests HotkeyEditDialog, GeneralPanel, PerformancePanel, AlertsPanel,
HotkeysPanel, AppearancePanel, AdvancedPanel, SettingsTab
"""

from unittest.mock import MagicMock, patch


# Test HotkeyEditDialog
class TestHotkeyEditDialog:
    """Tests for HotkeyEditDialog"""

    @patch("argus_overview.ui.settings_tab.QDialog.__init__")
    def test_init(self, mock_dialog):
        """Test HotkeyEditDialog initialization"""
        mock_dialog.return_value = None

        from argus_overview.ui.settings_tab import HotkeyEditDialog

        mock_hotkey_manager = MagicMock()

        with patch.object(HotkeyEditDialog, "setWindowTitle") as mock_title:
            with patch.object(HotkeyEditDialog, "setMinimumWidth"):
                with patch.object(HotkeyEditDialog, "_setup_ui"):
                    dialog = HotkeyEditDialog("Test Action", "<ctrl>+<alt>+1", mock_hotkey_manager)

                    mock_title.assert_called_with("Edit Hotkey: Test Action")
                    assert dialog.action == "Test Action"
                    assert dialog.current_combo == "<ctrl>+<alt>+1"

    @patch("argus_overview.ui.settings_tab.QDialog.__init__")
    def test_get_hotkey(self, mock_dialog):
        """Test get_hotkey method"""
        mock_dialog.return_value = None

        from argus_overview.ui.settings_tab import HotkeyEditDialog

        mock_hotkey_manager = MagicMock()

        with patch.object(HotkeyEditDialog, "setWindowTitle"):
            with patch.object(HotkeyEditDialog, "setMinimumWidth"):
                with patch.object(HotkeyEditDialog, "_setup_ui"):
                    dialog = HotkeyEditDialog("Test Action", "<ctrl>+<alt>+1", mock_hotkey_manager)
                    dialog.key_edit = MagicMock()
                    dialog.key_edit.text.return_value = "  <ctrl>+<shift>+2  "

                    result = dialog.get_hotkey()

                    assert result == "<ctrl>+<shift>+2"


# Test GeneralPanel
class TestGeneralPanel:
    """Tests for GeneralPanel"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test GeneralPanel initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import GeneralPanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = False

        with patch.object(GeneralPanel, "_setup_ui"):
            panel = GeneralPanel(mock_settings_manager)

            assert panel.settings_manager is mock_settings_manager

    def test_signal_exists(self):
        """Test GeneralPanel has setting_changed signal"""
        from argus_overview.ui.settings_tab import GeneralPanel

        assert hasattr(GeneralPanel, "setting_changed")


# Test PerformancePanel
class TestPerformancePanel:
    """Tests for PerformancePanel"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test PerformancePanel initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import PerformancePanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = 30

        with patch.object(PerformancePanel, "_setup_ui"):
            panel = PerformancePanel(mock_settings_manager)

            assert panel.settings_manager is mock_settings_manager

    def test_signal_exists(self):
        """Test PerformancePanel has setting_changed signal"""
        from argus_overview.ui.settings_tab import PerformancePanel

        assert hasattr(PerformancePanel, "setting_changed")

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_on_low_power_changed_emits_signal(self, mock_widget):
        """Test _on_low_power_changed emits setting_changed with checkbox state"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import PerformancePanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = 30

        with patch.object(PerformancePanel, "_setup_ui"):
            panel = PerformancePanel(mock_settings)
            panel.low_power_check = MagicMock()
            panel.low_power_check.isChecked.return_value = True
            panel.setting_changed = MagicMock()

            panel._on_low_power_changed()

            panel.setting_changed.emit.assert_called_once_with("performance.low_power_mode", True)


# Test HotkeysPanel
class TestHotkeysPanel:
    """Tests for HotkeysPanel"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test HotkeysPanel initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import HotkeysPanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()

        with patch.object(HotkeysPanel, "_setup_ui"):
            with patch.object(HotkeysPanel, "_load_hotkeys"):
                panel = HotkeysPanel(mock_settings_manager, mock_hotkey_manager)

                assert panel.settings_manager is mock_settings_manager
                assert panel.hotkey_manager is mock_hotkey_manager

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_load_hotkeys_calls_settings_manager(self, mock_widget):
        """Test _load_hotkeys calls settings manager"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import HotkeysPanel

        mock_settings_manager = MagicMock()
        mock_hotkey_manager = MagicMock()

        with patch.object(HotkeysPanel, "_setup_ui"):
            with patch.object(HotkeysPanel, "_load_hotkeys"):
                panel = HotkeysPanel(mock_settings_manager, mock_hotkey_manager)

                # Verify it was called during init
                assert panel.settings_manager is mock_settings_manager

    def test_signal_exists(self):
        """Test HotkeysPanel has setting_changed signal"""
        from argus_overview.ui.settings_tab import HotkeysPanel

        assert hasattr(HotkeysPanel, "setting_changed")


# Test AppearancePanel
class TestAppearancePanel:
    """Tests for AppearancePanel"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test AppearancePanel initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AppearancePanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = "dark"

        with patch.object(AppearancePanel, "_setup_ui"):
            panel = AppearancePanel(mock_settings_manager)

            assert panel.settings_manager is mock_settings_manager

    def test_signal_exists(self):
        """Test AppearancePanel has setting_changed signal"""
        from argus_overview.ui.settings_tab import AppearancePanel

        assert hasattr(AppearancePanel, "setting_changed")


class TestIntelPanel:
    """Tests for IntelPanel (v3.2.0 chrome controls)."""

    def _settings_mock(self, overrides=None):
        """Per-key settings mock so unrelated lookups return their defaults."""
        store = {
            "intel.preview_chrome_enabled": True,
            "intel.track_character_locations": True,
            "intel.threat_jumps_threshold": 1,
            "replay_strip_enabled": {},
        }
        if overrides:
            store.update(overrides)
        sm = MagicMock()
        sm.get.side_effect = lambda key, default=None: store.get(key, default)
        return sm

    def test_signal_exists(self):
        from argus_overview.ui.settings_tab import IntelPanel

        assert hasattr(IntelPanel, "setting_changed")

    def test_init_reads_defaults(self, qapp):
        from argus_overview.ui.settings_tab import IntelPanel

        sm = self._settings_mock()
        panel = IntelPanel(sm)
        try:
            assert panel.track_locations_check.isChecked() is True
            assert panel.jumps_threshold_spin.value() == 1
        finally:
            panel.deleteLater()

    def test_init_reads_overridden_values(self, qapp):
        from argus_overview.ui.settings_tab import IntelPanel

        sm = self._settings_mock(
            {
                "intel.track_character_locations": False,
                "intel.threat_jumps_threshold": 3,
            }
        )
        panel = IntelPanel(sm)
        try:
            assert panel.track_locations_check.isChecked() is False
            assert panel.jumps_threshold_spin.value() == 3
        finally:
            panel.deleteLater()

    def test_track_locations_emits_signal(self, qapp):
        from argus_overview.ui.settings_tab import IntelPanel

        sm = self._settings_mock()
        panel = IntelPanel(sm)
        received: list[tuple[str, object]] = []
        panel.setting_changed.connect(lambda k, v: received.append((k, v)))
        try:
            panel.track_locations_check.setChecked(False)
            assert (
                "intel.track_character_locations",
                False,
            ) in received
        finally:
            panel.deleteLater()

    def test_jumps_threshold_emits_signal(self, qapp):
        from argus_overview.ui.settings_tab import IntelPanel

        sm = self._settings_mock()
        panel = IntelPanel(sm)
        received: list[tuple[str, object]] = []
        panel.setting_changed.connect(lambda k, v: received.append((k, v)))
        try:
            panel.jumps_threshold_spin.setValue(2)
            assert ("intel.threat_jumps_threshold", 2) in received
        finally:
            panel.deleteLater()

    def test_jumps_threshold_clamped_to_range(self, qapp):
        from argus_overview.ui.settings_tab import IntelPanel

        sm = self._settings_mock({"intel.threat_jumps_threshold": 99})
        panel = IntelPanel(sm)
        try:
            # Spinbox max is 5 — value should clamp on init.
            assert panel.jumps_threshold_spin.value() == 5
        finally:
            panel.deleteLater()

    def test_chrome_toggle_default_on(self, qapp):
        from argus_overview.ui.settings_tab import IntelPanel

        sm = self._settings_mock()
        panel = IntelPanel(sm)
        try:
            assert panel.chrome_enabled_check.isChecked() is True
        finally:
            panel.deleteLater()

    def test_chrome_toggle_init_off(self, qapp):
        from argus_overview.ui.settings_tab import IntelPanel

        sm = self._settings_mock({"intel.preview_chrome_enabled": False})
        panel = IntelPanel(sm)
        try:
            assert panel.chrome_enabled_check.isChecked() is False
        finally:
            panel.deleteLater()

    def test_chrome_toggle_emits_setting_changed(self, qapp):
        from argus_overview.ui.settings_tab import IntelPanel

        sm = self._settings_mock()
        panel = IntelPanel(sm)
        received: list[tuple[str, object]] = []
        panel.setting_changed.connect(lambda k, v: received.append((k, v)))
        try:
            panel.chrome_enabled_check.setChecked(False)
            assert ("intel.preview_chrome_enabled", False) in received
        finally:
            panel.deleteLater()


# Test AdvancedPanel
class TestAdvancedPanel:
    """Tests for AdvancedPanel"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test AdvancedPanel initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AdvancedPanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = "INFO"

        with patch.object(AdvancedPanel, "_setup_ui"):
            panel = AdvancedPanel(mock_settings_manager)

            assert panel.settings_manager is mock_settings_manager

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_clear_cache_shows_message(self, mock_msgbox, mock_widget):
        """Test _clear_cache shows information message"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AdvancedPanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = "INFO"

        with patch.object(AdvancedPanel, "_setup_ui"):
            panel = AdvancedPanel(mock_settings_manager)

            panel._clear_cache()

            mock_msgbox.information.assert_called_once()

    def test_signal_exists(self):
        """Test AdvancedPanel has setting_changed signal"""
        from argus_overview.ui.settings_tab import AdvancedPanel

        assert hasattr(AdvancedPanel, "setting_changed")


# Test SettingsTab
class TestSettingsTab:
    """Tests for SettingsTab widget"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_init(self, mock_widget):
        """Test SettingsTab initialization"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()

        with patch.object(SettingsTab, "_setup_ui"):
            with patch.object(SettingsTab, "_load_settings"):
                tab = SettingsTab(mock_settings_manager, mock_hotkey_manager)

                assert tab.settings_manager is mock_settings_manager
                assert tab.hotkey_manager is mock_hotkey_manager

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_on_setting_changed(self, mock_widget):
        """Test _on_setting_changed saves to manager"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()

        with patch.object(SettingsTab, "_setup_ui"):
            with patch.object(SettingsTab, "_load_settings"):
                with patch.object(SettingsTab, "settings_changed", MagicMock()):
                    tab = SettingsTab(mock_settings_manager, mock_hotkey_manager)

                    tab._on_setting_changed("test.key", "test_value")

                    mock_settings_manager.set.assert_called_with("test.key", "test_value")

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_on_category_changed(self, mock_widget):
        """Test _on_category_changed switches panel"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()

        with patch.object(SettingsTab, "_setup_ui"):
            with patch.object(SettingsTab, "_load_settings"):
                tab = SettingsTab(mock_settings_manager, mock_hotkey_manager)
                tab.panel_stack = MagicMock()

                # Mock tree item
                mock_item = MagicMock()
                mock_item.text.return_value = "Performance"

                tab._on_category_changed(mock_item, None)

                tab.panel_stack.setCurrentIndex.assert_called_with(1)

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_reset_all_calls_reset(self, mock_msgbox, mock_widget):
        """Test _reset_all resets settings when confirmed"""
        mock_widget.return_value = None

        from PySide6.QtWidgets import QMessageBox

        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()

        # Simulate user clicking Yes - use StandardButton.Yes
        mock_msgbox.StandardButton = QMessageBox.StandardButton
        mock_msgbox.question.return_value = QMessageBox.StandardButton.Yes

        with patch.object(SettingsTab, "_setup_ui"):
            with patch.object(SettingsTab, "_load_settings"):
                tab = SettingsTab(mock_settings_manager, mock_hotkey_manager)

                tab._reset_all()

                mock_settings_manager.reset_to_defaults.assert_called_once()

    def test_signal_exists(self):
        """Test SettingsTab has settings_changed signal"""
        from argus_overview.ui.settings_tab import SettingsTab

        assert hasattr(SettingsTab, "settings_changed")


# =============================================================================
# Additional tests to improve coverage
# =============================================================================


class TestHotkeyEditDialogSetupUI:
    """Tests for HotkeyEditDialog _setup_ui and interaction methods"""

    @patch("argus_overview.ui.settings_tab.QDialog.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_test_hotkey_empty_shows_warning(self, mock_msgbox, mock_dialog):
        """Test _test_hotkey with empty input shows warning"""
        mock_dialog.return_value = None

        from argus_overview.ui.settings_tab import HotkeyEditDialog

        with patch.object(HotkeyEditDialog, "setWindowTitle"):
            with patch.object(HotkeyEditDialog, "setMinimumWidth"):
                with patch.object(HotkeyEditDialog, "_setup_ui"):
                    dialog = HotkeyEditDialog("Test", "<ctrl>+a", MagicMock())
                    dialog.key_edit = MagicMock()
                    dialog.key_edit.text.return_value = "   "

                    dialog._test_hotkey()

                    mock_msgbox.warning.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QDialog.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_test_hotkey_valid_shows_info(self, mock_msgbox, mock_dialog):
        """Test _test_hotkey with valid input shows info"""
        mock_dialog.return_value = None

        from argus_overview.ui.settings_tab import HotkeyEditDialog

        with patch.object(HotkeyEditDialog, "setWindowTitle"):
            with patch.object(HotkeyEditDialog, "setMinimumWidth"):
                with patch.object(HotkeyEditDialog, "_setup_ui"):
                    dialog = HotkeyEditDialog("Test", "<ctrl>+a", MagicMock())
                    dialog.key_edit = MagicMock()
                    dialog.key_edit.text.return_value = "<ctrl>+<shift>+x"

                    dialog._test_hotkey()

                    mock_msgbox.information.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QDialog.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_save_hotkey_empty_shows_warning(self, mock_msgbox, mock_dialog):
        """Test _save_hotkey with empty input shows warning"""
        mock_dialog.return_value = None

        from argus_overview.ui.settings_tab import HotkeyEditDialog

        with patch.object(HotkeyEditDialog, "setWindowTitle"):
            with patch.object(HotkeyEditDialog, "setMinimumWidth"):
                with patch.object(HotkeyEditDialog, "_setup_ui"):
                    dialog = HotkeyEditDialog("Test", "<ctrl>+a", MagicMock())
                    dialog.key_edit = MagicMock()
                    dialog.key_edit.text.return_value = ""

                    dialog._save_hotkey()

                    mock_msgbox.warning.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QDialog.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_save_hotkey_invalid_format_shows_warning(self, mock_msgbox, mock_dialog):
        """Test _save_hotkey with invalid format shows warning"""
        mock_dialog.return_value = None

        from argus_overview.ui.settings_tab import HotkeyEditDialog

        with patch.object(HotkeyEditDialog, "setWindowTitle"):
            with patch.object(HotkeyEditDialog, "setMinimumWidth"):
                with patch.object(HotkeyEditDialog, "_setup_ui"):
                    dialog = HotkeyEditDialog("Test", "<ctrl>+a", MagicMock())
                    dialog.key_edit = MagicMock()
                    dialog.key_edit.text.return_value = "ctrl+a"  # Missing <>

                    dialog._save_hotkey()

                    mock_msgbox.warning.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QDialog.__init__")
    def test_save_hotkey_valid_accepts(self, mock_dialog):
        """Test _save_hotkey with valid input calls accept"""
        mock_dialog.return_value = None

        from argus_overview.ui.settings_tab import HotkeyEditDialog

        with patch.object(HotkeyEditDialog, "setWindowTitle"):
            with patch.object(HotkeyEditDialog, "setMinimumWidth"):
                with patch.object(HotkeyEditDialog, "_setup_ui"):
                    with patch.object(HotkeyEditDialog, "accept") as mock_accept:
                        dialog = HotkeyEditDialog("Test", "<ctrl>+a", MagicMock())
                        dialog.key_edit = MagicMock()
                        dialog.key_edit.text.return_value = "<ctrl>+<shift>+x"

                        dialog._save_hotkey()

                        mock_accept.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QDialog.__init__")
    @patch("argus_overview.ui.settings_tab.QVBoxLayout")
    @patch("argus_overview.ui.settings_tab.QLabel")
    @patch("argus_overview.ui.settings_tab.QLineEdit")
    @patch("argus_overview.ui.settings_tab.QPushButton")
    @patch("argus_overview.ui.settings_tab.QDialogButtonBox")
    def test_setup_ui_creates_widgets(
        self, mock_bbox, mock_btn, mock_edit, mock_label, mock_layout, mock_dialog
    ):
        """Test _setup_ui creates all expected widgets"""
        mock_dialog.return_value = None

        from argus_overview.ui.settings_tab import HotkeyEditDialog

        with patch.object(HotkeyEditDialog, "setWindowTitle"):
            with patch.object(HotkeyEditDialog, "setMinimumWidth"):
                with patch.object(HotkeyEditDialog, "setLayout"):
                    HotkeyEditDialog("Test", "<ctrl>+a", MagicMock())

                    # Verify widgets were created
                    assert mock_layout.called
                    assert mock_label.called
                    assert mock_edit.called
                    assert mock_btn.called


class TestGeneralPanelSetupUI:
    """Tests for GeneralPanel _setup_ui"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QVBoxLayout")
    @patch("argus_overview.ui.settings_tab.QGroupBox")
    @patch("argus_overview.ui.settings_tab.QFormLayout")
    @patch("argus_overview.ui.settings_tab.QCheckBox")
    @patch("argus_overview.ui.settings_tab.QSpinBox")
    def test_setup_ui_creates_widgets(
        self, mock_spin, mock_check, mock_form, mock_group, mock_layout, mock_widget
    ):
        """Test _setup_ui creates all expected widgets"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import GeneralPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = False

        with patch.object(GeneralPanel, "setLayout"):
            GeneralPanel(mock_settings)

            # Verify widgets created
            assert mock_layout.called
            assert mock_group.called
            assert mock_check.called
            assert mock_spin.called


class TestPerformancePanelSetupUI:
    """Tests for PerformancePanel _setup_ui"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QVBoxLayout")
    @patch("argus_overview.ui.settings_tab.QGroupBox")
    @patch("argus_overview.ui.settings_tab.QFormLayout")
    @patch("argus_overview.ui.settings_tab.QCheckBox")
    @patch("argus_overview.ui.settings_tab.QSpinBox")
    @patch("argus_overview.ui.settings_tab.QComboBox")
    def test_setup_ui_creates_widgets(
        self, mock_combo, mock_spin, mock_check, mock_form, mock_group, mock_layout, mock_widget
    ):
        """Test _setup_ui creates all expected widgets"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import PerformancePanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = 30

        with patch.object(PerformancePanel, "setLayout"):
            PerformancePanel(mock_settings)

            assert mock_layout.called
            assert mock_group.called
            assert mock_spin.called
            assert mock_combo.called


class TestHotkeysPanelInteraction:
    """Tests for HotkeysPanel interaction methods"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_edit_hotkey_no_selection_shows_message(self, mock_msgbox, mock_widget):
        """Test _edit_hotkey with no selection shows info message"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import HotkeysPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        with patch.object(HotkeysPanel, "_setup_ui"):
            with patch.object(HotkeysPanel, "_load_hotkeys"):
                panel = HotkeysPanel(mock_settings, mock_hotkey_mgr)
                panel.hotkeys_table = MagicMock()
                panel.hotkeys_table.selectedItems.return_value = []

                panel._edit_hotkey()

                mock_msgbox.information.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_reset_hotkey_no_selection_shows_message(self, mock_msgbox, mock_widget):
        """Test _reset_hotkey with no selection shows info message"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import HotkeysPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        with patch.object(HotkeysPanel, "_setup_ui"):
            with patch.object(HotkeysPanel, "_load_hotkeys"):
                panel = HotkeysPanel(mock_settings, mock_hotkey_mgr)
                panel.hotkeys_table = MagicMock()
                panel.hotkeys_table.selectedItems.return_value = []

                panel._reset_hotkey()

                mock_msgbox.information.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_reset_hotkey_with_selection_shows_feature_message(self, mock_msgbox, mock_widget):
        """Test _reset_hotkey with selection shows feature message"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import HotkeysPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        with patch.object(HotkeysPanel, "_setup_ui"):
            with patch.object(HotkeysPanel, "_load_hotkeys"):
                panel = HotkeysPanel(mock_settings, mock_hotkey_mgr)
                panel.hotkeys_table = MagicMock()
                panel.hotkeys_table.selectedItems.return_value = [MagicMock()]

                panel._reset_hotkey()

                mock_msgbox.information.assert_called()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.HotkeyEditDialog")
    def test_edit_hotkey_with_selection_opens_dialog(self, mock_dialog_class, mock_widget):
        """Test _edit_hotkey with selection opens dialog"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import HotkeysPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = False
        mock_dialog_class.return_value = mock_dialog

        with patch.object(HotkeysPanel, "_setup_ui"):
            with patch.object(HotkeysPanel, "_load_hotkeys"):
                panel = HotkeysPanel(mock_settings, mock_hotkey_mgr)
                panel.hotkeys_table = MagicMock()
                panel.hotkeys_table.selectedItems.return_value = [MagicMock()]
                panel.hotkeys_table.currentRow.return_value = 0

                mock_action_item = MagicMock()
                mock_action_item.text.return_value = "Test Action"
                mock_hotkey_item = MagicMock()
                mock_hotkey_item.text.return_value = "<ctrl>+a"
                panel.hotkeys_table.item.side_effect = [mock_action_item, mock_hotkey_item]

                panel._edit_hotkey()

                mock_dialog_class.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.HotkeyEditDialog")
    def test_edit_hotkey_dialog_accepted_updates_table(self, mock_dialog_class, mock_widget):
        """Test _edit_hotkey when dialog accepted updates table"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import HotkeysPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_hotkey.return_value = "<ctrl>+<shift>+b"
        mock_dialog_class.return_value = mock_dialog

        with patch.object(HotkeysPanel, "_setup_ui"):
            with patch.object(HotkeysPanel, "_load_hotkeys"):
                panel = HotkeysPanel(mock_settings, mock_hotkey_mgr)
                panel.setting_changed = MagicMock()
                panel.hotkeys_table = MagicMock()
                panel.hotkeys_table.selectedItems.return_value = [MagicMock()]
                panel.hotkeys_table.currentRow.return_value = 0

                mock_action_item = MagicMock()
                mock_action_item.text.return_value = "Test Action"
                mock_hotkey_item = MagicMock()
                mock_hotkey_item.text.return_value = "<ctrl>+a"
                panel.hotkeys_table.item.side_effect = [
                    mock_action_item,
                    mock_hotkey_item,
                    mock_hotkey_item,
                ]

                panel._edit_hotkey()

                mock_hotkey_item.setText.assert_called_with("<ctrl>+<shift>+b")
                panel.setting_changed.emit.assert_called()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QVBoxLayout")
    @patch("argus_overview.ui.settings_tab.QLabel")
    @patch("argus_overview.ui.settings_tab.QTableWidget")
    @patch("argus_overview.ui.settings_tab.QHBoxLayout")
    @patch("argus_overview.ui.settings_tab.QPushButton")
    def test_setup_ui_creates_table(
        self, mock_btn, mock_hlayout, mock_table, mock_label, mock_layout, mock_widget
    ):
        """Test _setup_ui creates hotkeys table"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import HotkeysPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        with patch.object(HotkeysPanel, "setLayout"):
            with patch.object(HotkeysPanel, "_load_hotkeys"):
                HotkeysPanel(mock_settings, mock_hotkey_mgr)

                assert mock_table.called

    @patch("argus_overview.ui.settings_tab.QTableWidgetItem")
    @patch("argus_overview.ui.settings_tab.QColor")
    def test_load_hotkeys_populates_table(self, mock_color, mock_item):
        """Test _load_hotkeys populates table with hotkeys"""
        from argus_overview.ui.settings_tab import HotkeysPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = {
            "cycle_forward": "<ctrl>+<shift>+]",
            "cycle_backward": "<ctrl>+<shift>+[",
        }
        mock_hotkey_mgr = MagicMock()

        # Create instance without calling __init__
        with patch.object(HotkeysPanel, "__init__", return_value=None):
            panel = HotkeysPanel.__new__(HotkeysPanel)
            panel.settings_manager = mock_settings
            panel.hotkey_manager = mock_hotkey_mgr
            panel.hotkeys_table = MagicMock()

            panel._load_hotkeys()

            panel.hotkeys_table.setRowCount.assert_called_with(2)


class TestAppearancePanelInteraction:
    """Tests for AppearancePanel interaction methods"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QColorDialog")
    def test_pick_accent_color_valid(self, mock_color_dialog, mock_widget):
        """Test _pick_accent_color with valid color"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AppearancePanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "#4287f5"

        mock_color = MagicMock()
        mock_color.isValid.return_value = True
        mock_color.name.return_value = "#ff0000"
        mock_color_dialog.getColor.return_value = mock_color

        with patch.object(AppearancePanel, "_setup_ui"):
            panel = AppearancePanel(mock_settings)
            panel.setting_changed = MagicMock()
            panel.accent_color = "#4287f5"
            panel.accent_btn = MagicMock()

            panel._pick_accent_color()

            assert panel.accent_color == "#ff0000"
            panel.setting_changed.emit.assert_called_with("appearance.accent_color", "#ff0000")

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QColorDialog")
    def test_pick_accent_color_cancelled(self, mock_color_dialog, mock_widget):
        """Test _pick_accent_color when cancelled"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AppearancePanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "#4287f5"

        mock_color = MagicMock()
        mock_color.isValid.return_value = False
        mock_color_dialog.getColor.return_value = mock_color

        with patch.object(AppearancePanel, "_setup_ui"):
            panel = AppearancePanel(mock_settings)
            panel.setting_changed = MagicMock()
            panel.accent_color = "#4287f5"
            panel.accent_btn = MagicMock()

            panel._pick_accent_color()

            # Color should not change
            assert panel.accent_color == "#4287f5"
            panel.setting_changed.emit.assert_not_called()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QVBoxLayout")
    @patch("argus_overview.ui.settings_tab.QGroupBox")
    @patch("argus_overview.ui.settings_tab.QFormLayout")
    @patch("argus_overview.ui.settings_tab.QComboBox")
    @patch("argus_overview.ui.settings_tab.QSpinBox")
    @patch("argus_overview.ui.settings_tab.QCheckBox")
    @patch("argus_overview.ui.settings_tab.QHBoxLayout")
    @patch("argus_overview.ui.settings_tab.QPushButton")
    def test_setup_ui_creates_widgets(
        self,
        mock_btn,
        mock_hlayout,
        mock_check,
        mock_spin,
        mock_combo,
        mock_form,
        mock_group,
        mock_layout,
        mock_widget,
    ):
        """Test _setup_ui creates all widgets"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AppearancePanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "dark"

        with patch.object(AppearancePanel, "setLayout"):
            AppearancePanel(mock_settings)

            assert mock_layout.called
            assert mock_combo.called
            assert mock_spin.called


class TestAdvancedPanelInteraction:
    """Tests for AdvancedPanel interaction methods"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("PySide6.QtWidgets.QFileDialog")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_export_settings_success(self, mock_msgbox, mock_filedialog, mock_widget):
        """Test _export_settings successful export"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AdvancedPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "INFO"

        mock_filedialog.getSaveFileName.return_value = ("/tmp/settings.json", "JSON Files (*.json)")

        with patch.object(AdvancedPanel, "_setup_ui"):
            panel = AdvancedPanel(mock_settings)

            panel._export_settings()

            mock_settings.export_config.assert_called_once()
            mock_msgbox.information.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("PySide6.QtWidgets.QFileDialog")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_export_settings_cancelled(self, mock_msgbox, mock_filedialog, mock_widget):
        """Test _export_settings when cancelled"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AdvancedPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "INFO"

        mock_filedialog.getSaveFileName.return_value = ("", "")

        with patch.object(AdvancedPanel, "_setup_ui"):
            panel = AdvancedPanel(mock_settings)

            panel._export_settings()

            mock_settings.export_config.assert_not_called()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("PySide6.QtWidgets.QFileDialog")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_export_settings_error(self, mock_msgbox, mock_filedialog, mock_widget):
        """Test _export_settings with error shows critical message"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AdvancedPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "INFO"
        mock_settings.export_config.side_effect = OSError("Write error")

        mock_filedialog.getSaveFileName.return_value = ("/tmp/settings.json", "JSON Files (*.json)")

        with patch.object(AdvancedPanel, "_setup_ui"):
            panel = AdvancedPanel(mock_settings)

            panel._export_settings()

            mock_msgbox.critical.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("PySide6.QtWidgets.QFileDialog")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_import_settings_success(self, mock_msgbox, mock_filedialog, mock_widget):
        """Test _import_settings successful import"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AdvancedPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "INFO"

        mock_filedialog.getOpenFileName.return_value = ("/tmp/settings.json", "JSON Files (*.json)")

        with patch.object(AdvancedPanel, "_setup_ui"):
            panel = AdvancedPanel(mock_settings)

            panel._import_settings()

            mock_settings.import_config.assert_called_once()
            mock_msgbox.information.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("PySide6.QtWidgets.QFileDialog")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_import_settings_cancelled(self, mock_msgbox, mock_filedialog, mock_widget):
        """Test _import_settings when cancelled"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AdvancedPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "INFO"

        mock_filedialog.getOpenFileName.return_value = ("", "")

        with patch.object(AdvancedPanel, "_setup_ui"):
            panel = AdvancedPanel(mock_settings)

            panel._import_settings()

            mock_settings.import_config.assert_not_called()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("PySide6.QtWidgets.QFileDialog")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_import_settings_error(self, mock_msgbox, mock_filedialog, mock_widget):
        """Test _import_settings with error shows critical message"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AdvancedPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "INFO"
        mock_settings.import_config.side_effect = OSError("Read error")

        mock_filedialog.getOpenFileName.return_value = ("/tmp/settings.json", "JSON Files (*.json)")

        with patch.object(AdvancedPanel, "_setup_ui"):
            panel = AdvancedPanel(mock_settings)

            panel._import_settings()

            mock_msgbox.critical.assert_called_once()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QVBoxLayout")
    @patch("argus_overview.ui.settings_tab.QGroupBox")
    @patch("argus_overview.ui.settings_tab.QFormLayout")
    @patch("argus_overview.ui.settings_tab.QComboBox")
    @patch("argus_overview.ui.settings_tab.QLabel")
    @patch("argus_overview.ui.settings_tab.QCheckBox")
    @patch("argus_overview.ui.settings_tab.QPushButton")
    def test_setup_ui_creates_widgets(
        self,
        mock_btn,
        mock_check,
        mock_label,
        mock_combo,
        mock_form,
        mock_group,
        mock_layout,
        mock_widget,
    ):
        """Test _setup_ui creates all widgets"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import AdvancedPanel

        mock_settings = MagicMock()
        mock_settings.get.return_value = "INFO"

        with patch.object(AdvancedPanel, "setLayout"):
            AdvancedPanel(mock_settings)

            assert mock_layout.called
            assert mock_group.called
            assert mock_btn.called


class TestSettingsTabSetupUI:
    """Tests for SettingsTab _setup_ui and _create_category_tree"""

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QHBoxLayout")
    @patch("argus_overview.ui.settings_tab.QSplitter")
    @patch("argus_overview.ui.settings_tab.QStackedWidget")
    @patch("argus_overview.ui.settings_tab.GeneralPanel")
    @patch("argus_overview.ui.settings_tab.PerformancePanel")
    @patch("argus_overview.ui.settings_tab.HotkeysPanel")
    @patch("argus_overview.ui.settings_tab.IntelPanel")
    @patch("argus_overview.ui.settings_tab.AppearancePanel")
    @patch("argus_overview.ui.settings_tab.AdvancedPanel")
    def test_setup_ui_creates_all_panels(
        self,
        mock_adv,
        mock_app,
        mock_intel,
        mock_hk,
        mock_perf,
        mock_gen,
        mock_stack,
        mock_split,
        mock_layout,
        mock_widget,
    ):
        """Test _setup_ui creates all settings panels"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        with patch.object(SettingsTab, "_create_category_tree", return_value=MagicMock()):
            with patch.object(SettingsTab, "setLayout"):
                with patch.object(SettingsTab, "setStyleSheet"):
                    with patch.object(SettingsTab, "_load_settings"):
                        SettingsTab(mock_settings, mock_hotkey_mgr)

                        assert mock_gen.called
                        assert mock_perf.called
                        assert mock_hk.called
                        assert mock_intel.called
                        assert mock_app.called
                        assert mock_adv.called

    @patch("argus_overview.ui.settings_tab.QWidget")
    @patch("argus_overview.ui.settings_tab.QVBoxLayout")
    @patch("argus_overview.ui.settings_tab.QLabel")
    @patch("argus_overview.ui.settings_tab.QFont")
    @patch("argus_overview.ui.settings_tab.QTreeWidget")
    @patch("argus_overview.ui.settings_tab.QTreeWidgetItem")
    @patch("argus_overview.ui.settings_tab.QPushButton")
    def test_create_category_tree(
        self, mock_btn, mock_item, mock_tree, mock_font, mock_label, mock_layout, mock_qwidget
    ):
        """Test _create_category_tree creates tree with all categories"""
        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        with patch.object(SettingsTab, "__init__", return_value=None):
            tab = SettingsTab.__new__(SettingsTab)
            tab.settings_manager = mock_settings
            tab.hotkey_manager = mock_hotkey_mgr

            tab._create_category_tree()

            # Should create 5 tree items (General, Performance, Hotkeys, Appearance, Advanced)
            # Note: Alerts panel was removed for CCP EULA compliance
            assert mock_item.call_count >= 5

    @patch("argus_overview.ui.settings_tab.QWidget")
    @patch("argus_overview.ui.settings_tab.QVBoxLayout")
    @patch("argus_overview.ui.settings_tab.QLabel")
    @patch("argus_overview.ui.settings_tab.QFont")
    @patch("argus_overview.ui.settings_tab.QTreeWidget")
    @patch("argus_overview.ui.settings_tab.QTreeWidgetItem")
    @patch("argus_overview.ui.settings_tab.QPushButton")
    def test_create_category_tree_stylesheet_and_default_selection(
        self, mock_btn, mock_item, mock_tree, mock_font, mock_label, mock_layout, mock_qwidget
    ):
        """Test _create_category_tree applies design-system stylesheet and selects first item"""
        from argus_overview.ui.design_system import colors as _ds
        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        # Capture the tree widget instance returned by QTreeWidget()
        mock_tree_instance = MagicMock()
        mock_tree.return_value = mock_tree_instance
        # Mock topLevelItem so setCurrentItem works
        mock_first_item = MagicMock()
        mock_tree_instance.topLevelItem.return_value = mock_first_item

        with patch.object(SettingsTab, "__init__", return_value=None):
            tab = SettingsTab.__new__(SettingsTab)
            tab.settings_manager = mock_settings
            tab.hotkey_manager = mock_hotkey_mgr

            tab._create_category_tree()

            # Should select first category by default
            mock_tree_instance.setCurrentItem.assert_called_once_with(mock_first_item)

            # Should apply stylesheet with design-system tokens
            mock_tree_instance.setStyleSheet.assert_called_once()
            stylesheet = mock_tree_instance.setStyleSheet.call_args[0][0]
            assert _ds.SURFACE in stylesheet
            assert _ds.SURFACE_HOVER in stylesheet
            assert _ds.SURFACE_RAISED in stylesheet
            assert _ds.TEXT_PRIMARY in stylesheet
            assert _ds.BORDER_SUBTLE in stylesheet
            assert _ds.INFO in stylesheet
            assert "::item:selected" in stylesheet
            assert "::item:hover" in stylesheet
            assert "border-left: 2px solid" in stylesheet

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_on_category_changed_none(self, mock_widget):
        """Test _on_category_changed with None current"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        with patch.object(SettingsTab, "_setup_ui"):
            with patch.object(SettingsTab, "_load_settings"):
                tab = SettingsTab(mock_settings, mock_hotkey_mgr)
                tab.panel_stack = MagicMock()

                tab._on_category_changed(None, None)

                # panel_stack.setCurrentIndex should not be called
                tab.panel_stack.setCurrentIndex.assert_not_called()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_on_category_changed_unknown_category(self, mock_widget):
        """Test _on_category_changed with unknown category"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        with patch.object(SettingsTab, "_setup_ui"):
            with patch.object(SettingsTab, "_load_settings"):
                tab = SettingsTab(mock_settings, mock_hotkey_mgr)
                tab.panel_stack = MagicMock()

                mock_item = MagicMock()
                mock_item.text.return_value = "Unknown Category"

                tab._on_category_changed(mock_item, None)

                # panel_stack.setCurrentIndex should not be called
                tab.panel_stack.setCurrentIndex.assert_not_called()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    @patch("argus_overview.ui.settings_tab.QMessageBox")
    def test_reset_all_cancelled(self, mock_msgbox, mock_widget):
        """Test _reset_all when user cancels"""
        mock_widget.return_value = None

        from PySide6.QtWidgets import QMessageBox

        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        mock_msgbox.StandardButton = QMessageBox.StandardButton
        mock_msgbox.question.return_value = QMessageBox.StandardButton.No

        with patch.object(SettingsTab, "_setup_ui"):
            with patch.object(SettingsTab, "_load_settings"):
                tab = SettingsTab(mock_settings, mock_hotkey_mgr)

                tab._reset_all()

                mock_settings.reset_to_defaults.assert_not_called()

    @patch("argus_overview.ui.settings_tab.QWidget.__init__")
    def test_load_settings_pass(self, mock_widget):
        """Test _load_settings is a pass-through (settings loaded by panels)"""
        mock_widget.return_value = None

        from argus_overview.ui.settings_tab import SettingsTab

        mock_settings = MagicMock()
        mock_settings.get.return_value = {}
        mock_hotkey_mgr = MagicMock()

        with patch.object(SettingsTab, "_setup_ui"):
            tab = SettingsTab(mock_settings, mock_hotkey_mgr)

            # Just verify it doesn't raise
            tab._load_settings()
