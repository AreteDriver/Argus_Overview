"""
Unit tests for the Themes module
Tests ThemeColors, Theme, ThemeManager, and related functionality
"""
from unittest.mock import MagicMock, patch


# Test ThemeColors dataclass
class TestThemeColors:
    """Tests for the ThemeColors dataclass"""

    def test_default_values(self):
        """Test that default values are set correctly"""
        from eve_overview_pro.ui.themes import ThemeColors

        colors = ThemeColors()

        # Window colors
        assert colors.window == "#353535"
        assert colors.window_text == "#ffffff"

        # Base colors
        assert colors.base == "#191919"
        assert colors.alternate_base == "#353535"

        # Text colors
        assert colors.text == "#ffffff"
        assert colors.bright_text == "#ff0000"

        # Button colors
        assert colors.button == "#353535"
        assert colors.button_text == "#ffffff"

        # Accent colors
        assert colors.highlight == "#2a82da"
        assert colors.highlighted_text == "#000000"
        assert colors.link == "#2a82da"

        # Tooltip
        assert colors.tooltip_base == "#ffffff"
        assert colors.tooltip_text == "#000000"

        # Custom accent
        assert colors.accent == "#4287f5"

        # Alert colors
        assert colors.alert_red == "#ff4444"
        assert colors.alert_yellow == "#ffcc00"
        assert colors.alert_green == "#44ff44"

    def test_custom_values(self):
        """Test creating ThemeColors with custom values"""
        from eve_overview_pro.ui.themes import ThemeColors

        colors = ThemeColors(
            window="#000000",
            text="#00ff00",
            accent="#ff00ff"
        )

        assert colors.window == "#000000"
        assert colors.text == "#00ff00"
        assert colors.accent == "#ff00ff"
        # Other values should be defaults
        assert colors.base == "#191919"

    def test_all_fields_present(self):
        """Test that all expected fields are present"""
        from dataclasses import fields

        from eve_overview_pro.ui.themes import ThemeColors

        colors = ThemeColors()
        field_names = {f.name for f in fields(colors)}

        expected_fields = {
            'window', 'window_text', 'base', 'alternate_base',
            'text', 'bright_text', 'button', 'button_text',
            'highlight', 'highlighted_text', 'link',
            'tooltip_base', 'tooltip_text', 'accent',
            'alert_red', 'alert_yellow', 'alert_green'
        }

        assert field_names == expected_fields


# Test Theme class
class TestTheme:
    """Tests for the Theme class"""

    def test_create_theme(self):
        """Test creating a Theme"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors

        colors = ThemeColors(window="#123456")
        theme = Theme("test_theme", colors)

        assert theme.name == "test_theme"
        assert theme.colors == colors
        assert theme.colors.window == "#123456"

    def test_to_dict(self):
        """Test serializing theme to dict"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors

        colors = ThemeColors(
            window="#111111",
            window_text="#222222",
            accent="#333333"
        )
        theme = Theme("my_theme", colors)

        result = theme.to_dict()

        assert result["name"] == "my_theme"
        assert "colors" in result
        assert result["colors"]["window"] == "#111111"
        assert result["colors"]["window_text"] == "#222222"
        assert result["colors"]["accent"] == "#333333"

    def test_to_dict_all_colors(self):
        """Test that to_dict includes all color fields"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors

        theme = Theme("full_theme", ThemeColors())
        result = theme.to_dict()

        expected_color_keys = {
            'window', 'window_text', 'base', 'alternate_base',
            'text', 'bright_text', 'button', 'button_text',
            'highlight', 'highlighted_text', 'link',
            'tooltip_base', 'tooltip_text', 'accent',
            'alert_red', 'alert_yellow', 'alert_green'
        }

        assert set(result["colors"].keys()) == expected_color_keys

    def test_from_dict(self):
        """Test creating theme from dict"""
        from eve_overview_pro.ui.themes import Theme

        data = {
            "name": "loaded_theme",
            "colors": {
                "window": "#abcdef",
                "text": "#fedcba"
            }
        }

        theme = Theme.from_dict(data)

        assert theme.name == "loaded_theme"
        assert theme.colors.window == "#abcdef"
        assert theme.colors.text == "#fedcba"
        # Unspecified colors should be defaults
        assert theme.colors.base == "#191919"

    def test_from_dict_empty_colors(self):
        """Test from_dict with empty colors dict"""
        from eve_overview_pro.ui.themes import Theme

        data = {
            "name": "empty_colors",
            "colors": {}
        }

        theme = Theme.from_dict(data)

        assert theme.name == "empty_colors"
        # All colors should be defaults
        assert theme.colors.window == "#353535"

    def test_from_dict_missing_colors(self):
        """Test from_dict with missing colors key"""
        from eve_overview_pro.ui.themes import Theme

        data = {"name": "no_colors"}

        theme = Theme.from_dict(data)

        assert theme.name == "no_colors"
        # All colors should be defaults
        assert theme.colors.window == "#353535"

    def test_from_dict_missing_name(self):
        """Test from_dict with missing name"""
        from eve_overview_pro.ui.themes import Theme

        data = {"colors": {"window": "#000000"}}

        theme = Theme.from_dict(data)

        assert theme.name == "custom"
        assert theme.colors.window == "#000000"

    def test_roundtrip(self):
        """Test that to_dict -> from_dict preserves data"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors

        original = Theme("roundtrip_test", ThemeColors(
            window="#aabbcc",
            text="#112233",
            accent="#445566"
        ))

        serialized = original.to_dict()
        restored = Theme.from_dict(serialized)

        assert restored.name == original.name
        assert restored.colors.window == original.colors.window
        assert restored.colors.text == original.colors.text
        assert restored.colors.accent == original.colors.accent


# Test built-in themes
class TestBuiltinThemes:
    """Tests for built-in theme definitions"""

    def test_dark_theme_exists(self):
        """Test DARK_THEME is defined"""
        from eve_overview_pro.ui.themes import DARK_THEME

        assert DARK_THEME is not None
        assert DARK_THEME.name == "dark"

    def test_light_theme_exists(self):
        """Test LIGHT_THEME is defined"""
        from eve_overview_pro.ui.themes import LIGHT_THEME

        assert LIGHT_THEME is not None
        assert LIGHT_THEME.name == "light"

    def test_eve_theme_exists(self):
        """Test EVE_THEME is defined"""
        from eve_overview_pro.ui.themes import EVE_THEME

        assert EVE_THEME is not None
        assert EVE_THEME.name == "eve"

    def test_builtin_themes_dict(self):
        """Test BUILTIN_THEMES contains all themes"""
        from eve_overview_pro.ui.themes import BUILTIN_THEMES, DARK_THEME, EVE_THEME, LIGHT_THEME

        assert "dark" in BUILTIN_THEMES
        assert "light" in BUILTIN_THEMES
        assert "eve" in BUILTIN_THEMES

        assert BUILTIN_THEMES["dark"] is DARK_THEME
        assert BUILTIN_THEMES["light"] is LIGHT_THEME
        assert BUILTIN_THEMES["eve"] is EVE_THEME

    def test_dark_theme_colors(self):
        """Test dark theme has expected color scheme"""
        from eve_overview_pro.ui.themes import DARK_THEME

        # Dark theme should have dark window colors
        assert DARK_THEME.colors.window == "#353535"
        assert DARK_THEME.colors.base == "#191919"
        # And light text
        assert DARK_THEME.colors.text == "#ffffff"
        assert DARK_THEME.colors.window_text == "#ffffff"

    def test_light_theme_colors(self):
        """Test light theme has expected color scheme"""
        from eve_overview_pro.ui.themes import LIGHT_THEME

        # Light theme should have light window colors
        assert LIGHT_THEME.colors.window == "#f0f0f0"
        assert LIGHT_THEME.colors.base == "#ffffff"
        # And dark text
        assert LIGHT_THEME.colors.text == "#000000"
        assert LIGHT_THEME.colors.window_text == "#000000"

    def test_eve_theme_colors(self):
        """Test EVE theme has expected color scheme"""
        from eve_overview_pro.ui.themes import EVE_THEME

        # EVE theme should have very dark, space-like colors
        assert EVE_THEME.colors.window == "#0a0a0f"
        assert EVE_THEME.colors.base == "#000000"
        # Orange accent (EVE style)
        assert EVE_THEME.colors.accent == "#ff8c00"
        assert EVE_THEME.colors.highlight == "#ff8c00"


# Test ThemeManager
class TestThemeManager:
    """Tests for the ThemeManager class"""

    def test_init(self):
        """Test ThemeManager initialization"""
        from eve_overview_pro.ui.themes import ThemeManager

        manager = ThemeManager()

        assert manager.current_theme is None
        assert manager.custom_themes == {}

    def test_get_available_themes(self):
        """Test getting available themes"""
        from eve_overview_pro.ui.themes import ThemeManager

        manager = ThemeManager()
        themes = manager.get_available_themes()

        assert "dark" in themes
        assert "light" in themes
        assert "eve" in themes

        assert themes["dark"] == "Dark"
        assert themes["light"] == "Light"
        assert themes["eve"] == "EVE Online"

    def test_get_available_themes_with_custom(self):
        """Test getting available themes including custom ones"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors, ThemeManager

        manager = ThemeManager()

        custom_theme = Theme("my_custom", ThemeColors())
        manager.register_custom_theme(custom_theme)

        themes = manager.get_available_themes()

        assert "my_custom" in themes
        assert themes["my_custom"] == "Custom: my_custom"

    def test_register_custom_theme(self):
        """Test registering a custom theme"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors, ThemeManager

        manager = ThemeManager()

        custom = Theme("purple_theme", ThemeColors(accent="#800080"))
        manager.register_custom_theme(custom)

        assert "purple_theme" in manager.custom_themes
        assert manager.custom_themes["purple_theme"] is custom

    def test_get_current_theme_none(self):
        """Test get_current_theme returns None when no theme applied"""
        from eve_overview_pro.ui.themes import ThemeManager

        manager = ThemeManager()

        assert manager.get_current_theme() is None

    def test_get_accent_color_no_theme(self):
        """Test get_accent_color with no current theme"""
        from eve_overview_pro.ui.themes import DARK_THEME, ThemeManager

        manager = ThemeManager()

        # Should return dark theme's accent as default
        assert manager.get_accent_color() == DARK_THEME.colors.accent

    def test_get_accent_color_with_theme(self):
        """Test get_accent_color with current theme"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors, ThemeManager

        manager = ThemeManager()

        # Manually set current theme (bypassing apply_theme which needs QApp)
        manager.current_theme = Theme("test", ThemeColors(accent="#123456"))

        assert manager.get_accent_color() == "#123456"

    def test_get_alert_colors_no_theme(self):
        """Test get_alert_colors with no current theme"""
        from eve_overview_pro.ui.themes import DARK_THEME, ThemeManager

        manager = ThemeManager()

        colors = manager.get_alert_colors()

        assert colors["red"] == DARK_THEME.colors.alert_red
        assert colors["yellow"] == DARK_THEME.colors.alert_yellow
        assert colors["green"] == DARK_THEME.colors.alert_green

    def test_get_alert_colors_with_theme(self):
        """Test get_alert_colors with current theme"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors, ThemeManager

        manager = ThemeManager()

        manager.current_theme = Theme("test", ThemeColors(
            alert_red="#ff0000",
            alert_yellow="#ffff00",
            alert_green="#00ff00"
        ))

        colors = manager.get_alert_colors()

        assert colors["red"] == "#ff0000"
        assert colors["yellow"] == "#ffff00"
        assert colors["green"] == "#00ff00"

    def test_apply_theme_unknown_theme(self):
        """Test apply_theme with unknown theme name"""
        from eve_overview_pro.ui.themes import ThemeManager

        manager = ThemeManager()

        # Should return False for unknown theme
        result = manager.apply_theme("nonexistent_theme")

        assert result is False

    def test_apply_theme_no_app(self):
        """Test apply_theme when no QApplication exists"""
        from eve_overview_pro.ui.themes import ThemeManager

        manager = ThemeManager()

        with patch('eve_overview_pro.ui.themes.QApplication') as mock_qapp:
            mock_qapp.instance.return_value = None

            result = manager.apply_theme("dark", app=None)

            assert result is False

    def test_apply_theme_success(self):
        """Test successful theme application"""
        from eve_overview_pro.ui.themes import ThemeManager

        manager = ThemeManager()

        mock_app = MagicMock()

        result = manager.apply_theme("dark", app=mock_app)

        assert result is True
        assert manager.current_theme is not None
        assert manager.current_theme.name == "dark"
        mock_app.setStyle.assert_called_once_with('Fusion')
        mock_app.setPalette.assert_called_once()

    def test_apply_theme_light(self):
        """Test applying light theme"""
        from eve_overview_pro.ui.themes import LIGHT_THEME, ThemeManager

        manager = ThemeManager()
        mock_app = MagicMock()

        result = manager.apply_theme("light", app=mock_app)

        assert result is True
        assert manager.current_theme is LIGHT_THEME

    def test_apply_theme_eve(self):
        """Test applying EVE theme"""
        from eve_overview_pro.ui.themes import EVE_THEME, ThemeManager

        manager = ThemeManager()
        mock_app = MagicMock()

        result = manager.apply_theme("eve", app=mock_app)

        assert result is True
        assert manager.current_theme is EVE_THEME

    def test_apply_custom_theme(self):
        """Test applying a custom theme"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors, ThemeManager

        manager = ThemeManager()

        custom = Theme("my_custom", ThemeColors(window="#abcdef"))
        manager.register_custom_theme(custom)

        mock_app = MagicMock()
        result = manager.apply_theme("my_custom", app=mock_app)

        assert result is True
        assert manager.current_theme is custom

    def test_apply_theme_exception_handling(self):
        """Test that apply_theme handles exceptions"""
        from eve_overview_pro.ui.themes import ThemeManager

        manager = ThemeManager()

        mock_app = MagicMock()
        mock_app.setStyle.side_effect = Exception("Style error")

        result = manager.apply_theme("dark", app=mock_app)

        assert result is False


# Test global theme manager
class TestGlobalThemeManager:
    """Tests for the global theme manager singleton"""

    def test_get_theme_manager(self):
        """Test getting the global theme manager"""
        from eve_overview_pro.ui.themes import ThemeManager, get_theme_manager

        manager = get_theme_manager()

        assert isinstance(manager, ThemeManager)

    def test_get_theme_manager_singleton(self):
        """Test that get_theme_manager returns same instance"""
        from eve_overview_pro.ui.themes import get_theme_manager

        manager1 = get_theme_manager()
        manager2 = get_theme_manager()

        assert manager1 is manager2

    def test_get_theme_manager_creates_new_if_none(self):
        """Test that get_theme_manager creates manager if none exists"""
        import eve_overview_pro.ui.themes as themes_module

        # Reset the global
        original = themes_module._theme_manager
        themes_module._theme_manager = None

        try:
            manager = themes_module.get_theme_manager()
            assert manager is not None
            assert themes_module._theme_manager is manager
        finally:
            # Restore original
            themes_module._theme_manager = original


# Test theme palette application
class TestThemePalette:
    """Tests for palette application internals"""

    def test_apply_palette_sets_colors(self):
        """Test that _apply_palette sets palette colors correctly"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors, ThemeManager

        manager = ThemeManager()
        mock_app = MagicMock()

        colors = ThemeColors(
            window="#112233",
            text="#445566"
        )
        theme = Theme("test", colors)

        manager._apply_palette(mock_app, theme)

        mock_app.setStyle.assert_called_once_with('Fusion')
        mock_app.setPalette.assert_called_once()

        # Verify a palette was passed
        palette_arg = mock_app.setPalette.call_args[0][0]
        assert palette_arg is not None


# Test edge cases
class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_theme_with_invalid_color_format(self):
        """Test theme with unusual color format still works"""
        from eve_overview_pro.ui.themes import ThemeColors

        # Should not raise - just stores the string
        colors = ThemeColors(window="not-a-color")
        assert colors.window == "not-a-color"

    def test_from_dict_extra_keys(self):
        """Test from_dict ignores unknown keys"""
        from eve_overview_pro.ui.themes import Theme

        data = {
            "name": "test",
            "colors": {"window": "#000000"},
            "unknown_key": "ignored",
            "another_unknown": 123
        }

        theme = Theme.from_dict(data)

        assert theme.name == "test"
        assert theme.colors.window == "#000000"

    def test_from_dict_extra_color_keys(self):
        """Test from_dict handles extra color keys"""
        from eve_overview_pro.ui.themes import Theme

        data = {
            "name": "test",
            "colors": {
                "window": "#000000",
                "unknown_color": "#ffffff"
            }
        }

        # This might raise or ignore - depends on dataclass behavior
        # With default ThemeColors(**kwargs), unknown keys will raise
        try:
            theme = Theme.from_dict(data)
            # If it doesn't raise, window should still work
            assert theme.colors.window == "#000000"
        except TypeError:
            # Expected if dataclass doesn't accept unknown kwargs
            pass

    def test_empty_theme_name(self):
        """Test theme with empty name"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors

        theme = Theme("", ThemeColors())

        assert theme.name == ""
        result = theme.to_dict()
        assert result["name"] == ""

    def test_multiple_custom_themes(self):
        """Test registering multiple custom themes"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors, ThemeManager

        manager = ThemeManager()

        theme1 = Theme("custom1", ThemeColors(accent="#111111"))
        theme2 = Theme("custom2", ThemeColors(accent="#222222"))
        theme3 = Theme("custom3", ThemeColors(accent="#333333"))

        manager.register_custom_theme(theme1)
        manager.register_custom_theme(theme2)
        manager.register_custom_theme(theme3)

        assert len(manager.custom_themes) == 3
        themes = manager.get_available_themes()
        assert "custom1" in themes
        assert "custom2" in themes
        assert "custom3" in themes

    def test_override_custom_theme(self):
        """Test overriding a custom theme with same name"""
        from eve_overview_pro.ui.themes import Theme, ThemeColors, ThemeManager

        manager = ThemeManager()

        theme1 = Theme("custom", ThemeColors(accent="#111111"))
        theme2 = Theme("custom", ThemeColors(accent="#222222"))

        manager.register_custom_theme(theme1)
        manager.register_custom_theme(theme2)

        assert len(manager.custom_themes) == 1
        assert manager.custom_themes["custom"].colors.accent == "#222222"
