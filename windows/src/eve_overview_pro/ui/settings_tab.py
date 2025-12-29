"""
Settings Tab - Application settings configuration
Configure all application settings with category-based panels
"""
import logging
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class HotkeyEditDialog(QDialog):
    """Dialog for editing hotkey bindings"""

    def __init__(self, action: str, current_combo: str, hotkey_manager, parent=None):
        super().__init__(parent)
        self.action = action
        self.current_combo = current_combo
        self.hotkey_manager = hotkey_manager
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle(f"Edit Hotkey: {action}")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Action label
        action_label = QLabel(f"<b>Action:</b> {self.action}")
        layout.addWidget(action_label)

        # Current binding
        current_label = QLabel(f"Current: {self.current_combo}")
        current_label.setStyleSheet("color: #888;")
        layout.addWidget(current_label)

        # Key input
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Enter hotkey (e.g., Ctrl+Alt+1)")
        self.key_edit.setText(self.current_combo)
        layout.addWidget(self.key_edit)

        # Format hint
        hint_label = QLabel(
            "Format: <ctrl>+<alt>+<key> or <shift>+<key>\n"
            "Examples: <ctrl>+<alt>+1, <shift>+f5"
        )
        hint_label.setStyleSheet("color: #666; font-size: 9pt;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)

        # Test button
        test_btn = QPushButton("Test Hotkey")
        test_btn.clicked.connect(self._test_hotkey)
        layout.addWidget(test_btn)

        # Conflict check label
        self.conflict_label = QLabel("")
        self.conflict_label.setStyleSheet("color: #e74c3c;")
        layout.addWidget(self.conflict_label)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_hotkey)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _test_hotkey(self):
        """Test the hotkey binding"""
        combo = self.key_edit.text().strip()
        if not combo:
            QMessageBox.warning(self, "Invalid", "Please enter a hotkey.")
            return

        QMessageBox.information(
            self,
            "Test Hotkey",
            f"Hotkey '{combo}' would be registered for action '{self.action}'.\n\n"
            "Note: Actual testing requires hotkey manager integration."
        )

    def _save_hotkey(self):
        """Validate and save hotkey"""
        combo = self.key_edit.text().strip()
        if not combo:
            QMessageBox.warning(self, "Invalid", "Please enter a hotkey.")
            return

        # Basic validation
        if not ('<' in combo and '>' in combo):
            QMessageBox.warning(
                self, "Invalid Format",
                "Hotkey must be in format: <modifier>+<key>\n"
                "Example: <ctrl>+<alt>+1"
            )
            return

        self.accept()

    def get_hotkey(self) -> str:
        """Get the configured hotkey"""
        return self.key_edit.text().strip()


# Settings Panels

class GeneralPanel(QWidget):
    """General application settings"""
    setting_changed = Signal(str, object)

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        group = QGroupBox("General Settings")
        form = QFormLayout()

        # Start with system
        self.start_system_check = QCheckBox()
        self.start_system_check.setChecked(
            self.settings_manager.get("general.start_with_system", False)
        )
        self.start_system_check.stateChanged.connect(
            lambda: self.setting_changed.emit("general.start_with_system", self.start_system_check.isChecked())
        )
        form.addRow("Start with system:", self.start_system_check)

        # Minimize to tray
        self.minimize_tray_check = QCheckBox()
        self.minimize_tray_check.setChecked(
            self.settings_manager.get("general.minimize_to_tray", True)
        )
        self.minimize_tray_check.stateChanged.connect(
            lambda: self.setting_changed.emit("general.minimize_to_tray", self.minimize_tray_check.isChecked())
        )
        form.addRow("Minimize to tray:", self.minimize_tray_check)

        # Show notifications
        self.notifications_check = QCheckBox()
        self.notifications_check.setChecked(
            self.settings_manager.get("general.show_notifications", True)
        )
        self.notifications_check.stateChanged.connect(
            lambda: self.setting_changed.emit("general.show_notifications", self.notifications_check.isChecked())
        )
        form.addRow("Show notifications:", self.notifications_check)

        # Auto-save interval
        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(1, 60)
        self.auto_save_spin.setValue(
            self.settings_manager.get("general.auto_save_interval", 5)
        )
        self.auto_save_spin.setSuffix(" min")
        self.auto_save_spin.valueChanged.connect(
            lambda v: self.setting_changed.emit("general.auto_save_interval", v)
        )
        form.addRow("Auto-save interval:", self.auto_save_spin)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()
        self.setLayout(layout)


class PerformancePanel(QWidget):
    """Performance settings"""
    setting_changed = Signal(str, object)

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        group = QGroupBox("Performance Settings")
        form = QFormLayout()

        # Refresh rate
        self.refresh_rate_spin = QSpinBox()
        self.refresh_rate_spin.setRange(1, 60)
        self.refresh_rate_spin.setValue(
            self.settings_manager.get("performance.default_refresh_rate", 30)
        )
        self.refresh_rate_spin.setSuffix(" FPS")
        self.refresh_rate_spin.valueChanged.connect(
            lambda v: self.setting_changed.emit("performance.default_refresh_rate", v)
        )
        form.addRow("Default refresh rate:", self.refresh_rate_spin)

        # Capture workers
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 16)
        self.workers_spin.setValue(
            self.settings_manager.get("performance.capture_workers", 4)
        )
        self.workers_spin.valueChanged.connect(
            lambda v: self.setting_changed.emit("performance.capture_workers", v)
        )
        form.addRow("Capture workers:", self.workers_spin)

        # Caching
        self.caching_check = QCheckBox()
        self.caching_check.setChecked(
            self.settings_manager.get("performance.enable_caching", True)
        )
        self.caching_check.stateChanged.connect(
            lambda: self.setting_changed.emit("performance.enable_caching", self.caching_check.isChecked())
        )
        form.addRow("Enable caching:", self.caching_check)

        # Cache size
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        self.cache_size_spin.setValue(
            self.settings_manager.get("performance.cache_size_mb", 100)
        )
        self.cache_size_spin.setSuffix(" MB")
        self.cache_size_spin.valueChanged.connect(
            lambda v: self.setting_changed.emit("performance.cache_size_mb", v)
        )
        form.addRow("Cache size:", self.cache_size_spin)

        # Capture quality
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["low", "medium", "high"])
        current_quality = self.settings_manager.get("performance.capture_quality", "medium")
        self.quality_combo.setCurrentText(current_quality)
        self.quality_combo.currentTextChanged.connect(
            lambda v: self.setting_changed.emit("performance.capture_quality", v)
        )
        form.addRow("Capture quality:", self.quality_combo)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()
        self.setLayout(layout)


class AlertsPanel(QWidget):
    """Alert settings"""
    setting_changed = Signal(str, object)

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Enable alerts
        self.alerts_check = QCheckBox("Enable alerts")
        self.alerts_check.setChecked(
            self.settings_manager.get("alerts.enabled", True)
        )
        self.alerts_check.stateChanged.connect(
            lambda: self.setting_changed.emit("alerts.enabled", self.alerts_check.isChecked())
        )
        layout.addWidget(self.alerts_check)

        # Red flash alerts
        red_flash_group = QGroupBox("Red Flash Detection")
        red_flash_layout = QFormLayout()

        self.red_flash_threshold = QSlider(Qt.Orientation.Horizontal)
        self.red_flash_threshold.setRange(0, 100)
        self.red_flash_threshold.setValue(
            int(self.settings_manager.get("alerts.red_flash.threshold", 0.7) * 100)
        )
        self.red_flash_threshold.valueChanged.connect(
            lambda v: self.setting_changed.emit("alerts.red_flash.threshold", v / 100.0)
        )
        red_flash_layout.addRow("Threshold:", self.red_flash_threshold)

        self.red_flash_visual = QCheckBox()
        self.red_flash_visual.setChecked(
            self.settings_manager.get("alerts.red_flash.visual_border", True)
        )
        self.red_flash_visual.stateChanged.connect(
            lambda: self.setting_changed.emit("alerts.red_flash.visual_border", self.red_flash_visual.isChecked())
        )
        red_flash_layout.addRow("Visual border:", self.red_flash_visual)

        self.red_flash_sound = QCheckBox()
        self.red_flash_sound.setChecked(
            self.settings_manager.get("alerts.red_flash.sound_alert", False)
        )
        self.red_flash_sound.stateChanged.connect(
            lambda: self.setting_changed.emit("alerts.red_flash.sound_alert", self.red_flash_sound.isChecked())
        )
        red_flash_layout.addRow("Sound alert:", self.red_flash_sound)

        self.red_flash_cooldown = QSpinBox()
        self.red_flash_cooldown.setRange(1, 60)
        self.red_flash_cooldown.setValue(
            self.settings_manager.get("alerts.red_flash.cooldown", 5)
        )
        self.red_flash_cooldown.setSuffix(" sec")
        self.red_flash_cooldown.valueChanged.connect(
            lambda v: self.setting_changed.emit("alerts.red_flash.cooldown", v)
        )
        red_flash_layout.addRow("Cooldown:", self.red_flash_cooldown)

        red_flash_group.setLayout(red_flash_layout)
        layout.addWidget(red_flash_group)

        # Screen change alerts
        screen_change_group = QGroupBox("Screen Change Detection")
        screen_change_layout = QFormLayout()

        self.screen_change_threshold = QSlider(Qt.Orientation.Horizontal)
        self.screen_change_threshold.setRange(0, 100)
        self.screen_change_threshold.setValue(
            int(self.settings_manager.get("alerts.screen_change.threshold", 0.3) * 100)
        )
        self.screen_change_threshold.valueChanged.connect(
            lambda v: self.setting_changed.emit("alerts.screen_change.threshold", v / 100.0)
        )
        screen_change_layout.addRow("Threshold:", self.screen_change_threshold)

        self.screen_change_visual = QCheckBox()
        self.screen_change_visual.setChecked(
            self.settings_manager.get("alerts.screen_change.visual_border", True)
        )
        self.screen_change_visual.stateChanged.connect(
            lambda: self.setting_changed.emit("alerts.screen_change.visual_border", self.screen_change_visual.isChecked())
        )
        screen_change_layout.addRow("Visual border:", self.screen_change_visual)

        screen_change_group.setLayout(screen_change_layout)
        layout.addWidget(screen_change_group)

        layout.addStretch()
        self.setLayout(layout)


class HotkeysPanel(QWidget):
    """Hotkey settings"""
    setting_changed = Signal(str, object)

    def __init__(self, settings_manager, hotkey_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.hotkey_manager = hotkey_manager
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._load_hotkeys()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Format label
        format_label = QLabel("Format: <ctrl>+<alt>+<key> or <shift>+<key>")
        format_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(format_label)

        # Hotkeys table
        self.hotkeys_table = QTableWidget()
        self.hotkeys_table.setColumnCount(3)
        self.hotkeys_table.setHorizontalHeaderLabels(["Action", "Hotkey", "Status"])
        self.hotkeys_table.horizontalHeader().setStretchLastSection(False)
        self.hotkeys_table.setColumnWidth(0, 200)
        self.hotkeys_table.setColumnWidth(1, 150)
        self.hotkeys_table.setColumnWidth(2, 80)
        self.hotkeys_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.hotkeys_table)

        # Buttons
        buttons_layout = QHBoxLayout()

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_hotkey)
        buttons_layout.addWidget(edit_btn)

        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self._reset_hotkey)
        buttons_layout.addWidget(reset_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def _load_hotkeys(self):
        """Load hotkeys from settings"""
        hotkeys = self.settings_manager.get("hotkeys", {})

        self.hotkeys_table.setRowCount(len(hotkeys))
        for row, (action, combo) in enumerate(hotkeys.items()):
            # Action
            action_item = QTableWidgetItem(action.replace("_", " ").title())
            self.hotkeys_table.setItem(row, 0, action_item)

            # Hotkey
            hotkey_item = QTableWidgetItem(combo)
            self.hotkeys_table.setItem(row, 1, hotkey_item)

            # Status
            status_item = QTableWidgetItem("Active")
            status_item.setForeground(QColor(0, 200, 0))
            self.hotkeys_table.setItem(row, 2, status_item)

    def _edit_hotkey(self):
        """Edit selected hotkey"""
        selected = self.hotkeys_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select a hotkey to edit.")
            return

        row = self.hotkeys_table.currentRow()
        action = self.hotkeys_table.item(row, 0).text()
        current_combo = self.hotkeys_table.item(row, 1).text()

        dialog = HotkeyEditDialog(action, current_combo, self.hotkey_manager, self)
        if dialog.exec():
            new_combo = dialog.get_hotkey()
            self.hotkeys_table.item(row, 1).setText(new_combo)

            # Save to settings
            action_key = action.lower().replace(" ", "_")
            self.setting_changed.emit(f"hotkeys.{action_key}", new_combo)

    def _reset_hotkey(self):
        """Reset selected hotkey to default"""
        selected = self.hotkeys_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select a hotkey to reset.")
            return

        QMessageBox.information(self, "Feature", "Reset to default will be implemented in a future update.")


class AppearancePanel(QWidget):
    """Appearance settings"""
    setting_changed = Signal(str, object)

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        group = QGroupBox("Appearance Settings")
        form = QFormLayout()

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "system"])
        self.theme_combo.setCurrentText(
            self.settings_manager.get("appearance.theme", "dark")
        )
        self.theme_combo.currentTextChanged.connect(
            lambda v: self.setting_changed.emit("appearance.theme", v)
        )
        form.addRow("Theme:", self.theme_combo)

        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(
            self.settings_manager.get("appearance.font_size", 10)
        )
        self.font_size_spin.setSuffix(" pt")
        self.font_size_spin.valueChanged.connect(
            lambda v: self.setting_changed.emit("appearance.font_size", v)
        )
        form.addRow("Font size:", self.font_size_spin)

        # Compact mode
        self.compact_check = QCheckBox()
        self.compact_check.setChecked(
            self.settings_manager.get("appearance.compact_mode", False)
        )
        self.compact_check.stateChanged.connect(
            lambda: self.setting_changed.emit("appearance.compact_mode", self.compact_check.isChecked())
        )
        form.addRow("Compact mode:", self.compact_check)

        # Accent color
        accent_layout = QHBoxLayout()
        self.accent_color = self.settings_manager.get("appearance.accent_color", "#4287f5")
        self.accent_btn = QPushButton()
        self.accent_btn.setStyleSheet(f"background-color: {self.accent_color}; min-height: 30px;")
        self.accent_btn.clicked.connect(self._pick_accent_color)
        accent_layout.addWidget(self.accent_btn)
        accent_layout.addStretch()

        form.addRow("Accent color:", accent_layout)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()
        self.setLayout(layout)

    def _pick_accent_color(self):
        """Pick accent color"""
        color = QColorDialog.getColor(QColor(self.accent_color), self, "Select Accent Color")
        if color.isValid():
            self.accent_color = color.name()
            self.accent_btn.setStyleSheet(f"background-color: {self.accent_color}; min-height: 30px;")
            self.setting_changed.emit("appearance.accent_color", self.accent_color)


class AdvancedPanel(QWidget):
    """Advanced settings"""
    setting_changed = Signal(str, object)

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        group = QGroupBox("Advanced Settings")
        form = QFormLayout()

        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(
            self.settings_manager.get("advanced.log_level", "INFO")
        )
        self.log_level_combo.currentTextChanged.connect(
            lambda v: self.setting_changed.emit("advanced.log_level", v)
        )
        form.addRow("Log level:", self.log_level_combo)

        # Config directory
        self.config_dir_label = QLabel(
            self.settings_manager.get("advanced.config_directory", "~/.config/eve-veles-eyes")
        )
        self.config_dir_label.setStyleSheet("color: #888;")
        form.addRow("Config directory:", self.config_dir_label)

        # Enable debug
        self.debug_check = QCheckBox()
        self.debug_check.setChecked(
            self.settings_manager.get("advanced.enable_debug", False)
        )
        self.debug_check.stateChanged.connect(
            lambda: self.setting_changed.emit("advanced.enable_debug", self.debug_check.isChecked())
        )
        form.addRow("Enable debug:", self.debug_check)

        group.setLayout(form)
        layout.addWidget(group)

        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()

        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.clicked.connect(self._clear_cache)
        actions_layout.addWidget(clear_cache_btn)

        export_btn = QPushButton("Export Settings")
        export_btn.clicked.connect(self._export_settings)
        actions_layout.addWidget(export_btn)

        import_btn = QPushButton("Import Settings")
        import_btn.clicked.connect(self._import_settings)
        actions_layout.addWidget(import_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()
        self.setLayout(layout)

    def _clear_cache(self):
        """Clear application cache"""
        QMessageBox.information(self, "Clear Cache", "Cache clearing will be implemented in a future update.")

    def _export_settings(self):
        """Export settings to file"""
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                from pathlib import Path
                self.settings_manager.export_config(Path(filename))
                QMessageBox.information(self, "Success", f"Settings exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export settings: {e}")

    def _import_settings(self):
        """Import settings from file"""
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                from pathlib import Path
                self.settings_manager.import_config(Path(filename))
                QMessageBox.information(
                    self, "Success",
                    f"Settings imported from {filename}\nRestart required to apply all changes."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import settings: {e}")


class SettingsTab(QWidget):
    """Main Settings Tab widget"""
    settings_changed = Signal(str, object)  # key, value

    def __init__(self, settings_manager, hotkey_manager, alert_detector):
        super().__init__()
        self.settings_manager = settings_manager
        self.hotkey_manager = hotkey_manager
        self.alert_detector = alert_detector
        self.logger = logging.getLogger(__name__)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QHBoxLayout()

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Category tree
        left_panel = self._create_category_tree()
        splitter.addWidget(left_panel)

        # Right: Stacked panels
        self.panel_stack = QStackedWidget()

        # Create panels
        self.general_panel = GeneralPanel(self.settings_manager)
        self.general_panel.setting_changed.connect(self._on_setting_changed)
        self.panel_stack.addWidget(self.general_panel)

        self.performance_panel = PerformancePanel(self.settings_manager)
        self.performance_panel.setting_changed.connect(self._on_setting_changed)
        self.panel_stack.addWidget(self.performance_panel)

        self.alerts_panel = AlertsPanel(self.settings_manager)
        self.alerts_panel.setting_changed.connect(self._on_setting_changed)
        self.panel_stack.addWidget(self.alerts_panel)

        self.hotkeys_panel = HotkeysPanel(self.settings_manager, self.hotkey_manager)
        self.hotkeys_panel.setting_changed.connect(self._on_setting_changed)
        self.panel_stack.addWidget(self.hotkeys_panel)

        self.appearance_panel = AppearancePanel(self.settings_manager)
        self.appearance_panel.setting_changed.connect(self._on_setting_changed)
        self.panel_stack.addWidget(self.appearance_panel)

        self.advanced_panel = AdvancedPanel(self.settings_manager)
        self.advanced_panel.setting_changed.connect(self._on_setting_changed)
        self.panel_stack.addWidget(self.advanced_panel)

        splitter.addWidget(self.panel_stack)

        splitter.setSizes([200, 600])
        layout.addWidget(splitter)

        self.setLayout(layout)

    def _create_category_tree(self) -> QWidget:
        """Create category tree widget"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Settings")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)

        categories = [
            "General",
            "Performance",
            "Alerts",
            "Hotkeys",
            "Appearance",
            "Advanced"
        ]

        for category in categories:
            item = QTreeWidgetItem([category])
            self.category_tree.addTopLevelItem(item)

        self.category_tree.currentItemChanged.connect(self._on_category_changed)
        layout.addWidget(self.category_tree)

        # Reset button
        reset_btn = QPushButton("Reset All to Defaults")
        reset_btn.clicked.connect(self._reset_all)
        layout.addWidget(reset_btn)

        widget.setLayout(layout)
        return widget

    def _on_category_changed(self, current, previous):
        """Handle category change"""
        if current:
            categories = {
                "General": 0,
                "Performance": 1,
                "Alerts": 2,
                "Hotkeys": 3,
                "Appearance": 4,
                "Advanced": 5
            }
            category = current.text(0)
            if category in categories:
                self.panel_stack.setCurrentIndex(categories[category])

    def _load_settings(self):
        """Load settings from SettingsManager"""
        # Settings are loaded by individual panels
        pass

    def _on_setting_changed(self, key: str, value: Any):
        """Handle setting change"""
        self.logger.info(f"Setting changed: {key} = {value}")

        # Save to SettingsManager
        self.settings_manager.set(key, value)

        # Emit signal for main window to apply
        self.settings_changed.emit(key, value)

    def _reset_all(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Reset all settings to defaults?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_to_defaults()
            QMessageBox.information(
                self, "Reset Complete",
                "All settings have been reset to defaults.\nRestart required to apply changes."
            )
