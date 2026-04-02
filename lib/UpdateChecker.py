"""
Auto-update checker for OCR-Metal-Core-Washing

Checks GitHub Releases API for new versions and notifies user.
Runs in background thread to avoid blocking UI.
"""

import threading
import requests
from packaging import version as pkg_version
from PyQt5.QtWidgets import QMessageBox


class UpdateChecker:
    """Check for newer releases on GitHub"""

    REPO_URL = "https://api.github.com/repos/AHSO-CO-LTD/OCR-Metal-Core-Washing/releases/latest"
    TIMEOUT_SECONDS = 5  # Don't block UI for more than 5 seconds

    def __init__(self, current_version: str, parent=None):
        """
        Args:
            current_version: Current app version (e.g., "1.0.0")
            parent: Parent widget for showing dialogs
        """
        self.current_version = current_version
        self.parent = parent
        self.latest_version = None
        self.download_url = None

    def check_for_updates(self):
        """Check for updates in background thread"""
        thread = threading.Thread(target=self._check_async, daemon=True)
        thread.start()

    def _check_async(self):
        """Async update check (runs in background thread)"""
        try:
            response = requests.get(self.REPO_URL, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()

            data = response.json()
            self.latest_version = data.get("tag_name", "").lstrip("v")

            if not self.latest_version:
                return

            # Compare versions
            if pkg_version.parse(self.latest_version) > pkg_version.parse(self.current_version):
                self.download_url = data.get("html_url", "")
                self._show_update_available()

        except requests.exceptions.Timeout:
            pass  # Silent timeout — don't block startup
        except requests.exceptions.RequestException:
            pass  # Silent network error — don't block startup
        except Exception:
            pass  # Silent error — don't block startup

    def _show_update_available(self):
        """Show notification dialog to user"""
        if not self.parent:
            return

        msg_box = QMessageBox(self.parent)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("New Version Available")
        msg_box.setText(
            f"A new version is available!\n\n"
            f"Current: v{self.current_version}\n"
            f"Latest: v{self.latest_version}\n\n"
            f"Click 'Yes' to visit the download page."
        )
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        if msg_box.exec_() == QMessageBox.Yes:
            import webbrowser
            webbrowser.open(self.download_url)
