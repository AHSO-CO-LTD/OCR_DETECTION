"""
Loading Screen with Hardware/IO Validation

Displays connection status for:
- Hardware dongle (HASP Sentinel)
- Configuration file
- Database (MySQL)
- Camera (Basler/MindVision)
- PLC (Modbus/SLMP)

Shows warnings (not blocking) for failed connections.
User can proceed to MainScreen even with some warnings.
"""

import os
import logging
import pymysql
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QMessageBox
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer
)
from PyQt5.QtGui import QFont

from lib.Global import signal, catch_errors
from lib.Database import _load_db_config
from lib.Global import initialize_secure_dongle

# Configure logging
logger = logging.getLogger(__name__)


class CheckerThread(QThread):
    """Background thread for running connection checks"""

    # Signals
    status_update = pyqtSignal(str, str, bool)  # component, status, is_ok
    checks_complete = pyqtSignal(int)  # warning_count

    def __init__(self, config_path="config.yaml"):
        super().__init__()
        self.config_path = config_path
        self.warning_count = 0
        self.checks_completed = 0
        self.total_checks = 5

    def run(self):
        """Run all checks sequentially"""
        self.warning_count = 0

        # Check 1: Dongle
        self._check_dongle()

        # Check 2: Config
        self._check_config()

        # Check 3: Database
        self._check_database()

        # Check 4: Camera
        self._check_camera()

        # Check 5: PLC
        self._check_plc()

        # Emit completion with warning count
        self.checks_complete.emit(self.warning_count)

    def _check_dongle(self):
        """Check hardware dongle (HASP Sentinel)"""
        try:
            result = initialize_secure_dongle()
            if result:
                self.status_update.emit("Hardware Dongle", "[OK]", True)
            else:
                self.status_update.emit("Hardware Dongle", "✗ Not found", False)
                self.warning_count += 1
                logger.warning("Hardware dongle not found")
        except Exception as e:
            logger.exception("Dongle check failed")
            error_msg = str(e)[:40] if len(str(e)) > 40 else str(e)
            self.status_update.emit("Hardware Dongle", f"✗ {error_msg}", False)
            self.warning_count += 1
        self.checks_completed += 1
        self._emit_progress()

    def _check_config(self):
        """Check if config.yaml exists"""
        try:
            if os.path.exists(self.config_path):
                self.status_update.emit("Config File", "[OK]", True)
            else:
                self.status_update.emit("Config File", "✗ Not found", False)
                self.warning_count += 1
                logger.warning(f"Config file not found: {self.config_path}")
        except Exception as e:
            logger.exception("Config check failed")
            self.status_update.emit("Config File", "✗ Error", False)
            self.warning_count += 1
        self.checks_completed += 1
        self._emit_progress()

    def _check_database(self):
        """Check database connectivity"""
        try:
            # Load config
            config = _load_db_config()

            # Try to connect with 10-second timeout
            try:
                with pymysql.connect(
                    host=config.get("host", "localhost"),
                    port=config.get("port", 3306),
                    user=config.get("user", "root"),
                    password=config.get("password", ""),
                    database=config.get("database", "DRB_Metalcore"),
                    connect_timeout=10,
                ) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()

                self.status_update.emit("Database", "[OK]", True)
                logger.info("Database connection successful")

            except pymysql.err.OperationalError as e:
                logger.warning(f"Database connection failed: {e}")
                self.status_update.emit("Database", "✗ Connection failed", False)
                self.warning_count += 1
            except pymysql.err.DatabaseError as e:
                logger.warning(f"Database query failed: {e}")
                self.status_update.emit("Database", "✗ Query failed", False)
                self.warning_count += 1

        except Exception as e:
            logger.exception("Database check failed")
            error_msg = str(e)[:40] if len(str(e)) > 40 else str(e)
            self.status_update.emit("Database", f"✗ {error_msg}", False)
            self.warning_count += 1

        self.checks_completed += 1
        self._emit_progress()

    def _check_camera(self):
        """Check camera availability"""
        try:
            from pypylon import pylon

            # Try to enumerate devices
            tlFactory = pylon.TlFactory.GetInstance()
            devices = tlFactory.EnumerateDevices()

            if len(devices) > 0:
                self.status_update.emit("Camera", "[OK]", True)
                logger.info(f"Camera found: {len(devices)} device(s)")
            else:
                self.status_update.emit("Camera", "✗ Not found", False)
                self.warning_count += 1
                logger.warning("No camera devices found")

        except ImportError:
            logger.warning("Pypylon SDK not installed")
            self.status_update.emit("Camera", "✗ SDK not installed", False)
            self.warning_count += 1
        except Exception as e:
            logger.exception("Camera check failed")
            error_msg = str(e)[:40] if len(str(e)) > 40 else str(e)
            self.status_update.emit("Camera", f"✗ {error_msg}", False)
            self.warning_count += 1

        self.checks_completed += 1
        self._emit_progress()

    def _check_plc(self):
        """Check PLC connectivity"""
        try:
            # Load PLC config
            config = _load_db_config()
            protocol_type = config.get("plc", {}).get("protocol", "modbus_tcp")

            # Check protocol type first to avoid port conversion errors for non-TCP protocols
            if protocol_type in ["modbus_tcp", "TCP"]:
                host = config.get("plc", {}).get("host", "192.168.3.250")
                port = int(config.get("plc", {}).get("port", 502))
                from pymodbus.client import ModbusTcpClient

                client = ModbusTcpClient(host=host, port=port, timeout=10)

                try:
                    result = client.connect()

                    if result:
                        # Try to read a register to verify connection
                        try:
                            response = client.read_coils(address=0, count=1)
                            if response.isError():
                                logger.warning(f"PLC read failed: {response}")
                                self.status_update.emit("PLC", "✗ Read failed", False)
                                self.warning_count += 1
                            else:
                                self.status_update.emit("PLC", "[OK]", True)
                                logger.info("PLC connection successful")
                        except Exception as e:
                            logger.warning(f"PLC read timeout: {e}")
                            self.status_update.emit("PLC", "✗ Read timeout", False)
                            self.warning_count += 1
                    else:
                        logger.warning(f"PLC connection failed: {host}:{port}")
                        self.status_update.emit("PLC", "✗ Connection failed", False)
                        self.warning_count += 1

                finally:
                    # Ensure socket is always closed
                    client.close()

            else:
                # For other protocols (RTU, SLMP), just show as ready
                # and let MainScreen handle actual connection
                logger.info(f"PLC protocol {protocol_type} - manual config")
                self.status_update.emit("PLC", "[READY] (manual config)", True)

        except ImportError:
            logger.warning("Pymodbus not available")
            self.status_update.emit("PLC", "✗ Modbus not available", False)
            self.warning_count += 1
        except Exception as e:
            logger.exception("PLC check failed")
            error_msg = str(e)[:40] if len(str(e)) > 40 else str(e)
            self.status_update.emit("PLC", f"✗ {error_msg}", False)
            self.warning_count += 1

        self.checks_completed += 1
        self._emit_progress()

    def _emit_progress(self):
        """Emit progress update (currently just updates internally)"""
        # Progress is tracked by checks_completed / total_checks
        pass


class LoadingScreen(QWidget):
    """Loading screen with connection status checks"""

    # Signals
    loading_complete = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.warning_count = 0
        self.check_items = {}  # {component_name: label_widget}
        self.checker_thread = None

        self.setWindowTitle("Loading - OCR Detection")
        self.setStyleSheet("background-color: white;")
        self.init_ui()

        # Store reference to self for cleanup
        self._cleanup_on_destroy = True

    def init_ui(self):
        """Initialize UI layout"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Title
        title = QLabel("OCR Detection System")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Initializing...")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        main_layout.addWidget(subtitle)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Check items - initialize dict and add containers to layout
        self.check_items = {}
        for name in ["Hardware Dongle", "Config File", "Database", "Camera", "PLC"]:
            container = self._create_check_item(name)
            main_layout.addWidget(container)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4ad456;
            }
        """
        )
        main_layout.addWidget(self.progress_bar)

        # Status message
        self.status_label = QLabel("Starting checks...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(self.status_label)

        # Warnings label
        self.warnings_label = QLabel("")
        self.warnings_label.setAlignment(Qt.AlignCenter)
        self.warnings_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        main_layout.addWidget(self.warnings_label)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator2)

        # Continue button
        self.continue_button = QPushButton("Continue")
        self.continue_button.setEnabled(False)
        self.continue_button.setMinimumHeight(40)
        self.continue_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4ad456;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3da349;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #999;
            }
        """
        )
        self.continue_button.clicked.connect(self.on_continue)
        main_layout.addWidget(self.continue_button)

        self.setLayout(main_layout)

    def _create_check_item(self, name):
        """Create a check item widget (icon + label + status)"""
        container = QFrame()
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Status label (initially gray ○)
        status_label = QLabel("○")
        status_label.setStyleSheet("color: #999; font-size: 18px; font-weight: bold;")
        status_label.setFixedWidth(25)
        layout.addWidget(status_label)

        # Component name
        name_label = QLabel(name)
        name_font = QFont()
        name_font.setPointSize(11)
        name_label.setFont(name_font)
        name_label.setFixedWidth(150)
        layout.addWidget(name_label)

        # Status text (initially empty)
        status_text = QLabel("")
        status_font = QFont()
        status_font.setPointSize(10)
        status_text.setFont(status_font)
        status_text.setStyleSheet("color: #666;")
        layout.addWidget(status_text)

        container.setLayout(layout)

        # Store references for updates
        self.check_items[name] = {
            "container": container,
            "status_icon": status_label,
            "status_text": status_text,
        }

        return container

    def start_checks(self):
        """Start the checker thread"""
        # Clean up previous thread if it exists
        if self.checker_thread is not None:
            try:
                self.checker_thread.quit()
                self.checker_thread.wait(5000)  # 5 second timeout
            except Exception as e:
                logger.warning(f"Failed to cleanup previous thread: {e}")
            finally:
                self.checker_thread = None

        # Create and start new thread
        self.checker_thread = CheckerThread()
        self.checker_thread.status_update.connect(self.on_status_update)
        self.checker_thread.checks_complete.connect(self.on_checks_complete)
        self.checker_thread.finished.connect(self.on_checker_finished)
        self.checker_thread.start()
        logger.info("Starting connection checks")

    def on_checker_finished(self):
        """Called when checker thread finishes"""
        if self.checker_thread is not None:
            try:
                self.checker_thread.quit()
                self.checker_thread.wait()
            except Exception as e:
                logger.warning(f"Error cleaning up thread: {e}")
            finally:
                self.checker_thread = None

    def closeEvent(self, event):
        """Clean up thread when window closes"""
        if self.checker_thread is not None:
            try:
                self.checker_thread.quit()
                self.checker_thread.wait(5000)
            except Exception as e:
                logger.warning(f"Error closing thread: {e}")
        super().closeEvent(event)

    def on_status_update(self, component, status, is_ok):
        """Handle status update from checker thread"""
        if component not in self.check_items:
            return

        item = self.check_items[component]
        status_icon = item["status_icon"]
        status_text = item["status_text"]

        # Update icon
        if is_ok is True:
            status_icon.setText("[OK]")
            status_icon.setStyleSheet("color: #4ad456; font-size: 18px; font-weight: bold;")
        elif is_ok is False:
            status_icon.setText("✗")
            status_icon.setStyleSheet("color: #ff9800; font-size: 18px; font-weight: bold;")
        else:  # None = checking
            status_icon.setText("⏳")
            status_icon.setStyleSheet("color: #ffb74d; font-size: 18px; font-weight: bold;")

        # Update text
        status_text.setText(status)

        # Update progress
        completed = sum(
            1 for item in self.check_items.values()
            if item["status_icon"].text() in ["[OK]", "[FAIL]"]
        )
        progress = int((completed / 5) * 100)
        self.progress_bar.setValue(progress)

        # Update status message
        self.status_label.setText(f"Checking {component}...")

    def on_checks_complete(self, warning_count):
        """Called when all checks complete"""
        self.warning_count = warning_count

        # Update progress to 100%
        self.progress_bar.setValue(100)

        # Update status message
        if warning_count == 0:
            self.status_label.setText("All systems ready!")
            self.status_label.setStyleSheet("color: #4ad456; font-weight: bold;")
            self.warnings_label.setText("")
        else:
            self.status_label.setText("Ready with warnings")
            self.status_label.setStyleSheet("color: #666;")
            self.warnings_label.setText(f"⚠ {warning_count} connection(s) failed - but you can continue")
            self.warnings_label.setStyleSheet("color: #ff9800; font-weight: bold;")

        # Enable continue button
        self.continue_button.setEnabled(True)

    def on_continue(self):
        """User clicked Continue button"""
        self.loading_complete.emit()


def create_loading_screen(parent=None):
    """Factory function to create and configure LoadingScreen"""
    screen = LoadingScreen(parent)
    return screen
