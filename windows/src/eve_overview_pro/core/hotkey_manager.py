"""Global hotkey management - supports both modifier combos and single keys"""
import logging
from typing import Callable, Dict, Optional, Set

from pynput import keyboard
from PySide6.QtCore import QObject, Signal


class HotkeyManager(QObject):
    """Manages global hotkeys - supports single keys and modifier combinations"""

    hotkey_triggered = Signal(str)

    def __init__(self):
        super().__init__()
        self.hotkeys: Dict[str, Dict] = {}
        self.combo_listener: Optional[keyboard.GlobalHotKeys] = None
        self.key_listener: Optional[keyboard.Listener] = None
        self.logger = logging.getLogger(__name__)

        # Track single-key hotkeys separately
        self.single_key_hotkeys: Dict[str, Dict] = {}  # key_char -> {name, callback}
        self.combo_hotkeys: Dict[str, Dict] = {}  # combo_string -> {name, callback}

        # Track currently pressed modifiers
        self.pressed_modifiers: Set[str] = set()

    def register_hotkey(self, name: str, key_combo: str, callback: Callable) -> bool:
        """Register a global hotkey"""
        try:
            self.hotkeys[name] = {'combo': key_combo, 'callback': callback}

            # Determine if single key or combo
            if self._is_single_key(key_combo):
                key_char = key_combo.strip('<>').lower()
                self.single_key_hotkeys[key_char] = {'name': name, 'callback': callback}
            else:
                self.combo_hotkeys[key_combo] = {'name': name, 'callback': callback}

            self._restart_listeners()
            self.logger.info(f"Registered hotkey '{name}': {key_combo}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register hotkey: {e}")
            return False

    def _is_single_key(self, key_combo: str) -> bool:
        """Check if hotkey is a single key (no modifiers)"""
        # Single key format: <x> or just x
        combo = key_combo.strip()

        # Check if contains + (modifier separator)
        if '+' in combo:
            return False

        # Check if it's a modifier key itself
        modifiers = ['ctrl', 'alt', 'shift', 'cmd', 'super', 'win']
        key = combo.strip('<>').lower()
        if key in modifiers:
            return False

        return True

    def unregister_hotkey(self, name: str) -> bool:
        """Unregister a hotkey"""
        if name in self.hotkeys:
            combo = self.hotkeys[name]['combo']

            # Remove from appropriate dict
            if self._is_single_key(combo):
                key_char = combo.strip('<>').lower()
                if key_char in self.single_key_hotkeys:
                    del self.single_key_hotkeys[key_char]
            else:
                if combo in self.combo_hotkeys:
                    del self.combo_hotkeys[combo]

            del self.hotkeys[name]
            self._restart_listeners()
            return True
        return False

    def _restart_listeners(self):
        """Restart all hotkey listeners"""
        # Stop existing listeners
        if self.combo_listener:
            try:
                self.combo_listener.stop()
            except Exception:
                pass
            self.combo_listener = None

        if self.key_listener:
            try:
                self.key_listener.stop()
            except Exception:
                pass
            self.key_listener = None

        # Start combo listener if we have combo hotkeys
        if self.combo_hotkeys:
            self._start_combo_listener()

        # Start key listener if we have single-key hotkeys
        if self.single_key_hotkeys:
            self._start_key_listener()

    def _start_combo_listener(self):
        """Start the GlobalHotKeys listener for modifier combinations"""
        hotkey_map = {}
        for combo, info in self.combo_hotkeys.items():
            callback = info['callback']
            name = info['name']

            def make_callback(cb=callback, hk_name=name):
                def wrapper():
                    cb()
                    self.hotkey_triggered.emit(hk_name)
                return wrapper

            hotkey_map[combo] = make_callback()

        try:
            self.combo_listener = keyboard.GlobalHotKeys(hotkey_map)
            self.combo_listener.start()
        except Exception as e:
            self.logger.error(f"Failed to start combo listener: {e}")

    def _start_key_listener(self):
        """Start the Listener for single-key hotkeys"""
        try:
            self.key_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.key_listener.start()
        except Exception as e:
            self.logger.error(f"Failed to start key listener: {e}")

    def _on_key_press(self, key):
        """Handle key press for single-key hotkeys"""
        try:
            # Track modifiers
            if hasattr(key, 'name'):
                if key.name in ('ctrl', 'ctrl_l', 'ctrl_r'):
                    self.pressed_modifiers.add('ctrl')
                    return
                elif key.name in ('alt', 'alt_l', 'alt_r', 'alt_gr'):
                    self.pressed_modifiers.add('alt')
                    return
                elif key.name in ('shift', 'shift_l', 'shift_r'):
                    self.pressed_modifiers.add('shift')
                    return

            # Only trigger single-key hotkeys when NO modifiers are pressed
            if self.pressed_modifiers:
                return

            # Get the key character
            if hasattr(key, 'char') and key.char:
                key_char = key.char.lower()
            elif hasattr(key, 'name') and key.name:
                key_char = key.name.lower()
            else:
                return

            # Check if this key has a hotkey registered
            if key_char in self.single_key_hotkeys:
                info = self.single_key_hotkeys[key_char]
                try:
                    info['callback']()
                    self.hotkey_triggered.emit(info['name'])
                except Exception as e:
                    self.logger.error(f"Error in hotkey callback: {e}")

        except Exception as e:
            self.logger.debug(f"Key press handling error: {e}")

    def _on_key_release(self, key):
        """Handle key release to track modifiers"""
        try:
            if hasattr(key, 'name'):
                if key.name in ('ctrl', 'ctrl_l', 'ctrl_r'):
                    self.pressed_modifiers.discard('ctrl')
                elif key.name in ('alt', 'alt_l', 'alt_r', 'alt_gr'):
                    self.pressed_modifiers.discard('alt')
                elif key.name in ('shift', 'shift_l', 'shift_r'):
                    self.pressed_modifiers.discard('shift')
        except Exception:
            pass

    def start(self):
        """Start listening"""
        self._restart_listeners()

    def stop(self):
        """Stop listening"""
        if self.combo_listener:
            try:
                self.combo_listener.stop()
                self.combo_listener = None
            except Exception:
                pass

        if self.key_listener:
            try:
                self.key_listener.stop()
                self.key_listener = None
            except Exception:
                pass

    def parse_key_combo(self, combo_string: str) -> str:
        """Parse human-readable key combo"""
        key_map = {
            'ctrl': '<ctrl>', 'control': '<ctrl>',
            'alt': '<alt>', 'shift': '<shift>',
            'super': '<cmd>', 'win': '<cmd>', 'cmd': '<cmd>',
        }

        parts = combo_string.lower().split('+')
        formatted_parts = []

        for part in parts:
            part = part.strip()
            if part in key_map:
                formatted_parts.append(key_map[part])
            elif len(part) == 1:
                formatted_parts.append(part)
            elif part.startswith('f') and part[1:].isdigit():
                formatted_parts.append(f'<{part}>')
            else:
                formatted_parts.append(f'<{part}>')

        return '+'.join(formatted_parts)

    def format_key_combo(self, pynput_combo: str) -> str:
        """Format pynput combo to human-readable"""
        parts = pynput_combo.split('+')
        formatted_parts = []

        for part in parts:
            part = part.strip('<>').capitalize()
            if part == 'Cmd':
                part = 'Super'
            formatted_parts.append(part)

        return '+'.join(formatted_parts)
