"""Global hotkey management - supports both modifier combos and single keys.

Threading model:
    pynput listeners run on background threads.  All callbacks are
    dispatched to the Qt GUI thread via the ``_invoke_callback`` signal
    (auto-queued connection) so that slot methods can safely modify
    widgets without cross-thread crashes.
"""

import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal

try:
    from pynput import keyboard

    PYNPUT_AVAILABLE = True
except ImportError:
    keyboard = None
    PYNPUT_AVAILABLE = False


class HotkeyManager(QObject):
    """Manages global hotkeys - supports single keys and modifier combinations"""

    hotkey_triggered = Signal(str)
    _invoke_callback = Signal(str)  # hotkey name → looked up and called on GUI thread

    def __init__(self):
        super().__init__()
        self.hotkeys: dict[str, dict] = {}
        self.combo_listener = None
        self.key_listener = None
        self.logger = logging.getLogger(__name__)

        if not PYNPUT_AVAILABLE:
            self.logger.warning("pynput not available — global hotkeys disabled")

        # Track single-key hotkeys separately
        self.single_key_hotkeys: dict[str, dict] = {}  # key_char -> {name, callback}
        self.combo_hotkeys: dict[str, dict] = {}  # combo_string -> {name, callback}

        # Track currently pressed modifiers
        self.pressed_modifiers: set[str] = set()

        # Connect callback dispatcher (queued → runs on GUI thread)
        self._invoke_callback.connect(self._dispatch_callback)

    def _normalize_combo(self, key_combo: str) -> str:
        """Normalize hotkey combo for pynput compatibility.

        Fixes common format issues:
        - <ctrl>+<v> -> <ctrl>+v (single letters shouldn't have brackets)
        - <ctrl>+<R> -> <ctrl>+r (lowercase letters)
        """
        parts = key_combo.split("+")
        normalized = []
        modifiers = {"ctrl", "alt", "shift", "cmd", "super", "win"}

        for part in parts:
            part = part.strip()
            inner = part.strip("<>").lower()

            # Keep modifiers and special keys in brackets
            if inner in modifiers or len(inner) > 1:
                normalized.append(f"<{inner}>")
            else:
                # Single character - no brackets, lowercase
                normalized.append(inner)

        return "+".join(normalized)

    def register_hotkey(self, name: str, key_combo: str, callback: Callable) -> bool:
        """Register a global hotkey"""
        if not PYNPUT_AVAILABLE:
            self.logger.warning(f"Cannot register hotkey '{name}': pynput not available")
            return False
        try:
            # Normalize the combo for pynput
            normalized_combo = self._normalize_combo(key_combo)
            self.hotkeys[name] = {"combo": normalized_combo, "callback": callback}

            # Determine if single key or combo
            if self._is_single_key(normalized_combo):
                key_char = normalized_combo.strip("<>").lower()
                self.single_key_hotkeys[key_char] = {"name": name, "callback": callback}
            else:
                self.combo_hotkeys[normalized_combo] = {
                    "name": name,
                    "callback": callback,
                }

            self._restart_listeners()
            self.logger.info(f"Registered hotkey '{name}': {normalized_combo}")
            return True
        except (ValueError, RuntimeError, OSError) as e:
            self.logger.error(f"Failed to register hotkey: {e}")
            return False

    def _is_single_key(self, key_combo: str) -> bool:
        """Check if hotkey is a single key (no modifiers)"""
        # Single key format: <x> or just x
        combo = key_combo.strip()

        # Check if contains + (modifier separator)
        if "+" in combo:
            return False

        # Check if it's a modifier key itself
        modifiers = ["ctrl", "alt", "shift", "cmd", "super", "win"]
        key = combo.strip("<>").lower()
        if key in modifiers:
            return False

        return True

    def unregister_hotkey(self, name: str, restart: bool = True) -> bool:
        """Unregister a hotkey

        Args:
            name: Hotkey name to unregister
            restart: Whether to restart listeners immediately (set False for batching)
        """
        if name in self.hotkeys:
            combo = self.hotkeys[name]["combo"]

            # Remove from appropriate dict
            if self._is_single_key(combo):
                key_char = combo.strip("<>").lower()
                if key_char in self.single_key_hotkeys:
                    del self.single_key_hotkeys[key_char]
            else:
                if combo in self.combo_hotkeys:
                    del self.combo_hotkeys[combo]

            del self.hotkeys[name]
            if restart:
                self._restart_listeners()
            return True
        return False

    def _restart_listeners(self):
        """Restart all hotkey listeners"""
        if not PYNPUT_AVAILABLE:
            return
        # Stop existing listeners
        if self.combo_listener:
            try:
                self.combo_listener.stop()
            except (RuntimeError, OSError) as e:
                self.logger.debug(f"Error stopping combo listener: {e}")
            self.combo_listener = None

        if self.key_listener:
            try:
                self.key_listener.stop()
            except (RuntimeError, OSError) as e:
                self.logger.debug(f"Error stopping key listener: {e}")
            self.key_listener = None

        # Start combo listener if we have combo hotkeys
        if self.combo_hotkeys:
            self._start_combo_listener()

        # Start key listener if we have single-key hotkeys
        if self.single_key_hotkeys:
            self._start_key_listener()

    def _dispatch_callback(self, hotkey_name: str):
        """Dispatch hotkey callback on the GUI thread (connected via queued signal)."""
        if hotkey_name in self.hotkeys:
            try:
                self.hotkeys[hotkey_name]["callback"]()
                self.hotkey_triggered.emit(hotkey_name)
            except (RuntimeError, TypeError, ValueError) as e:
                self.logger.error(f"Error in hotkey callback '{hotkey_name}': {e}")

    def _start_combo_listener(self):
        """Start the GlobalHotKeys listener for modifier combinations"""
        hotkey_map = {}
        for combo, info in self.combo_hotkeys.items():
            name = info["name"]

            def make_callback(hk_name=name):
                def wrapper():
                    # Bounce to GUI thread via signal (listener runs on bg thread)
                    self._invoke_callback.emit(hk_name)

                return wrapper

            hotkey_map[combo] = make_callback()

        try:
            self.combo_listener = keyboard.GlobalHotKeys(hotkey_map)
            self.combo_listener.start()
        except (RuntimeError, OSError) as e:
            self.logger.error(f"Failed to start combo listener: {e}")

    def _start_key_listener(self):
        """Start the Listener for single-key hotkeys"""
        try:
            self.key_listener = keyboard.Listener(
                on_press=self._on_key_press, on_release=self._on_key_release
            )
            self.key_listener.start()
        except (RuntimeError, OSError) as e:
            self.logger.error(f"Failed to start key listener: {e}")

    # Modifier key name mappings
    _MODIFIER_KEYS = {
        "ctrl": ("ctrl", "ctrl_l", "ctrl_r"),
        "alt": ("alt", "alt_l", "alt_r", "alt_gr"),
        "shift": ("shift", "shift_l", "shift_r"),
    }

    def _track_modifier_press(self, key) -> bool:
        """Track modifier key press. Returns True if key was a modifier."""
        if not hasattr(key, "name"):
            return False
        for mod_name, key_names in self._MODIFIER_KEYS.items():
            if key.name in key_names:
                self.pressed_modifiers.add(mod_name)
                return True
        return False

    def _get_key_char(self, key) -> str | None:
        """Extract key character from key event."""
        if hasattr(key, "char") and key.char:
            return key.char.lower()
        if hasattr(key, "name") and key.name:
            return key.name.lower()
        return None

    def _on_key_press(self, key):
        """Handle key press for single-key hotkeys (called on listener thread)"""
        try:
            # Track modifiers - don't process further if it was a modifier
            if self._track_modifier_press(key):
                return

            # Only trigger single-key hotkeys when NO modifiers are pressed
            if self.pressed_modifiers:
                return

            # Get key character and check for registered hotkey
            key_char = self._get_key_char(key)
            if key_char and key_char in self.single_key_hotkeys:
                info = self.single_key_hotkeys[key_char]
                # Bounce to GUI thread via signal (listener runs on bg thread)
                self._invoke_callback.emit(info["name"])

        except (AttributeError, TypeError, RuntimeError) as e:
            self.logger.debug(f"Key press handling error: {e}")

    def _on_key_release(self, key):
        """Handle key release to track modifiers"""
        try:
            if hasattr(key, "name"):
                if key.name in ("ctrl", "ctrl_l", "ctrl_r"):
                    self.pressed_modifiers.discard("ctrl")
                elif key.name in ("alt", "alt_l", "alt_r", "alt_gr"):
                    self.pressed_modifiers.discard("alt")
                elif key.name in ("shift", "shift_l", "shift_r"):
                    self.pressed_modifiers.discard("shift")
        except (AttributeError, TypeError) as e:
            self.logger.debug(f"Key release handling error: {e}")

    def start(self):
        """Start listening"""
        if not PYNPUT_AVAILABLE:
            return
        self._restart_listeners()

    def pause(self):
        """Temporarily pause listeners (for key recording)"""
        if not PYNPUT_AVAILABLE:
            return
        self.logger.debug("Pausing hotkey listeners")
        if self.combo_listener:
            try:
                self.combo_listener.stop()
            except (RuntimeError, OSError) as e:
                self.logger.debug(f"Error stopping combo listener: {e}")
            self.combo_listener = None

        if self.key_listener:
            try:
                self.key_listener.stop()
            except (RuntimeError, OSError) as e:
                self.logger.debug(f"Error stopping key listener: {e}")
            self.key_listener = None

    def resume(self):
        """Resume listeners after pause"""
        if not PYNPUT_AVAILABLE:
            return
        self.logger.debug("Resuming hotkey listeners")
        self._restart_listeners()

    def stop(self):
        """Stop listening"""
        if not PYNPUT_AVAILABLE:
            return
        if self.combo_listener:
            try:
                self.combo_listener.stop()
                self.combo_listener = None
            except (RuntimeError, OSError) as e:
                self.logger.debug(f"Error stopping combo listener: {e}")
                self.combo_listener = None

        if self.key_listener:
            try:
                self.key_listener.stop()
                self.key_listener = None
            except (RuntimeError, OSError) as e:
                self.logger.debug(f"Error stopping key listener: {e}")
                self.key_listener = None

    def parse_key_combo(self, combo_string: str) -> str:
        """Parse human-readable key combo"""
        key_map = {
            "ctrl": "<ctrl>",
            "control": "<ctrl>",
            "alt": "<alt>",
            "shift": "<shift>",
            "super": "<cmd>",
            "win": "<cmd>",
            "cmd": "<cmd>",
        }

        parts = combo_string.lower().split("+")
        formatted_parts = []

        for part in parts:
            part = part.strip()
            if part in key_map:
                formatted_parts.append(key_map[part])
            elif len(part) == 1:
                formatted_parts.append(part)
            elif part.startswith("f") and part[1:].isdigit():
                formatted_parts.append(f"<{part}>")
            else:
                formatted_parts.append(f"<{part}>")

        return "+".join(formatted_parts)

    def format_key_combo(self, pynput_combo: str) -> str:
        """Format pynput combo to human-readable"""
        parts = pynput_combo.split("+")
        formatted_parts = []

        for part in parts:
            part = part.strip("<>").capitalize()
            if part == "Cmd":
                part = "Super"
            formatted_parts.append(part)

        return "+".join(formatted_parts)
