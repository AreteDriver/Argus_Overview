"""
Intel Tab - EVE Online chat log monitoring and intel alerts.

Monitors configured intel channels for hostile reports and triggers
visual and audio alerts.
"""

import logging
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from argus_overview.intel.alerts import AlertConfig, AlertDispatcher, AlertType
from argus_overview.intel.log_watcher import ChatLogWatcher, ChatMessage
from argus_overview.intel.parser import IntelParser, IntelReport, ThreatLevel


class IntelLogTable(QTableWidget):
    """Table widget for displaying intel reports."""

    entry_selected = Signal(object)  # IntelReport

    # Colors for threat levels
    THREAT_COLORS = {
        ThreatLevel.CLEAR: QColor("#2E7D32"),  # Green
        ThreatLevel.INFO: QColor("#0288D1"),  # Blue
        ThreatLevel.WARNING: QColor("#F57C00"),  # Orange
        ThreatLevel.DANGER: QColor("#D32F2F"),  # Red
        ThreatLevel.CRITICAL: QColor("#B71C1C"),  # Dark red
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.reports: List[IntelReport] = []

        self._setup_table()

    def _setup_table(self):
        """Setup table columns and appearance."""
        columns = ["Time", "Threat", "System", "Count", "Ships", "Message"]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)

        # Appearance
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

        # Column sizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Threat
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # System
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Count
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Ships
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Message

        # Selection signal
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def add_report(self, report: IntelReport):
        """Add an intel report to the table."""
        self.reports.insert(0, report)  # Newest first

        # Insert at top
        self.insertRow(0)

        # Time
        time_str = report.timestamp.strftime("%H:%M:%S")
        time_item = QTableWidgetItem(time_str)
        time_item.setData(Qt.ItemDataRole.UserRole, report)
        self.setItem(0, 0, time_item)

        # Threat level
        threat_item = QTableWidgetItem(report.threat_level.value.upper())
        threat_color = self.THREAT_COLORS.get(report.threat_level, QColor("#888"))
        threat_item.setForeground(QBrush(threat_color))
        threat_item.setFont(QFont("", -1, QFont.Weight.Bold))
        self.setItem(0, 1, threat_item)

        # System
        system_item = QTableWidgetItem(report.system or "Unknown")
        self.setItem(0, 2, system_item)

        # Count
        count_str = str(report.hostile_count) if report.hostile_count else "-"
        count_item = QTableWidgetItem(count_str)
        self.setItem(0, 3, count_item)

        # Ships
        ships_str = ", ".join(report.ship_types[:3]) if report.ship_types else "-"
        if len(report.ship_types) > 3:
            ships_str += f" +{len(report.ship_types) - 3}"
        ships_item = QTableWidgetItem(ships_str)
        self.setItem(0, 4, ships_item)

        # Message (truncated)
        msg_text = report.raw_message[:100]
        if len(report.raw_message) > 100:
            msg_text += "..."
        msg_item = QTableWidgetItem(msg_text)
        msg_item.setToolTip(report.raw_message)
        self.setItem(0, 5, msg_item)

        # Apply row background color based on threat
        for col in range(self.columnCount()):
            item = self.item(0, col)
            if item:
                bg_color = QColor(threat_color)
                bg_color.setAlpha(30)  # Very transparent
                item.setBackground(QBrush(bg_color))

        # Limit rows (keep last 500)
        while self.rowCount() > 500:
            self.removeRow(self.rowCount() - 1)
            self.reports.pop()

    def _on_selection_changed(self):
        """Handle row selection."""
        items = self.selectedItems()
        if items:
            row = items[0].row()
            if row < len(self.reports):
                self.entry_selected.emit(self.reports[row])

    def get_selected_report(self) -> Optional[IntelReport]:
        """Get currently selected report."""
        items = self.selectedItems()
        if items:
            row = items[0].row()
            if row < len(self.reports):
                return self.reports[row]
        return None

    def clear_all(self):
        """Clear all reports."""
        self.reports.clear()
        self.setRowCount(0)


class IntelTab(QWidget):
    """
    Intel monitoring tab.

    Monitors EVE chat logs for intel and triggers alerts.
    """

    # Signals
    intel_received = Signal(object)  # IntelReport
    alert_triggered = Signal(object, object)  # IntelReport, AlertType

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager

        # Core components
        self.log_watcher = ChatLogWatcher()
        self.intel_parser = IntelParser()
        self.alert_config = self._load_alert_config()
        self.alert_dispatcher = AlertDispatcher(self.alert_config)

        # Connect internal signals
        self.log_watcher.message_received.connect(self._on_chat_message)
        self.log_watcher.error_occurred.connect(self._on_watcher_error)
        self.alert_dispatcher.alert_triggered.connect(self._on_alert_triggered)

        # UI setup
        self._setup_ui()
        self._load_settings()

        self.logger.info("Intel tab initialized")

    def _load_alert_config(self) -> AlertConfig:
        """Load alert configuration from settings."""
        return AlertConfig(
            enabled=self.settings_manager.get("intel.alerts_enabled", True),
            visual_border=self.settings_manager.get("intel.visual_border", True),
            visual_overlay=self.settings_manager.get("intel.visual_overlay", True),
            audio=self.settings_manager.get("intel.audio_enabled", True),
            system_notification=self.settings_manager.get("intel.system_notification", False),
            min_threat_level=self.settings_manager.get("intel.min_threat_level", "warning"),
            jumps_threshold=self.settings_manager.get("intel.jumps_threshold", 5),
            cooldown_seconds=self.settings_manager.get("intel.cooldown_seconds", 5),
        )

    def _load_settings(self):
        """Load settings from settings manager."""
        # Monitored channels
        channels = self.settings_manager.get("intel.channels", ["Alliance", "Intel"])
        self.log_watcher.set_monitored_channels(channels)
        self._update_channel_list()

        # Custom log path
        custom_path = self.settings_manager.get("intel.custom_log_path", "")
        if custom_path:
            path = Path(custom_path)
            if path.exists():
                self.log_watcher.set_log_directory(path)

        # Update UI
        self._update_settings_ui()

    def _save_settings(self):
        """Save settings to settings manager."""
        # Channels
        channels = list(self.log_watcher.monitored_channels)
        self.settings_manager.set("intel.channels", channels, auto_save=False)

        # Alert config
        self.settings_manager.set(
            "intel.alerts_enabled", self.alert_config.enabled, auto_save=False
        )
        self.settings_manager.set(
            "intel.visual_border", self.alert_config.visual_border, auto_save=False
        )
        self.settings_manager.set(
            "intel.visual_overlay", self.alert_config.visual_overlay, auto_save=False
        )
        self.settings_manager.set("intel.audio_enabled", self.alert_config.audio, auto_save=False)
        self.settings_manager.set(
            "intel.system_notification", self.alert_config.system_notification, auto_save=False
        )
        self.settings_manager.set(
            "intel.min_threat_level", self.alert_config.min_threat_level, auto_save=False
        )
        self.settings_manager.set(
            "intel.jumps_threshold", self.alert_config.jumps_threshold, auto_save=False
        )
        self.settings_manager.set(
            "intel.cooldown_seconds", self.alert_config.cooldown_seconds, auto_save=False
        )

        self.settings_manager.save_settings()

    def _setup_ui(self):
        """Setup the tab UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main content with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

        # Left: Intel log
        log_panel = self._create_log_panel()
        splitter.addWidget(log_panel)

        # Right: Settings panel
        settings_panel = self._create_settings_panel()
        splitter.addWidget(settings_panel)

        # Set splitter sizes (70/30)
        splitter.setSizes([700, 300])

        # Status bar
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self.status_label)

    def _create_toolbar(self) -> QWidget:
        """Create toolbar with action buttons."""
        toolbar = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        toolbar.setLayout(layout)

        # Start/Stop button
        self.start_stop_btn = QPushButton("Start Monitoring")
        self.start_stop_btn.setCheckable(True)
        self.start_stop_btn.clicked.connect(self._toggle_monitoring)
        layout.addWidget(self.start_stop_btn)

        # Add channel button
        add_channel_btn = QPushButton("Add Channel")
        add_channel_btn.clicked.connect(self._add_channel)
        layout.addWidget(add_channel_btn)

        # Clear log button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self._clear_log)
        layout.addWidget(clear_btn)

        # Test alert button
        test_btn = QPushButton("Test Alert")
        test_btn.clicked.connect(self._test_alert)
        layout.addWidget(test_btn)

        layout.addStretch()

        # Log directory indicator
        self.log_dir_label = QLabel("Log Dir: Not found")
        self.log_dir_label.setStyleSheet("color: #888;")
        layout.addWidget(self.log_dir_label)

        return toolbar

    def _create_log_panel(self) -> QWidget:
        """Create intel log display panel."""
        panel = QGroupBox("Intel Log")
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Intel table
        self.intel_table = IntelLogTable()
        self.intel_table.entry_selected.connect(self._on_entry_selected)
        self.intel_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.intel_table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.intel_table)

        return panel

    def _create_settings_panel(self) -> QWidget:
        """Create settings panel."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Channels group
        channels_group = QGroupBox("Monitored Channels")
        channels_layout = QVBoxLayout()
        channels_group.setLayout(channels_layout)

        self.channel_list = QListWidget()
        self.channel_list.setMaximumHeight(100)
        channels_layout.addWidget(self.channel_list)

        channel_btns = QHBoxLayout()
        remove_channel_btn = QPushButton("Remove")
        remove_channel_btn.clicked.connect(self._remove_channel)
        channel_btns.addWidget(remove_channel_btn)
        channel_btns.addStretch()
        channels_layout.addLayout(channel_btns)

        layout.addWidget(channels_group)

        # Alert settings group
        alert_group = QGroupBox("Alert Settings")
        alert_layout = QFormLayout()
        alert_group.setLayout(alert_layout)

        # Enable alerts
        self.alerts_enabled_cb = QCheckBox("Enable Alerts")
        self.alerts_enabled_cb.setChecked(self.alert_config.enabled)
        self.alerts_enabled_cb.stateChanged.connect(self._on_alert_setting_changed)
        alert_layout.addRow(self.alerts_enabled_cb)

        # Visual border
        self.visual_border_cb = QCheckBox("Visual Border Flash")
        self.visual_border_cb.setChecked(self.alert_config.visual_border)
        self.visual_border_cb.stateChanged.connect(self._on_alert_setting_changed)
        alert_layout.addRow(self.visual_border_cb)

        # Visual overlay
        self.visual_overlay_cb = QCheckBox("Show Overlay Notification")
        self.visual_overlay_cb.setChecked(self.alert_config.visual_overlay)
        self.visual_overlay_cb.stateChanged.connect(self._on_alert_setting_changed)
        alert_layout.addRow(self.visual_overlay_cb)

        # Audio
        self.audio_cb = QCheckBox("Audio Alert")
        self.audio_cb.setChecked(self.alert_config.audio)
        self.audio_cb.stateChanged.connect(self._on_alert_setting_changed)
        alert_layout.addRow(self.audio_cb)

        # System notification
        self.sys_notify_cb = QCheckBox("Desktop Notification")
        self.sys_notify_cb.setChecked(self.alert_config.system_notification)
        self.sys_notify_cb.stateChanged.connect(self._on_alert_setting_changed)
        alert_layout.addRow(self.sys_notify_cb)

        # Minimum threat level
        self.threat_level_combo = QComboBox()
        self.threat_level_combo.addItems(["info", "warning", "danger", "critical"])
        idx = self.threat_level_combo.findText(self.alert_config.min_threat_level)
        if idx >= 0:
            self.threat_level_combo.setCurrentIndex(idx)
        self.threat_level_combo.currentTextChanged.connect(self._on_alert_setting_changed)
        alert_layout.addRow("Min Threat Level:", self.threat_level_combo)

        # Jumps threshold
        self.jumps_spin = QSpinBox()
        self.jumps_spin.setRange(0, 50)
        self.jumps_spin.setValue(self.alert_config.jumps_threshold)
        self.jumps_spin.valueChanged.connect(self._on_alert_setting_changed)
        alert_layout.addRow("Alert within (jumps):", self.jumps_spin)

        # Cooldown
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(0, 60)
        self.cooldown_spin.setValue(self.alert_config.cooldown_seconds)
        self.cooldown_spin.valueChanged.connect(self._on_alert_setting_changed)
        alert_layout.addRow("Cooldown (seconds):", self.cooldown_spin)

        layout.addWidget(alert_group)

        # Current system group
        location_group = QGroupBox("Current Location")
        location_layout = QFormLayout()
        location_group.setLayout(location_layout)

        self.current_system_edit = QLineEdit()
        self.current_system_edit.setPlaceholderText("e.g., HED-GP")
        self.current_system_edit.textChanged.connect(self._on_current_system_changed)
        location_layout.addRow("Current System:", self.current_system_edit)

        location_note = QLabel("Set your current system to enable jump distance filtering")
        location_note.setStyleSheet("color: #888; font-size: 10px;")
        location_note.setWordWrap(True)
        location_layout.addRow(location_note)

        layout.addWidget(location_group)

        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _update_channel_list(self):
        """Update the channel list display."""
        self.channel_list.clear()
        for channel in sorted(self.log_watcher.monitored_channels):
            self.channel_list.addItem(channel)

    def _update_settings_ui(self):
        """Update settings UI from config."""
        self.alerts_enabled_cb.setChecked(self.alert_config.enabled)
        self.visual_border_cb.setChecked(self.alert_config.visual_border)
        self.visual_overlay_cb.setChecked(self.alert_config.visual_overlay)
        self.audio_cb.setChecked(self.alert_config.audio)
        self.sys_notify_cb.setChecked(self.alert_config.system_notification)

        idx = self.threat_level_combo.findText(self.alert_config.min_threat_level)
        if idx >= 0:
            self.threat_level_combo.setCurrentIndex(idx)

        self.jumps_spin.setValue(self.alert_config.jumps_threshold)
        self.cooldown_spin.setValue(self.alert_config.cooldown_seconds)

    def _update_log_dir_label(self):
        """Update log directory label."""
        log_dir = self.log_watcher.get_log_directory()
        if log_dir:
            # Show abbreviated path
            path_str = str(log_dir)
            if len(path_str) > 40:
                path_str = "..." + path_str[-37:]
            self.log_dir_label.setText(f"Log Dir: {path_str}")
            self.log_dir_label.setToolTip(str(log_dir))
            self.log_dir_label.setStyleSheet("color: #4CAF50;")
        else:
            self.log_dir_label.setText("Log Dir: Not found")
            self.log_dir_label.setStyleSheet("color: #F44336;")

    # -------------------------------------------------------------------------
    # Slots and handlers
    # -------------------------------------------------------------------------

    @Slot()
    def _toggle_monitoring(self):
        """Toggle intel monitoring on/off."""
        if self.log_watcher.is_running():
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self):
        """Start intel monitoring."""
        self.log_watcher.start()
        self.start_stop_btn.setText("Stop Monitoring")
        self.start_stop_btn.setChecked(True)
        self.status_label.setText("Status: Monitoring...")
        self.status_label.setStyleSheet("color: #4CAF50; padding: 5px;")
        self._update_log_dir_label()
        self.logger.info("Intel monitoring started")

    def _stop_monitoring(self):
        """Stop intel monitoring."""
        self.log_watcher.stop()
        self.start_stop_btn.setText("Start Monitoring")
        self.start_stop_btn.setChecked(False)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        self.logger.info("Intel monitoring stopped")

    @Slot()
    def _add_channel(self):
        """Add a new channel to monitor."""
        channel, ok = QInputDialog.getText(
            self,
            "Add Intel Channel",
            "Enter channel name (e.g., Alliance, Intel):",
        )
        if ok and channel:
            channel = channel.strip()
            if channel:
                self.log_watcher.add_channel(channel)
                self._update_channel_list()
                self._save_settings()
                self.logger.info(f"Added intel channel: {channel}")

    @Slot()
    def _remove_channel(self):
        """Remove selected channel."""
        item = self.channel_list.currentItem()
        if item:
            channel = item.text()
            self.log_watcher.remove_channel(channel)
            self._update_channel_list()
            self._save_settings()
            self.logger.info(f"Removed intel channel: {channel}")

    @Slot()
    def _clear_log(self):
        """Clear the intel log."""
        self.intel_table.clear_all()
        self.logger.info("Intel log cleared")

    @Slot()
    def _test_alert(self):
        """Trigger a test alert."""
        self.alert_dispatcher.test_alert(ThreatLevel.WARNING)

    @Slot(object)
    def _on_chat_message(self, message: ChatMessage):
        """Handle incoming chat message."""
        # Check if it's from a monitored channel
        if self.log_watcher.monitored_channels:
            if message.channel.lower() not in self.log_watcher.monitored_channels:
                return

        # Parse for intel
        report = self.intel_parser.parse(
            message.message,
            timestamp=message.timestamp,
            channel=message.channel,
            reporter=message.speaker,
        )

        if report:
            self.logger.debug(f"Intel detected: {report.system} - {report.threat_level.value}")

            # Add to table
            self.intel_table.add_report(report)

            # Dispatch alerts
            self.alert_dispatcher.dispatch(report)

            # Emit signal
            self.intel_received.emit(report)

    @Slot(str)
    def _on_watcher_error(self, error: str):
        """Handle watcher error."""
        self.logger.error(f"Log watcher error: {error}")
        self.status_label.setText(f"Error: {error}")
        self.status_label.setStyleSheet("color: #F44336; padding: 5px;")

    @Slot(object)
    def _on_entry_selected(self, report: IntelReport):
        """Handle intel entry selection."""
        # Could show details panel in future
        pass

    @Slot(object, object)
    def _on_alert_triggered(self, report: IntelReport, alert_type: AlertType):
        """Handle alert trigger."""
        self.alert_triggered.emit(report, alert_type)

    @Slot()
    def _on_alert_setting_changed(self):
        """Handle alert setting change."""
        self.alert_config.enabled = self.alerts_enabled_cb.isChecked()
        self.alert_config.visual_border = self.visual_border_cb.isChecked()
        self.alert_config.visual_overlay = self.visual_overlay_cb.isChecked()
        self.alert_config.audio = self.audio_cb.isChecked()
        self.alert_config.system_notification = self.sys_notify_cb.isChecked()
        self.alert_config.min_threat_level = self.threat_level_combo.currentText()
        self.alert_config.jumps_threshold = self.jumps_spin.value()
        self.alert_config.cooldown_seconds = self.cooldown_spin.value()

        self.alert_dispatcher.set_config(self.alert_config)
        self._save_settings()

    @Slot(str)
    def _on_current_system_changed(self, system: str):
        """Handle current system change."""
        # In future, could integrate with system map for jump calculations
        self.settings_manager.set("intel.current_system", system.strip())

    def _show_context_menu(self, pos):
        """Show context menu for intel entry."""
        report = self.intel_table.get_selected_report()
        if not report:
            return

        menu = QMenu(self)

        # Copy system
        if report.system:
            copy_system = menu.addAction("Copy System Name")
            copy_system.triggered.connect(lambda: self._copy_to_clipboard(report.system))

        # Copy message
        copy_msg = menu.addAction("Copy Message")
        copy_msg.triggered.connect(lambda: self._copy_to_clipboard(report.raw_message))

        menu.addSeparator()

        # Delete entry
        delete_action = menu.addAction("Delete Entry")
        delete_action.triggered.connect(self._delete_selected_entry)

        menu.exec(self.intel_table.mapToGlobal(pos))

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def _delete_selected_entry(self):
        """Delete selected intel entry."""
        rows = self.intel_table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            self.intel_table.removeRow(row)
            if row < len(self.intel_table.reports):
                self.intel_table.reports.pop(row)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def get_alert_dispatcher(self) -> AlertDispatcher:
        """Get the alert dispatcher for connecting signals."""
        return self.alert_dispatcher

    def stop(self):
        """Stop monitoring (called on app close)."""
        if self.log_watcher.is_running():
            self.log_watcher.stop()
