"""
About Dialog with donation link
"""
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class AboutDialog(QDialog):
    """About dialog with version info and donation link"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Argus Overview")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title = QLabel("Argus Overview")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Version
        version = QLabel("Version 2.3 - ActionRegistry Edition")
        version_font = QFont()
        version_font.setPointSize(12)
        version.setFont(version_font)
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #888;")
        layout.addWidget(version)

        # Platform
        platform = "Windows" if sys.platform == "win32" else "Linux"
        platform_label = QLabel(f"Platform: {platform}")
        platform_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        platform_label.setStyleSheet("color: #666;")
        layout.addWidget(platform_label)

        layout.addSpacing(20)

        # Description
        description = QLabel(
            "The Complete Professional Multi-Boxing Solution\n"
            "for EVE Online"
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addSpacing(10)

        # Features
        features = QLabel(
            "• Real-time Window Preview (30 FPS)\n"
            "• Character & Team Management\n"
            "• Smart Grid Layouts\n"
            "• Alert Detection\n"
            "• Settings Synchronization\n"
            "• Global Hotkeys"
        )
        features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(features)

        layout.addSpacing(20)

        # Donation section
        donation_label = QLabel("☕ Support Development")
        donation_font = QFont()
        donation_font.setPointSize(14)
        donation_font.setBold(True)
        donation_label.setFont(donation_font)
        donation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(donation_label)

        donation_text = QLabel(
            "If you find Argus Overview useful,\n"
            "consider supporting its development:"
        )
        donation_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        donation_text.setStyleSheet("color: #888;")
        layout.addWidget(donation_text)

        # Buy Me a Coffee button
        coffee_btn = QPushButton("☕ Buy Me a Coffee")
        coffee_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFDD00;
                color: #000;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #FFED4E;
            }
            QPushButton:pressed {
                background-color: #E5C400;
            }
        """)
        coffee_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        coffee_btn.clicked.connect(self._open_donation_link)

        coffee_layout = QHBoxLayout()
        coffee_layout.addStretch()
        coffee_layout.addWidget(coffee_btn)
        coffee_layout.addStretch()
        layout.addLayout(coffee_layout)

        layout.addSpacing(20)

        # Links
        links_layout = QVBoxLayout()

        github_link = QLabel('<a href="https://github.com/AreteDriver/Argus_Overview">GitHub Repository</a>')
        github_link.setOpenExternalLinks(True)
        github_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        links_layout.addWidget(github_link)

        issues_link = QLabel('<a href="https://github.com/AreteDriver/Argus_Overview/issues">Report Issues</a>')
        issues_link.setOpenExternalLinks(True)
        issues_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        links_layout.addWidget(issues_link)

        layout.addLayout(links_layout)

        layout.addStretch()

        # Credits
        credits = QLabel(
            "Made with ❤️ by AreteDriver\n"
            "For the EVE Online community"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(credits)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        close_layout.addStretch()
        layout.addLayout(close_layout)

        self.setLayout(layout)

    def _open_donation_link(self):
        """Open Buy Me a Coffee link in browser"""
        QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/aretedriver"))
