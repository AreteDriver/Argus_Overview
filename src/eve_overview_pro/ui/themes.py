"""
Themes - Customizable appearance themes for the application
v2.2 Feature: Dark, Light, EVE, and Custom themes
"""
import logging
from dataclasses import dataclass
from typing import Dict, Optional

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


@dataclass
class ThemeColors:
    """Color scheme for a theme"""
    # Window colors
    window: str = "#353535"
    window_text: str = "#ffffff"

    # Base colors (text inputs, lists)
    base: str = "#191919"
    alternate_base: str = "#353535"

    # Text colors
    text: str = "#ffffff"
    bright_text: str = "#ff0000"

    # Button colors
    button: str = "#353535"
    button_text: str = "#ffffff"

    # Accent colors
    highlight: str = "#2a82da"
    highlighted_text: str = "#000000"
    link: str = "#2a82da"

    # Tooltip
    tooltip_base: str = "#ffffff"
    tooltip_text: str = "#000000"

    # Custom accent (for borders, focus, etc.)
    accent: str = "#4287f5"

    # Alert colors
    alert_red: str = "#ff4444"
    alert_yellow: str = "#ffcc00"
    alert_green: str = "#44ff44"


class Theme:
    """A complete theme definition"""

    def __init__(self, name: str, colors: ThemeColors):
        self.name = name
        self.colors = colors

    def to_dict(self) -> Dict:
        """Serialize theme to dict"""
        return {
            "name": self.name,
            "colors": {
                "window": self.colors.window,
                "window_text": self.colors.window_text,
                "base": self.colors.base,
                "alternate_base": self.colors.alternate_base,
                "text": self.colors.text,
                "bright_text": self.colors.bright_text,
                "button": self.colors.button,
                "button_text": self.colors.button_text,
                "highlight": self.colors.highlight,
                "highlighted_text": self.colors.highlighted_text,
                "link": self.colors.link,
                "tooltip_base": self.colors.tooltip_base,
                "tooltip_text": self.colors.tooltip_text,
                "accent": self.colors.accent,
                "alert_red": self.colors.alert_red,
                "alert_yellow": self.colors.alert_yellow,
                "alert_green": self.colors.alert_green,
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Theme':
        """Create theme from dict"""
        colors = ThemeColors(**data.get("colors", {}))
        return cls(data.get("name", "custom"), colors)


# Built-in themes
DARK_THEME = Theme("dark", ThemeColors(
    window="#353535",
    window_text="#ffffff",
    base="#191919",
    alternate_base="#353535",
    text="#ffffff",
    bright_text="#ff0000",
    button="#353535",
    button_text="#ffffff",
    highlight="#2a82da",
    highlighted_text="#000000",
    link="#2a82da",
    tooltip_base="#ffffff",
    tooltip_text="#000000",
    accent="#4287f5",
    alert_red="#ff4444",
    alert_yellow="#ffcc00",
    alert_green="#44ff44",
))

LIGHT_THEME = Theme("light", ThemeColors(
    window="#f0f0f0",
    window_text="#000000",
    base="#ffffff",
    alternate_base="#f5f5f5",
    text="#000000",
    bright_text="#ff0000",
    button="#e0e0e0",
    button_text="#000000",
    highlight="#0078d7",
    highlighted_text="#ffffff",
    link="#0066cc",
    tooltip_base="#ffffcc",
    tooltip_text="#000000",
    accent="#0066cc",
    alert_red="#cc0000",
    alert_yellow="#cc9900",
    alert_green="#009900",
))

EVE_THEME = Theme("eve", ThemeColors(
    window="#0a0a0f",
    window_text="#e0e0e0",
    base="#000000",
    alternate_base="#0f0f1a",
    text="#c0c0c0",
    bright_text="#ff6600",
    button="#1a1a2e",
    button_text="#e0e0e0",
    highlight="#ff8c00",
    highlighted_text="#000000",
    link="#ff8c00",
    tooltip_base="#1a1a2e",
    tooltip_text="#ffffff",
    accent="#ff8c00",
    alert_red="#ff2200",
    alert_yellow="#ffaa00",
    alert_green="#00ff66",
))

# All built-in themes
BUILTIN_THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "eve": EVE_THEME,
}


class ThemeManager:
    """
    Manages application theming.

    Features:
    - Switch between built-in themes
    - Support custom themes from config
    - Apply theme to application palette
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_theme: Optional[Theme] = None
        self.custom_themes: Dict[str, Theme] = {}

    def get_available_themes(self) -> Dict[str, str]:
        """
        Get list of available theme names.

        Returns:
            Dict mapping theme_id to display_name
        """
        themes = {
            "dark": "Dark",
            "light": "Light",
            "eve": "EVE Online",
        }

        for name in self.custom_themes:
            themes[name] = f"Custom: {name}"

        return themes

    def apply_theme(self, theme_name: str, app: Optional[QApplication] = None) -> bool:
        """
        Apply a theme to the application.

        Args:
            theme_name: Name of theme to apply
            app: QApplication instance (uses global if not provided)

        Returns:
            True if successful
        """
        # Get the theme
        if theme_name in BUILTIN_THEMES:
            theme = BUILTIN_THEMES[theme_name]
        elif theme_name in self.custom_themes:
            theme = self.custom_themes[theme_name]
        else:
            self.logger.error(f"Unknown theme: {theme_name}")
            return False

        # Get application
        if app is None:
            app = QApplication.instance()

        if app is None:
            self.logger.error("No QApplication instance")
            return False

        # Apply the theme
        try:
            self._apply_palette(app, theme)
            self.current_theme = theme
            self.logger.info(f"Applied theme: {theme_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply theme: {e}")
            return False

    def _apply_palette(self, app: QApplication, theme: Theme):
        """Apply theme colors to application palette"""
        colors = theme.colors
        palette = QPalette()

        # Set Fusion style for consistent appearance
        app.setStyle('Fusion')

        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(colors.window))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.window_text))

        # Base colors
        palette.setColor(QPalette.ColorRole.Base, QColor(colors.base))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.alternate_base))

        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(colors.text))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(colors.bright_text))

        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(colors.button))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.button_text))

        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.highlight))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.highlighted_text))

        # Link color
        palette.setColor(QPalette.ColorRole.Link, QColor(colors.link))

        # Tooltip colors
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors.tooltip_base))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors.tooltip_text))

        app.setPalette(palette)

    def register_custom_theme(self, theme: Theme):
        """
        Register a custom theme.

        Args:
            theme: Theme to register
        """
        self.custom_themes[theme.name] = theme
        self.logger.info(f"Registered custom theme: {theme.name}")

    def get_current_theme(self) -> Optional[Theme]:
        """Get currently applied theme"""
        return self.current_theme

    def get_accent_color(self) -> str:
        """Get current theme's accent color"""
        if self.current_theme:
            return self.current_theme.colors.accent
        return DARK_THEME.colors.accent

    def get_alert_colors(self) -> Dict[str, str]:
        """Get current theme's alert colors"""
        if self.current_theme:
            return {
                "red": self.current_theme.colors.alert_red,
                "yellow": self.current_theme.colors.alert_yellow,
                "green": self.current_theme.colors.alert_green,
            }
        return {
            "red": DARK_THEME.colors.alert_red,
            "yellow": DARK_THEME.colors.alert_yellow,
            "green": DARK_THEME.colors.alert_green,
        }


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
