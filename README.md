# OCR Detection System

AI-powered optical character recognition and defect detection system for industrial metal core washing lines. Integrates computer vision, deep learning inference, and PLC automation for automated quality control.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Security Features](#security-features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Building for Production](#building-for-production)
- [Deployment](#deployment)
- [Database](#database)
- [AI Models](#ai-models)
- [PLC Integration](#plc-integration)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contact](#contact)

---

## Overview

The OCR Detection System is designed to automate quality inspection of metal cores on industrial washing lines. The system:

1. **Captures images** from Basler or MindVision cameras
2. **Detects defects** using YOLO deep learning models
3. **Recognizes characters** via OCR (Optical Character Recognition)
4. **Validates results** against reference standards
5. **Reports pass/fail** status to PLC (Modbus/SLMP)
6. **Logs all data** to MySQL for compliance (21CFR Part 11)

**Target Environment:** Windows 10/11 (64-bit) industrial machines
**Primary Use Case:** Metal core inspection in DRB washing lines

---

## Features

### Core Capabilities

- ✅ **Multi-camera support** (Basler pylon, MindVision MVSDK)
- ✅ **YOLO11 detection** with real-time inference
- ✅ **OCR character recognition** (custom-trained models)
- ✅ **ROI (Region of Interest)** auto-detection
- ✅ **PLC communication** (Modbus TCP/RTU, SLMP Mitsubishi)
- ✅ **Live video feed** with annotations
- ✅ **Defect localization** with bounding boxes

### Security & Compliance

- ✅ **Bcrypt password hashing** (12-round salts)
- ✅ **SQL injection prevention** (column whitelist validation)
- ✅ **Session management** with 8-hour token expiry
- ✅ **Audit trail logging** (LoginAudit & AuditTrial tables)
- ✅ **21CFR Part 11 compliance** ready
- ✅ **Hardware dongle licensing** (HASP Sentinel)
- ✅ **Role-based access control** (Admin, Operator)

### DevOps & Deployment

- ✅ **Automated Windows EXE builds** via PyInstaller
- ✅ **GitHub Actions CI/CD workflow**
- ✅ **Auto-update checker** (GitHub Releases API)
- ✅ **Externalized configuration** (config.yaml)
- ✅ **Single-instance enforcement** (Windows Mutex)
- ✅ **Comprehensive error logging**

### Performance Optimization (v1.1.0+)

- ✅ **Event-driven PLC polling** (QTimer, non-blocking)
- ✅ **Adaptive interval adjustment** (auto-speedup/backoff)
- ✅ **10% CPU reduction** (87.5-90.2% vs baseline)
- ✅ **2.8x smoother UI** (45ms → 16ms frame time)
- ✅ **64% less latency jitter** (±1.2ms → ±0.2ms)
- ✅ **Automatic retry storm prevention**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface (PyQt5)                      │
│  ┌───────────────────┐              ┌───────────────────────┐  │
│  │  Login Screen     │ ────────────→ │  Main Control Panel   │  │
│  │  (2FA ready)      │              │  (Live video + stats) │  │
│  └───────────────────┘              └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           │                                    │
           ├──────────────┬────────────────────┤
           ▼              ▼                      ▼
    ┌──────────────┐ ┌──────────┐  ┌─────────────────────┐
    │ Database     │ │ Camera   │  │ PLC / Sensors       │
    │ (MySQL 8.0) │ │ (Basler) │  │ (Modbus/SLMP)       │
    └──────────────┘ └──────────┘  └─────────────────────┘
           │              │                      │
           └──────────────┴────────────────────┬─┘
                          ▼
                  ┌──────────────────┐
                  │ AI Inference     │
                  │ - YOLO11 detect  │
                  │ - OCR recognize  │
                  │ - Result compare │
                  └──────────────────┘
                          │
                          ▼
                  ┌──────────────────┐
                  │ Result Output    │
                  │ - Pass/Fail      │
                  │ - Defect log     │
                  │ - Statistics     │
                  └──────────────────┘
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **UI Framework** | PyQt5 |
| **AI/ML** | YOLOv11 (Ultralytics), PyTorch 2.0 + CUDA 11.7 |
| **Camera** | Basler (pylon SDK), MindVision (MVSDK) |
| **PLC Protocol** | Modbus TCP/RTU (pymodbus), SLMP (pymcprotocol) |
| **Database** | MySQL 8.0+ (pymysql) |
| **Security** | Bcrypt (12 rounds), secrets module, HASP Sentinel |
| **Image Processing** | OpenCV, cvzone, pyqtgraph |
| **Source Protection** | Cython (.pyd compilation) |
| **Build Tool** | PyInstaller (Windows x64) |
| **OS Target** | Windows 10/11 (64-bit) |
| **Python** | 3.9.x |

---

## Security Features

### Password Management
- Passwords stored as **bcrypt hashes** (never plaintext)
- Hash verification via `check_password()` function
- All new passwords hashed before database insertion
- Login UI never displays password hashes

### Database Security
- **Column name validation** prevents SQL injection attacks
- All model classes enforce `allowed_columns` whitelist
- Raw column names are never interpolated into SQL queries

### Session Management
- Session tokens generated with `secrets.token_hex(32)`
- **8-hour expiry** for all sessions
- Tokens stored in `current_session` table with TTL
- Automatic session cleanup on logout

### Audit Trail (21CFR Part 11)
- **LoginAudit** table logs every login attempt
- **AuditTrial** table logs all data modifications
- Records: UserID, Action, Timestamp, Details, Status
- Immutable logs for compliance verification

### Access Control
- **Administrator** role: cannot be locked out
- **Operator** role: locked after 3 failed login attempts
- Role-based feature access in UI

### Hardware Licensing
- Dongle check via `System8.dll` (HASP Sentinel)
- License validation on startup
- Automatic error reporting if dongle missing

---

## Installation

### System Requirements

- **OS:** Windows 10/11 (64-bit)
- **Python:** 3.9.x (CPython)
- **RAM:** 8 GB minimum (16 GB recommended for CUDA)
- **GPU:** NVIDIA with CUDA 11.7 support (optional, for faster inference)
- **MySQL:** 8.0+ (local or remote)
- **Camera SDK:** Basler pylon or MindVision MVSDK
- **Hardware Dongle:** HASP Sentinel (required for production)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies:**
- `PyQt5` — GUI framework
- `torch` — Deep learning (with CUDA support)
- `ultralytics` — YOLO models
- `opencv-python` — Image processing
- `pymysql` — MySQL connectivity
- `bcrypt` — Password hashing
- `pymodbus` — Modbus protocol
- `pymcprotocol` — Mitsubishi PLC
- `pypylon` — Basler camera SDK
- `packaging` — Version comparison

### Step 2: Camera SDKs

**For Basler:**
```bash
pip install pypylon
```

**For MindVision:**
- Download MVSDK from vendor
- Copy DLLs to `RunTime_Sofware/MVSDK/x64/`

### Step 3: CUDA Support (Optional)

For GPU acceleration, install CUDA 11.7:
```bash
# Download from: https://developer.nvidia.com/cuda-11-7-0-download-archive
# Verify installation:
python -c "import torch; print(torch.cuda.is_available())"
```

---

## Configuration

### 1. Create `config.yaml`

Copy the example configuration:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your environment:

```yaml
database:
  host: "localhost"          # MySQL server address
  port: 3306                 # MySQL port
  user: "root"               # MySQL username
  password: "your_password"  # MySQL password (change immediately!)
  database: "DRB_Metalcore"  # Database name

plc:
  protocol: "modbus_tcp"     # modbus_tcp | modbus_rtu | slmp
  host: "192.168.3.250"      # PLC IP address
  port: 502                  # Modbus TCP port

camera:
  type: "basler"             # basler | mindvision
  trigger_mode: "hardware"   # hardware | software

ai:
  inference_device: "cuda"   # cuda | cpu
  confidence_threshold: 0.5
```

### 2. Database Configuration

Initialize MySQL:

```bash
mysql -u root -p < DRB_Metalcore_text.sql
```

This creates:
- `users` — User accounts (hashed passwords)
- `current_session` — Active sessions with tokens
- `loginaudit` — Login audit trail
- `auditlog` — Data modification audit trail
- `products` — Reference standards
- `test_results` — Detection results

### 3. Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | Admin@DRB2024! | Administrator |
| operator1 | Oper@DRB2024! | Operator |

⚠️ **SECURITY:** Change default passwords immediately after deployment!

---

## Running the Application

### Development Mode

```bash
python main.py
```

The app will:
1. Check for single instance (Windows Mutex)
2. Verify hardware dongle
3. Load configuration from `config.yaml`
4. Show login screen
5. Connect to database, camera, and PLC
6. Load AI models into memory
7. Check for software updates (GitHub Releases)

### Keyboard Shortcuts

- `Ctrl+Q` — Quit application
- `F5` — Refresh live camera feed
- `Space` — Capture single frame
- `Ctrl+R` — Reset system state

### Log Files

- `lib/dongle_log.txt` — Hardware dongle check log
- Windows Event Log — Application errors and warnings

---

## Building for Production

### Step 1: Compile Cython Modules (Optional)

For source code protection, compile Python modules to `.pyd`:

```bash
cd lib
python setup.py build_ext --inplace
# Output: *.cp39-win_amd64.pyd files
```

### Step 2: Build Windows EXE

```bash
pyinstaller main.spec --noconfirm
```

**Output:**
- `dist/DRB-OCR-AI/` — Executable folder
- `dist/DRB-OCR-AI/DRB-OCR-AI.exe` — Main application

**Configuration in `main.spec`:**
- Excluded modules (onnx, transformers, matplotlib) to reduce size
- Included binaries: pypylon DLLs, camera SDKs
- Included data: UI files, icons, model weights, config template
- Hidden imports: all 3rd-party dependencies

### Step 3: Create Installer

```bash
# PowerShell
$version = git describe --tags --always
Compress-Archive -Path dist/DRB-OCR-AI -DestinationPath DRB-OCR-AI-$version.zip
```

Or use NSIS for `.exe` installer (optional).

---

## Deployment

### GitHub Actions Workflow

The repo includes `.github/workflows/build-release.yml` which:

1. **Triggers on:** Git tag push (`v*`) or manual workflow dispatch
2. **Builds:** Windows EXE via PyInstaller on self-hosted runner
3. **Creates:** GitHub Release with ZIP artifact
4. **Auto-generates:** Release notes from commits

### Release Process

```bash
# 1. Update version in lib/version.py
echo '__version__ = "1.1.0"' > lib/version.py

# 2. Update CHANGELOG.md with new features

# 3. Create and push tag
git tag v1.1.0
git push origin v1.1.0

# 4. GitHub Actions automatically builds and releases
# 5. In-app update checker notifies users
```

### Update Checker

The app automatically checks for new versions:

```python
# From lib/UpdateChecker.py
UpdateChecker(current_version="1.0.0", parent=self)
.check_for_updates()  # Runs async, 3s after app startup
```

- Queries GitHub Releases API
- Compares semantic versions
- Shows dialog if update available
- Links to download page

---

## Database

### Schema Overview

**users** — User account management
```sql
id, username, password_hash, role, active, created_at
```

**current_session** — Active sessions with token
```sql
user_id, token, expires_at, ip_address, user_agent, created_at
```

**loginaudit** — Login attempt audit trail
```sql
user_id, username, event_type, ip_address, status, created_at
```

**auditlog** — Data modification audit trail
```sql
username, action, table_name, details, created_at
```

**products** — Reference standards
```sql
id, name, expected_value, tolerance, created_by, created_at
```

**test_results** — Detection results
```sql
id, timestamp, image_path, detected_value, reference_value, pass_fail, details
```

### Backup & Recovery

```bash
# Backup database
mysqldump -u root -p DRB_Metalcore > backup_$(date +%Y%m%d).sql

# Restore from backup
mysql -u root -p DRB_Metalcore < backup_20260402.sql
```

### Query Audit Trail

```sql
-- View recent login attempts
SELECT username, event_type, ip_address, created_at
FROM loginaudit
ORDER BY created_at DESC LIMIT 20;

-- View data modifications
SELECT username, action, table_name, created_at
FROM auditlog
WHERE table_name = 'products'
ORDER BY created_at DESC;
```

---

## AI Models

### Detection Models (YOLO)

The app uses multiple YOLO models for different product lines:

| Model File | Purpose | Accuracy |
|-----------|---------|----------|
| `yolo11n.pt` | Nano baseline (fast) | 78% |
| `BL-40_120_0.995.pt` | BL-40 product line | 99.5% |
| `IS35R_*.pt` | IS35R series variants | 98%+ |
| `SL-*.pt` | SL product line | 97%+ |
| `best_seg.pt` | Instance segmentation | 96% |

### Localization (ROI Detection)

- `Location.pth` — Detects product region
- `Location_OCR2.pth` — OCR field localization

### Character Recognition (OCR)

- `OCV5.th` — 5-digit character model
- `OCV6.th` — 6-digit character model

### Loading Models

```python
# From Display.py
from RunTime_Sofware.Runtime_Software import DeepLearningTool

tool = DeepLearningTool()
tool.load_model("BL-40_120_0.995.pt")  # Load detection model
results = tool.inference(image_array)  # Run inference
```

### Model Training (Custom)

Models are trained externally using:
- `RunTime_Sofware/Runtime_Software.py` — Training interface
- `Deep_Learning_Tool.pyi` — Type hints
- Dataset in `RunTime_Sofware/dataset.yaml`

To use custom models:
1. Train with external tool (e.g., Ultralytics)
2. Export weights to `.pt` format
3. Place in root directory or `RunTime_Sofware/`
4. Update model path in UI

---

## PLC Integration

### Supported Protocols

**1. Modbus TCP**
- Default: IP `192.168.3.250`, Port `502`
- Common industrial standard
- Use for remote PLCs or Ethernet-connected devices

**2. Modbus RTU**
- Serial COM port connection
- Lower latency than TCP
- Use for direct serial connection

**3. SLMP (Mitsubishi)**
- Dedicated protocol for Mitsubishi Q-series, L-series, iQ-R
- Port `5000` (configurable)
- Better real-time performance

### Signal Mapping

**Input Signals (from PLC to App):**
- `M0` — Trigger image capture
- `M1` — Machine stop signal
- `M2` — Machine run signal
- `M100` — Control lighting

**Output Signals (from App to PLC):**
- `M101` — Send pass/fail result

### Configuration

Edit `config.yaml`:

```yaml
plc:
  protocol: "modbus_tcp"
  host: "192.168.3.250"
  port: 502
  timeout: 5.0
  retries: 3
```

Or configure in-app via Settings screen.

### Auto-Reconnect

If PLC connection fails:
- System tracks consecutive failures
- Reconnects after 5 failed attempts (configurable)
- Logs each reconnection attempt
- Shows error notification to operator
- Uses exponential backoff to prevent retry storms

```python
# From lib/QTimerPLCController.py (Phase 6 optimization)
if fail_count >= RECONNECT_THRESHOLD:
    self._try_reconnect()
```

### Performance Optimization (v1.1.0 - Phase 6)

**Event-Driven Non-Blocking Polling**

Version 1.1.0 introduces `QTimerPLCController`, replacing blocking `time.sleep()` with PyQt5's event-driven QTimer:

**Benefits:**
- ✅ **CPU:** 10% reduction (87.5-90.2% vs 100%)
- ✅ **UI Responsiveness:** 2.8x smoother (45ms → 16ms frame time)
- ✅ **Latency:** 64% less jitter (±1.2ms → ±0.2ms)
- ✅ **Memory:** Zero allocation churn during polling
- ✅ **Network:** 98% fewer packets on PLC reconnect

**Adaptive Intervals:**
- Speedup: On 10 consecutive successful reads → reduce interval by 10% (min 1ms)
- Backoff: On 3 consecutive failures → increase interval by 50% (max 100ms)
- Prevents retry storms when PLC is unreachable
- Automatic optimization, no manual tuning needed

**Migration:**
- Drop-in replacement for old `PLCController`
- Same signal interface (backward compatible)
- No code changes needed in MainScreen.py (already integrated)

**Implementation:**
```python
# QTimerPLCController automatically handles:
from lib.QTimerPollHandler import AdaptiveQTimerPollHandler

# Adaptive intervals: 1ms (fast) → 100ms (slow)
self.poll_handler = AdaptiveQTimerPollHandler(
    base_interval_ms=2,
    min_interval_ms=1,
    max_interval_ms=100
)

# On success: speedup
# On error: backoff (prevents retry storms)
```

**Detailed Analysis:**
See [`PHASE_6_BENCHMARK.md`](PHASE_6_BENCHMARK.md) for comprehensive performance metrics, methodology, and real-world impact analysis.

### Testing PLC Connection

```bash
# Test Modbus TCP connection
python -c "
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('192.168.3.250', port=502)
print('Connected:', client.connect())
"
```

---

## Troubleshooting

### Common Issues

**Q: "Could not find hardware dongle"**
- Check HASP Sentinel key is connected
- Reinstall dongle drivers: https://www.thalesgroup.com/
- Run `lib/dongle_log.txt` for details

**Q: "Failed to connect to camera"**
- Verify camera USB connection
- Ensure Basler pylon or MVSDK installed
- Check camera IP (for network cameras)
- Try: `python -c "import pypylon; print(pypylon.GetCamera())"`

**Q: "Database connection error"**
- Verify MySQL is running
- Check credentials in `config.yaml`
- Verify database exists: `mysql -u root -p -e "SHOW DATABASES;"`

**Q: "PLC connection timeout"**
- Verify PLC IP address and port
- Test network connectivity: `ping 192.168.3.250`
- Check PLC firmware/protocol compatibility
- Review `.github/workflows/build-release.yml` for CI/CD details

**Q: "AI inference slow (high latency)"**
- Enable GPU: set `inference_device: "cuda"` in config
- Reduce model size (use nano or small variant)
- Lower input image resolution
- Decrease `confidence_threshold`

**Q: "Application crashes on startup"**
- Check Windows Event Viewer for error logs
- Verify all AI model weights exist
- Try disabling auto-update: modify `lib/Main_Screen.py` line 188
- Run in debug mode: `python main.py` (not EXE)

### Debug Mode

```bash
# Run with verbose logging
python -u main.py 2>&1 | tee debug.log

# Check PyQt5 signal trace
export QT_DEBUG_PLUGINS=1
python main.py
```

### Log Files

- **Dongle:** `lib/dongle_log.txt`
- **Windows:** Event Viewer → Windows Logs → Application
- **Camera:** `lib/camera.log` (if enabled)
- **Database:** MySQL logs at `C:\ProgramData\MySQL\MySQL Server 8.0\data\`

---

## Development

### Project Structure

```
OCR_Detection/
├── main.py                    # Application entry point
├── main.spec                  # PyInstaller configuration
├── requirements.txt           # Python dependencies
├── config.yaml.example        # Configuration template
├── DRB_Metalcore_text.sql     # Database schema
│
├── lib/
│   ├── Global.py              # Global variables, signals, utilities
│   ├── Database.py            # ORM, models, SQL injection prevention
│   ├── Authentication.py      # User management, password hashing
│   ├── Login_Screen.py        # Login UI, session token generation
│   ├── Main_Screen.py         # Main control panel
│   ├── Camera_Program.py      # Camera control (Basler/MindVision)
│   ├── Display.py             # Image display, ROI, AI inference
│   ├── PLC.py                 # PLC communication, auto-reconnect
│   ├── StackUI.py             # UI stacking (Login → Main)
│   ├── UpdateChecker.py       # Auto-update checker (GitHub API)
│   ├── version.py             # Version string
│   ├── System8.dll            # HASP Sentinel dongle driver
│   └── setup.py               # Cython build script
│
├── form_UI/                   # Qt Designer UI files
│   ├── screenLogin.ui         # Login screen
│   ├── screenMain.ui          # Main screen (1280x800)
│   ├── Authentication.ui      # User management
│   └── all-icons/             # Icon assets
│
├── RunTime_Sofware/           # AI/ML runtime
│   ├── Runtime_Software.py    # Deep learning interface
│   ├── Deep_Learning_Tool.pyi # Type hints
│   ├── dataset.yaml           # Model training config
│   └── MVSDK/                 # MindVision camera SDK
│
├── .github/
│   └── workflows/
│       └── build-release.yml  # GitHub Actions CI/CD
│
├── .gitignore                 # Ignore patterns (config.yaml, *.pt)
├── README.md                  # This file
└── CHANGELOG.md               # Release notes and version history
```

### Code Quality

- **Type hints:** Python 3.9+ type annotations used throughout
- **Error handling:** `@catch_errors` decorator for graceful failures
- **Signals:** PyQt5 signals for thread-safe communication
- **Constants:** Magic numbers extracted to class constants
- **Security:** All SQL uses column validation, passwords use bcrypt

### Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally
3. Commit with descriptive message: `git commit -m "feat: add feature"`
4. Push to branch: `git push origin feature/my-feature`
5. Create Pull Request on GitHub

---

## License

**Proprietary Software**

This software is proprietary to AHSO Co., Ltd. Unauthorized copying, modification, or distribution is prohibited.

For licensing inquiries, contact: [support@ahso.co]

---

## Contact

**AHSO Co., Ltd.**
AI/Vision System Development & Integration

- **Email:** support@ahso.co
- **Website:** https://www.ahso.co/
- **GitHub:** https://github.com/AHSO-CO-LTD/OCR_DETECTION

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **1.0.0** | 2026-04-02 | Initial release with security hardening, auto-update, GitHub Actions |
| | | See [CHANGELOG.md](CHANGELOG.md) for detailed history |

---

**Last Updated:** 2026-04-02
**Status:** Production Ready ✅
