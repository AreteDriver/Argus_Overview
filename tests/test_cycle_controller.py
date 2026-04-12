"""Unit tests for centralized window activation and cycling behavior."""

from unittest.mock import MagicMock

from argus_overview.core.cycle_controller import CycleController


def create_controller():
    """Build a controller with mocked window operations and settings."""
    window_ops = MagicMock()
    window_ops._window_mgr = MagicMock()
    window_ops._window_mgr.is_valid_window_id.return_value = True
    window_ops.activate_window.return_value = True
    window_ops.minimize_window.return_value = True

    settings_manager = MagicMock()
    settings_manager.get.return_value = False
    settings_manager.get_last_activated_window.return_value = None

    return CycleController(window_ops, settings_manager), window_ops, settings_manager


class TestActivateWindow:
    def test_activate_window_activates_valid_window(self):
        controller, window_ops, settings = create_controller()

        result = controller.activate_window("0x123")

        assert result is True
        settings.set_last_activated_window.assert_called_once_with("0x123")
        window_ops.activate_window.assert_called_once_with("0x123")
        window_ops.minimize_window.assert_not_called()

    def test_activate_window_rejects_invalid_window_id(self):
        controller, window_ops, settings = create_controller()
        window_ops._window_mgr.is_valid_window_id.return_value = False

        result = controller.activate_window("bad")

        assert result is False
        settings.set_last_activated_window.assert_not_called()
        window_ops.activate_window.assert_not_called()

    def test_activate_window_auto_minimizes_previous_window(self):
        controller, window_ops, settings = create_controller()

        def get_side_effect(key, default=None):
            if key == "performance.auto_minimize_inactive":
                return True
            return default

        settings.get.side_effect = get_side_effect
        settings.get_last_activated_window.return_value = "0xOLD"

        result = controller.activate_window("0xNEW")

        assert result is True
        window_ops.minimize_window.assert_called_once_with("0xOLD")
        settings.set_last_activated_window.assert_called_once_with("0xNEW")
        window_ops.activate_window.assert_called_once_with("0xNEW")

    def test_activate_window_handles_activation_exception(self):
        controller, window_ops, settings = create_controller()
        window_ops.activate_window.side_effect = OSError("display unavailable")

        result = controller.activate_window("0x123")

        assert result is False
        settings.set_last_activated_window.assert_called_once_with("0x123")


class TestActivateCharacter:
    def test_activate_character_looks_up_and_activates_window(self):
        controller, window_ops, settings = create_controller()

        result = controller.activate_character("Pilot", lambda name: "0xABC")

        assert result is True
        settings.set_last_activated_window.assert_called_once_with("0xABC")
        window_ops.activate_window.assert_called_once_with("0xABC")

    def test_activate_character_returns_false_when_lookup_fails(self):
        controller, window_ops, settings = create_controller()

        result = controller.activate_character("Missing", lambda name: None)

        assert result is False
        settings.set_last_activated_window.assert_not_called()
        window_ops.activate_window.assert_not_called()


class TestCycle:
    def test_cycle_advances_to_next_live_member(self):
        controller, window_ops, settings = create_controller()
        members = ["Alpha", "Bravo", "Charlie"]
        lookup = {"Bravo": None, "Charlie": "0xCCC"}

        index, character = controller.cycle(
            members=members,
            current_index=0,
            direction=1,
            window_lookup=lambda name: lookup.get(name),
        )

        assert index == 2
        assert character == "Charlie"
        settings.set_last_activated_window.assert_called_once_with("0xCCC")
        window_ops.activate_window.assert_called_once_with("0xCCC")

    def test_cycle_returns_current_index_when_no_live_windows_exist(self):
        controller, window_ops, settings = create_controller()

        index, character = controller.cycle(
            members=["Alpha", "Bravo"],
            current_index=1,
            direction=1,
            window_lookup=lambda name: None,
        )

        assert index == 1
        assert character is None
        settings.set_last_activated_window.assert_not_called()
        window_ops.activate_window.assert_not_called()
