"""
Unit tests for the HotkeyManager module.

Tests cover:
- Hotkey registration/unregistration
- Single key vs combo detection
- Key combo parsing
- Key combo formatting
- Modifier tracking
"""
import pytest
from unittest.mock import MagicMock, patch

from eve_overview_pro.core.hotkey_manager import HotkeyManager


class TestHotkeyManagerInit:
    """Tests for HotkeyManager initialization"""

    def test_initial_state(self):
        """Manager starts with correct state"""
        manager = HotkeyManager()

        assert manager.hotkeys == {}
        assert manager.single_key_hotkeys == {}
        assert manager.combo_hotkeys == {}
        assert manager.pressed_modifiers == set()
        assert manager.combo_listener is None
        assert manager.key_listener is None


class TestIsSingleKey:
    """Tests for _is_single_key detection"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        return HotkeyManager()

    def test_single_letter(self, manager):
        """Single letter is single key"""
        assert manager._is_single_key("a") is True
        assert manager._is_single_key("<a>") is True

    def test_single_number(self, manager):
        """Single number is single key"""
        assert manager._is_single_key("1") is True
        assert manager._is_single_key("<1>") is True

    def test_function_key(self, manager):
        """Function key alone is single key"""
        assert manager._is_single_key("<f1>") is True
        assert manager._is_single_key("<F12>") is True

    def test_combo_with_ctrl(self, manager):
        """Ctrl+key is combo"""
        assert manager._is_single_key("<ctrl>+a") is False
        assert manager._is_single_key("<ctrl>+<shift>+a") is False

    def test_combo_with_alt(self, manager):
        """Alt+key is combo"""
        assert manager._is_single_key("<alt>+x") is False

    def test_combo_with_shift(self, manager):
        """Shift+key is combo"""
        assert manager._is_single_key("<shift>+<f1>") is False

    def test_modifier_alone_is_not_single(self, manager):
        """Modifier keys alone are not single keys"""
        assert manager._is_single_key("<ctrl>") is False
        assert manager._is_single_key("<alt>") is False
        assert manager._is_single_key("<shift>") is False


class TestRegisterHotkey:
    """Tests for hotkey registration"""

    @pytest.fixture
    def manager(self):
        """Create manager with mocked listeners"""
        m = HotkeyManager()
        m._restart_listeners = MagicMock()  # Don't actually start listeners
        return m

    def test_register_single_key(self, manager):
        """Can register single key hotkey"""
        callback = MagicMock()
        result = manager.register_hotkey("test", "a", callback)

        assert result is True
        assert "test" in manager.hotkeys
        assert "a" in manager.single_key_hotkeys
        assert len(manager.combo_hotkeys) == 0

    def test_register_combo(self, manager):
        """Can register combo hotkey"""
        callback = MagicMock()
        result = manager.register_hotkey("test", "<ctrl>+a", callback)

        assert result is True
        assert "test" in manager.hotkeys
        assert "<ctrl>+a" in manager.combo_hotkeys
        assert len(manager.single_key_hotkeys) == 0

    def test_register_stores_callback(self, manager):
        """Registration stores callback"""
        callback = MagicMock()
        manager.register_hotkey("test", "x", callback)

        assert manager.hotkeys["test"]["callback"] == callback
        assert manager.single_key_hotkeys["x"]["callback"] == callback

    def test_register_restarts_listeners(self, manager):
        """Registration restarts listeners"""
        callback = MagicMock()
        manager.register_hotkey("test", "a", callback)

        manager._restart_listeners.assert_called()

    def test_register_multiple_hotkeys(self, manager):
        """Can register multiple hotkeys"""
        manager.register_hotkey("hk1", "a", MagicMock())
        manager.register_hotkey("hk2", "<ctrl>+b", MagicMock())
        manager.register_hotkey("hk3", "c", MagicMock())

        assert len(manager.hotkeys) == 3
        assert len(manager.single_key_hotkeys) == 2
        assert len(manager.combo_hotkeys) == 1


class TestUnregisterHotkey:
    """Tests for hotkey unregistration"""

    @pytest.fixture
    def manager(self):
        """Create manager with registered hotkeys"""
        m = HotkeyManager()
        m._restart_listeners = MagicMock()
        m.register_hotkey("single", "a", MagicMock())
        m.register_hotkey("combo", "<ctrl>+b", MagicMock())
        return m

    def test_unregister_single_key(self, manager):
        """Can unregister single key hotkey"""
        result = manager.unregister_hotkey("single")

        assert result is True
        assert "single" not in manager.hotkeys
        assert "a" not in manager.single_key_hotkeys

    def test_unregister_combo(self, manager):
        """Can unregister combo hotkey"""
        result = manager.unregister_hotkey("combo")

        assert result is True
        assert "combo" not in manager.hotkeys
        assert "<ctrl>+b" not in manager.combo_hotkeys

    def test_unregister_nonexistent(self, manager):
        """Returns False for nonexistent hotkey"""
        result = manager.unregister_hotkey("nonexistent")
        assert result is False

    def test_unregister_restarts_listeners(self, manager):
        """Unregistration restarts listeners"""
        manager._restart_listeners.reset_mock()
        manager.unregister_hotkey("single")
        manager._restart_listeners.assert_called()


class TestParseKeyCombo:
    """Tests for parse_key_combo method"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        return HotkeyManager()

    def test_parse_ctrl_a(self, manager):
        """Parses Ctrl+A"""
        result = manager.parse_key_combo("ctrl+a")
        assert result == "<ctrl>+a"

    def test_parse_ctrl_shift_f1(self, manager):
        """Parses Ctrl+Shift+F1"""
        result = manager.parse_key_combo("ctrl+shift+f1")
        assert result == "<ctrl>+<shift>+<f1>"

    def test_parse_alt_x(self, manager):
        """Parses Alt+X"""
        result = manager.parse_key_combo("alt+x")
        assert result == "<alt>+x"

    def test_parse_super(self, manager):
        """Parses Super/Win key"""
        assert manager.parse_key_combo("super+a") == "<cmd>+a"
        assert manager.parse_key_combo("win+a") == "<cmd>+a"

    def test_parse_control_alias(self, manager):
        """Control is alias for Ctrl"""
        result = manager.parse_key_combo("control+a")
        assert result == "<ctrl>+a"

    def test_parse_with_spaces(self, manager):
        """Handles spaces in combo string"""
        result = manager.parse_key_combo("ctrl + shift + a")
        assert result == "<ctrl>+<shift>+a"

    def test_parse_single_key(self, manager):
        """Parses single key"""
        result = manager.parse_key_combo("a")
        assert result == "a"


class TestFormatKeyCombo:
    """Tests for format_key_combo method"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        return HotkeyManager()

    def test_format_ctrl_a(self, manager):
        """Formats <ctrl>+a"""
        result = manager.format_key_combo("<ctrl>+a")
        assert result == "Ctrl+A"

    def test_format_ctrl_shift_f1(self, manager):
        """Formats <ctrl>+<shift>+<f1>"""
        result = manager.format_key_combo("<ctrl>+<shift>+<f1>")
        assert result == "Ctrl+Shift+F1"

    def test_format_cmd_to_super(self, manager):
        """Cmd becomes Super"""
        result = manager.format_key_combo("<cmd>+a")
        assert result == "Super+A"


class TestModifierTracking:
    """Tests for modifier key tracking"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        return HotkeyManager()

    def test_initial_no_modifiers(self, manager):
        """Starts with no modifiers pressed"""
        assert len(manager.pressed_modifiers) == 0

    def test_on_key_release_clears_ctrl(self, manager):
        """Releasing ctrl clears modifier"""
        manager.pressed_modifiers.add('ctrl')

        mock_key = MagicMock()
        mock_key.name = 'ctrl_l'

        manager._on_key_release(mock_key)

        assert 'ctrl' not in manager.pressed_modifiers

    def test_on_key_release_clears_alt(self, manager):
        """Releasing alt clears modifier"""
        manager.pressed_modifiers.add('alt')

        mock_key = MagicMock()
        mock_key.name = 'alt_l'

        manager._on_key_release(mock_key)

        assert 'alt' not in manager.pressed_modifiers

    def test_on_key_release_clears_shift(self, manager):
        """Releasing shift clears modifier"""
        manager.pressed_modifiers.add('shift')

        mock_key = MagicMock()
        mock_key.name = 'shift_l'

        manager._on_key_release(mock_key)

        assert 'shift' not in manager.pressed_modifiers


class TestOnKeyPress:
    """Tests for key press handling"""

    @pytest.fixture
    def manager(self):
        """Create manager with registered single-key hotkey"""
        m = HotkeyManager()
        m._restart_listeners = MagicMock()
        m.callback = MagicMock()
        m.register_hotkey("test", "x", m.callback)
        return m

    def test_triggers_registered_hotkey(self, manager):
        """Triggers callback for registered key"""
        mock_key = MagicMock()
        mock_key.char = 'x'
        del mock_key.name  # Remove name attribute

        manager._on_key_press(mock_key)

        manager.callback.assert_called_once()

    def test_ignores_unregistered_key(self, manager):
        """Ignores unregistered keys"""
        mock_key = MagicMock()
        mock_key.char = 'y'
        del mock_key.name

        manager._on_key_press(mock_key)

        manager.callback.assert_not_called()

    def test_blocked_when_modifier_pressed(self, manager):
        """Single key blocked when modifier held"""
        manager.pressed_modifiers.add('ctrl')

        mock_key = MagicMock()
        mock_key.char = 'x'
        del mock_key.name

        manager._on_key_press(mock_key)

        manager.callback.assert_not_called()

    def test_tracks_ctrl_press(self, manager):
        """Tracks ctrl key press"""
        mock_key = MagicMock()
        mock_key.name = 'ctrl_l'

        manager._on_key_press(mock_key)

        assert 'ctrl' in manager.pressed_modifiers


class TestStartStop:
    """Tests for start/stop methods"""

    def test_start_calls_restart(self):
        """Start calls _restart_listeners"""
        manager = HotkeyManager()
        manager._restart_listeners = MagicMock()

        manager.start()

        manager._restart_listeners.assert_called_once()

    def test_stop_clears_listeners(self):
        """Stop clears listeners"""
        manager = HotkeyManager()
        manager.combo_listener = MagicMock()
        manager.key_listener = MagicMock()

        manager.stop()

        assert manager.combo_listener is None
        assert manager.key_listener is None

    def test_stop_handles_listener_exception(self):
        """Stop handles exception from listener.stop()"""
        manager = HotkeyManager()
        mock_combo = MagicMock()
        mock_combo.stop.side_effect = RuntimeError("Stop failed")
        manager.combo_listener = mock_combo

        mock_key = MagicMock()
        mock_key.stop.side_effect = RuntimeError("Stop failed")
        manager.key_listener = mock_key

        # Should not raise - just silently catch exception
        manager.stop()

        # stop() was called even though it raised
        mock_combo.stop.assert_called_once()
        mock_key.stop.assert_called_once()


class TestRestartListeners:
    """Tests for _restart_listeners method"""

    def test_stops_existing_combo_listener(self):
        """Stops existing combo listener before restart"""
        manager = HotkeyManager()
        mock_listener = MagicMock()
        manager.combo_listener = mock_listener

        with patch.object(manager, '_start_combo_listener'):
            with patch.object(manager, '_start_key_listener'):
                manager._restart_listeners()

        mock_listener.stop.assert_called_once()
        assert manager.combo_listener is None or manager.combo_listener != mock_listener

    def test_stops_existing_key_listener(self):
        """Stops existing key listener before restart"""
        manager = HotkeyManager()
        mock_listener = MagicMock()
        manager.key_listener = mock_listener

        with patch.object(manager, '_start_combo_listener'):
            with patch.object(manager, '_start_key_listener'):
                manager._restart_listeners()

        mock_listener.stop.assert_called_once()

    def test_handles_stop_exception(self):
        """Handles exception when stopping listeners"""
        manager = HotkeyManager()
        mock_listener = MagicMock()
        mock_listener.stop.side_effect = RuntimeError("Stop failed")
        manager.combo_listener = mock_listener

        with patch.object(manager, '_start_combo_listener'):
            with patch.object(manager, '_start_key_listener'):
                # Should not raise
                manager._restart_listeners()

    def test_starts_combo_listener_when_combos_exist(self):
        """Starts combo listener when combo hotkeys registered"""
        manager = HotkeyManager()
        manager.combo_hotkeys = {"<ctrl>+a": {"name": "test", "callback": MagicMock()}}

        with patch.object(manager, '_start_combo_listener') as mock_start:
            with patch.object(manager, '_start_key_listener'):
                manager._restart_listeners()

        mock_start.assert_called_once()

    def test_starts_key_listener_when_single_keys_exist(self):
        """Starts key listener when single-key hotkeys registered"""
        manager = HotkeyManager()
        manager.single_key_hotkeys = {"a": {"name": "test", "callback": MagicMock()}}

        with patch.object(manager, '_start_combo_listener'):
            with patch.object(manager, '_start_key_listener') as mock_start:
                manager._restart_listeners()

        mock_start.assert_called_once()


class TestStartComboListener:
    """Tests for _start_combo_listener method"""

    def test_creates_global_hotkeys(self):
        """Creates GlobalHotKeys with registered combos"""
        manager = HotkeyManager()
        callback = MagicMock()
        manager.combo_hotkeys = {"<ctrl>+a": {"name": "test", "callback": callback}}

        with patch('eve_overview_pro.core.hotkey_manager.keyboard.GlobalHotKeys') as mock_ghk:
            manager._start_combo_listener()

        mock_ghk.assert_called_once()
        # Verify the combo was passed
        call_args = mock_ghk.call_args[0][0]
        assert "<ctrl>+a" in call_args

    def test_handles_exception(self):
        """Handles exception when creating listener"""
        manager = HotkeyManager()
        manager.combo_hotkeys = {"<ctrl>+a": {"name": "test", "callback": MagicMock()}}

        with patch('eve_overview_pro.core.hotkey_manager.keyboard.GlobalHotKeys') as mock_ghk:
            mock_ghk.side_effect = RuntimeError("Failed")
            # Should not raise
            manager._start_combo_listener()


class TestStartKeyListener:
    """Tests for _start_key_listener method"""

    def test_creates_listener(self):
        """Creates keyboard Listener"""
        manager = HotkeyManager()

        with patch('eve_overview_pro.core.hotkey_manager.keyboard.Listener') as mock_listener:
            manager._start_key_listener()

        mock_listener.assert_called_once()

    def test_handles_exception(self):
        """Handles exception when creating listener"""
        manager = HotkeyManager()

        with patch('eve_overview_pro.core.hotkey_manager.keyboard.Listener') as mock_listener:
            mock_listener.side_effect = RuntimeError("Failed")
            # Should not raise
            manager._start_key_listener()


class TestOnKeyPressAdvanced:
    """Advanced tests for key press handling"""

    @pytest.fixture
    def manager(self):
        """Create manager with registered single-key hotkey"""
        m = HotkeyManager()
        m._restart_listeners = MagicMock()
        m.callback = MagicMock()
        m.register_hotkey("test", "x", m.callback)
        return m

    def test_tracks_alt_press(self, manager):
        """Tracks alt key press"""
        mock_key = MagicMock()
        mock_key.name = 'alt_l'

        manager._on_key_press(mock_key)

        assert 'alt' in manager.pressed_modifiers

    def test_tracks_alt_gr_press(self, manager):
        """Tracks alt_gr key press"""
        mock_key = MagicMock()
        mock_key.name = 'alt_gr'

        manager._on_key_press(mock_key)

        assert 'alt' in manager.pressed_modifiers

    def test_tracks_shift_press(self, manager):
        """Tracks shift key press"""
        mock_key = MagicMock()
        mock_key.name = 'shift_r'

        manager._on_key_press(mock_key)

        assert 'shift' in manager.pressed_modifiers

    def test_uses_key_name_when_no_char(self, manager):
        """Uses key.name when key.char is None"""
        manager.register_hotkey("enter", "enter", manager.callback)

        mock_key = MagicMock()
        mock_key.char = None
        mock_key.name = 'enter'

        manager._on_key_press(mock_key)

        assert manager.callback.call_count == 1

    def test_handles_key_without_char_or_name(self, manager):
        """Handles key with neither char nor name"""
        mock_key = MagicMock()
        mock_key.char = None
        mock_key.name = None

        # Should not raise
        manager._on_key_press(mock_key)
        manager.callback.assert_not_called()

    def test_handles_callback_exception(self, manager):
        """Handles exception from callback"""
        manager.callback.side_effect = RuntimeError("Callback failed")

        mock_key = MagicMock()
        mock_key.char = 'x'
        del mock_key.name

        # Should not raise
        manager._on_key_press(mock_key)

    def test_handles_key_processing_exception(self, manager):
        """Handles exception during key processing"""
        mock_key = MagicMock()
        # Create a key that will cause issues
        type(mock_key).char = property(lambda self: (_ for _ in ()).throw(RuntimeError()))

        # Should not raise
        manager._on_key_press(mock_key)


class TestOnKeyReleaseAdvanced:
    """Advanced tests for key release handling"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        return HotkeyManager()

    def test_handles_key_without_name(self, manager):
        """Handles key without name attribute"""
        mock_key = MagicMock(spec=[])  # No attributes

        # Should not raise
        manager._on_key_release(mock_key)

    def test_clears_ctrl_r(self, manager):
        """Clears ctrl on ctrl_r release"""
        manager.pressed_modifiers.add('ctrl')
        mock_key = MagicMock()
        mock_key.name = 'ctrl_r'

        manager._on_key_release(mock_key)

        assert 'ctrl' not in manager.pressed_modifiers

    def test_clears_alt_r(self, manager):
        """Clears alt on alt_r release"""
        manager.pressed_modifiers.add('alt')
        mock_key = MagicMock()
        mock_key.name = 'alt_r'

        manager._on_key_release(mock_key)

        assert 'alt' not in manager.pressed_modifiers

    def test_clears_alt_gr(self, manager):
        """Clears alt on alt_gr release"""
        manager.pressed_modifiers.add('alt')
        mock_key = MagicMock()
        mock_key.name = 'alt_gr'

        manager._on_key_release(mock_key)

        assert 'alt' not in manager.pressed_modifiers


class TestRegisterHotkeyErrors:
    """Tests for error handling in hotkey registration"""

    def test_register_returns_false_on_exception(self):
        """Returns False when registration fails"""
        manager = HotkeyManager()

        # Make _restart_listeners raise
        manager._restart_listeners = MagicMock(side_effect=RuntimeError("Failed"))

        result = manager.register_hotkey("test", "a", MagicMock())

        assert result is False


class TestParseKeyComboEdgeCases:
    """Edge case tests for parse_key_combo"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager"""
        return HotkeyManager()

    def test_parse_unknown_key(self, manager):
        """Parses unknown keys by wrapping in brackets"""
        result = manager.parse_key_combo("ctrl+escape")
        assert result == "<ctrl>+<escape>"

    def test_parse_special_key(self, manager):
        """Parses special keys"""
        result = manager.parse_key_combo("ctrl+space")
        assert result == "<ctrl>+<space>"

    def test_parse_cmd_key(self, manager):
        """Parses cmd key"""
        result = manager.parse_key_combo("cmd+a")
        assert result == "<cmd>+a"
