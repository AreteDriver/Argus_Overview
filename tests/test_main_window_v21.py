"""
Unit tests for the Main Window v2.1 module
Tests MainWindowV21 - the main application window
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock


# Test MainWindowV21 initialization
class TestMainWindowV21Init:
    """Tests for MainWindowV21 initialization"""

    def test_class_exists(self):
        """Test that MainWindowV21 class exists and can be imported"""
        from eve_overview_pro.ui.main_window_v21 import MainWindowV21

        assert MainWindowV21 is not None

    def test_class_inherits_from_qmainwindow(self):
        """Test that MainWindowV21 inherits from QMainWindow"""
        from eve_overview_pro.ui.main_window_v21 import MainWindowV21
        from PySide6.QtWidgets import QMainWindow

        assert issubclass(MainWindowV21, QMainWindow)


# Helper to create a mock window without Qt initialization
def create_mock_window():
    """Create a mock MainWindowV21 without Qt initialization"""
    from eve_overview_pro.ui.main_window_v21 import MainWindowV21

    # Create a MagicMock that uses the real methods from MainWindowV21
    window = MagicMock(spec=MainWindowV21)
    window.logger = MagicMock()

    # Bind the real methods to our mock
    window._toggle_visibility = lambda: MainWindowV21._toggle_visibility(window)
    window._toggle_thumbnails = lambda: MainWindowV21._toggle_thumbnails(window)
    window._get_cycling_group_members = lambda: MainWindowV21._get_cycling_group_members(window)
    window._get_window_id_for_character = lambda char: MainWindowV21._get_window_id_for_character(window, char)
    window._cycle_next = lambda: MainWindowV21._cycle_next(window)
    window._cycle_prev = lambda: MainWindowV21._cycle_prev(window)
    window._activate_window = lambda wid: MainWindowV21._activate_window(window, wid)
    window._minimize_all_windows = lambda: MainWindowV21._minimize_all_windows(window)
    window._restore_all_windows = lambda: MainWindowV21._restore_all_windows(window)
    window._activate_character = lambda char: MainWindowV21._activate_character(window, char)
    window._on_profile_selected = lambda name: MainWindowV21._on_profile_selected(window, name)
    window._show_settings = lambda: MainWindowV21._show_settings(window)
    window._reload_config = lambda: MainWindowV21._reload_config(window)
    window._quit_application = lambda: MainWindowV21._quit_application(window)
    window._apply_setting = lambda k, v: MainWindowV21._apply_setting(window, k, v)
    window._on_character_detected = lambda wid, char: MainWindowV21._on_character_detected(window, wid, char)
    window._on_team_selected = lambda team: MainWindowV21._on_team_selected(window, team)
    window._on_layout_applied = lambda name: MainWindowV21._on_layout_applied(window, name)
    window.closeEvent = lambda e: MainWindowV21.closeEvent(window, e)
    window._show_about_dialog = lambda: MainWindowV21._show_about_dialog(window)
    window._open_url = lambda url: MainWindowV21._open_url(window, url)
    window._open_donation_link = lambda: MainWindowV21._open_donation_link(window)
    window._on_new_character_discovered = lambda c, wid, t: MainWindowV21._on_new_character_discovered(window, c, wid, t)

    return window


# Test visibility toggle
class TestToggleVisibility:
    """Tests for _toggle_visibility method"""

    def test_toggle_visibility_hides_when_visible(self):
        """Test that toggle hides window when visible"""
        window = create_mock_window()

        # Mock methods
        window.isVisible = MagicMock(return_value=True)
        window.hide = MagicMock()
        window.show = MagicMock()

        window._toggle_visibility()

        window.hide.assert_called_once()
        window.show.assert_not_called()

    def test_toggle_visibility_shows_when_hidden(self):
        """Test that toggle shows window when hidden"""
        window = create_mock_window()

        # Mock methods
        window.isVisible = MagicMock(return_value=False)
        window.hide = MagicMock()
        window.show = MagicMock()
        window.raise_ = MagicMock()
        window.activateWindow = MagicMock()

        window._toggle_visibility()

        window.show.assert_called_once()
        window.raise_.assert_called_once()
        window.activateWindow.assert_called_once()


# Test toggle thumbnails
class TestToggleThumbnails:
    """Tests for _toggle_thumbnails method"""

    def test_toggle_thumbnails_calls_main_tab(self):
        """Test that toggle calls main_tab method"""
        window = create_mock_window()
        window.main_tab = MagicMock()

        window._toggle_thumbnails()

        window.main_tab.toggle_thumbnails_visibility.assert_called_once()

    def test_toggle_thumbnails_handles_no_main_tab(self):
        """Test that toggle handles missing main_tab gracefully"""
        window = create_mock_window()
        # No main_tab attribute

        # Should not raise
        window._toggle_thumbnails()


# Test cycling group members
class TestCyclingGroupMembers:
    """Tests for _get_cycling_group_members method"""

    def test_get_cycling_group_members_returns_current_group(self):
        """Test getting members from current cycling group"""
        window = create_mock_window()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {
            "Default": ["Char1", "Char2"],
            "PvP": ["Char3", "Char4"]
        }
        window.current_cycling_group = "PvP"

        result = window._get_cycling_group_members()

        assert result == ["Char3", "Char4"]

    def test_get_cycling_group_members_fallback_to_default(self):
        """Test fallback to Default group"""
        window = create_mock_window()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {
            "Default": ["Char1", "Char2"]
        }
        window.current_cycling_group = "NonExistent"

        result = window._get_cycling_group_members()

        assert result == ["Char1", "Char2"]


# Test window ID lookup
class TestGetWindowIdForCharacter:
    """Tests for _get_window_id_for_character method"""

    def test_get_window_id_found(self):
        """Test finding window ID for character"""
        window = create_mock_window()

        # Mock main_tab with window_manager
        mock_frame = MagicMock()
        mock_frame.character_name = "TestPilot"

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x12345": mock_frame
        }

        result = window._get_window_id_for_character("TestPilot")

        assert result == "0x12345"

    def test_get_window_id_not_found(self):
        """Test window ID not found returns None"""
        window = create_mock_window()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}

        result = window._get_window_id_for_character("Unknown")

        assert result is None


# Test cycle next/prev
class TestCycling:
    """Tests for _cycle_next and _cycle_prev methods"""

    def test_cycle_next_advances_index(self):
        """Test cycle_next advances cycling index"""
        window = create_mock_window()
        window.cycling_index = 0
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {
            "Default": ["Char1", "Char2", "Char3"]
        }
        window.current_cycling_group = "Default"

        # Mock finding window
        mock_frame = MagicMock()
        mock_frame.character_name = "Char2"
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x12345": mock_frame
        }

        window._activate_window = MagicMock()

        window._cycle_next()

        assert window.cycling_index == 1

    def test_cycle_next_wraps_around(self):
        """Test cycle_next wraps to beginning"""
        window = create_mock_window()
        window.cycling_index = 2  # Last position
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {
            "Default": ["Char1", "Char2", "Char3"]
        }
        window.current_cycling_group = "Default"

        # Mock finding window
        mock_frame = MagicMock()
        mock_frame.character_name = "Char1"
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x12345": mock_frame
        }

        window._activate_window = MagicMock()

        window._cycle_next()

        assert window.cycling_index == 0  # Wrapped to beginning

    def test_cycle_prev_decrements_index(self):
        """Test cycle_prev decrements cycling index"""
        window = create_mock_window()
        window.cycling_index = 2
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {
            "Default": ["Char1", "Char2", "Char3"]
        }
        window.current_cycling_group = "Default"

        # Mock finding window
        mock_frame = MagicMock()
        mock_frame.character_name = "Char2"
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x12345": mock_frame
        }

        window._activate_window = MagicMock()

        window._cycle_prev()

        assert window.cycling_index == 1


# Test activate window
class TestActivateWindow:
    """Tests for _activate_window method"""

    @patch('subprocess.run')
    def test_activate_window_calls_xdotool(self, mock_subprocess):
        """Test that activate_window calls xdotool"""
        window = create_mock_window()

        window._activate_window("0x12345")

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'xdotool' in call_args
        assert 'windowactivate' in call_args
        assert '0x12345' in call_args

    @patch('subprocess.run')
    def test_activate_window_handles_exception(self, mock_subprocess):
        """Test that activate_window handles exceptions"""
        mock_subprocess.side_effect = Exception("xdotool failed")

        window = create_mock_window()

        # Should not raise
        window._activate_window("0x12345")

        window.logger.error.assert_called()


# Test minimize/restore all windows
class TestMinimizeRestoreWindows:
    """Tests for _minimize_all_windows and _restore_all_windows"""

    def test_minimize_all_windows(self):
        """Test minimizing all EVE windows"""
        window = create_mock_window()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x111": MagicMock(),
            "0x222": MagicMock()
        }

        window.capture_system = MagicMock()
        window.capture_system.minimize_window.return_value = True

        window.system_tray = MagicMock()

        window._minimize_all_windows()

        assert window.capture_system.minimize_window.call_count == 2
        window.system_tray.show_notification.assert_called()

    def test_restore_all_windows(self):
        """Test restoring all EVE windows"""
        window = create_mock_window()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x111": MagicMock(),
            "0x222": MagicMock()
        }

        window.capture_system = MagicMock()
        window.capture_system.restore_window.return_value = True

        window.system_tray = MagicMock()

        window._restore_all_windows()

        assert window.capture_system.restore_window.call_count == 2
        window.system_tray.show_notification.assert_called()


# Test activate character
class TestActivateCharacter:
    """Tests for _activate_character method"""

    def test_activate_character_found(self):
        """Test activating a found character"""
        window = create_mock_window()

        mock_frame = MagicMock()
        mock_frame.character_name = "TestPilot"

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x12345": mock_frame
        }

        window.capture_system = MagicMock()

        window._activate_character("TestPilot")

        window.capture_system.activate_window.assert_called_with("0x12345")

    def test_activate_character_not_found(self):
        """Test activating a character not found"""
        window = create_mock_window()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}

        window._activate_character("Unknown")

        window.logger.warning.assert_called()


# Test profile selection
class TestProfileSelection:
    """Tests for _on_profile_selected method"""

    def test_on_profile_selected_loads_preset(self):
        """Test that profile selection loads preset"""
        window = create_mock_window()

        mock_preset = MagicMock()
        window.layout_manager = MagicMock()
        window.layout_manager.get_preset.return_value = mock_preset

        window.system_tray = MagicMock()

        window._on_profile_selected("MyProfile")

        window.layout_manager.get_preset.assert_called_with("MyProfile")
        window.system_tray.set_current_profile.assert_called_with("MyProfile")


# Test show settings
class TestShowSettings:
    """Tests for _show_settings method"""

    def test_show_settings_switches_to_tab(self):
        """Test that show_settings shows window and switches tab"""
        window = create_mock_window()
        window.show = MagicMock()
        window.raise_ = MagicMock()
        window.tabs = MagicMock()

        window._show_settings()

        window.show.assert_called_once()
        window.raise_.assert_called_once()
        window.tabs.setCurrentIndex.assert_called_with(4)


# Test reload config
class TestReloadConfig:
    """Tests for _reload_config method"""

    def test_reload_config_reloads_settings(self):
        """Test that reload_config reloads all settings"""
        window = create_mock_window()

        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = True

        window.theme_manager = MagicMock()

        window.auto_discovery = MagicMock()
        window.auto_discovery.scan_timer = MagicMock()
        window.auto_discovery.scan_timer.isActive.return_value = False

        window.system_tray = MagicMock()

        window._apply_initial_settings = MagicMock()

        window._reload_config()

        window.settings_manager.load_settings.assert_called_once()
        window._apply_initial_settings.assert_called_once()
        window.theme_manager.apply_theme.assert_called_once()
        window.system_tray.show_notification.assert_called()


# Test quit application
class TestQuitApplication:
    """Tests for _quit_application method"""

    @patch('eve_overview_pro.ui.main_window_v21.QApplication')
    def test_quit_application_calls_quit(self, mock_app):
        """Test that quit_application calls QApplication.quit"""
        window = create_mock_window()

        window._quit_application()

        mock_app.quit.assert_called_once()


# Test apply setting
class TestApplySetting:
    """Tests for _apply_setting method"""

    def test_apply_setting_performance(self):
        """Test applying performance setting"""
        window = create_mock_window()

        window._apply_setting("performance.capture_workers", 8)

        window.logger.info.assert_called()
        window.logger.warning.assert_called()

    def test_apply_setting_alerts(self):
        """Test applying alerts setting triggers config update"""
        window = create_mock_window()
        window._apply_initial_settings = MagicMock()

        window._apply_setting("alerts.enabled", True)

        window._apply_initial_settings.assert_called_once()


# Test character detected
class TestOnCharacterDetected:
    """Tests for _on_character_detected slot"""

    def test_on_character_detected_assigns_window(self):
        """Test that character detection assigns window"""
        window = create_mock_window()
        window.character_manager = MagicMock()

        window._on_character_detected("0x12345", "TestPilot")

        window.character_manager.assign_window.assert_called_with("TestPilot", "0x12345")


# Test team selected
class TestOnTeamSelected:
    """Tests for _on_team_selected slot"""

    def test_on_team_selected_loads_layout(self):
        """Test that team selection loads associated layout"""
        window = create_mock_window()

        mock_team = MagicMock()
        mock_team.name = "Fleet1"
        mock_team.layout_name = "FleetLayout"

        window.layouts_tab = MagicMock()

        window._on_team_selected(mock_team)

        window.layouts_tab.load_layout.assert_called_with("FleetLayout")


# Test layout applied
class TestOnLayoutApplied:
    """Tests for _on_layout_applied slot"""

    def test_on_layout_applied_logs(self):
        """Test that layout applied logs message"""
        window = create_mock_window()

        window._on_layout_applied("MyLayout")

        window.logger.info.assert_called()


# Test close event
class TestCloseEvent:
    """Tests for closeEvent handler"""

    def test_close_event_minimizes_to_tray(self):
        """Test that close minimizes to tray when enabled"""
        window = create_mock_window()

        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = True  # minimize_to_tray enabled

        window.system_tray = MagicMock()
        window.system_tray.is_visible.return_value = True

        window.hide = MagicMock()

        mock_event = MagicMock()

        window.closeEvent(mock_event)

        window.hide.assert_called_once()
        mock_event.ignore.assert_called_once()

    def test_close_event_actually_closes(self):
        """Test that close actually closes when tray disabled"""
        window = create_mock_window()

        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = False  # minimize_to_tray disabled

        window.auto_discovery = MagicMock()
        window.capture_system = MagicMock()
        window.hotkey_manager = MagicMock()
        window.system_tray = MagicMock()
        window.character_manager = MagicMock()

        mock_event = MagicMock()

        window.closeEvent(mock_event)

        window.auto_discovery.stop.assert_called_once()
        window.capture_system.stop.assert_called_once()
        window.hotkey_manager.stop.assert_called_once()
        window.settings_manager.save_settings.assert_called_once()
        window.character_manager.save_data.assert_called_once()
        mock_event.accept.assert_called_once()


# Test about dialog
class TestAboutDialog:
    """Tests for _show_about_dialog method"""

    @patch('eve_overview_pro.ui.about_dialog.AboutDialog')
    def test_show_about_dialog_creates_dialog(self, mock_dialog_class):
        """Test that show_about_dialog creates and shows dialog"""
        window = create_mock_window()

        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        window._show_about_dialog()

        mock_dialog_class.assert_called_once_with(window)
        mock_dialog.exec.assert_called_once()


# Test open URL
class TestOpenUrl:
    """Tests for _open_url and _open_donation_link methods"""

    @patch('PySide6.QtGui.QDesktopServices.openUrl')
    def test_open_url(self, mock_open_url):
        """Test opening URL"""
        window = create_mock_window()

        window._open_url("https://example.com")

        mock_open_url.assert_called_once()

    @patch('PySide6.QtGui.QDesktopServices.openUrl')
    def test_open_donation_link(self, mock_open_url):
        """Test opening donation link"""
        window = create_mock_window()

        window._open_donation_link()

        mock_open_url.assert_called_once()


# Test new character discovered
class TestNewCharacterDiscovered:
    """Tests for _on_new_character_discovered slot"""

    def test_on_new_character_discovered_adds_window(self):
        """Test that new character adds window to main tab"""
        window = create_mock_window()

        # Mock main_tab
        mock_frame = MagicMock()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}  # Not already there
        window.main_tab.window_manager.add_window.return_value = mock_frame

        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = True  # show_notifications

        window.system_tray = MagicMock()

        window._on_new_character_discovered("NewPilot", "0x99999", "EVE - NewPilot")

        window.main_tab.window_manager.add_window.assert_called_with("0x99999", "NewPilot")
        window.system_tray.show_notification.assert_called()
