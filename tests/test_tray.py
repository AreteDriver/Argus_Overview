"""
Unit tests for the System Tray module
Tests SystemTray class functionality
"""
from unittest.mock import MagicMock, patch


class TestSystemTrayInit:
    """Tests for SystemTray initialization"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_init_creates_tray_icon(self, mock_qobject_init, mock_qmenu,
                                     mock_tray_icon, mock_menu_builder,
                                     mock_registry):
        """Test that init creates tray icon"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()

                mock_tray_icon.assert_called()
                assert tray.tray_icon is not None

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_init_sets_tooltip(self, mock_qobject_init, mock_qmenu,
                                mock_tray_icon_class, mock_menu_builder,
                                mock_registry):
        """Test that init sets correct tooltip"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_tray_icon = MagicMock()
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                SystemTray()

                mock_tray_icon.setToolTip.assert_called_once()
                tooltip_arg = mock_tray_icon.setToolTip.call_args[0][0]
                assert "Argus Overview" in tooltip_arg

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_init_state(self, mock_qobject_init, mock_qmenu,
                        mock_tray_icon, mock_menu_builder, mock_registry):
        """Test initial state values"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()

                assert tray._visible is True
                assert tray._profiles == []
                assert tray._current_profile is None


class TestCreateIcon:
    """Tests for _create_icon method"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_create_icon_returns_qicon(self, mock_qobject_init, mock_qmenu,
                                        mock_tray_icon, mock_menu_builder,
                                        mock_registry):
        """Test that _create_icon returns a QIcon"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                SystemTray()

                # setIcon should have been called with the mocked icon
                mock_tray_icon.return_value.setIcon.assert_called()

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_create_icon_method_exists(self, mock_qobject_init, mock_qmenu,
                                        mock_tray_icon, mock_menu_builder,
                                        mock_registry):
        """Test that _create_icon method exists"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                SystemTray()

                # Method should exist
                assert hasattr(SystemTray, '_create_icon')
                assert callable(SystemTray._create_icon)


class TestShowHide:
    """Tests for show/hide methods"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_show(self, mock_qobject_init, mock_qmenu, mock_tray_icon_class,
                  mock_menu_builder, mock_registry):
        """Test show method"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_tray_icon = MagicMock()
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()
                tray.show()

                mock_tray_icon.show.assert_called_once()

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_hide(self, mock_qobject_init, mock_qmenu, mock_tray_icon_class,
                  mock_menu_builder, mock_registry):
        """Test hide method"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_tray_icon = MagicMock()
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()
                tray.hide()

                mock_tray_icon.hide.assert_called_once()

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_is_visible(self, mock_qobject_init, mock_qmenu, mock_tray_icon_class,
                        mock_menu_builder, mock_registry):
        """Test is_visible method"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_tray_icon = MagicMock()
        mock_tray_icon.isVisible.return_value = True
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()
                result = tray.is_visible()

                assert result is True
                mock_tray_icon.isVisible.assert_called_once()


class TestProfiles:
    """Tests for profile management"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_set_profiles(self, mock_qobject_init, mock_qmenu,
                          mock_tray_icon, mock_menu_builder, mock_registry):
        """Test set_profiles method"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu') as mock_setup:
                tray = SystemTray()
                mock_setup.reset_mock()

                profiles = ["Profile1", "Profile2", "Profile3"]
                tray.set_profiles(profiles, current="Profile2")

                assert tray._profiles == profiles
                assert tray._current_profile == "Profile2"
                mock_setup.assert_called_once()

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_set_current_profile(self, mock_qobject_init, mock_qmenu,
                                  mock_tray_icon, mock_menu_builder, mock_registry):
        """Test set_current_profile method"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu') as mock_setup:
                tray = SystemTray()
                mock_setup.reset_mock()

                tray.set_current_profile("NewProfile")

                assert tray._current_profile == "NewProfile"
                mock_setup.assert_called_once()


class TestNotifications:
    """Tests for notification functionality"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_show_notification_when_supported(self, mock_qobject_init, mock_qmenu,
                                               mock_tray_icon_class, mock_menu_builder,
                                               mock_registry):
        """Test show_notification when messages are supported"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_tray_icon = MagicMock()
        mock_tray_icon.supportsMessages.return_value = True
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()
                tray.show_notification("Title", "Message")

                mock_tray_icon.showMessage.assert_called_once()

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_show_notification_when_not_supported(self, mock_qobject_init, mock_qmenu,
                                                   mock_tray_icon_class, mock_menu_builder,
                                                   mock_registry):
        """Test show_notification when messages are not supported"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_tray_icon = MagicMock()
        mock_tray_icon.supportsMessages.return_value = False
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()
                tray.show_notification("Title", "Message")

                mock_tray_icon.showMessage.assert_not_called()


class TestTooltip:
    """Tests for tooltip functionality"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_update_tooltip(self, mock_qobject_init, mock_qmenu,
                            mock_tray_icon_class, mock_menu_builder, mock_registry):
        """Test update_tooltip method"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_tray_icon = MagicMock()
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()
                mock_tray_icon.setToolTip.reset_mock()

                tray.update_tooltip("New Tooltip Text")

                mock_tray_icon.setToolTip.assert_called_once_with("New Tooltip Text")


class TestTrayActivation:
    """Tests for tray icon activation handling"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_double_click_emits_show_hide(self, mock_qobject_init, mock_qmenu,
                                           mock_tray_icon_class, mock_menu_builder,
                                           mock_registry):
        """Test double-click on tray emits show_hide_requested"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_tray_icon = MagicMock()
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import QSystemTrayIcon, SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()

                # Mock the signal emit
                tray.show_hide_requested = MagicMock()

                # Simulate double-click
                tray._on_tray_activated(QSystemTrayIcon.ActivationReason.DoubleClick)

                tray.show_hide_requested.emit.assert_called_once()

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_single_click_no_emit(self, mock_qobject_init, mock_qmenu,
                                   mock_tray_icon_class, mock_menu_builder,
                                   mock_registry):
        """Test single-click does not emit (context menu handles it)"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_tray_icon = MagicMock()
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import QSystemTrayIcon, SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()

                tray.show_hide_requested = MagicMock()

                # Simulate single-click (Trigger)
                tray._on_tray_activated(QSystemTrayIcon.ActivationReason.Trigger)

                tray.show_hide_requested.emit.assert_not_called()


class TestSignals:
    """Tests for SystemTray signals"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_signals_exist(self, mock_qobject_init, mock_qmenu,
                           mock_tray_icon, mock_menu_builder, mock_registry):
        """Test that all expected signals exist"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()

                # Check all expected signals exist
                assert hasattr(tray, 'show_hide_requested')
                assert hasattr(tray, 'toggle_thumbnails_requested')
                assert hasattr(tray, 'minimize_all_requested')
                assert hasattr(tray, 'restore_all_requested')
                assert hasattr(tray, 'profile_selected')
                assert hasattr(tray, 'settings_requested')
                assert hasattr(tray, 'reload_config_requested')
                assert hasattr(tray, 'quit_requested')


class TestProfileSelection:
    """Tests for profile selection handling"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_on_profile_selected(self, mock_qobject_init, mock_qmenu,
                                  mock_tray_icon, mock_menu_builder, mock_registry):
        """Test _on_profile_selected emits signal"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            with patch.object(SystemTray, '_setup_menu'):
                tray = SystemTray()

                tray.profile_selected = MagicMock()

                tray._on_profile_selected("TestProfile")

                tray.profile_selected.emit.assert_called_once_with("TestProfile")


class TestMenuSetup:
    """Tests for menu setup"""

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_setup_menu_uses_menu_builder(self, mock_qobject_init, mock_qmenu,
                                           mock_tray_icon_class, mock_menu_builder_class,
                                           mock_registry):
        """Test _setup_menu uses MenuBuilder"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_menu_builder = MagicMock()
        mock_menu_builder.build_tray_menu.return_value = MagicMock()
        mock_menu_builder_class.return_value = mock_menu_builder

        mock_tray_icon = MagicMock()
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            SystemTray()

            mock_menu_builder.build_tray_menu.assert_called()
            mock_tray_icon.setContextMenu.assert_called()

    @patch('eve_overview_pro.ui.tray.ActionRegistry')
    @patch('eve_overview_pro.ui.tray.MenuBuilder')
    @patch('eve_overview_pro.ui.tray.QSystemTrayIcon')
    @patch('eve_overview_pro.ui.tray.QMenu')
    @patch('eve_overview_pro.ui.tray.QObject.__init__')
    def test_setup_menu_passes_handlers(self, mock_qobject_init, mock_qmenu,
                                         mock_tray_icon_class, mock_menu_builder_class,
                                         mock_registry):
        """Test _setup_menu passes correct handlers"""
        mock_qobject_init.return_value = None
        mock_registry_instance = MagicMock()
        mock_registry.get_instance.return_value = mock_registry_instance

        mock_menu_builder = MagicMock()
        mock_menu_builder.build_tray_menu.return_value = MagicMock()
        mock_menu_builder_class.return_value = mock_menu_builder

        mock_tray_icon = MagicMock()
        mock_tray_icon_class.return_value = mock_tray_icon

        from eve_overview_pro.ui.tray import SystemTray

        with patch.object(SystemTray, '_create_icon', return_value=MagicMock()):
            SystemTray()

            # Verify build_tray_menu was called with handlers
            call_kwargs = mock_menu_builder.build_tray_menu.call_args[1]
            assert 'handlers' in call_kwargs
            handlers = call_kwargs['handlers']

            # Check expected handler keys
            assert 'show_hide' in handlers
            assert 'toggle_thumbnails' in handlers
            assert 'minimize_all' in handlers
            assert 'restore_all' in handlers
            assert 'settings' in handlers
            assert 'reload_config' in handlers
            assert 'quit' in handlers
