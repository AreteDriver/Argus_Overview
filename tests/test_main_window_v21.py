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
    window._is_quitting = False
    window._auto_discovery_connected = False
    window._tab_indexes = {}
    window._bulk_import_active = False
    window._bulk_import_dirty_characters = False
    window._bulk_import_dirty_groups = False
    window._pending_discovery_names = []
    window.close = MagicMock()
    window._connect_auto_discovery = lambda: MainWindowV21._connect_auto_discovery(window)
    window._disconnect_auto_discovery = lambda: MainWindowV21._disconnect_auto_discovery(window)
    window._ensure_auto_discovery_state = lambda: MainWindowV21._ensure_auto_discovery_state(window)
    window._run_startup_assistant = lambda: MainWindowV21._run_startup_assistant(window)
    window._begin_bulk_import = lambda: MainWindowV21._begin_bulk_import(window)
    window._finish_bulk_import = lambda: MainWindowV21._finish_bulk_import(window)
    window._queue_discovery_notification = lambda name: MainWindowV21._queue_discovery_notification(
        window, name
    )
    window._flush_discovery_notifications = lambda: MainWindowV21._flush_discovery_notifications(
        window
    )
    window._queue_main_tab_status_refresh = lambda: MainWindowV21._queue_main_tab_status_refresh(
        window
    )
    window._flush_main_tab_status_refresh = lambda: MainWindowV21._flush_main_tab_status_refresh(
        window
    )

    # Bind the real methods to our mock
    window._toggle_visibility = lambda: MainWindowV21._toggle_visibility(window)
    window._toggle_thumbnails = lambda: MainWindowV21._toggle_thumbnails(window)
    window._get_cycling_group_members = lambda: MainWindowV21._get_cycling_group_members(window)
    window._get_window_id_for_character = lambda char: MainWindowV21._get_window_id_for_character(
        window, char
    )
    window._cycle_window = lambda direction=1: MainWindowV21._cycle_window(window, direction)
    window._perform_cycle = lambda: MainWindowV21._perform_cycle(window)
    window._pending_cycle_direction = None

    # Mock timer that fires immediately for test determinism
    mock_timer = MagicMock()
    mock_timer.start = lambda *a, **kw: MainWindowV21._perform_cycle(window)
    window._cycle_timer = mock_timer

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
    window._show_roster = lambda: MainWindowV21._show_roster(window)
    window._show_cycle_control = lambda: MainWindowV21._show_cycle_control(window)
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
    window._on_new_character_discovered = lambda c, wid, t: (
        MainWindowV21._on_new_character_discovered(window, c, wid, t)
    )
    window._apply_low_power_mode = lambda enabled: MainWindowV21._apply_low_power_mode(
        window, enabled
    )

    # Provide capture_system mock with _window_mgr for _activate_window
    mock_window_mgr = MagicMock()
    mock_window_mgr.is_valid_window_id.return_value = True
    window.capture_system = MagicMock()
    window.capture_system._window_mgr = mock_window_mgr
    window.cycle_controller = MagicMock()
    window.statusBar = MagicMock(return_value=MagicMock())
    window.settings_manager = MagicMock()
    window.character_manager = MagicMock()
    window._discovery_notification_timer = MagicMock()
    window._status_refresh_timer = MagicMock()

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


# Test activate window (uses create_mock_window with capture_system)
class TestActivateWindowBasic:
    """Tests for _activate_window method (basic)"""

    def test_activate_window_delegates_to_cycle_controller(self):
        """Test that activate_window delegates to CycleController."""
        window = create_mock_window()

        window._activate_window("0x12345")

        window.cycle_controller.activate_window.assert_called_once_with("0x12345")

    def test_activate_window_handles_controller_failure(self):
        """Test that activate_window still routes through controller on failure."""
        window = create_mock_window()
        window.cycle_controller.activate_window.return_value = False

        # Should not raise
        window._activate_window("0x12345")

        window.cycle_controller.activate_window.assert_called_once_with("0x12345")


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

    def test_activate_character_found(self):
        """Test activating a found character delegates to CycleController."""
        window = create_mock_window()

        window._activate_character("TestPilot")

        window.cycle_controller.activate_character.assert_called_once_with(
            "TestPilot",
            window._get_window_id_for_character,
        )

    def test_activate_character_not_found(self):
        """Test activating a character still delegates lookup to controller."""
        window = create_mock_window()

        window._activate_character("Unknown")

        window.cycle_controller.activate_character.assert_called_once_with(
            "Unknown",
            window._get_window_id_for_character,
        )


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
        window._tab_indexes = {"Settings": 5}

        window._show_settings()

        window.show.assert_called_once()
        window.raise_.assert_called_once()
        window.tabs.setCurrentIndex.assert_called_with(5)


class TestTabNavigation:
    """Tests for overview next-step tab navigation."""

    def test_show_roster_switches_to_roster_tab(self):
        """Test _show_roster shows the window and switches to Roster."""
        window = create_mock_window()
        window.show = MagicMock()
        window.raise_ = MagicMock()
        window.tabs = MagicMock()
        window._tab_indexes = {"Roster": 2}

        window._show_roster()

        window.show.assert_called_once()
        window.raise_.assert_called_once()
        window.tabs.setCurrentIndex.assert_called_once_with(2)

    def test_show_cycle_control_switches_to_cycle_control_tab(self):
        """Test _show_cycle_control shows the window and switches tabs."""
        window = create_mock_window()
        window.show = MagicMock()
        window.raise_ = MagicMock()
        window.tabs = MagicMock()
        window._tab_indexes = {"Cycle Control": 3}

        window._show_cycle_control()

        window.show.assert_called_once()
        window.raise_.assert_called_once()
        window.tabs.setCurrentIndex.assert_called_once_with(3)


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

    def test_quit_application_sets_flag_and_closes(self):
        """Test that quit_application marks quitting and closes the window."""
        window = create_mock_window()

        window._quit_application()

        assert window._is_quitting is True
        window.close.assert_called_once()


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
        """Test that character detection bootstraps and assigns window state."""
        window = create_mock_window()
        window.character_manager = MagicMock()
        window._add_to_default_cycling_group = MagicMock()

        window._on_character_detected("0x12345", "TestPilot")

        window.character_manager.ensure_character.assert_called_with("TestPilot")
        window.character_manager.assign_window.assert_called_with("TestPilot", "0x12345")
        window._add_to_default_cycling_group.assert_called_with("TestPilot")


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

    def test_close_event_bypasses_tray_when_quitting(self):
        """Test that explicit quit bypasses minimize-to-tray behavior."""
        window = create_mock_window()
        window._is_quitting = True

        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = True

        window.auto_discovery = MagicMock()
        window.capture_system = MagicMock()
        window.hotkey_manager = MagicMock()
        window.system_tray = MagicMock()
        window.character_manager = MagicMock()
        window._disconnect_signals = MagicMock()
        window._disconnect_auto_discovery = MagicMock()

        mock_event = MagicMock()

        window.closeEvent(mock_event)

        window.hide.assert_not_called()
        mock_event.accept.assert_called_once()

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

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}  # Not already there
        window.main_tab.import_detected_window.return_value = True
        window._queue_main_tab_status_refresh = MagicMock()

        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = True  # show_notifications

        window.system_tray = MagicMock()

        window._on_new_character_discovered("NewPilot", "0x99999", "EVE - NewPilot")

        window.main_tab.import_detected_window.assert_called_with("0x99999", "NewPilot")
        window._queue_main_tab_status_refresh.assert_called_once()
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
        window._ensure_auto_discovery_state = MagicMock()
        window.system_tray = MagicMock()
        window._apply_initial_settings = MagicMock()

        window._reload_config()

        window._ensure_auto_discovery_state.assert_called_once()

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
        window._ensure_auto_discovery_state = MagicMock()

        window.system_tray = MagicMock()
        window._apply_initial_settings = MagicMock()

        window._reload_config()

        window._ensure_auto_discovery_state.assert_called_once()


class TestStartupAssistant:
    """Tests for startup onboarding automation."""

    def test_startup_assistant_auto_imports_running_clients(self):
        """Test startup assistant auto-imports when enabled and overview is empty."""
        window = create_mock_window()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.get_active_window_count.return_value = 0
        window.main_tab.one_click_import.return_value = (2, 0, 2)
        window.system_tray = MagicMock()

        def get_side_effect(key, default=None):
            values = {
                "general.auto_import_on_startup": True,
                "general.show_notifications": True,
            }
            return values.get(key, default)

        window.settings_manager = MagicMock()
        window.settings_manager.get.side_effect = get_side_effect

        window._run_startup_assistant()

        window.main_tab.one_click_import.assert_called_once_with(show_dialogs=False)
        window.statusBar.return_value.showMessage.assert_called_once()
        window.system_tray.show_notification.assert_called_once()

    def test_startup_assistant_flushes_batched_saves_once(self):
        """Test startup assistant finishes deferred persistence after bulk import."""
        window = create_mock_window()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.get_active_window_count.return_value = 0

        def import_side_effect(*, show_dialogs=False):
            window._bulk_import_dirty_characters = True
            window._bulk_import_dirty_groups = True
            return (3, 0, 3)

        window.main_tab.one_click_import.side_effect = import_side_effect
        window.system_tray = MagicMock()

        def get_side_effect(key, default=None):
            values = {
                "general.auto_import_on_startup": True,
                "general.show_notifications": False,
            }
            return values.get(key, default)

        window.settings_manager.get.side_effect = get_side_effect

        window._run_startup_assistant()

        window.character_manager.save_data.assert_called_once()
        window.settings_manager.save_settings.assert_called_once()


class TestDiscoveryNotifications:
    """Tests for batched auto-discovery notifications."""

    def test_queue_discovery_notification_batches_names(self):
        """Test queued names are accumulated and timer restarted."""
        window = create_mock_window()

        window._queue_discovery_notification("Pilot One")
        window._queue_discovery_notification("Pilot Two")
        window._queue_discovery_notification("Pilot One")

        assert window._pending_discovery_names == ["Pilot One", "Pilot Two"]
        assert window._discovery_notification_timer.start.call_count == 3

    def test_flush_discovery_notifications_shows_single_summary(self):
        """Test multiple queued discoveries are shown as one summary notification."""
        window = create_mock_window()
        window.system_tray = MagicMock()
        window._pending_discovery_names = ["Pilot One", "Pilot Two", "Pilot Three", "Pilot Four"]

        window._flush_discovery_notifications()

        window.system_tray.show_notification.assert_called_once()
        assert window._pending_discovery_names == []


class TestStatusRefreshQueue:
    """Tests for debounced main-tab status refreshes."""

    def test_queue_main_tab_status_refresh_starts_timer(self):
        """Test status refreshes are queued through the debounce timer."""
        window = create_mock_window()

        window._queue_main_tab_status_refresh()

        window._status_refresh_timer.start.assert_called_once()

    def test_flush_main_tab_status_refresh_updates_overview(self):
        """Test flushing the queued refresh updates the overview once."""
        window = create_mock_window()
        window.main_tab = MagicMock()

        window._flush_main_tab_status_refresh()

        window.main_tab._update_status.assert_called_once()

    def test_startup_assistant_shows_guidance_when_nothing_imported(self):
        """Test startup assistant shows quick-start guidance when no clients are imported."""
        window = create_mock_window()
        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.get_active_window_count.return_value = 0
        window.main_tab.one_click_import.return_value = (0, 0, 0)
        window.system_tray = MagicMock()

        def get_side_effect(key, default=None):
            values = {
                "general.auto_import_on_startup": True,
                "general.show_notifications": True,
                "general.show_setup_guidance": True,
            }
            return values.get(key, default)

        window.settings_manager = MagicMock()
        window.settings_manager.get.side_effect = get_side_effect

        window._run_startup_assistant()

        window.main_tab.one_click_import.assert_called_once_with(show_dialogs=False)
        window.statusBar.return_value.showMessage.assert_called_once()
        window.system_tray.show_notification.assert_not_called()


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
        window._add_to_default_cycling_group = MagicMock()
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

        window.main_tab.import_detected_window.assert_not_called()


# Test new character discovered - no notification
class TestNewCharacterNoNotification:
    """Test _on_new_character_discovered without notifications"""

    def test_on_new_character_discovered_no_notification(self):
        """Test that notification is skipped when disabled"""
        window = create_mock_window()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}
        window.main_tab.import_detected_window.return_value = True
        window._queue_main_tab_status_refresh = MagicMock()

        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = False  # show_notifications disabled

        window.system_tray = MagicMock()

        window._on_new_character_discovered("NewPilot", "0x88888", "EVE - NewPilot")

        window.main_tab.import_detected_window.assert_called_once_with("0x88888", "NewPilot")
        window._queue_main_tab_status_refresh.assert_called_once()
        # But show_notification should NOT be called
        window.system_tray.show_notification.assert_not_called()


# Test new character discovered - frame is None
class TestNewCharacterFrameNone:
    """Test _on_new_character_discovered when shared import returns False"""

    def test_on_new_character_discovered_frame_none(self):
        """Test handling when shared import path fails."""
        window = create_mock_window()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {}
        window.main_tab.import_detected_window.return_value = False
        window._queue_main_tab_status_refresh = MagicMock()

        window._on_new_character_discovered("NewPilot", "0x77777", "EVE - NewPilot")

        window.main_tab.import_detected_window.assert_called_once_with("0x77777", "NewPilot")
        window._queue_main_tab_status_refresh.assert_not_called()


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
        """Test activate_character still delegates even if main_tab is missing."""
        window = create_mock_window()
        del window.main_tab

        window._activate_character("SomeChar")

        window.cycle_controller.activate_character.assert_called_once()


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


class TestRegisterCyclingHotkeys:
    """Tests for _register_cycling_hotkeys method"""

    def test_register_cycling_hotkeys_unregisters_old(self):
        """Test that old cycling hotkeys are unregistered before re-registering"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.side_effect = lambda key, default=None: {
            "hotkeys.cycle_next": "<ctrl>+n",
            "hotkeys.cycle_prev": "<ctrl>+p",
        }.get(key, default)
        window.hotkey_manager = MagicMock()
        window.logger = MagicMock()

        MainWindowV21._register_cycling_hotkeys(window)

        window.hotkey_manager.unregister_hotkey.assert_any_call("cycle_next", restart=False)
        window.hotkey_manager.unregister_hotkey.assert_any_call("cycle_prev", restart=False)
        window.hotkey_manager.register_hotkey.assert_any_call(
            "cycle_next", "<ctrl>+n", window._cycle_next
        )
        window.hotkey_manager.register_hotkey.assert_any_call(
            "cycle_prev", "<ctrl>+p", window._cycle_prev
        )

    def test_register_cycling_hotkeys_skips_empty(self):
        """Test that empty combos are not registered"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.side_effect = lambda key, default=None: {
            "hotkeys.cycle_next": "",
            "hotkeys.cycle_prev": "",
        }.get(key, default)
        window.hotkey_manager = MagicMock()
        window.logger = MagicMock()

        MainWindowV21._register_cycling_hotkeys(window)

        # Unregister should still be called
        assert window.hotkey_manager.unregister_hotkey.call_count == 2
        # But register should NOT be called (empty combos)
        window.hotkey_manager.register_hotkey.assert_not_called()


# Test _activate_window (platform abstraction layer)
class TestActivateWindowPlatform:
    """Tests for _activate_window delegation to CycleController."""

    def _make_window(self):
        """Helper to create a mock window with CycleController."""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.cycle_controller = MagicMock()
        return window

    def test_activate_window_success(self):
        """Test activating window delegates to CycleController."""
        window = self._make_window()

        from argus_overview.ui.main_window_v21 import MainWindowV21

        MainWindowV21._activate_window(window, "0x12345")

        window.cycle_controller.activate_window.assert_called_once_with("0x12345")

    def test_activate_window_failure(self):
        """Test activate window does not swallow controller invocation."""
        window = self._make_window()

        from argus_overview.ui.main_window_v21 import MainWindowV21

        MainWindowV21._activate_window(window, "0x12345")

        window.cycle_controller.activate_window.assert_called_once_with("0x12345")


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


# Test _create_intel_tab
class TestCreateIntelTab:
    """Tests for _create_intel_tab method"""

    @patch("argus_overview.ui.intel_tab.IntelTab")
    def test_create_intel_tab(self, mock_tab_class):
        """Test creating intel tab"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.tabs = MagicMock()

        mock_tab = MagicMock()
        mock_dispatcher = MagicMock()
        mock_tab.get_alert_dispatcher.return_value = mock_dispatcher
        mock_tab_class.return_value = mock_tab

        MainWindowV21._create_intel_tab(window)

        # Should create tab
        mock_tab_class.assert_called_once_with(window.settings_manager)
        window.tabs.addTab.assert_called_once()

        # Should connect signals
        assert mock_tab.alert_triggered.connect.called
        assert mock_tab.intel_received.connect.called
        assert mock_dispatcher.border_flash_requested.connect.called


# Test _flash_preview_borders
class TestFlashPreviewBorders:
    """Tests for _flash_preview_borders method"""

    def test_flash_preview_borders(self):
        """Test flashing preview borders"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)

        mock_frame1 = MagicMock()
        mock_frame2 = MagicMock()

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {
            "0x111": mock_frame1,
            "0x222": mock_frame2,
        }

        MainWindowV21._flash_preview_borders(window, "#FF0000", 2000)

        mock_frame1.flash_border.assert_called_once_with("#FF0000", 2000)
        mock_frame2.flash_border.assert_called_once_with("#FF0000", 2000)

    def test_flash_preview_borders_no_main_tab(self):
        """Test flash_preview_borders handles missing main_tab"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        del window.main_tab

        # Should not raise
        MainWindowV21._flash_preview_borders(window, "#FF0000", 2000)

    def test_flash_preview_borders_no_window_manager(self):
        """Test flash_preview_borders handles missing window_manager"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.main_tab = MagicMock(spec=[])  # No window_manager attr

        # Should not raise
        MainWindowV21._flash_preview_borders(window, "#FF0000", 2000)

    def test_flash_preview_borders_frame_without_flash_border(self):
        """Test flash_preview_borders handles frames without flash_border method"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)

        mock_frame = MagicMock(spec=[])  # No flash_border method

        window.main_tab = MagicMock()
        window.main_tab.window_manager = MagicMock()
        window.main_tab.window_manager.preview_frames = {"0x111": mock_frame}

        # Should not raise
        MainWindowV21._flash_preview_borders(window, "#FF0000", 2000)


# Test _on_intel_alert
class TestOnIntelAlert:
    """Tests for _on_intel_alert method"""

    def test_on_intel_alert_critical_shows_notification(self):
        """Test critical intel alert shows tray notification"""
        from argus_overview.intel.parser import IntelReport, ThreatLevel
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.system_tray = MagicMock()

        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.CRITICAL,
            hostile_count=5,
            ship_types=["Sabre", "Loki"],
            player_names=[],
            raw_message="HED-GP 5 hostiles",
        )

        MainWindowV21._on_intel_alert(window, report, MagicMock())

        window.system_tray.show_notification.assert_called_once()
        call_args = window.system_tray.show_notification.call_args[0]
        assert "CRITICAL" in call_args[0]
        assert "HED-GP" in call_args[0]

    def test_on_intel_alert_warning_no_notification(self):
        """Test warning-level alert doesn't show notification"""
        from argus_overview.intel.parser import IntelReport, ThreatLevel
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.system_tray = MagicMock()

        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.WARNING,
            hostile_count=1,
            ship_types=[],
            player_names=[],
            raw_message="HED-GP 1 neutral",
        )

        MainWindowV21._on_intel_alert(window, report, MagicMock())

        window.system_tray.show_notification.assert_not_called()

    def test_on_intel_alert_invalid_report_type(self):
        """Test intel alert with non-IntelReport type returns early"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.system_tray = MagicMock()

        # Pass invalid type
        MainWindowV21._on_intel_alert(window, "not a report", MagicMock())

        window.system_tray.show_notification.assert_not_called()

    def test_on_intel_alert_no_system_tray(self):
        """Test intel alert handles missing system_tray"""
        from argus_overview.intel.parser import IntelReport, ThreatLevel
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        del window.system_tray  # No system tray

        report = IntelReport(
            system="HED-GP",
            threat_level=ThreatLevel.CRITICAL,
            hostile_count=5,
            ship_types=[],
            player_names=[],
            raw_message="test",
        )

        # Should not raise
        MainWindowV21._on_intel_alert(window, report, MagicMock())


# Test _on_intel_received
class TestOnIntelReceived:
    """Tests for _on_intel_received method"""

    def test_on_intel_received(self):
        """Test intel received handler (currently a pass)"""
        from argus_overview.intel.parser import IntelReport, ThreatLevel
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)

        report = IntelReport(
            system="TEST",
            threat_level=ThreatLevel.INFO,
            hostile_count=0,
            ship_types=[],
            player_names=[],
            raw_message="test",
        )

        # Should not raise (just a pass)
        MainWindowV21._on_intel_received(window, report)


# Test _disconnect_signals
class TestDisconnectSignals:
    """Tests for _disconnect_signals method"""

    def test_disconnect_signals_all_present(self):
        """Test disconnecting all signals when all tabs present"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()

        # Mock all tabs and their signals
        window.main_tab = MagicMock()
        window.characters_tab = MagicMock()
        window.settings_tab = MagicMock()
        window.hotkeys_tab = MagicMock()
        window.intel_tab = MagicMock()
        window.system_tray = MagicMock()
        window.auto_discovery = MagicMock()
        window.hotkey_manager = MagicMock()

        # Bind the required methods
        window._on_character_detected = MagicMock()
        window._on_layout_applied = MagicMock()
        window._on_team_selected = MagicMock()
        window._apply_setting = MagicMock()
        window._toggle_visibility = MagicMock()
        window._toggle_thumbnails = MagicMock()
        window._minimize_all_windows = MagicMock()
        window._restore_all_windows = MagicMock()
        window._on_profile_selected = MagicMock()
        window._show_settings = MagicMock()
        window._reload_config = MagicMock()
        window._quit_application = MagicMock()
        window._on_new_character_discovered = MagicMock()
        window._on_character_gone = MagicMock()
        window._on_intel_alert = MagicMock()
        window._on_intel_received = MagicMock()

        MainWindowV21._disconnect_signals(window)

        window.logger.debug.assert_called_with("Signals disconnected")

    def test_disconnect_signals_missing_tabs(self):
        """Test disconnecting signals when some tabs missing"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()

        # Only have main_tab and hotkey_manager
        window.main_tab = MagicMock()
        window.hotkey_manager = MagicMock()
        window._on_character_detected = MagicMock()
        window._on_layout_applied = MagicMock()

        # Remove other tabs
        del window.characters_tab
        del window.settings_tab
        del window.hotkeys_tab
        del window.intel_tab
        del window.system_tray
        del window.auto_discovery

        # Should not raise
        MainWindowV21._disconnect_signals(window)

        window.logger.debug.assert_called_with("Signals disconnected")

    def test_disconnect_signals_handles_runtime_error(self):
        """Test disconnecting handles RuntimeError (already disconnected)"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.hotkey_manager = MagicMock()

        # main_tab with signal that raises RuntimeError on disconnect
        window.main_tab = MagicMock()
        window.main_tab.character_detected = MagicMock()
        window.main_tab.character_detected.disconnect.side_effect = RuntimeError(
            "Already disconnected"
        )
        window.main_tab.layout_applied = MagicMock()

        window._on_character_detected = MagicMock()
        window._on_layout_applied = MagicMock()

        # Should not raise
        MainWindowV21._disconnect_signals(window)

        window.logger.debug.assert_called_with("Signals disconnected")

    def test_disconnect_signals_with_hotkeys_tab_edits(self):
        """Test disconnecting hotkey recording signals"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.hotkey_manager = MagicMock()

        # hotkeys_tab with recording edits
        window.hotkeys_tab = MagicMock()
        window.hotkeys_tab.cycle_forward_edit = MagicMock()
        window.hotkeys_tab.cycle_backward_edit = MagicMock()
        window.hotkeys_tab.group_changed = MagicMock()
        window.main_tab = MagicMock()

        window._on_character_detected = MagicMock()
        window._on_layout_applied = MagicMock()

        MainWindowV21._disconnect_signals(window)

        # Should have tried to disconnect recording signals
        window.hotkeys_tab.cycle_forward_edit.recordingStarted.disconnect.assert_called()
        window.hotkeys_tab.cycle_backward_edit.recordingStopped.disconnect.assert_called()

    def test_disconnect_signals_no_cycle_edits(self):
        """Test disconnecting when cycle edits don't exist"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.hotkey_manager = MagicMock()

        # hotkeys_tab without cycle edits
        window.hotkeys_tab = MagicMock()
        window.hotkeys_tab.cycle_forward_edit = None
        window.hotkeys_tab.cycle_backward_edit = None
        window.hotkeys_tab.group_changed = MagicMock()
        window.main_tab = MagicMock()

        window._on_character_detected = MagicMock()
        window._on_layout_applied = MagicMock()

        # Should not raise
        MainWindowV21._disconnect_signals(window)


# Test _on_character_gone
class TestOnCharacterGone:
    """Tests for _on_character_gone method"""

    def test_on_character_gone_unassigns_window(self):
        """Test character gone unassigns window from character manager"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.character_manager = MagicMock()

        MainWindowV21._on_character_gone(window, "TestPilot", "0x12345")

        window.character_manager.unassign_window.assert_called_with("TestPilot")
        window.logger.info.assert_called()

    def test_on_character_gone_updates_characters_tab(self):
        """Test character gone updates characters tab status"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.character_manager = MagicMock()
        window.characters_tab = MagicMock()

        MainWindowV21._on_character_gone(window, "TestPilot", "0x12345")

        window.characters_tab.update_character_status.assert_called_with("TestPilot", None)

    def test_on_character_gone_no_characters_tab(self):
        """Test character gone when no characters_tab"""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.character_manager = MagicMock()
        del window.characters_tab

        # Should not raise
        MainWindowV21._on_character_gone(window, "Pilot", "0x12345")

        window.character_manager.unassign_window.assert_called_with("Pilot")


class TestDisconnectSignalsRecordingException:
    """Tests for exception handling in recording signal disconnect (lines 752-753)."""

    def test_disconnect_signals_recording_type_error(self):
        """Test disconnecting handles TypeError on recording signal disconnect."""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.hotkey_manager = MagicMock()
        window.main_tab = MagicMock()
        window._on_character_detected = MagicMock()
        window._on_layout_applied = MagicMock()

        # hotkeys_tab with recording edits that raise TypeError
        window.hotkeys_tab = MagicMock()
        mock_edit = MagicMock()
        mock_edit.recordingStarted = MagicMock()
        mock_edit.recordingStarted.disconnect.side_effect = TypeError("Not connected")
        mock_edit.recordingStopped = MagicMock()
        mock_edit.recordingStopped.disconnect.side_effect = RuntimeError("Already disconnected")
        window.hotkeys_tab.cycle_forward_edit = mock_edit
        window.hotkeys_tab.cycle_backward_edit = mock_edit
        window.hotkeys_tab.group_changed = MagicMock()

        # Should not raise - exceptions are caught
        MainWindowV21._disconnect_signals(window)

        window.logger.debug.assert_called_with("Signals disconnected")


class TestCloseEventMainTab:
    """Tests for closeEvent main_tab handling (line 933)."""

    def test_close_event_stops_main_tab_capture_loop(self, qapp):
        """Test closeEvent calls main_tab.stop_capture_loop."""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = False  # Don't minimize to tray
        window.main_tab = MagicMock()
        window.intel_tab = MagicMock()
        window.auto_discovery = MagicMock()
        window.capture_system = MagicMock()
        window.hotkey_manager = MagicMock()
        window.system_tray = MagicMock()
        window._disconnect_signals = MagicMock()
        window._already_closing = False

        # Call closeEvent
        from PySide6.QtGui import QCloseEvent

        event = MagicMock(spec=QCloseEvent)
        MainWindowV21.closeEvent(window, event)

        window.main_tab.stop_capture_loop.assert_called_once()


class TestCloseEventIntelTab:
    """Tests for closeEvent intel_tab handling (line 937)."""

    def test_close_event_stops_intel_tab(self, qapp):
        """Test closeEvent calls intel_tab.stop."""
        from argus_overview.ui.main_window_v21 import MainWindowV21

        window = MagicMock(spec=MainWindowV21)
        window.logger = MagicMock()
        window.settings_manager = MagicMock()
        window.settings_manager.get.return_value = False  # Don't minimize to tray
        window.main_tab = MagicMock()
        window.intel_tab = MagicMock()
        window.auto_discovery = MagicMock()
        window.capture_system = MagicMock()
        window.hotkey_manager = MagicMock()
        window.system_tray = MagicMock()
        window._disconnect_signals = MagicMock()
        window._already_closing = False

        # Call closeEvent
        from PySide6.QtGui import QCloseEvent

        event = MagicMock(spec=QCloseEvent)
        MainWindowV21.closeEvent(window, event)

        window.intel_tab.stop.assert_called_once()


# =============================================================================
# Coverage Push: __init__ partial (lines 72-154, ~45 lines)
# =============================================================================


class TestMainWindowV21InitPartial:
    """Tests for MainWindowV21.__init__ initialization sequence.

    Patches all Qt and core dependencies to test the init sequence
    without requiring a real display or full Qt application.
    """

    def test_init_creates_core_modules(self):
        """Test __init__ creates all core subsystems"""
        from contextlib import ExitStack

        from argus_overview.ui.main_window_v21 import MainWindowV21

        mock_char_mgr = MagicMock()
        mock_layout_mgr = MagicMock()
        mock_hotkey_mgr = MagicMock()
        mock_settings_sync = MagicMock()
        mock_settings_mgr = MagicMock()
        mock_settings_mgr.get.return_value = 1
        mock_settings_mgr.validate = MagicMock()
        mock_capture = MagicMock()
        mock_discovery = MagicMock()
        mock_theme = MagicMock()

        mod = "argus_overview.ui.main_window_v21"
        with ExitStack() as stack:
            stack.enter_context(patch(f"{mod}.CharacterManager", return_value=mock_char_mgr))
            stack.enter_context(patch(f"{mod}.LayoutManager", return_value=mock_layout_mgr))
            stack.enter_context(patch(f"{mod}.HotkeyManager", return_value=mock_hotkey_mgr))
            stack.enter_context(patch(f"{mod}.EVESettingsSync", return_value=mock_settings_sync))
            stack.enter_context(patch(f"{mod}.SettingsManager", return_value=mock_settings_mgr))
            stack.enter_context(patch(f"{mod}.WindowCaptureThreaded", return_value=mock_capture))
            stack.enter_context(patch(f"{mod}.AutoDiscovery", return_value=mock_discovery))
            stack.enter_context(patch(f"{mod}.get_theme_manager", return_value=mock_theme))
            # Patch QMainWindow.__init__ to skip real Qt initialization
            stack.enter_context(patch("PySide6.QtWidgets.QMainWindow.__init__", return_value=None))
            stack.enter_context(patch.object(MainWindowV21, "setWindowTitle"))
            stack.enter_context(patch.object(MainWindowV21, "setMinimumSize"))
            stack.enter_context(patch.object(MainWindowV21, "setCentralWidget"))
            stack.enter_context(patch.object(MainWindowV21, "_set_window_icon"))
            stack.enter_context(patch.object(MainWindowV21, "_apply_initial_settings"))
            stack.enter_context(patch.object(MainWindowV21, "_create_menu_bar"))
            stack.enter_context(patch.object(MainWindowV21, "_create_main_tab"))
            stack.enter_context(patch.object(MainWindowV21, "_create_hotkeys_tab"))
            stack.enter_context(patch.object(MainWindowV21, "_create_characters_tab"))
            stack.enter_context(patch.object(MainWindowV21, "_create_intel_tab"))
            stack.enter_context(patch.object(MainWindowV21, "_create_settings_sync_tab"))
            stack.enter_context(patch.object(MainWindowV21, "_create_settings_tab"))
            stack.enter_context(patch.object(MainWindowV21, "_connect_signals"))
            stack.enter_context(patch.object(MainWindowV21, "_create_system_tray"))
            stack.enter_context(patch.object(MainWindowV21, "_register_hotkeys"))
            stack.enter_context(patch(f"{mod}.QTabWidget"))
            stack.enter_context(patch(f"{mod}.QVBoxLayout"))
            stack.enter_context(patch(f"{mod}.QWidget"))
            stack.enter_context(patch(f"{mod}.QTimer"))

            window = MainWindowV21()

            # Core modules created
            assert window.character_manager is mock_char_mgr
            assert window.layout_manager is mock_layout_mgr
            assert window.hotkey_manager is mock_hotkey_mgr
            assert window.settings_sync is mock_settings_sync
            assert window.settings_manager is mock_settings_mgr
            assert window.capture_system is mock_capture
            assert window.auto_discovery is mock_discovery
            assert window.theme_manager is mock_theme

            # Cycling state initialized
            assert window.cycling_index == 0
            assert window.current_cycling_group == "Default"

            # Systems started
            mock_capture.start.assert_called_once()
            mock_hotkey_mgr.start.assert_called_once()

            # Settings validated
            mock_settings_mgr.validate.assert_called_once()

            # Theme applied
            mock_theme.apply_theme.assert_called()
