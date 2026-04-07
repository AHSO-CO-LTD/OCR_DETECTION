# OCR Detection System - Deployment Guide (v1.1.0+)

Complete deployment instructions for OCR Detection System with Phase 6 performance optimization.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [PLC Integration](#plc-integration)
6. [Camera Setup](#camera-setup)
7. [Database Setup](#database-setup)
8. [Verification](#verification)
9. [Performance Monitoring](#performance-monitoring)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Hardware
- [ ] Industrial PC with Windows 10/11 (64-bit)
- [ ] Minimum: Intel i7 / AMD Ryzen 5, 16GB RAM, 256GB SSD
- [ ] Recommended: Intel i9 / Ryzen 9, 32GB RAM, 512GB SSD
- [ ] NVIDIA GPU (optional, for faster inference)

### Network & Connectivity
- [ ] PLC connected to same network (Modbus TCP) or serial port (RTU)
- [ ] Camera connected via USB or Gigabit Ethernet
- [ ] Network stability (low packet loss, latency < 10ms to PLC)
- [ ] Firewall allows MySQL port 3306 (if remote database)

### Software
- [ ] Python 3.9+ installed (if building from source)
- [ ] PyQt5 5.15.0+ (included in installer)
- [ ] NVIDIA drivers (if using GPU)

### Licensing
- [ ] HASP Sentinel hardware dongle connected and recognized
- [ ] License file present and valid

---

## System Requirements

### Minimum (Basic Operations)
```
OS:            Windows 10/11 (64-bit)
CPU:           Intel i7 or AMD Ryzen 5 (4-core)
RAM:           16 GB DDR4
Storage:       256 GB SSD (C: drive)
GPU:           Optional (CPU inference works)
Network:       Gigabit Ethernet
```

### Recommended (Production)
```
OS:            Windows Server 2019+ or Windows 10 Pro
CPU:           Intel i9 or AMD Ryzen 9 (8+ cores)
RAM:           32 GB DDR4
Storage:       512 GB SSD (fast I/O for logging)
GPU:           NVIDIA RTX 3080+ (12GB+ VRAM)
Network:       Dedicated Gigabit Ethernet
Monitor:       24"+ 1080p or higher
```

### v1.1.0 Phase 6 Performance Improvements

The event-driven polling in v1.1.0 provides:

| Metric | Improvement | Benefit |
|--------|------------|---------|
| **CPU Usage** | 10% reduction | Lower heat, longer hardware lifespan |
| **UI Responsiveness** | 2.8x smoother | Better operator experience |
| **Latency** | 64% less jitter | More consistent performance |
| **Memory** | Zero allocation churn | Stable memory usage |

**Result:** Significantly lower resource consumption, especially on the polling thread.

---

## Installation Steps

### Step 1: Download Installer

1. Go to GitHub Releases: https://github.com/AHSO-CO-LTD/OCR_DETECTION/releases
2. Download latest `.exe` installer (v1.1.0+)
3. Verify file size (typically 200-300 MB)

### Step 2: Run Installer

```bash
# Option A: Run installer directly
DRB-OCR-AI-v1.1.0.exe

# Option B: Command-line installation
DRB-OCR-AI-v1.1.0.exe /S /D=C:\OCR-Detection
```

**Installation Location:** `C:\OCR-Detection\` (recommended)

### Step 3: Create Configuration File

Copy `config.yaml.example` to `config.yaml`:

```bash
cd C:\OCR-Detection
copy config.yaml.example config.yaml
```

Edit `config.yaml` with your settings (see Configuration section below).

### Step 4: Start Application

```bash
# From Start Menu
OCR Detection System

# Or command-line
C:\OCR-Detection\OCR Detection.exe
```

---

## Configuration

### config.yaml Structure

```yaml
# Database Configuration
database:
  host: "192.168.3.100"      # MySQL server IP
  port: 3306
  username: "ocr_user"       # MySQL username
  password: "secure_password" # Change this!
  database: "DRB_Metalcore"

# Camera Configuration
camera:
  provider: "basler"         # or "mindvision"
  exposure_time_ms: 10
  gain_db: 5.0

# PLC Configuration
plc:
  protocol: "modbus_tcp"     # or "modbus_rtu", "slmp"
  host: "192.168.3.250"      # PLC IP (Modbus TCP)
  port: 502
  timeout: 5.0
  retries: 3

# UI Settings
ui:
  screen_width: 1920
  screen_height: 1080
  full_screen: false
```

### Security Best Practices

1. **Database Credentials**
   ```yaml
   # ❌ DON'T: Hardcode passwords
   password: "admin123"

   # ✅ DO: Use environment variables
   password: ${DB_PASSWORD}  # Set via environment
   ```

2. **File Permissions**
   ```bash
   # Restrict config.yaml access
   icacls config.yaml /grant:r "%USERNAME%:F" /inheritance:r
   ```

3. **Credentials Storage**
   - Store in Windows Credential Manager
   - Or use environment variables
   - Never commit credentials to git

---

## PLC Integration

### Modbus TCP Setup

**Hardware Connection:**
1. Connect PLC to network via Ethernet
2. Note PLC's IP address (e.g., `192.168.3.250`)
3. Verify network connectivity:
   ```bash
   ping 192.168.3.250
   ```

**Software Configuration:**
```yaml
plc:
  protocol: "modbus_tcp"
  host: "192.168.3.250"
  port: 502
```

### Modbus RTU Setup

**Hardware Connection:**
1. Connect PLC to serial port (COM3, COM4, etc.)
2. Check Device Manager for port number
3. Verify serial cable quality (shielded recommended)

**Software Configuration:**
```yaml
plc:
  protocol: "modbus_rtu"
  port: "COM3"
  baudrate: 9600
```

### SLMP Setup (Mitsubishi)

**Hardware Connection:**
1. Configure Mitsubishi Q-series/L-series IP address
2. Connect via Ethernet

**Software Configuration:**
```yaml
plc:
  protocol: "slmp"
  host: "192.168.3.250"
  port: 5000
```

### Signal Mapping

| Signal | Type | Function |
|--------|------|----------|
| **M0** | Input | Trigger image capture |
| **M1** | Input | Machine stop signal |
| **M2** | Input | Machine run signal |
| **M100** | Output | Lighting control |
| **M101** | Output | Pass/Fail result |

### Phase 6 Auto-Reconnect

v1.1.0 includes intelligent reconnection:

- **Adaptive Backoff:** Automatically increases polling interval when PLC is unreachable
- **Retry Prevention:** Reduces network traffic by 98% during disconnections
- **Automatic Recovery:** Resumes normal polling when PLC comes back online
- **No Configuration Needed:** Works out-of-the-box

**Monitoring:**
```python
# Check PLC connection status
app.PLC.is_connected()  # Returns: True/False

# Get polling statistics
stats = app.PLC.get_poll_stats()
print(f"Polls: {stats['total_polls']}")
print(f"Errors: {stats['total_errors']}")
print(f"Interval: {app.PLC.get_current_poll_interval()}ms")
```

---

## Camera Setup

### Basler pylon

```bash
# Install pylon runtime
# Download from: https://www.baslerweb.com/en/products/software/basler-pylon-camera-software/

# Install pypylon
pip install pypylon
```

**Configuration:**
```yaml
camera:
  provider: "basler"
  exposure_time_ms: 10
  gain_db: 5.0
```

### MindVision MVSDK

```bash
# Download MVSDK from MindVision website
# Install SDK to: C:\Program Files\MindVision\

pip install opencv-python
```

**Configuration:**
```yaml
camera:
  provider: "mindvision"
  exposure_time_ms: 8
```

---

## Database Setup

### Prerequisites

- MySQL 8.0+ server
- Database admin access
- Network connectivity to database server

### Step 1: Create Database

```sql
-- Connect to MySQL as admin
mysql -u root -p

-- Create database
CREATE DATABASE DRB_Metalcore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'ocr_user'@'%' IDENTIFIED BY 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DRB_Metalcore.* TO 'ocr_user'@'%';
FLUSH PRIVILEGES;
```

### Step 2: Initialize Tables

Tables are automatically created on first run by the ORM (peewee).

**Initial users:**
```sql
-- Default credentials (CHANGE ON FIRST LOGIN!)
-- Admin: admin / Admin@DRB2024!
-- Operator: operator1 / Oper@DRB2024!
```

### Step 3: Verify Connection

```bash
# Test from application startup
# App will show error if database unreachable
```

---

## Verification

### Pre-Production Testing

**1. Startup Check**
```
✅ Application launches without errors
✅ No error dialogs on startup
✅ Hardware dongle recognized
```

**2. Database Connectivity**
```
✅ Login screen works
✅ Main screen loads without database errors
✅ Settings can be saved
```

**3. Camera Verification**
```
✅ Camera detected and connected
✅ Live video feed displays
✅ Frame rate ≥ 30 FPS
```

**4. PLC Connectivity**
```
✅ PLC connection established
✅ Signal M0 (capture) works
✅ Signal M101 (result) sends correctly
✅ Reconnection works (unplug ethernet, reconnect)
```

**5. Performance Metrics (v1.1.0)**
```
✅ CPU usage: < 50% (10% reduction from v1.0.0)
✅ Memory: Stable (no leaks over 1 hour)
✅ Latency: < 3ms jitter (64% improvement)
✅ UI responsiveness: Smooth during inference
```

---

## Performance Monitoring

### Phase 6 Optimization Metrics

**Monitoring PLC Polling:**

```python
# In application, access polling stats:
from lib.QTimerPLCController import QTimerPLCController

plc = QTimerPLCController()
stats = plc.get_poll_stats()

print(f"Total polls: {stats['total_polls']}")
print(f"Total errors: {stats['total_errors']}")
print(f"Current interval: {plc.get_current_poll_interval()}ms")
```

**Expected Values (v1.1.0):**
```
Normal operation:
- Current interval: 1-5ms (adaptive)
- Error rate: < 1%
- CPU usage: 10-30% (polling thread only)

Under network stress:
- Current interval: Auto-backs off to 50-100ms
- Error rate: Increases temporarily
- CPU usage: Drops as interval increases (retry storm prevented)
```

### Monitoring Tools

**Windows Task Manager:**
1. Open Task Manager
2. Go to "Processes" tab
3. Find "OCR Detection" process
4. Monitor: CPU %, Memory, Disk I/O

**Advanced Monitoring:**
```bash
# Via command line
tasklist | findstr "OCR Detection"
taskkill /IM "OCR Detection.exe" /F  # Force terminate if needed
```

---

## Troubleshooting

### Issue: "Could not find hardware dongle"

**Cause:** HASP Sentinel key not connected or drivers missing

**Solution:**
1. Check USB connection
2. Install HASP Sentinel drivers
3. Restart application
4. Check Device Manager for "HASP Sentinel" device

### Issue: "Database connection failed"

**Cause:** MySQL server unreachable or credentials wrong

**Solution:**
1. Verify MySQL server is running
2. Check config.yaml credentials
3. Test network connectivity: `ping <database-host>`
4. Check firewall allows port 3306

### Issue: "Camera not detected"

**Cause:** Camera drivers missing or USB connection issue

**Solution:**
1. Check USB cable connection
2. Install camera drivers:
   - Basler: pylon software
   - MindVision: MVSDK
3. Restart application
4. Check Device Manager for camera

### Issue: "PLC connection failed, retrying..."

**Cause:** PLC unreachable or network issue (EXPECTED behavior in v1.1.0)

**Solution:**
1. Check PLC network connectivity: `ping <plc-ip>`
2. Verify PLC IP in config.yaml
3. Check Modbus port (502 for TCP, COM port for RTU)
4. Application will auto-reconnect when PLC is available
5. Monitor polling interval in logs (backs off during disconnection)

### Issue: "High CPU usage"

**Cause:** GPU-accelerated inference or excessive logging

**Solution:**
1. Check Task Manager for CPU-intensive process
2. Disable debug logging in settings
3. Update GPU drivers (if using GPU)
4. Reduce inference batch size

---

## Support & Maintenance

### Regular Maintenance

**Weekly:**
- Check application logs for errors
- Monitor database size
- Verify PLC connection stability

**Monthly:**
- Backup database
- Review audit trail logs
- Update Windows/drivers

**Quarterly:**
- Full system performance test
- Database optimization (ANALYZE tables)
- Review security logs

### Getting Help

- Check README.md for general information
- Review CHANGELOG.md for v1.1.0 improvements
- See PHASE_6_BENCHMARK.md for performance details
- Contact: support@ahso-co.com

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **1.1.0** | 2026-04-07 | Phase 6: QTimer polling (10% CPU reduction) |
| **1.0.0** | 2026-04-02 | Initial production release |

---

## License

Proprietary - AHSO Co., Ltd.

For commercial use, contact: sales@ahso-co.com
