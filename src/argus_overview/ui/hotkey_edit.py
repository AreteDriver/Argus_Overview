"""
Hotkey Edit Widget - Captures actual keypresses for hotkey assignment.

Allows setting any key combination including F13-F20, special keys, etc.

Threading model:
    pynput key listeners run on a background thread.  All Qt widget
    updates are bounced to the GUI thread via private signals
    (_display_update_requested, _finalize_requested) so that
    ``QLineEdit.setText`` is never called from the listener thread.
"""

import logging

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

# Import pynput for key capture
try:
    from pynput import keyboard

    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class HotkeyEdit(QWidget):
    """
    Widget for capturing and displaying hotkey combinations.

    Click "Record" then press any key/combination to set it.
    Supports F1-F20, modifiers, and any other keys pynput can detect.
    """

    # Emitted when hotkey changes (Qt convention uses camelCase for signals)
    hotkeyChanged = Signal(str)  # noqa: N815
    recordingStarted = Signal()  # noqa: N815
    recordingStopped = Signal()  # noqa: N815

    # Private signals for thread-safe GUI updates from listener thread
    _display_update_requested = Signal(str)
    _finalize_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        self._hotkey = ""
        self._recording = False
        self._pressed_keys: set[str] = set()
        self._listener: keyboard.Listener | None = None
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._stop_recording)

        # Connect thread-safe signals (queued connection to GUI thread)
        self._display_update_requested.connect(self._do_display_update)
        self._finalize_requested.connect(self._do_finalize)

        self._setup_ui()

    def _setup_ui(self):
        """Create the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Display field (read-only)
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setPlaceholderText("Click Record to set hotkey")
        layout.addWidget(self.display, stretch=1)

        # Record button
        self.record_btn = QPushButton("Record")
        self.record_btn.setFixedWidth(70)
        self.record_btn.clicked.connect(self._toggle_recording)
        layout.addWidget(self.record_btn)

        # Clear button
        self.clear_btn = QPushButton("×")
        self.clear_btn.setFixedWidth(30)
        self.clear_btn.setToolTip("Clear hotkey")
        self.clear_btn.clicked.connect(self._clear_hotkey)
        layout.addWidget(self.clear_btn)

    def text(self) -> str:
        """Get current hotkey string."""
        return self._hotkey

    def setText(self, hotkey: str):
        """Set hotkey string."""
        self._hotkey = hotkey
        self.display.setText(hotkey)

    def _toggle_recording(self):
        """Start or stop recording."""
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start capturing keypresses."""
        if not PYNPUT_AVAILABLE:
            self.display.setText("pynput not available")
            return

        # Signal to pause other listeners (avoid X11 conflicts)
        self.recordingStarted.emit()

        self._recording = True
        self._pressed_keys.clear()
        self.record_btn.setText("Press key...")
        self.record_btn.setStyleSheet("background-color: #c0392b; color: white;")
        self.display.setText("Waiting for keypress...")

        # Start listener
        self._listener = keyboard.Listener(
            on_press=self._on_key_press, on_release=self._on_key_release
        )
        self._listener.start()

        # Timeout after 10 seconds
        self._timeout_timer.start(10000)

    def _stop_recording(self):
        """Stop capturing keypresses."""
        self._recording = False
        self.record_btn.setText("Record")
        self.record_btn.setStyleSheet("")
        self._timeout_timer.stop()

        if self._listener:
            self._listener.stop()
            self._listener = None

        # Signal to resume other listeners
        self.recordingStopped.emit()

        # If no key was captured, restore previous
        if not self._hotkey:
            self.display.setText("")
            self.display.setPlaceholderText("Click Record to set hotkey")

    def _on_key_press(self, key):
        """Handle key press during recording (called on listener thread)."""
        if not self._recording:
            return

        key_str = self._key_to_string(key)
        if key_str:
            self._pressed_keys.add(key_str)
            # Bounce display update to GUI thread via signal
            display_str = self._format_pressed_keys()
            self._display_update_requested.emit(display_str)

    def _on_key_release(self, key):
        """Handle key release - finalize the hotkey (called on listener thread)."""
        if not self._recording or not self._pressed_keys:
            return

        # Snapshot keys before clearing — _do_finalize reads this on GUI thread
        self._finalized_keys = self._pressed_keys.copy()
        self._pressed_keys.clear()  # Prevent duplicate signals from remaining key releases
        self._finalize_requested.emit()

    def _key_to_string(self, key) -> str | None:
        """Convert pynput key to string format."""
        # Modifier keys
        if (
            key == keyboard.Key.ctrl_l
            or key == keyboard.Key.ctrl_r
            or key == keyboard.Key.ctrl
        ):
            return "ctrl"
        if (
            key == keyboard.Key.alt_l
            or key == keyboard.Key.alt_r
            or key == keyboard.Key.alt
        ):
            return "alt"
        if key == keyboard.Key.alt_gr:
            return "alt"
        if (
            key == keyboard.Key.shift_l
            or key == keyboard.Key.shift_r
            or key == keyboard.Key.shift
        ):
            return "shift"
        if (
            key == keyboard.Key.cmd
            or key == keyboard.Key.cmd_l
            or key == keyboard.Key.cmd_r
        ):
            return "cmd"

        # Special keys
        if hasattr(key, "name") and key.name:
            return key.name.lower()

        # Character keys
        if hasattr(key, "char") and key.char:
            return key.char.lower()

        return None

    @staticmethod
    def _format_keys(keys: set[str]) -> str:
        """Format a set of keys into display string (thread-safe, no GUI calls)."""
        if not keys:
            return ""

        modifiers = {"ctrl", "alt", "shift", "cmd", "super", "win"}
        mod_keys = sorted([k for k in keys if k in modifiers])
        other_keys = sorted([k for k in keys if k not in modifiers])

        parts = mod_keys + other_keys
        return "+".join(f"<{p}>" for p in parts)

    def _format_pressed_keys(self) -> str:
        """Format currently pressed keys (convenience wrapper)."""
        return self._format_keys(self._pressed_keys)

    def _do_display_update(self, display_str: str):
        """Update display widget (runs on GUI thread via signal)."""
        self.display.setText(display_str)

    def _do_finalize(self):
        """Finalize and save the captured hotkey (runs on GUI thread via signal)."""
        keys = getattr(self, "_finalized_keys", self._pressed_keys)
        if not keys:
            self._stop_recording()
            return

        self._hotkey = self._format_keys(keys)
        self.display.setText(self._hotkey)
        self.hotkeyChanged.emit(self._hotkey)
        self.logger.info(f"Hotkey captured: {self._hotkey}")

        self._stop_recording()

    def _clear_hotkey(self):
        """Clear the current hotkey."""
        self._hotkey = ""
        self.display.setText("")
        self.display.setPlaceholderText("Click Record to set hotkey")
        self.hotkeyChanged.emit("")
