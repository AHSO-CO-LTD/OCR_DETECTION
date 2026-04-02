# Changelog

All notable changes to OCR-Metal-Core-Washing will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
