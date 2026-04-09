"""
Update Dialog - User interface for application updates
Shows version info, changelog, download progress, and update controls
"""

import re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon

from lib.Updater import DeltaUpdater, UpdateInfo


class UpdateNotificationDialog(QDialog):
    """
    Dialog for notifying user about available update
    Shows version, changelog, and action buttons
    """

    update_confirmed = pyqtSignal()  # User clicked "Update Now"
    update_skipped = pyqtSignal()     # User clicked "Skip" or "Remind Later"

    def __init__(self, update_info: UpdateInfo, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("Application Update Available")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Header - Update icon and version info
        header = QWidget()
        header_layout = QHBoxLayout(header)

        # Icon placeholder (you can add a real icon here)
        icon_label = QLabel("🔄")
        icon_label.setFont(QFont("Arial", 32))
        icon_label.setAlignment(Qt.AlignCenter)

        # Version info
        version_widget = QWidget()
        version_layout = QVBoxLayout(version_widget)
        version_layout.setContentsMargins(10, 0, 0, 0)

        title = QLabel(f"New Version Available: v{self.update_info.version}")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        version_layout.addWidget(title)

        size_mb = self.update_info.file_size / (1024 * 1024)
        package_label = QLabel(
            f"Package type: {self.update_info.package_type.upper()} "
            f"(Download size: ~{size_mb:.1f} MB)"
        )
        package_label.setFont(QFont("Arial", 10))
        package_label.setStyleSheet("color: #666666;")
        version_layout.addWidget(package_label)

        header_layout.addWidget(icon_label)
        header_layout.addWidget(version_widget)
        header_layout.addStretch()

        layout.addWidget(header)

        # Changelog
        changelog_label = QLabel("What's New:")
        changelog_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(changelog_label)

        changelog_text = QTextEdit()
        changelog_text.setReadOnly(True)
        changelog_text.setMaximumHeight(150)
        changelog_text.setText(self._format_changelog(self.update_info.changelog))
        layout.addWidget(changelog_text)

        # Info message
        info_label = QLabel(
            "Your application will restart automatically after the update is complete."
        )
        info_label.setStyleSheet("color: #FF9800; background-color: #FFF3E0; padding: 10px; border-radius: 4px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        skip_button = QPushButton("Skip for Now")
        skip_button.setMinimumWidth(120)
        skip_button.clicked.connect(self.on_skip)
        button_layout.addWidget(skip_button)

        update_button = QPushButton("Update Now")
        update_button.setMinimumWidth(120)
        update_button.setStyleSheet(
            "QPushButton {"
            "  background-color: #4CAF50;"
            "  color: white;"
            "  font-weight: bold;"
            "  padding: 8px;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #45a049;"
            "}"
        )
        update_button.clicked.connect(self.on_update)
        button_layout.addWidget(update_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _format_changelog(self, changelog: str) -> str:
        """Format changelog text for display"""
        if not changelog:
            return "No changelog available"

        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', changelog)

        # Limit to first 500 characters
        if len(text) > 500:
            text = text[:500] + "\n... (see full changelog on GitHub)"

        return text

    def on_update(self):
        """Handle update button click"""
        self.update_confirmed.emit()
        self.accept()

    def on_skip(self):
        """Handle skip button click"""
        self.update_skipped.emit()
        self.reject()


class UpdateProgressDialog(QDialog):
    """
    Dialog showing update progress
    Displays download progress, status messages, and estimated time
    """

    cancel_requested = pyqtSignal()

    def __init__(self, update_info: UpdateInfo, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.start_time = None
        self.downloaded_bytes = 0
        self.setWindowTitle("Updating Application")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(250)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)  # No close button

        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Updating Application...")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Status message
        self.status_label = QLabel("Preparing update...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Details
        self.details_label = QLabel("Starting download...")
        self.details_label.setStyleSheet("color: #666666; font-size: 10px;")
        layout.addWidget(self.details_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self.on_cancel)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def update_status(self, status_text: str):
        """Update status message"""
        self.status_label.setText(status_text)

    def update_progress(self, downloaded: int, total: int):
        """Update download progress"""
        import time
        if self.start_time is None:
            self.start_time = time.time()

        self.downloaded_bytes = downloaded

        if total > 0:
            percentage = int((downloaded / total) * 100)
            self.progress_bar.setValue(percentage)

            # Calculate speed and ETA
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                speed = downloaded / elapsed / (1024 * 1024)  # MB/s
                remaining_bytes = total - downloaded
                eta_seconds = remaining_bytes / (downloaded / elapsed) if elapsed > 0 else 0

                # Format details
                downloaded_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)

                eta_text = self._format_eta(eta_seconds)
                details = (
                    f"Downloaded: {downloaded_mb:.1f}/{total_mb:.1f} MB "
                    f"| Speed: {speed:.1f} MB/s | ETA: {eta_text}"
                )
                self.details_label.setText(details)

    def on_cancel(self):
        """Handle cancel button click"""
        self.cancel_requested.emit()
        self.reject()

    def on_complete(self):
        """Call when update completes"""
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ Update completed successfully!")
        self.details_label.setText("Application will restart in 3 seconds...")
        self.cancel_button.setText("Close")

        # Auto close after 3 seconds
        QTimer.singleShot(3000, self.accept)

    def on_error(self, error_msg: str):
        """Handle error during update"""
        self.status_label.setText(f"[FAIL] Update failed: {error_msg}")
        self.status_label.setStyleSheet("color: #D32F2F;")
        self.cancel_button.setText("Close")

    @staticmethod
    def _format_eta(seconds: float) -> str:
        """Format ETA in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Test UpdateNotificationDialog
    update_info = UpdateInfo(
        "1.2.0",
        "• Fixed camera reconnection bug\n• Improved PLC communication\n• Added new features",
        "core"
    )
    update_info.file_size = 15 * 1024 * 1024  # 15 MB

    dialog = UpdateNotificationDialog(update_info)
    dialog.exec_()
