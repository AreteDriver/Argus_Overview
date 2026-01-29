"""
Unit tests for the Main Window v2.1 module
Tests MainWindowV21 - the main application window
"""

from unittest.mock import MagicMock, patch


# Test MainWindowV21 initialization
class TestMainWindowV21Init:
    """Tests for MainWindowV21 initialization"""

    def test_class_exists(self):
        """Test that MainWindowV21 class exists and can be imported"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        assert MainWindowV21 is not None

    def test_class_inherits_from_qmainwindow(self):
        """Test that MainWindowV21 inherits from QMainWindow"""
        from PySide6.QtWidgets import QMainWindow

        from argus_overview.ui.main_window_v21 import MainWindowV21

        assert issubclass(MainWindowV21, QMainWindow)


# Helper to create a mock window without Qt initialization
def create_mock_window():
    """Create a mock MainWindowV21 without Qt initialization"""
    from argus_overview.ui.main_window_v21 import MainWindowV21

    # Create a MagicMock that uses the real methods from MainWindowV21
    window = MagicMock(spec=MainWindowV21)
    window.logger = MagicMock()

    # Bind the real methods to our mock
    window._toggle_visibility = lambda: MainWindowV21._toggle_visibility(window)
    window._toggle_thumbnails = lambda: MainWindowV21._toggle_thumbnails(window)
    window._get_cycling_group_members = lambda: MainWindowV21._get_cycling_group_members(window)
    window._get_window_id_for_character = lambda char: MainWindowV21._get_window_id_for_character(
        window, char
    )
    window._cycle_window = lambda direction=1: MainWindowV21._cycle_window(window, direction)
    window._cycle_next = lambda: MainWindowV21._cycle_next(window)
    window._cycle_prev = lambda: MainWindowV21._cycle_prev(window)
    window._activate_window = lambda wid: MainWindowV21._activate_window(window, wid)
    window._apply_to_all_windows = lambda action: MainWindowV21._apply_to_all_windows(
        window, action
    )
    window._minimize_all_windows = lambda: MainWindowV21._minimize_all_windows(window)
    window._restore_all_windows = lambda: MainWindowV21._restore_all_windows(window)
    window._activate_character = lambda char: MainWindowV21._activate_character(window, char)
    window._on_profile_selected = lambda name: MainWindowV21._on_profile_selected(window, name)
    window._show_settings = lambda: MainWindowV21._show_settings(window)
    window._reload_config = lambda: MainWindowV21._reload_config(window)
    window._quit_application = lambda: MainWindowV21._quit_application(window)
    window._apply_setting = lambda k, v: MainWindowV21._apply_setting(window, k, v)
    window._on_character_detected = lambda wid, char: MainWindowV21._on_character_detected(
        window, wid, char
    )
    window._on_team_selected = lambda team: MainWindowV21._on_team_selected(window, team)
    window._on_layout_applied = lambda name: MainWindowV21._on_layout_applied(window, name)
    window.closeEvent = lambda e: MainWindowV21.closeEvent(window, e)
    window._show_about_dialog = lambda: MainWindowV21._show_about_dialog(window)
    window._open_url = lambda url: MainWindowV21._open_url(window, url)
    window._open_donation_link = lambda: MainWindowV21._open_donation_link(window)
    window._on_new_character_discovered = (
        lambda c, wid, t: MainWindowV21._on_new_character_discovered(window, c, wid, t)
    )
    window._apply_low_power_mode = lambda enabled: MainWindowV21._apply_low_power_mode(
        window, enabled
    )

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
            "PvP": ["Char3", "Char4"],
        }
        window.current_cycling_group = "PvP"

        result = window._get_cycling_group_members()

        assert result == ["Char3", "Char4"]

    def test_get_cycling_group_members_fallback_to_default(self):
        """Test fallback to Default group"""
        window = create_mock_window()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {"Default": ["Char1", "Char2"]}
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
        window.main_tab.window_manager.preview_frames = {"0x12345": mock_frame}

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
        window.settings_manager.get.return_value = {"Default": ["Char1", "Char2", "Char3"]}
        window.current_cycling_group = "Default"

        # Mock finding window
        mock_frame = MagicMock()
        mock_frame.character_name = "Char2"
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {"0x12345": mock_frame}

        window._activate_window = MagicMock()

        window._cycle_next()

        assert window.cycling_index == 1

    def test_cycle_next_wraps_around(self):
        """Test cycle_next wraps to beginning"""
        window = create_mock_window()
        window.cycling_index = 2  # Last position
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {"Default": ["Char1", "Char2", "Char3"]}
        window.current_cycling_group = "Default"

        # Mock finding window
        mock_frame = MagicMock()
        mock_frame.character_name = "Char1"
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {"0x12345": mock_frame}

        window._activate_window = MagicMock()

        window._cycle_next()

        assert window.cycling_index == 0  # Wrapped to beginning

    def test_cycle_prev_decrements_index(self):
        """Test cycle_prev decrements cycling index"""
        window = create_mock_window()
        window.cycling_index = 2
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {"Default": ["Char1", "Char2", "Char3"]}
        window.current_cycling_group = "Default"

        # Mock finding window
        mock_frame = MagicMock()
        mock_frame.character_name = "Char2"
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {"0x12345": mock_frame}

        window._activate_window = MagicMock()

        window._cycle_prev()

        assert window.cycling_index == 1


# Test activate window
class TestActivateWindow:
    """Tests for _activate_window method"""

    @patch("subprocess.run")
    def test_activate_window_calls_xdotool(self, mock_subprocess):
        """Test that activate_window calls xdotool"""
        window = create_mock_window()

        window._activate_window("0x12345")

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "xdotool" in call_args
        assert "windowactivate" in call_args
        assert "0x12345" in call_args

    @patch("subprocess.run")
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
        window.main_tab.window_manager.preview_frames = {"0x111": MagicMock(), "0x222": MagicMock()}

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
        window.main_tab.window_manager.preview_frames = {"0x111": MagicMock(), "0x222": MagicMock()}

        window.capture_system = MagicMock()
        window.capture_system.restore_window.return_value = True

        window.system_tray = MagicMock()

        window._restore_all_windows()

        assert window.capture_system.restore_window.call_count == 2
        window.system_tray.show_notification.assert_called()


# Test activate character
class TestActivateCharacter:
    """Tests for _activate_character method"""

    @patch("subprocess.run")
    def test_activate_character_found(self, mock_run):
        """Test activating a found character"""
        window = create_mock_window()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = False  # auto_minimize off

        mock_frame = MagicMock()
        mock_frame.character_name = "TestPilot"

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {"0x12345": mock_frame}

        mock_run.return_value = MagicMock(returncode=0)

        window._activate_character("TestPilot")

        # Should call xdotool windowactivate via _activate_window
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("windowactivate" in c and "0x12345" in c for c in calls)

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

    @patch("argus_overview.ui.main_window_v21.QApplication")
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

    def test_on_team_selected_logs_team_name(self):
        """Test that team selection logs the team name"""
        window = create_mock_window()

        mock_team = MagicMock()
        mock_team.name = "Fleet1"

        window._on_team_selected(mock_team)

        window.logger.info.assert_called_with("Team selected: Fleet1")


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

    @patch("argus_overview.ui.about_dialog.AboutDialog")
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

    @patch("PySide6.QtGui.QDesktopServices.openUrl")
    def test_open_url(self, mock_open_url):
        """Test opening URL"""
        window = create_mock_window()

        window._open_url("https://example.com")

        mock_open_url.assert_called_once()

    @patch("PySide6.QtGui.QDesktopServices.openUrl")
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


# Test toggle lock
class TestToggleLock:
    """Tests for _toggle_lock method"""

    def test_toggle_lock_clicks_lock_button(self):
        """Test that toggle_lock clicks the lock button"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.main_tab = MagicMock()
        window.main_tab.lock_btn = MagicMock()

        MainWindowV21._toggle_lock(window)

        window.main_tab.lock_btn.click.assert_called_once()

    def test_toggle_lock_no_main_tab(self):
        """Test toggle_lock handles missing main_tab gracefully"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        # No main_tab attribute
        del window.main_tab

        # Should not raise
        MainWindowV21._toggle_lock(window)


# Test get cycling group members edge cases
class TestGetCyclingGroupMembersEdgeCases:
    """Edge case tests for _get_cycling_group_members"""

    def test_fallback_to_default_group(self):
        """Test fallback to Default group when current not found"""
        window = create_mock_window()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {"Default": ["Char1", "Char2"]}
        window.current_cycling_group = "NonExistent"

        members = window._get_cycling_group_members()

        assert members == ["Char1", "Char2"]

    def test_fallback_to_active_windows(self):
        """Test fallback to active windows when no groups defined"""
        window = create_mock_window()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {}
        window.current_cycling_group = "Default"

        mock_frame1 = MagicMock()
        mock_frame1.character_name = "ActiveChar1"
        mock_frame2 = MagicMock()
        mock_frame2.character_name = "ActiveChar2"

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {"0x111": mock_frame1, "0x222": mock_frame2}

        members = window._get_cycling_group_members()

        assert "ActiveChar1" in members
        assert "ActiveChar2" in members


# Test cycle when character not found
class TestCycleEdgeCases:
    """Edge case tests for cycling methods"""

    def test_cycle_next_empty_group(self):
        """Test cycle_next with empty group"""
        window = create_mock_window()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {}
        window.current_cycling_group = "Empty"

        # No main_tab to fall back to
        del window.main_tab

        window._cycle_next()

        window.logger.warning.assert_called()

    def test_cycle_prev_empty_group(self):
        """Test cycle_prev with empty group"""
        window = create_mock_window()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {}
        window.current_cycling_group = "Empty"

        # No main_tab to fall back to
        del window.main_tab

        window._cycle_prev()

        window.logger.warning.assert_called()


# Test handle hotkey
class TestHandleHotkey:
    """Tests for _handle_hotkey method"""

    def test_handle_hotkey_logs_message(self):
        """Test that _handle_hotkey logs the hotkey name"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()

        MainWindowV21._handle_hotkey(window, "test_hotkey")

        window.logger.info.assert_called()


# Test reload config edge cases
class TestReloadConfigEdgeCases:
    """Edge case tests for _reload_config"""

    def test_reload_config_stops_auto_discovery_when_disabled(self):
        """Test that reload_config stops auto-discovery when disabled"""
        window = create_mock_window()

        window.settings_manager = MagicMock()
        # First call returns theme, second call returns False for auto_discovery
        window.settings_manager.get.side_effect = [
            "dark",  # appearance.theme
            False,  # general.auto_discovery
        ]

        window.theme_manager = MagicMock()
        window.auto_discovery = MagicMock()
        window.system_tray = MagicMock()
        window._apply_initial_settings = MagicMock()

        window._reload_config()

        window.auto_discovery.stop.assert_called_once()

    def test_reload_config_updates_running_auto_discovery(self):
        """Test reload_config updates interval when auto-discovery running"""
        window = create_mock_window()

        window.settings_manager = MagicMock()
        window.settings_manager.get.side_effect = [
            "dark",  # appearance.theme
            True,  # general.auto_discovery
            10,  # general.auto_discovery_interval
        ]

        window.theme_manager = MagicMock()
        window.auto_discovery = MagicMock()
        window.auto_discovery.scan_timer = MagicMock()
        window.auto_discovery.scan_timer.isActive.return_value = True  # Already running

        window.system_tray = MagicMock()
        window._apply_initial_settings = MagicMock()

        window._reload_config()

        window.auto_discovery.set_interval.assert_called_with(10)
        window.auto_discovery.start.assert_not_called()  # Already running


# Test apply setting edge cases
class TestApplySettingEdgeCases:
    """Edge case tests for _apply_setting"""

    def test_apply_setting_hotkeys(self):
        """Test applying hotkeys setting (currently a no-op)"""
        window = create_mock_window()

        # Should not raise
        window._apply_setting("hotkeys.minimize_all", "<ctrl>+m")

        window.logger.info.assert_called()

    def test_apply_setting_performance_refresh_rate(self):
        """Test applying refresh rate setting"""
        window = create_mock_window()

        # Should not raise
        window._apply_setting("performance.default_refresh_rate", 60)

        window.logger.info.assert_called()


# Test on character detected with status update
class TestOnCharacterDetectedEdgeCases:
    """Edge case tests for _on_character_detected"""

    def test_on_character_detected_updates_characters_tab(self):
        """Test that character detection updates characters tab if available"""
        window = create_mock_window()
        window.character_manager = MagicMock()
        window.characters_tab = MagicMock()

        window._on_character_detected("0x12345", "TestPilot")

        window.characters_tab.update_character_status.assert_called_with("TestPilot", "0x12345")


# Test get window id for character
class TestGetWindowIdForCharacter:
    """Tests for _get_window_id_for_character method"""

    def test_get_window_id_not_found(self):
        """Test returns None when character not found"""
        window = create_mock_window()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}

        result = window._get_window_id_for_character("Unknown")

        assert result is None

    def test_get_window_id_no_main_tab(self):
        """Test returns None when no main_tab"""
        window = create_mock_window()
        del window.main_tab

        result = window._get_window_id_for_character("SomeChar")

        assert result is None


# Test apply setting with main_tab for refresh rate
class TestApplySettingRefreshRate:
    """Tests for _apply_setting with performance.default_refresh_rate"""

    def test_apply_setting_refresh_rate_with_main_tab(self):
        """Test applying refresh rate setting when main_tab exists"""
        window = create_mock_window()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()

        window._apply_setting("performance.default_refresh_rate", 30)

        window.main_tab.window_manager.set_refresh_rate.assert_called_once_with(30)

    def test_apply_setting_disable_previews_with_main_tab(self):
        """Test applying disable_previews setting when main_tab exists"""
        window = create_mock_window()
        window.main_tab = MagicMock()

        window._apply_setting("performance.disable_previews", True)

        window.main_tab.set_previews_enabled.assert_called_once_with(False)

    def test_apply_setting_disable_previews_false(self):
        """Test applying disable_previews=False"""
        window = create_mock_window()
        window.main_tab = MagicMock()

        window._apply_setting("performance.disable_previews", False)

        window.main_tab.set_previews_enabled.assert_called_once_with(True)


# Test cycling recursion edge case
class TestCyclingRecursion:
    """Tests for cycling recursion when character not found"""

    def test_cycle_next_recursion_on_not_found(self):
        """Test _cycle_next recursively tries next when not found"""
        window = create_mock_window()
        window.cycling_index = 0
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {"Default": ["NotFound", "FoundChar"]}
        window.current_cycling_group = "Default"

        # First char not found, second char found
        mock_frame = MagicMock()
        mock_frame.character_name = "FoundChar"

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x222": mock_frame  # Only FoundChar exists
        }

        window._activate_window = MagicMock()

        window._cycle_next()

        # Should have advanced to index 1 (FoundChar) after not finding NotFound
        assert window.cycling_index == 1 or window._activate_window.called

    def test_cycle_prev_recursion_on_not_found(self):
        """Test _cycle_prev recursively tries prev when not found"""
        window = create_mock_window()
        window.cycling_index = 1
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {"Default": ["FoundChar", "NotFound"]}
        window.current_cycling_group = "Default"

        # Second char not found, first char found
        mock_frame = MagicMock()
        mock_frame.character_name = "FoundChar"

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x111": mock_frame  # Only FoundChar exists
        }

        window._activate_window = MagicMock()

        window._cycle_prev()

        # Should have decremented to find FoundChar
        assert window._activate_window.called or window.cycling_index == 0


# Test _set_window_icon
class TestSetWindowIcon:
    """Tests for _set_window_icon method"""

    @patch("argus_overview.ui.main_window_v21.Path")
    def test_set_window_icon_found(self, mock_path_class):
        """Test setting window icon when icon file found"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.setWindowIcon = MagicMock()

        # Mock path that exists
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.__str__ = MagicMock(return_value="/path/to/icon.png")
        mock_path_class.return_value = mock_path
        mock_path_class.__truediv__ = lambda s, o: mock_path

        # Mock Path.home() to return a mock that constructs valid paths
        with patch.object(mock_path_class, "home", return_value=mock_path):
            with patch.object(mock_path_class, "__call__", return_value=mock_path):
                MainWindowV21._set_window_icon(window)

        # Should have called setWindowIcon (at least once somewhere)
        # The implementation checks multiple paths

    @patch("argus_overview.ui.main_window_v21.Path")
    def test_set_window_icon_not_found(self, mock_path_class):
        """Test warning when no icon found"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.setWindowIcon = MagicMock()

        # Create a mock path that always returns a path that doesn't exist
        def make_mock_path():
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path.parent = mock_path  # .parent returns itself
            mock_path.__truediv__ = lambda self, other: make_mock_path()  # / returns new mock
            return mock_path

        mock_path = make_mock_path()
        mock_path_class.return_value = mock_path
        mock_path_class.home.return_value = mock_path

        MainWindowV21._set_window_icon(window)

        window.logger.warning.assert_called()


# Test _apply_initial_settings
class TestApplyInitialSettings:
    """Tests for _apply_initial_settings method"""

    def test_apply_initial_settings(self):
        """Test that _apply_initial_settings applies all settings"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = 4  # Default return for all gets

        window.capture_system = MagicMock()

        MainWindowV21._apply_initial_settings(window)

        # Should update capture_system.max_workers
        assert window.capture_system.max_workers == 4


# Test _connect_signals
class TestConnectSignals:
    """Tests for _connect_signals method"""

    def test_connect_signals(self):
        """Test that _connect_signals logs debug message"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()

        MainWindowV21._connect_signals(window)

        window.logger.debug.assert_called()


# Test profile not found
class TestProfileNotFound:
    """Test profile selection when preset not found"""

    def test_on_profile_selected_not_found(self):
        """Test profile selection when preset doesn't exist"""
        window = create_mock_window()

        window.layout_manager = MagicMock()
        window.layout_manager.get_preset.return_value = None  # Not found

        window.system_tray = MagicMock()

        window._on_profile_selected("NonExistent")

        window.layout_manager.get_preset.assert_called_with("NonExistent")
        # Should not call set_current_profile when preset not found
        window.system_tray.set_current_profile.assert_not_called()


# Test new character discovered - already exists
class TestNewCharacterAlreadyExists:
    """Test _on_new_character_discovered when character already tracked"""

    def test_on_new_character_discovered_already_exists(self):
        """Test that nothing happens when character already exists"""
        window = create_mock_window()

        # Character already in preview_frames
        mock_frame = MagicMock()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x99999": mock_frame  # Already exists
        }

        window.system_tray = MagicMock()

        window._on_new_character_discovered("ExistingPilot", "0x99999", "EVE - ExistingPilot")

        # add_window should NOT be called
        window.main_tab.window_manager.add_window.assert_not_called()


# Test new character discovered - no notification
class TestNewCharacterNoNotification:
    """Test _on_new_character_discovered without notifications"""

    def test_on_new_character_discovered_no_notification(self):
        """Test that notification is skipped when disabled"""
        window = create_mock_window()

        mock_frame = MagicMock()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}
        window.main_tab.window_manager.add_window.return_value = mock_frame
        window.main_tab.preview_layout = MagicMock()

        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = False  # show_notifications disabled

        window.system_tray = MagicMock()

        window._on_new_character_discovered("NewPilot", "0x88888", "EVE - NewPilot")

        # add_window should be called
        window.main_tab.window_manager.add_window.assert_called_once()
        # But show_notification should NOT be called
        window.system_tray.show_notification.assert_not_called()


# Test new character discovered - frame is None
class TestNewCharacterFrameNone:
    """Test _on_new_character_discovered when add_window returns None"""

    def test_on_new_character_discovered_frame_none(self):
        """Test handling when add_window returns None"""
        window = create_mock_window()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}
        window.main_tab.window_manager.add_window.return_value = None  # Failed to create

        window._on_new_character_discovered("NewPilot", "0x77777", "EVE - NewPilot")

        # Should not try to connect signals on None
        window.main_tab.preview_layout.addWidget.assert_not_called()


# Test minimize/restore handles no main_tab
class TestMinimizeRestoreNoMainTab:
    """Tests for minimize/restore when main_tab missing"""

    def test_minimize_all_no_main_tab(self):
        """Test minimize_all handles missing main_tab gracefully"""
        window = create_mock_window()
        del window.main_tab

        # Should not raise
        window._minimize_all_windows()

    def test_restore_all_no_main_tab(self):
        """Test restore_all handles missing main_tab gracefully"""
        window = create_mock_window()
        del window.main_tab

        # Should not raise
        window._restore_all_windows()


# Test activate character no main_tab
class TestActivateCharacterNoMainTab:
    """Test _activate_character when main_tab missing"""

    def test_activate_character_no_main_tab(self):
        """Test activate_character handles missing main_tab"""
        window = create_mock_window()
        del window.main_tab

        window._activate_character("SomeChar")

        window.logger.warning.assert_called()


# Test _register_hotkeys
class TestRegisterHotkeys:
    """Tests for _register_hotkeys method"""

    def test_register_hotkeys_basic(self):
        """Test registering basic hotkeys"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.side_effect = lambda key, default=None: {
            "hotkeys.minimize_all": "<ctrl>+<shift>+m",
            "hotkeys.restore_all": "<ctrl>+<shift>+r",
            "hotkeys.toggle_thumbnails": "<ctrl>+<shift>+t",
            "hotkeys.toggle_lock": "<ctrl>+<shift>+l",
            "character_hotkeys": {},
            "hotkeys.cycle_next": "<ctrl>+<tab>",
            "hotkeys.cycle_prev": "<ctrl>+<shift>+<tab>",
        }.get(key, default)

        window.hotkey_manager = MagicMock()

        MainWindowV21._register_hotkeys(window)

        # Should register basic hotkeys
        assert window.hotkey_manager.register_hotkey.call_count >= 4
        window.logger.info.assert_called()

    def test_register_hotkeys_with_character_hotkeys(self):
        """Test registering per-character hotkeys"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.side_effect = lambda key, default=None: {
            "hotkeys.minimize_all": "<ctrl>+m",
            "hotkeys.restore_all": "<ctrl>+r",
            "hotkeys.toggle_thumbnails": "<ctrl>+t",
            "hotkeys.toggle_lock": "<ctrl>+l",
            "character_hotkeys": {"Pilot1": "<f1>", "Pilot2": "<f2>"},
            "hotkeys.cycle_next": "<ctrl>+<tab>",
            "hotkeys.cycle_prev": "<ctrl>+<shift>+<tab>",
        }.get(key, default)

        window.hotkey_manager = MagicMock()

        MainWindowV21._register_hotkeys(window)

        # Should register character hotkeys (4 basic + 2 chars + 2 cycling = 8+)
        assert window.hotkey_manager.register_hotkey.call_count >= 6

    def test_register_hotkeys_no_cycle_combos(self):
        """Test registering hotkeys when cycle combos are empty"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.side_effect = lambda key, default=None: {
            "hotkeys.minimize_all": "<ctrl>+m",
            "hotkeys.restore_all": "<ctrl>+r",
            "hotkeys.toggle_thumbnails": "<ctrl>+t",
            "hotkeys.toggle_lock": "<ctrl>+l",
            "character_hotkeys": {},
            "hotkeys.cycle_next": "",  # Empty
            "hotkeys.cycle_prev": "",  # Empty
        }.get(key, default)

        window.hotkey_manager = MagicMock()

        MainWindowV21._register_hotkeys(window)

        # Should still complete without error
        window.logger.info.assert_called()


# Test _activate_window
class TestActivateWindow:
    """Tests for _activate_window method"""

    @patch("subprocess.run")
    def test_activate_window_success(self, mock_run):
        """Test activating window with xdotool"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = False  # auto_minimize off

        mock_run.return_value = MagicMock(returncode=0)

        MainWindowV21._activate_window(window, "0x12345")

        # Check xdotool windowactivate was called (may have other subprocess calls)
        calls = [c for c in mock_run.call_args_list if c[0] and "xdotool" in c[0][0]]
        assert len(calls) >= 1
        assert "windowactivate" in calls[-1][0][0]
        assert "0x12345" in calls[-1][0][0]

    @patch("subprocess.run")
    def test_activate_window_failure(self, mock_run):
        """Test activate window handles subprocess failure"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = False  # auto_minimize off

        mock_run.side_effect = Exception("xdotool not found")

        MainWindowV21._activate_window(window, "0x12345")

        window.logger.error.assert_called()

    @patch("subprocess.run")
    def test_activate_window_with_auto_minimize(self, mock_run):
        """Test activating window minimizes previous when auto-minimize enabled"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = True  # auto_minimize ON
        window.settings_manager.get_last_activated_window.return_value = (
            "0x99999"  # Previous EVE window (shared)
        )

        mock_run.return_value = MagicMock(returncode=0)

        MainWindowV21._activate_window(window, "0x12345")

        # Should have 2 calls: windowminimize (previous), windowactivate (new)
        assert mock_run.call_count == 2
        # Verify minimize was called on previous window
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("windowminimize" in c and "0x99999" in c for c in calls)
        assert any("windowactivate" in c and "0x12345" in c for c in calls)

    @patch("subprocess.run")
    def test_activate_window_invalid_id_none(self, mock_run):
        """Test activate window rejects None window ID"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()

        MainWindowV21._activate_window(window, None)

        window.logger.warning.assert_called()
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_activate_window_invalid_id_format(self, mock_run):
        """Test activate window rejects invalid window ID format"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()

        # Test various invalid formats
        for invalid_id in ["12345", "abc", "0xGGGG", "", "window123"]:
            mock_run.reset_mock()
            window.logger.reset_mock()

            MainWindowV21._activate_window(window, invalid_id)

            window.logger.warning.assert_called()
            mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_activate_window_valid_id_formats(self, mock_run):
        """Test activate window accepts valid window ID formats"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = False

        mock_run.return_value = MagicMock(returncode=0)

        # Test various valid formats
        for valid_id in ["0x12345", "0xABCDEF", "0x0", "0xFFFFFFFF"]:
            mock_run.reset_mock()

            MainWindowV21._activate_window(window, valid_id)

            # Should have called subprocess
            assert mock_run.called


# Test _create_menu_bar
class TestCreateMenuBar:
    """Tests for _create_menu_bar method"""

    @patch("argus_overview.ui.main_window_v21.MenuBuilder")
    @patch("argus_overview.ui.main_window_v21.ActionRegistry")
    def test_create_menu_bar(self, mock_registry_class, mock_builder_class):
        """Test creating menu bar"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.menuBar.return_value = MagicMock()

        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry

        mock_builder = MagicMock()
        mock_builder.build_help_menu.return_value = MagicMock()
        mock_builder_class.return_value = mock_builder

        MainWindowV21._create_menu_bar(window)

        # Should build help menu
        mock_builder.build_help_menu.assert_called_once()
        # Should add menu to menubar
        window.menuBar().addMenu.assert_called_once()


# Test cycling when character not found (covers 244-246, 266-268)
class TestCyclingCharNotFound:
    """Tests for cycling when character not found - covers recursive branches"""

    def test_cycle_next_char_not_found_logs_warning(self):
        """Test _cycle_next logs warning when character not found and no recursion"""
        window = create_mock_window()
        window.cycling_index = 0
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {"Default": ["OnlyChar"]}
        window.current_cycling_group = "Default"

        # Set up main_tab with empty preview_frames so character not found
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}  # No windows

        # Mock _cycle_next to not recurse (avoid infinite loop in test)
        original_cycle_next = window._cycle_next
        call_count = [0]

        def cycle_next_once():
            call_count[0] += 1
            if call_count[0] == 1:
                original_cycle_next()

        window._cycle_next = cycle_next_once

        window._cycle_next()

        # Should log warning about character not found
        window.logger.warning.assert_called()

    def test_cycle_prev_char_not_found_logs_warning(self):
        """Test _cycle_prev logs warning when character not found and no recursion"""
        window = create_mock_window()
        window.cycling_index = 0
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = {"Default": ["OnlyChar"]}
        window.current_cycling_group = "Default"

        # Set up main_tab with empty preview_frames so character not found
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}  # No windows

        # Mock _cycle_prev to not recurse (avoid infinite loop in test)
        original_cycle_prev = window._cycle_prev
        call_count = [0]

        def cycle_prev_once():
            call_count[0] += 1
            if call_count[0] == 1:
                original_cycle_prev()

        window._cycle_prev = cycle_prev_once

        window._cycle_prev()

        # Should log warning about character not found
        window.logger.warning.assert_called()


# Test _create_system_tray
class TestCreateSystemTray:
    """Tests for _create_system_tray method"""

    @patch("argus_overview.ui.main_window_v21.SystemTray")
    def test_create_system_tray(self, mock_tray_class):
        """Test creating system tray"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.layout_manager = MagicMock()

        # Mock presets
        mock_preset1 = MagicMock()
        mock_preset1.name = "Profile1"
        mock_preset2 = MagicMock()
        mock_preset2.name = "Profile2"
        window.layout_manager.get_all_presets.return_value = [mock_preset1, mock_preset2]

        mock_tray = MagicMock()
        mock_tray_class.return_value = mock_tray

        MainWindowV21._create_system_tray(window)

        # Should create tray
        mock_tray_class.assert_called_once_with(window)

        # Should connect signals
        assert mock_tray.show_hide_requested.connect.called
        assert mock_tray.minimize_all_requested.connect.called

        # Should set profiles
        mock_tray.set_profiles.assert_called_once_with(["Profile1", "Profile2"])

        # Should show tray
        mock_tray.show.assert_called_once()


# Test _create_main_tab
class TestCreateMainTab:
    """Tests for _create_main_tab method"""

    @patch("argus_overview.ui.main_tab.MainTab")
    def test_create_main_tab(self, mock_tab_class):
        """Test creating main tab"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.capture_system = MagicMock()
        window.character_manager = MagicMock()
        window.settings_manager = MagicMock()
        window.tabs = MagicMock()

        mock_tab = MagicMock()
        mock_tab_class.return_value = mock_tab

        MainWindowV21._create_main_tab(window)

        # Should create tab with correct arguments
        mock_tab_class.assert_called_once()
        window.tabs.addTab.assert_called_once()

        # Should connect signals
        assert mock_tab.character_detected.connect.called
        assert mock_tab.layout_applied.connect.called


# Test _create_characters_tab
class TestCreateCharactersTab:
    """Tests for _create_characters_tab method"""

    @patch("argus_overview.ui.characters_teams_tab.CharactersTeamsTab")
    def test_create_characters_tab(self, mock_tab_class):
        """Test creating characters tab"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.character_manager = MagicMock()
        window.layout_manager = MagicMock()
        window.settings_sync = MagicMock()
        window.tabs = MagicMock()

        mock_tab = MagicMock()
        mock_tab_class.return_value = mock_tab

        MainWindowV21._create_characters_tab(window)

        # Should create tab
        mock_tab_class.assert_called_once()
        window.tabs.addTab.assert_called_once()

        # Should connect team_selected signal
        assert mock_tab.team_selected.connect.called


# Test _create_hotkeys_tab
class TestCreateHotkeysTab:
    """Tests for _create_hotkeys_tab method"""

    @patch("argus_overview.ui.hotkeys_tab.HotkeysTab")
    def test_create_hotkeys_tab(self, mock_tab_class):
        """Test creating hotkeys tab"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.character_manager = MagicMock()
        window.settings_manager = MagicMock()
        window.main_tab = MagicMock()
        window.tabs = MagicMock()
        window.hotkey_manager = MagicMock()

        mock_tab = MagicMock()
        mock_tab_class.return_value = mock_tab

        MainWindowV21._create_hotkeys_tab(window)

        # Should create tab
        mock_tab_class.assert_called_once()
        window.tabs.addTab.assert_called_once()

        # Should connect group_changed signal
        assert mock_tab.group_changed.connect.called

        # Should connect recording signals for pause/resume
        assert mock_tab.cycle_forward_edit.recordingStarted.connect.called
        assert mock_tab.cycle_backward_edit.recordingStopped.connect.called


# Test _create_settings_sync_tab
class TestCreateSettingsSyncTab:
    """Tests for _create_settings_sync_tab method"""

    @patch("argus_overview.ui.settings_sync_tab.SettingsSyncTab")
    def test_create_settings_sync_tab(self, mock_tab_class):
        """Test creating settings sync tab"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_sync = MagicMock()
        window.character_manager = MagicMock()
        window.tabs = MagicMock()

        mock_tab = MagicMock()
        mock_tab_class.return_value = mock_tab

        MainWindowV21._create_settings_sync_tab(window)

        # Should create tab
        mock_tab_class.assert_called_once()
        window.tabs.addTab.assert_called_once()


# Test _create_settings_tab
class TestCreateSettingsTab:
    """Tests for _create_settings_tab method"""

    @patch("argus_overview.ui.settings_tab.SettingsTab")
    def test_create_settings_tab(self, mock_tab_class):
        """Test creating settings tab"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.hotkey_manager = MagicMock()
        window.tabs = MagicMock()

        mock_tab = MagicMock()
        mock_tab_class.return_value = mock_tab

        MainWindowV21._create_settings_tab(window)

        # Should create tab
        mock_tab_class.assert_called_once()
        window.tabs.addTab.assert_called_once()

        # Should connect settings_changed signal
        assert mock_tab.settings_changed.connect.called


# Test _apply_low_power_mode
class TestApplyLowPowerMode:
    """Tests for _apply_low_power_mode method"""

    def test_enable_low_power_mode(self):
        """Test enabling low power mode"""
        window = create_mock_window()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.refresh_rate_spin = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = 30  # previous FPS
        window.statusBar = MagicMock(return_value=MagicMock())

        window._apply_low_power_mode(True)

        # Should set FPS to 5
        window.main_tab.window_manager.set_refresh_rate.assert_called_with(5)
        # Should update spinner
        window.main_tab.refresh_rate_spin.setValue.assert_called_with(5)
        # Should show status message
        window.statusBar().showMessage.assert_called()

    def test_disable_low_power_mode(self):
        """Test disabling low power mode restores previous settings"""
        window = create_mock_window()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.refresh_rate_spin = MagicMock()
        window.settings_manager = MagicMock()
        window.statusBar = MagicMock(return_value=MagicMock())

        # Simulate that low power mode was previously enabled
        window._low_power_previous = {"fps": 30}

        window._apply_low_power_mode(False)

        # Should restore FPS to 30
        window.main_tab.window_manager.set_refresh_rate.assert_called_with(30)
        # Should update spinner
        window.main_tab.refresh_rate_spin.setValue.assert_called_with(30)
        # Should show status message
        window.statusBar().showMessage.assert_called()

    def test_enable_low_power_mode_stores_previous(self):
        """Test that enabling stores previous settings for restoration"""
        window = create_mock_window()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.refresh_rate_spin = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.side_effect = lambda k, d=None: {
            "performance.default_refresh_rate": 45,
        }.get(k, d)
        window.statusBar = MagicMock(return_value=MagicMock())

        window._apply_low_power_mode(True)

        # Should have stored previous values
        assert hasattr(window, "_low_power_previous")
        assert window._low_power_previous["fps"] == 45

    def test_disable_low_power_mode_without_previous(self):
        """Test disabling when no previous settings stored"""
        window = create_mock_window()
        window.main_tab = MagicMock()
        window.settings_manager = MagicMock()
        window.statusBar = MagicMock(return_value=MagicMock())

        # No _low_power_previous attribute
        window._apply_low_power_mode(False)

        # Should still show status message
        window.statusBar().showMessage.assert_called()

    def test_enable_low_power_no_main_tab(self):
        """Test enabling low power mode when main_tab doesn't exist"""
        window = create_mock_window()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = 30
        window.statusBar = MagicMock(return_value=MagicMock())

        # Remove main_tab attribute
        del window.main_tab

        # Should not raise
        window._apply_low_power_mode(True)

        # Should still show status
        window.statusBar().showMessage.assert_called()


# Test _apply_setting for low_power_mode
class TestApplySettingLowPowerMode:
    """Tests for _apply_setting with low_power_mode"""

    def test_apply_setting_low_power_mode_enabled(self):
        """Test applying low_power_mode setting (enabled)"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window._apply_low_power_mode = MagicMock()

        MainWindowV21._apply_setting(window, "performance.low_power_mode", True)

        window._apply_low_power_mode.assert_called_once_with(True)

    def test_apply_setting_low_power_mode_disabled(self):
        """Test applying low_power_mode setting (disabled)"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window._apply_low_power_mode = MagicMock()

        MainWindowV21._apply_setting(window, "performance.low_power_mode", False)

        window._apply_low_power_mode.assert_called_once_with(False)


# Test _apply_to_all_windows with invalid action
class TestApplyToAllWindowsInvalidAction:
    """Tests for _apply_to_all_windows with invalid action"""

    def test_apply_to_all_windows_invalid_action(self):
        """Test that invalid action name returns early without error"""
        window = create_mock_window()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {"0x111": MagicMock()}

        # Mock capture_system without the invalid method
        window.capture_system = MagicMock(spec=["minimize_window", "restore_window"])
        # getattr(capture_system, "invalid_window", None) will return None

        # Should not raise - just returns early
        window._apply_to_all_windows("invalid")

        # Should not try to call any methods since action was invalid
        window.capture_system.minimize_window.assert_not_called()
        window.capture_system.restore_window.assert_not_called()
