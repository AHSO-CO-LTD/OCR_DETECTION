"""
Delta Update Manager - Intelligent application updater
Supports manifest-based incremental updates with automatic restart
"""

import os
import json
import hashlib
import shutil
import zipfile
import tempfile
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from lib.Global import signal


class UpdateInfo:
    """Container for update information"""
    def __init__(self, version: str, changelog: str = "", package_type: str = "core"):
        self.version = version
        self.changelog = changelog
        self.package_type = package_type  # "core", "full", or "none"
        self.download_url = ""
        self.file_size = 0
        self.changed_files = []


class DeltaUpdater(QThread):
    """
    Manages delta updates for OCR Detection application

    Signals:
        - status_changed: (status_text) - Status update message
        - progress: (current_bytes, total_bytes) - Download progress
        - update_available: (UpdateInfo) - New version detected
        - update_complete: () - Update successfully applied
        - error: (error_message) - Error occurred
    """

    status_changed = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current_bytes, total_bytes
    update_available = pyqtSignal(UpdateInfo)
    update_complete = pyqtSignal()
    error = pyqtSignal(str)

    GITHUB_API = "https://api.github.com/repos/AHSO-CO-LTD/OCR_DETECTION/releases/latest"
    TIMEOUT = 10  # seconds
    CHUNK_SIZE = 8192  # bytes

    def __init__(self, app_path: str = None):
        super().__init__()
        self.daemon = True

        # Determine app directory
        if app_path:
            self.app_path = Path(app_path)
        else:
            if getattr(sys, 'frozen', False):
                # Running as EXE
                self.app_path = Path(sys.executable).parent
            else:
                # Running as script
                self.app_path = Path(__file__).parent.parent

        self.manifest_path = self.app_path / "manifest.json"
        self.update_dir = self.app_path / "temp"
        self.backup_dir = self.app_path / "backup"

        # Create temp directory
        self.update_dir.mkdir(exist_ok=True)

        self.current_version = self._get_current_version()
        self.local_manifest = self._load_manifest()

    def _get_current_version(self) -> str:
        """Get current app version"""
        try:
            version_file = self.app_path / "lib" / "version.py"
            with open(version_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('__version__'):
                        return line.split('=')[1].strip().strip('"\'')
        except Exception as e:
            print(f"Warning: Could not read version: {e}")
        return "1.0.0"

    def _load_manifest(self) -> Dict:
        """Load local manifest.json"""
        try:
            if self.manifest_path.exists():
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load manifest: {e}")
        return {"version": self.current_version, "files": {}}

    def check_for_updates(self) -> Optional[UpdateInfo]:
        """
        Check if new version is available
        Returns UpdateInfo if update found, None otherwise
        """
        try:
            self.status_changed.emit("Checking for updates...")

            response = requests.get(self.GITHUB_API, timeout=self.TIMEOUT)
            response.raise_for_status()
            release = response.json()

            latest_version = release['tag_name'].lstrip('v')
            latest_url = release['html_url']

            # Compare versions
            if self._compare_versions(latest_version, self.current_version) <= 0:
                self.status_changed.emit("You are running the latest version")
                return None

            # Fetch manifest for the new version
            manifest = self._fetch_remote_manifest(latest_version)
            if not manifest:
                # Fallback: if manifest not available, download full package
                update_info = UpdateInfo(latest_version, "New version available", "full")
                update_info.download_url = latest_url
                return update_info

            # Determine what to download
            changed_files = self._find_changed_files(manifest)
            package_type = self._determine_package(manifest, changed_files)

            update_info = UpdateInfo(
                latest_version,
                release.get('body', 'No changelog available'),
                package_type
            )
            update_info.changed_files = changed_files
            update_info.file_size = self._get_package_size(manifest, package_type)
            update_info.download_url = self._get_download_url(release, package_type, latest_version)

            self.update_available.emit(update_info)
            return update_info

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to check updates: {str(e)}"
            self.error.emit(error_msg)
            return None

    def download_and_apply(self, update_info: UpdateInfo) -> bool:
        """
        Download and apply update
        Returns True if successful, False otherwise
        """
        try:
            # Download
            if not self._download_package(update_info):
                return False

            # Extract
            if not self._extract_package(update_info):
                return False

            # Create backup
            self._backup_current_app()

            # Apply update
            if not self._apply_update(update_info):
                return False

            # Create restart script
            self._create_restart_script()

            self.update_complete.emit()
            return True

        except Exception as e:
            error_msg = f"Update failed: {str(e)}"
            self.error.emit(error_msg)
            return False

    def _fetch_remote_manifest(self, version: str) -> Optional[Dict]:
        """Fetch manifest.json from GitHub release"""
        try:
            # Try to get manifest from release assets
            url = f"https://api.github.com/repos/AHSO-CO-LTD/OCR_DETECTION/releases/tags/v{version}"
            response = requests.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
            release = response.json()

            # Look for manifest in assets
            for asset in release.get('assets', []):
                if asset['name'] == f"manifest-v{version}.json":
                    manifest_url = asset['browser_download_url']
                    manifest_response = requests.get(manifest_url, timeout=self.TIMEOUT)
                    manifest_response.raise_for_status()
                    return manifest_response.json()

            return None

        except Exception as e:
            print(f"Warning: Could not fetch remote manifest: {e}")
            return None

    def _find_changed_files(self, remote_manifest: Dict) -> list:
        """Compare local and remote manifests, return changed files"""
        changed = []
        local_files = self.local_manifest.get('files', {})
        remote_files = remote_manifest.get('files', {})

        for file_path, file_info in remote_files.items():
            local_hash = local_files.get(file_path, {}).get('hash', '')
            remote_hash = file_info.get('hash', '')

            if local_hash != remote_hash:
                changed.append(file_path)

        return changed

    def _determine_package(self, manifest: Dict, changed_files: list) -> str:
        """Determine whether to download core or full package"""
        packages = manifest.get('packages', {})
        core_files = set()
        deps_files = set()

        # Collect files by package
        for file_path, file_info in manifest.get('files', {}).items():
            pkg = file_info.get('package', 'core')
            if pkg == 'core':
                core_files.add(file_path)
            elif pkg == 'deps':
                deps_files.add(file_path)

        changed_set = set(changed_files)

        # If only core files changed, download core
        if changed_set.issubset(core_files):
            return "core"

        # If deps changed, download full (safer)
        if any(f in deps_files for f in changed_set):
            return "full"

        return "core"

    def _get_package_size(self, manifest: Dict, package_type: str) -> int:
        """Get download size for package type"""
        packages = manifest.get('packages', {})
        return packages.get(package_type, {}).get('size', 0)

    def _get_download_url(self, release: dict, package_type: str, version: str) -> str:
        """Get GitHub download URL for package"""
        asset_name = f"DRB-OCR-AI-v{version}-{package_type}.zip"

        for asset in release.get('assets', []):
            if asset['name'] == asset_name:
                return asset['browser_download_url']

        # Fallback to full package
        asset_name = f"DRB-OCR-AI-v{version}-full.zip"
        for asset in release.get('assets', []):
            if asset['name'] == asset_name:
                return asset['browser_download_url']

        return ""

    def _download_package(self, update_info: UpdateInfo) -> bool:
        """Download update package"""
        try:
            if not update_info.download_url:
                raise ValueError("No download URL available")

            self.status_changed.emit(f"Downloading {update_info.package_type} package...")

            file_path = self.update_dir / f"update-{update_info.version}.zip"

            response = requests.get(
                update_info.download_url,
                timeout=self.TIMEOUT,
                stream=True
            )
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)

            self.status_changed.emit("Download complete")
            return True

        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self.error.emit(error_msg)
            return False

    def _extract_package(self, update_info: UpdateInfo) -> bool:
        """Extract update package"""
        try:
            self.status_changed.emit("Extracting update files...")

            file_path = self.update_dir / f"update-{update_info.version}.zip"
            extract_path = self.update_dir / "extracted"

            if extract_path.exists():
                shutil.rmtree(extract_path)
            extract_path.mkdir(parents=True)

            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            self.status_changed.emit("Extraction complete")
            return True

        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            self.error.emit(error_msg)
            return False

    def _backup_current_app(self):
        """Create backup of current app before updating"""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)

            # Backup only app directory, not dependencies
            backup_app = self.backup_dir / "app"
            backup_app.mkdir(parents=True)

            # Backup important files only
            for item in ['DRB-OCR-AI.exe', 'lib', 'form_UI']:
                src = self.app_path / item
                dst = backup_app / item
                if src.exists():
                    if src.is_dir():
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)

            print(f"Backup created at {self.backup_dir}")

        except Exception as e:
            print(f"Warning: Backup failed: {e}")

    def _apply_update(self, update_info: UpdateInfo) -> bool:
        """Apply extracted update to app directory"""
        try:
            self.status_changed.emit("Applying updates...")

            extract_path = self.update_dir / "extracted"
            src_app = extract_path / "DRB-OCR-AI" if (extract_path / "DRB-OCR-AI").exists() else extract_path

            # Copy files, overwriting existing
            for item in src_app.iterdir():
                dst = self.app_path / item.name
                if item.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)

            # Update local manifest
            remote_manifest_path = src_app / "manifest.json"
            if remote_manifest_path.exists():
                shutil.copy2(remote_manifest_path, self.manifest_path)

            self.status_changed.emit("Updates applied successfully")
            return True

        except Exception as e:
            error_msg = f"Apply failed: {str(e)}"
            self.error.emit(error_msg)
            return False

    def _create_restart_script(self):
        """Create batch script to restart application"""
        try:
            script_path = self.app_path / "restart.bat"

            # Get exe name and path
            exe_name = "DRB-OCR-AI.exe"
            exe_path = self.app_path / exe_name

            script_content = f"""@echo off
REM Wait for app to close
timeout /t 2 /nobreak

REM Clean up temp files
if exist "{self.update_dir}" (
    rmdir /s /q "{self.update_dir}"
)

REM Start application
cd /d "{self.app_path}"
start "" "{exe_path}"

REM Delete this script
del "%~f0"
"""

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            print(f"Restart script created: {script_path}")

        except Exception as e:
            print(f"Warning: Could not create restart script: {e}")

    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """
        Compare two semantic versions
        Returns: 1 if v1 > v2, -1 if v1 < v2, 0 if equal
        """
        from packaging import version
        try:
            ver1 = version.parse(v1)
            ver2 = version.parse(v2)
            if ver1 > ver2:
                return 1
            elif ver1 < ver2:
                return -1
            return 0
        except Exception:
            return 0

    def trigger_restart(self):
        """Trigger application restart"""
        try:
            script_path = self.app_path / "restart.bat"
            if script_path.exists():
                # Start batch script and exit app
                subprocess.Popen(
                    [str(script_path)],
                    cwd=str(self.app_path),
                    shell=True
                )
                # Exit current application
                sys.exit(0)
        except Exception as e:
            print(f"Error triggering restart: {e}")
            self.error.emit(f"Failed to restart: {str(e)}")

    def run(self):
        """QThread run method - check for updates"""
        self.check_for_updates()


if __name__ == "__main__":
    # Test
    updater = DeltaUpdater()
    print(f"Current version: {updater.current_version}")
    updater.check_for_updates()
