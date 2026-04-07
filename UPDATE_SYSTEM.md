# OCR Detection v1.1.0+ - Smart Update & Installation System

## Overview

This document describes the intelligent update system for OCR Detection with three key features:

1. **Small Installer** - Online installer (~2-3 MB) that downloads the application during installation
2. **One-Click Auto-Updates** - Users are notified of updates and can update with a single click
3. **Delta Updates** - Only changed files are downloaded (~10-20 MB for code updates, full package for dependency updates)

---

## Architecture

### Components

#### 1. Core Update Engine (`lib/Updater.py`)

**Class:** `DeltaUpdater`

- **Purpose:** Intelligent update manager with manifest-based delta downloads
- **Features:**
  - Checks GitHub API for latest version
  - Downloads manifest.json to compare local vs remote files
  - Determines optimal package (core.zip or full.zip)
  - Downloads only changed files
  - Applies updates with automatic backup
  - Creates batch script for restart

**Key Methods:**
```python
check_for_updates() -> Optional[UpdateInfo]
  # Returns UpdateInfo if update available

download_and_apply(update_info: UpdateInfo) -> bool
  # Downloads and applies update, returns success status

trigger_restart()
  # Restarts the application safely
```

**Signals:**
- `status_changed(str)` - Status update messages
- `progress(int, int)` - Download progress (current, total)
- `update_available(UpdateInfo)` - New version detected
- `update_complete()` - Update applied successfully
- `error(str)` - Error occurred

#### 2. Update UI (`lib/UpdateDialog.py`)

**Classes:** `UpdateNotificationDialog`, `UpdateProgressDialog`

**UpdateNotificationDialog:**
- Shows available version and changelog
- Displays download size for selected package
- "Update Now" / "Skip for Now" buttons

**UpdateProgressDialog:**
- Live download progress bar (%)
- Download speed (MB/s) and ETA
- Current/total file size
- Cancel button
- Auto-closes 3 seconds after completion

#### 3. Enhanced Update Checker (`lib/UpdateChecker.py`)

- Integrated with `DeltaUpdater`
- Shows new `UpdateDialog` instead of simple message box
- Handles user interactions (update/skip)
- Manages download progress display
- Triggers automatic restart

#### 4. CI/CD Manifest Generator (`scripts/generate_manifest.py`)

**Purpose:** Generates update infrastructure during build process

**Generates:**
- `manifest.json` - File inventory with SHA256 hashes
- `core.zip` - Application code only (~10-20 MB)
- `full.zip` - Complete application with dependencies (~300 MB)

**Usage:**
```bash
python scripts/generate_manifest.py dist/DRB-OCR-AI/ 1.2.0
```

**Output Manifest Structure:**
```json
{
  "version": "1.2.0",
  "generated_date": "2026-04-10T15:30:00",
  "files": {
    "DRB-OCR-AI.exe": {
      "hash": "sha256:abc123...",
      "size": 15728640,
      "package": "core"
    },
    "_internal/torch/lib.dll": {
      "hash": "sha256:def456...",
      "size": 209715200,
      "package": "deps"
    }
  },
  "packages": {
    "core": {
      "size": 15000000,
      "asset": "DRB-OCR-AI-v1.2.0-core.zip"
    },
    "full": {
      "size": 350000000,
      "asset": "DRB-OCR-AI-v1.2.0-full.zip"
    }
  }
}
```

#### 5. Inno Setup Installer (`installer/DRB-OCR-AI.iss`)

**Purpose:** Create lightweight online installer

**Features:**
- Small installer size (~2-3 MB)
- Downloads latest application version from GitHub during installation
- Supports both English and Vietnamese
- Creates desktop/start menu shortcuts
- Registers application in Windows
- Creates necessary directories for updates

**Build:**
```bash
# Requires Inno Setup 6.0+ to be installed
iscc installer/DRB-OCR-AI.iss
```

---

## Update Flow

### Checking for Updates

```
App startup (3 seconds after UI load)
    ↓
UpdateChecker.check_for_updates() [background thread]
    ↓
DeltaUpdater.check_for_updates()
    ├─ Fetch https://api.github.com/repos/AHSO-CO-LTD/OCR_DETECTION/releases/latest
    ├─ Compare version with current (lib/version.py)
    ├─ If newer version found:
    │   ├─ Fetch manifest.json from release assets
    │   ├─ Compare local vs remote manifests
    │   ├─ Determine package type (core vs full)
    │   └─ Emit update_available(UpdateInfo)
    └─ Return UpdateInfo or None

If update available:
    ↓
Show UpdateNotificationDialog
    ├─ Version: v1.2.0
    ├─ Changes: Changelog from GitHub
    ├─ Size: ~8.5 MB (core) or ~350 MB (full)
    └─ Buttons: [Update Now] [Skip for Now]
```

### Downloading & Applying Update

```
User clicks "Update Now"
    ↓
Show UpdateProgressDialog
    ↓
DeltaUpdater.download_and_apply()
    ├─ Download package from GitHub Release
    │   ├─ Progress bar: 0% → 100%
    │   ├─ Speed: 2.3 MB/s (example)
    │   └─ ETA: ~3 seconds
    ├─ Extract files to temp directory
    ├─ Backup current app to backup/
    ├─ Apply files from extracted/ to app/
    ├─ Update local manifest.json
    ├─ Create restart.bat script
    └─ Emit update_complete()

Progress dialog shows completion:
    ├─ ✅ Update completed successfully!
    ├─ Application will restart in 3 seconds...
    └─ Auto-closes after 3s

restart.bat executes:
    ├─ Wait 2 seconds (for app to exit)
    ├─ Clean up temp/ directory
    ├─ Start DRB-OCR-AI.exe
    └─ Delete itself
```

---

## Package Selection Logic

The update system intelligently chooses which package to download:

| Scenario | Package | Size | Download Time |
|----------|---------|------|---|
| Only code files changed | `core.zip` | ~10-20 MB | ~10-30 seconds |
| Dependencies updated (torch, cv2, etc.) | `full.zip` | ~300 MB | ~3-5 minutes |
| First time install | `full.zip` | ~300 MB | N/A |

**Examples:**

```python
# Example 1: Bug fix in lib/Main_Screen.py
changed_files = ["lib/Main_Screen.py"]
# → Download core.zip (~15 MB)

# Example 2: Upgrade torch library version
changed_files = ["_internal/torch/lib/..."]
# → Download full.zip (~300 MB)

# Example 3: Multiple changes
changed_files = ["lib/Main_Screen.py", "lib/Camera_Program.py", "_internal/cv2/..."]
# → Download full.zip (~300 MB) [safer to include all deps]
```

---

## File Structure

```
OCR_DETECTION/
├── lib/
│   ├── Updater.py                 (Core update engine)
│   ├── UpdateDialog.py            (UI dialogs)
│   ├── UpdateChecker.py           (Integration layer)
│   └── version.py                 (Current version)
│
├── scripts/
│   └── generate_manifest.py       (Manifest generator)
│
├── installer/
│   ├── DRB-OCR-AI.iss            (Inno Setup script)
│   ├── license.txt               (License for installer)
│   └── info.txt                  (Installation info)
│
├── .github/workflows/
│   └── build-release.yml         (CI/CD pipeline)
│
└── UPDATE_SYSTEM.md              (This file)
```

---

## Installation Methods

### Method 1: Online Installer (Recommended for End Users)

**Download:** `DRB-OCR-AI-Installer.exe` (~2-3 MB)

**What happens:**
1. User downloads lightweight installer
2. Runs installer
3. Installer downloads latest full package from GitHub
4. Extracts and creates shortcuts
5. Launches application

**Advantages:**
- Smallest download for initial installation
- Always installs latest version
- No separate update step needed

### Method 2: Manual Download (for Offline/Development)

**Download:** `DRB-OCR-AI-v1.2.0-full.zip` (~300 MB)

**Process:**
1. Download ZIP from releases
2. Extract to `C:\OCR-Detection\`
3. Run `DRB-OCR-AI.exe`

**For Updates:**
- Application automatically notifies of updates
- One-click update (uses delta if only code changed)

---

## CI/CD Integration

### GitHub Actions Workflow

The build pipeline automatically:

1. **Build Step (Windows):**
   ```
   PyInstaller build → dist/DRB-OCR-AI/
        ↓
   python scripts/generate_manifest.py dist/DRB-OCR-AI/ 1.2.0
        ↓
   Creates:
   - manifest.json (in dist/DRB-OCR-AI/)
   - DRB-OCR-AI-v1.2.0-core.zip (~10-20 MB)
   - DRB-OCR-AI-v1.2.0-full.zip (~300 MB)
   ```

2. **Release Step (Ubuntu):**
   ```
   Download artifacts from build
        ↓
   Upload to GitHub Release:
   - manifest-v1.2.0.json
   - DRB-OCR-AI-v1.2.0-core.zip
   - DRB-OCR-AI-v1.2.0-full.zip
   - (GitHub generates release notes)
   ```

### Release Process

```bash
# 1. Update version
vim lib/version.py
# Change __version__ = "1.2.0"

# 2. Update changelog
vim CHANGELOG.md
# Add v1.2.0 section with changes

# 3. Commit changes
git add lib/version.py CHANGELOG.md
git commit -m "chore: bump version to 1.2.0"

# 4. Create tag (triggers GitHub Actions)
git tag v1.2.0
git push origin main --tags

# 5. Wait for GitHub Actions to build and release
# → Build job creates packages and manifest
# → Release job uploads to GitHub Release
```

---

## Error Handling & Recovery

### Download Errors

- **Network timeout:** Shows "Download failed. Check your connection and try again."
- **Corrupted file:** Detects via SHA256 hash, retries or falls back to full package
- **Server unavailable:** Returns to main app, user can retry later

### Update Errors

- **Extraction failed:** Shows error, reverts to backed-up version
- **File permissions:** Shows "Permission denied. Run as Administrator."
- **Disk space:** Shows "Insufficient disk space"

### Recovery

All error scenarios:
1. Keep backup in `backup/` directory
2. Show clear error message to user
3. Allow user to retry or continue without update
4. Log error details to `logs/update.log`

---

## Configuration

Update behavior can be customized in `lib/Updater.py`:

```python
class DeltaUpdater:
    GITHUB_API = "https://api.github.com/repos/AHSO-CO-LTD/OCR_DETECTION/releases/latest"
    TIMEOUT = 10  # seconds
    CHUNK_SIZE = 8192  # bytes
```

In `lib/UpdateChecker.py`:

```python
class UpdateChecker:
    TIMEOUT_SECONDS = 10
```

---

## User Experience Timeline

### First Launch After Update Notification

```
T+0:00   → User sees "New version available" dialog
T+0:05   → User clicks "Update Now"
T+0:10   → Download progress dialog appears
T+0:15   → Download starts (~2.3 MB/s)
T+2:40   → Download complete for core.zip (~20 MB)
T+2:50   → Files extracted and applied
T+3:00   → "Update completed! Restarting..." message
T+3:03   → Application automatically restarts
T+3:05   → New version running
```

**Total time for core update:** ~3 minutes
**Total time for full update:** ~5-7 minutes (depends on connection)

---

## Testing

### Test Checklist

- [ ] Check for updates on startup (no internet)
- [ ] Check for updates on startup (with new version available)
- [ ] Click "Update Now" and monitor progress
- [ ] Check download speed/ETA accuracy
- [ ] Verify update applies correctly
- [ ] Verify application restarts
- [ ] Check backup was created in `backup/`
- [ ] Test cancel during download
- [ ] Test network interruption during download
- [ ] Verify manifest.json is updated after update

### Manual Testing

```bash
# Simulate update check
cd OCR_Detection
python -c "from lib.Updater import DeltaUpdater; u = DeltaUpdater(); u.check_for_updates()"

# Generate manifest for testing
python scripts/generate_manifest.py dist/DRB-OCR-AI/ 1.2.0
```

---

## Troubleshooting

### Update Check Not Running

**Problem:** "You are running the latest version" always shown

**Solution:**
1. Check internet connection
2. Verify GitHub API is accessible: `curl https://api.github.com/repos/AHSO-CO-LTD/OCR_DETECTION/releases/latest`
3. Check logs in `app/logs/`

### Update Stuck at Download

**Problem:** Progress bar frozen at 50%

**Solution:**
1. Close and restart application
2. Check internet connection and firewall
3. Manually download from GitHub releases
4. Try again after a few minutes

### Application Won't Start After Update

**Problem:** "Application failed to start"

**Solution:**
1. Restore from backup: `copy backup/app/* app/ /Y`
2. Run application
3. Report issue with `logs/update.log` attached

---

## Future Enhancements

- [ ] Auto-install updates without user prompt (configurable)
- [ ] Pause/resume download capability
- [ ] Verify digital signatures on packages
- [ ] Support for beta/nightly builds
- [ ] Rollback to previous version (easy restore from backup)
- [ ] Update scheduling (e.g., "update at 2 AM")
- [ ] Multi-language changelog display
- [ ] Statistics: track update adoption rates

---

## References

- [GitHub API - Releases](https://docs.github.com/en/rest/releases/releases)
- [Inno Setup Documentation](https://jrsoftware.org/isdocs/)
- [semantic versioning](https://semver.org/)
- [PyQt5 Signals/Slots](https://doc.qt.io/qt-5/signalsandslots.html)

---

## Support

For issues or questions about the update system:
- GitHub Issues: https://github.com/AHSO-CO-LTD/OCR_DETECTION/issues
- Email: support@ahso-co.com

---

**Version:** 1.0
**Last Updated:** 2026-04-10
**Status:** Production Ready ✅
