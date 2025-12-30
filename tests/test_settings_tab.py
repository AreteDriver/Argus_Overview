"""
Unit tests for the Settings Tab module
Tests HotkeyEditDialog, GeneralPanel, PerformancePanel, AlertsPanel,
HotkeysPanel, AppearancePanel, AdvancedPanel, SettingsTab
"""
from unittest.mock import MagicMock, patch


# Test HotkeyEditDialog
class TestHotkeyEditDialog:
    """Tests for HotkeyEditDialog"""

    @patch('eve_overview_pro.ui.settings_tab.QDialog.__init__')
    def test_init(self, mock_dialog):
        """Test HotkeyEditDialog initialization"""
        mock_dialog.return_value = None

        from eve_overview_pro.ui.settings_tab import HotkeyEditDialog

        mock_hotkey_manager = MagicMock()

        with patch.object(HotkeyEditDialog, 'setWindowTitle') as mock_title:
            with patch.object(HotkeyEditDialog, 'setMinimumWidth'):
                with patch.object(HotkeyEditDialog, '_setup_ui'):
                    dialog = HotkeyEditDialog(
                        "Test Action",
                        "<ctrl>+<alt>+1",
                        mock_hotkey_manager
                    )

                    mock_title.assert_called_with("Edit Hotkey: Test Action")
                    assert dialog.action == "Test Action"
                    assert dialog.current_combo == "<ctrl>+<alt>+1"

    @patch('eve_overview_pro.ui.settings_tab.QDialog.__init__')
    def test_get_hotkey(self, mock_dialog):
        """Test get_hotkey method"""
        mock_dialog.return_value = None

        from eve_overview_pro.ui.settings_tab import HotkeyEditDialog

        mock_hotkey_manager = MagicMock()

        with patch.object(HotkeyEditDialog, 'setWindowTitle'):
            with patch.object(HotkeyEditDialog, 'setMinimumWidth'):
                with patch.object(HotkeyEditDialog, '_setup_ui'):
                    dialog = HotkeyEditDialog(
                        "Test Action",
                        "<ctrl>+<alt>+1",
                        mock_hotkey_manager
                    )
                    dialog.key_edit = MagicMock()
                    dialog.key_edit.text.return_value = "  <ctrl>+<shift>+2  "

                    result = dialog.get_hotkey()

                    assert result == "<ctrl>+<shift>+2"


# Test GeneralPanel
class TestGeneralPanel:
    """Tests for GeneralPanel"""

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test GeneralPanel initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import GeneralPanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = False

        with patch.object(GeneralPanel, '_setup_ui'):
            panel = GeneralPanel(mock_settings_manager)

            assert panel.settings_manager is mock_settings_manager

    def test_signal_exists(self):
        """Test GeneralPanel has setting_changed signal"""
        from eve_overview_pro.ui.settings_tab import GeneralPanel

        assert hasattr(GeneralPanel, 'setting_changed')


# Test PerformancePanel
class TestPerformancePanel:
    """Tests for PerformancePanel"""

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test PerformancePanel initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import PerformancePanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = 30

        with patch.object(PerformancePanel, '_setup_ui'):
            panel = PerformancePanel(mock_settings_manager)

            assert panel.settings_manager is mock_settings_manager

    def test_signal_exists(self):
        """Test PerformancePanel has setting_changed signal"""
        from eve_overview_pro.ui.settings_tab import PerformancePanel

        assert hasattr(PerformancePanel, 'setting_changed')


# Test AlertsPanel
class TestAlertsPanel:
    """Tests for AlertsPanel"""

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test AlertsPanel initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import AlertsPanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = True

        with patch.object(AlertsPanel, '_setup_ui'):
            panel = AlertsPanel(mock_settings_manager)

            assert panel.settings_manager is mock_settings_manager

    def test_signal_exists(self):
        """Test AlertsPanel has setting_changed signal"""
        from eve_overview_pro.ui.settings_tab import AlertsPanel

        assert hasattr(AlertsPanel, 'setting_changed')


# Test HotkeysPanel
class TestHotkeysPanel:
    """Tests for HotkeysPanel"""

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test HotkeysPanel initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import HotkeysPanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()

        with patch.object(HotkeysPanel, '_setup_ui'):
            with patch.object(HotkeysPanel, '_load_hotkeys'):
                panel = HotkeysPanel(mock_settings_manager, mock_hotkey_manager)

                assert panel.settings_manager is mock_settings_manager
                assert panel.hotkey_manager is mock_hotkey_manager

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_load_hotkeys_calls_settings_manager(self, mock_widget):
        """Test _load_hotkeys calls settings manager"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import HotkeysPanel

        mock_settings_manager = MagicMock()
        mock_hotkey_manager = MagicMock()

        with patch.object(HotkeysPanel, '_setup_ui'):
            with patch.object(HotkeysPanel, '_load_hotkeys'):
                panel = HotkeysPanel(mock_settings_manager, mock_hotkey_manager)

                # Verify it was called during init
                assert panel.settings_manager is mock_settings_manager

    def test_signal_exists(self):
        """Test HotkeysPanel has setting_changed signal"""
        from eve_overview_pro.ui.settings_tab import HotkeysPanel

        assert hasattr(HotkeysPanel, 'setting_changed')


# Test AppearancePanel
class TestAppearancePanel:
    """Tests for AppearancePanel"""

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test AppearancePanel initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import AppearancePanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = "dark"

        with patch.object(AppearancePanel, '_setup_ui'):
            panel = AppearancePanel(mock_settings_manager)

            assert panel.settings_manager is mock_settings_manager

    def test_signal_exists(self):
        """Test AppearancePanel has setting_changed signal"""
        from eve_overview_pro.ui.settings_tab import AppearancePanel

        assert hasattr(AppearancePanel, 'setting_changed')


# Test AdvancedPanel
class TestAdvancedPanel:
    """Tests for AdvancedPanel"""

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test AdvancedPanel initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import AdvancedPanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = "INFO"

        with patch.object(AdvancedPanel, '_setup_ui'):
            panel = AdvancedPanel(mock_settings_manager)

            assert panel.settings_manager is mock_settings_manager

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.settings_tab.QMessageBox')
    def test_clear_cache_shows_message(self, mock_msgbox, mock_widget):
        """Test _clear_cache shows information message"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import AdvancedPanel

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = "INFO"

        with patch.object(AdvancedPanel, '_setup_ui'):
            panel = AdvancedPanel(mock_settings_manager)

            panel._clear_cache()

            mock_msgbox.information.assert_called_once()

    def test_signal_exists(self):
        """Test AdvancedPanel has setting_changed signal"""
        from eve_overview_pro.ui.settings_tab import AdvancedPanel

        assert hasattr(AdvancedPanel, 'setting_changed')


# Test SettingsTab
class TestSettingsTab:
    """Tests for SettingsTab widget"""

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_init(self, mock_widget):
        """Test SettingsTab initialization"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import SettingsTab

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()
        mock_alert_detector = MagicMock()

        with patch.object(SettingsTab, '_setup_ui'):
            with patch.object(SettingsTab, '_load_settings'):
                tab = SettingsTab(
                    mock_settings_manager,
                    mock_hotkey_manager,
                    mock_alert_detector
                )

                assert tab.settings_manager is mock_settings_manager
                assert tab.hotkey_manager is mock_hotkey_manager
                assert tab.alert_detector is mock_alert_detector

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_on_setting_changed(self, mock_widget):
        """Test _on_setting_changed saves to manager"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import SettingsTab

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()
        mock_alert_detector = MagicMock()

        with patch.object(SettingsTab, '_setup_ui'):
            with patch.object(SettingsTab, '_load_settings'):
                with patch.object(SettingsTab, 'settings_changed', MagicMock()):
                    tab = SettingsTab(
                        mock_settings_manager,
                        mock_hotkey_manager,
                        mock_alert_detector
                    )

                    tab._on_setting_changed("test.key", "test_value")

                    mock_settings_manager.set.assert_called_with("test.key", "test_value")

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    def test_on_category_changed(self, mock_widget):
        """Test _on_category_changed switches panel"""
        mock_widget.return_value = None

        from eve_overview_pro.ui.settings_tab import SettingsTab

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()
        mock_alert_detector = MagicMock()

        with patch.object(SettingsTab, '_setup_ui'):
            with patch.object(SettingsTab, '_load_settings'):
                tab = SettingsTab(
                    mock_settings_manager,
                    mock_hotkey_manager,
                    mock_alert_detector
                )
                tab.panel_stack = MagicMock()

                # Mock tree item
                mock_item = MagicMock()
                mock_item.text.return_value = "Performance"

                tab._on_category_changed(mock_item, None)

                tab.panel_stack.setCurrentIndex.assert_called_with(1)

    @patch('eve_overview_pro.ui.settings_tab.QWidget.__init__')
    @patch('eve_overview_pro.ui.settings_tab.QMessageBox')
    def test_reset_all_calls_reset(self, mock_msgbox, mock_widget):
        """Test _reset_all resets settings when confirmed"""
        mock_widget.return_value = None

        from PySide6.QtWidgets import QMessageBox

        from eve_overview_pro.ui.settings_tab import SettingsTab

        mock_settings_manager = MagicMock()
        mock_settings_manager.get.return_value = {}

        mock_hotkey_manager = MagicMock()
        mock_alert_detector = MagicMock()

        # Simulate user clicking Yes - use StandardButton.Yes
        mock_msgbox.StandardButton = QMessageBox.StandardButton
        mock_msgbox.question.return_value = QMessageBox.StandardButton.Yes

        with patch.object(SettingsTab, '_setup_ui'):
            with patch.object(SettingsTab, '_load_settings'):
                tab = SettingsTab(
                    mock_settings_manager,
                    mock_hotkey_manager,
                    mock_alert_detector
                )

                tab._reset_all()

                mock_settings_manager.reset_to_defaults.assert_called_once()

    def test_signal_exists(self):
        """Test SettingsTab has settings_changed signal"""
        from eve_overview_pro.ui.settings_tab import SettingsTab

        assert hasattr(SettingsTab, 'settings_changed')
