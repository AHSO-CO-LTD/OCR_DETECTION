"""
Enhanced Auto-update Checker - Intelligent delta updates
Checks GitHub Releases API for new versions with manifest-based delta updates
Provides one-click update with automatic restart capability
"""

import threading
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer

from lib.Updater import DeltaUpdater, UpdateInfo
from lib.UpdateDialog import UpdateNotificationDialog, UpdateProgressDialog


class UpdateChecker:
    """Check for newer releases on GitHub with delta update capability"""

    TIMEOUT_SECONDS = 10

    def __init__(self, current_version: str, parent=None, app_path=None):
        """
        Args:
            current_version: Current app version (e.g., "1.0.0")
            parent: Parent widget for showing dialogs
            app_path: Path to application directory
        """
        self.current_version = current_version
        self.parent = parent
        self.app_path = app_path

        # Initialize delta updater
        self.delta_updater = DeltaUpdater(app_path)

        # Connect updater signals
        self.delta_updater.error.connect(self._on_updater_error)
        self.delta_updater.status_changed.connect(self._on_updater_status)
        self.delta_updater.update_available.connect(self._on_update_found)

        self.update_info = None
        self.progress_dialog = None

    def check_for_updates(self):
        """Check for updates in background thread"""
        thread = threading.Thread(target=self._check_async, daemon=True)
        thread.start()

    def _check_async(self):
        """Async update check (runs in background thread)"""
        try:
            # Use delta updater to check
            update_info = self.delta_updater.check_for_updates()

            if update_info:
                self.update_info = update_info
                QTimer.singleShot(0, self._show_update_dialog)

        except Exception:
            pass  # Silent error — don't block startup

    def _show_update_dialog(self):
        """Show update notification dialog"""
        if not self.parent or not self.update_info:
            return

        dialog = UpdateNotificationDialog(self.update_info, self.parent)
        dialog.update_confirmed.connect(self._on_update_confirmed)
        dialog.update_skipped.connect(self._on_update_skipped)
        dialog.exec_()

    def _on_update_confirmed(self):
        """Handle user confirming update"""
        if not self.update_info:
            return

        # Show progress dialog
        self.progress_dialog = UpdateProgressDialog(self.update_info, self.parent)

        # Connect updater signals to progress dialog
        self.delta_updater.progress.connect(self.progress_dialog.update_progress)
        self.delta_updater.status_changed.connect(self.progress_dialog.update_status)
        self.delta_updater.update_complete.connect(self._on_update_complete)
        self.delta_updater.error.connect(lambda msg: self.progress_dialog.on_error(msg))

        # Start update in separate thread
        thread = threading.Thread(
            target=self.delta_updater.download_and_apply,
            args=(self.update_info,),
            daemon=True
        )
        thread.start()

        # Show progress dialog
        self.progress_dialog.exec_()

    def _on_update_skipped(self):
        """Handle user skipping update"""
        # Do nothing, user will be reminded next time
        pass

    def _on_update_found(self, update_info: UpdateInfo):
        """Handle update found signal from delta updater"""
        self.update_info = update_info

    def _on_update_complete(self):
        """Handle update completed"""
        if self.progress_dialog:
            self.progress_dialog.on_complete()

            # Schedule restart after dialog closes
            QTimer.singleShot(3100, self._trigger_restart)

    def _on_updater_error(self, error_msg: str):
        """Handle error from delta updater"""
        if self.progress_dialog:
            self.progress_dialog.on_error(error_msg)

    def _on_updater_status(self, status_msg: str):
        """Handle status update from delta updater"""
        if self.progress_dialog:
            self.progress_dialog.update_status(status_msg)

    def _trigger_restart(self):
        """Trigger application restart"""
        try:
            self.delta_updater.trigger_restart()
        except Exception as e:
            print(f"Error triggering restart: {e}")
            if self.parent:
                QMessageBox.information(
                    self.parent,
                    "Update Complete",
                    "Update completed successfully! Please restart the application to apply changes."
                )
