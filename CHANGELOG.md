# Changelog

All notable changes to OCR-Metal-Core-Washing will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-04-10

### Added - Intelligent Delta Update System ✨
- **Online Installer:** Lightweight installer (~2-3 MB) that downloads latest version during installation
- **Auto-Update Notifications:** Automatic version check 3 seconds after app launch
- **One-Click Updates:** Single button to download and apply updates automatically
- **Delta/Incremental Updates:** Manifest-based change detection (SHA256 hashes)
  - Core updates (~10-20 MB) for code-only changes
  - Full updates (~350 MB) when dependencies change
  - 90% of updates are much faster (30-40 seconds vs 5 minutes)
- **Update UI Components:**
  - UpdateNotificationDialog: Shows version, changelog, and download size
  - UpdateProgressDialog: Live progress bar with speed and ETA
  - Automatic restart after update completion
- **Smart Package Selection:** Intelligently chooses core.zip vs full.zip based on what changed
- **Automatic Backup:** Backup created before applying updates for safety
- **CI/CD Integration:** Manifest generation and package splitting automated in GitHub Actions

### Technical Details
- **lib/Updater.py** (462 lines): Core delta update engine with QThread signals
- **lib/UpdateDialog.py** (292 lines): PyQt5 dialogs for update notification and progress
- **lib/UpdateChecker.py** (133 lines): Integration layer with DeltaUpdater
- **scripts/generate_manifest.py** (213 lines): CI/CD manifest and package generator
- **installer/DRB-OCR-AI.iss**: Inno Setup online installer configuration

### Performance Impact
- **Initial Download:** 300 MB → 2-3 MB (100x smaller)
- **Typical Update:** 5 minutes → 30-40 seconds (8x faster)
- **Code Update Size:** 350 MB → 15-20 MB (17x smaller)
- **Installation:** Fully automatic, no manual steps needed

### Documentation
- **UPDATE_SYSTEM.md:** Complete architecture and usage guide
- **TEST_UPDATE_SYSTEM.md:** Comprehensive test results (13+ tests passed)
- **CODE_REVIEW.md:** Detailed code review and quality metrics
- **RELEASE_PREPARATION.md:** Release checklist and verification steps

### Security
- HTTPS-only downloads from GitHub
- SHA256 hash validation for file integrity
- Automatic backup before update
- Safe restart via batch script (no injection attacks)
- Proper error handling with fallback to full package

### Testing
- 13+ automated test cases (all passed ✅)
- Core logic tests: Version comparison, file categorization, delta detection
- Update simulation: Full v1.1.0 → v1.2.0 scenario tested
- Error handling: Network timeout, corruption, permission denied verified
- Integration: UpdateChecker, DeltaUpdater, UpdateDialog confirmed working

### Changed
- UpdateChecker now shows interactive UpdateDialog instead of simple message box
- Application startup includes automatic update check
- Update check runs in background thread (non-blocking)

### Fixed
- Optional imports: pypylon and pymcprotocol now gracefully handle missing SDKs
- Camera_Program.py: Basler camera now optional, shows clear error if not installed
- main.py: Optional imports wrapped in try-except blocks

---

## [1.1.0] - 2026-04-07

### Added
- **Performance:** Phase 6 QTimer-based non-blocking PLC polling
  - Replaces blocking `time.sleep(0.002)` with event-driven PyQt5 QTimer
  - AdaptiveQTimerPollHandler with automatic interval adjustment (1-100ms)
  - Speedup on success (10 consecutive reads → reduce interval by 10%)
  - Backoff on error (3 consecutive failures → increase interval by 50%)
- **Performance:** Batch PLC polling support (BatchQTimerPollHandler)
- **Optimization:** QTimerPLCController as drop-in replacement for blocking PLCController
- **Testing:** 26 comprehensive unit tests for QTimer polling (81% coverage)
- **Documentation:** PHASE_6_BENCHMARK.md with detailed performance analysis

### Performance Improvements
- **CPU:** 10% reduction (87.5-90.2% vs 100% baseline)
- **UI Responsiveness:** 2.8x smoother (45ms → 16ms frame time)
- **Latency Jitter:** 64% improvement (±1.2ms → ±0.2ms)
- **Memory:** Zero allocation churn during polling
- **Network:** 98% fewer packets on PLC reconnect (prevents retry storms)

### Changed
- MainScreen.py now uses QTimerPLCController instead of blocking PLCController
- All signal interface remains identical (backward compatible)
- PLC polling is now event-driven with adaptive intervals

### Technical Details
- QTimerPollHandler: Basic non-blocking polling (280 lines)
- QTimerPLCController: Drop-in replacement for PLCController (280 lines)
- BatchQTimerPollHandler: Batch processing support
- Adaptive algorithm: BACKOFF_MULTIPLIER=1.5, SPEEDUP_DIVISOR=1.1

---

## [1.0.0] - 2026-04-02

### Added
- **Security:** Bcrypt password hashing (no more plaintext passwords)
- **Security:** Column name validation in ORM to prevent SQL injection
- **Security:** Session token + 8-hour expiry for user sessions
- **Audit Trail:** Enabled LoginAudit & AuditTrial tables for 21CFR Part 11 compliance
- **Configuration:** External config.yaml for database credentials (no longer hardcoded)
- **Code Quality:** Named constants for magic numbers (EXPECTED_QUANTITY, NG_FRAME_THRESHOLD, AUTO_STOP_TIMEOUT_MS)
- **Code Quality:** Centralized button stylesheets as class constants
- **PLC:** Auto-reconnect logic when connection fails (50 consecutive failures threshold)
- **Documentation:** Comprehensive README with system architecture, setup, and deployment instructions
- **.gitignore:** Proper ignore patterns for credentials, model weights, cython builds

### Fixed
- **Critical:** catch_errors decorator was losing function return values (missing return in except block)
- **Code:** Removed 15+ lines of debug code and hardcoded test paths in Display.py

### Changed
- Password validation enforces bcrypt format
- Database connection now reads from config.yaml
- PLC read loop now has reconnect capability for robustness

### Security
- 🔒 No more hardcoded database credentials in source
- 🔒 Passwords hashed with bcrypt (12 salt rounds)
- 🔒 Session tokens generated with secrets.token_hex(32)
- 🔒 SQL injection protection via column name whitelist validation
- 🔒 Audit trail fully enabled for compliance

---

## Release Process

### Creating a new release:

1. Update version in `lib/version.py`:
   ```
   __version__ = "1.X.0"
   ```

2. Update CHANGELOG.md with new section:
   ```
   ## [1.X.0] - YYYY-MM-DD
   ### Added
   - Feature description
   ```

3. Create git tag:
   ```bash
   git tag v1.X.0
   git push origin v1.X.0
   ```

4. GitHub Actions automatically:
   - Builds Windows EXE via PyInstaller
   - Creates GitHub Release with artifacts
   - Attaches installer to release

5. In-app update checker will notify users of new version

---

## Unreleased

### Planned
- [ ] Session validation check on app startup
- [ ] Auto-update downloader (not just notify)
- [ ] Multi-language UI support
- [ ] Dark mode theme

---

[1.0.0]: https://github.com/AHSO-CO-LTD/OCR-Metal-Core-Washing/releases/tag/v1.0.0
