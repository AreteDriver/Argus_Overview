"""Global hotkey management"""
from typing import Callable, Dict, Optional
from pynput import keyboard
from PySide6.QtCore import QObject, Signal
import logging


class HotkeyManager(QObject):
    """Manages global hotkeys"""
    
    hotkey_triggered = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.hotkeys: Dict[str, Dict] = {}
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self.logger = logging.getLogger(__name__)
        
    def register_hotkey(self, name: str, key_combo: str, callback: Callable) -> bool:
        """Register a global hotkey"""
        try:
            self.hotkeys[name] = {'combo': key_combo, 'callback': callback}
            self._restart_listener()
            self.logger.info(f"Registered hotkey '{name}': {key_combo}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register hotkey: {e}")
            return False
    
    def unregister_hotkey(self, name: str) -> bool:
        """Unregister a hotkey"""
        if name in self.hotkeys:
            del self.hotkeys[name]
            self._restart_listener()
            return True
        return False
    
    def _restart_listener(self):
        """Restart the hotkey listener"""
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass  # Ignore errors when stopping old listener
        
        if not self.hotkeys:
            return
        
        hotkey_map = {}
        for name, info in self.hotkeys.items():
            combo = info['combo']
            callback = info['callback']
            
            def make_callback(cb=callback, hk_name=name):
                def wrapper():
                    cb()
                    self.hotkey_triggered.emit(hk_name)
                return wrapper
            
            hotkey_map[combo] = make_callback()
        
        try:
            self.listener = keyboard.GlobalHotKeys(hotkey_map)
            self.listener.start()
        except Exception as e:
            self.logger.error(f"Failed to start listener: {e}")
    
    def start(self):
        """Start listening"""
        self._restart_listener()
    
    def stop(self):
        """Stop listening"""
        if self.listener:
            try:
                self.listener.stop()
                self.listener = None
            except Exception:
                pass  # Ignore errors during shutdown
    
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
